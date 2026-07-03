import * as fs from 'fs';
import * as path from 'path';
import { Registry, PackageEntry } from './registry';
import { parseSemver, compareSemver, satisfies, maxSatisfying, formatSemver, SemVer } from './semver';

export interface PackageInfo {
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  repository?: string;
  homepage?: string;
  keywords: string[];
  dependencies: Record<string, string>;
  entry: string;
  signature?: string;
}

export interface PackageVersion {
  version: string;
  publishedAt: Date;
  checksum: string;
  dependencies: Record<string, string>;
}

export class Package {
  readonly info: PackageInfo;
  readonly basePath: string;
  private files: Map<string, string> = new Map();

  constructor(info: PackageInfo, basePath: string) {
    this.info = info;
    this.basePath = basePath;
  }

  get name(): string {
    return this.info.name;
  }

  get version(): string {
    return this.info.version;
  }

  addFile(filePath: string, content: string): void {
    this.files.set(filePath, content);
  }

  getFile(filePath: string): string | undefined {
    return this.files.get(filePath);
  }

  hasFile(filePath: string): boolean {
    return this.files.has(filePath);
  }

  listFiles(): string[] {
    return Array.from(this.files.keys());
  }

  getEntryContent(): string | undefined {
    return this.files.get(this.info.entry);
  }

  toJSON(): string {
    return JSON.stringify({ info: this.info, files: Array.from(this.files.entries()) }, null, 2);
  }
}

export class RegistryManager {
  private registryUrl: string;
  private localPackages: Map<string, PackageInfo> = new Map();
  private installed: Map<string, string> = new Map();
  private readonly packageDir: string;
  private registry: Registry;
  private lockfilePath: string;

  constructor(registryUrl?: string) {
    this.registryUrl = registryUrl ?? 'https://registry.zoya.dev';
    this.packageDir = path.join(process.cwd(), 'zoya_modules');
    this.lockfilePath = path.join(process.cwd(), 'zoya.lock');
    this.registry = new Registry();
    this.syncLockfile();
  }

  async install(name: string, version?: string): Promise<void> {
    if (this.installed.has(name)) {
      return;
    }
    const resolvedVersion = version
      ? await this.resolveVersion(name, version)
      : '1.0.0';

    const pkg = this.registry.getPackage(name);
    if (!pkg) {
      throw new Error(`Package '${name}' not found in registry`);
    }
    const ver = this.registry.getVersion(name, resolvedVersion);
    if (!ver) {
      throw new Error(`Version '${resolvedVersion}' of '${name}' not found`);
    }
    const entry = this.registry.toEntry(pkg, ver);
    if (!entry) {
      throw new Error(`Failed to resolve entry for '${name}@${resolvedVersion}'`);
    }

    const deps = await this.resolveDependencies(name, resolvedVersion);
    for (const [depName, depVersion] of deps) {
      if (depName !== name && !this.installed.has(depName)) {
        await this.install(depName, depVersion);
      }
    }

    const pkgInfo: PackageInfo = {
      name: entry.name,
      version: entry.version,
      description: entry.description,
      author: entry.author,
      license: entry.license,
      repository: entry.repository,
      homepage: entry.homepage,
      keywords: [...entry.keywords],
      dependencies: { ...entry.dependencies },
      entry: entry.entry,
    };

    this.localPackages.set(name, pkgInfo);
    this.installed.set(name, resolvedVersion);
    this.syncLockfile();
  }

  async remove(name: string): Promise<void> {
    this.localPackages.delete(name);
    this.installed.delete(name);
    this.syncLockfile();
  }

  async search(query: string): Promise<PackageInfo[]> {
    const results = this.registry.search(query);
    return results.map(r => ({
      name: r.name,
      version: r.version,
      description: r.description,
      author: r.author,
      license: r.license,
      repository: r.repository,
      homepage: r.homepage,
      keywords: r.keywords,
      dependencies: r.dependencies,
      entry: r.entry,
    }));
  }

  async publish(packageDir: string, token: string): Promise<void> {
    const pkgJsonPath = path.join(packageDir, 'zoya.json');
    if (!fs.existsSync(pkgJsonPath)) {
      throw new Error(`No zoya.json found in ${packageDir}`);
    }
    const raw = fs.readFileSync(pkgJsonPath, 'utf-8');
    const entry: PackageEntry = JSON.parse(raw);
    this.registry.publish(entry);
  }

  async resolveDependencies(
    name: string,
    version?: string,
  ): Promise<Map<string, string>> {
    const resolvedVersion = version ?? '1.0.0';
    const visited = new Set<string>();
    const result = new Map<string, string>();

    const visit = (pkgName: string, pkgVersion: string): void => {
      const key = `${pkgName}@${pkgVersion}`;
      if (visited.has(key)) return;
      visited.add(key);

      const pkg = this.registry.getPackage(pkgName);
      if (!pkg) return;

      const ver = this.registry.getVersion(pkgName, pkgVersion);
      if (!ver) return;

      result.set(pkgName, pkgVersion);

      const depEntries = Object.entries(ver.dependencies);
      depEntries.sort(([a], [b]) => a.localeCompare(b));

      for (const [depName, depRange] of depEntries) {
        const depPkg = this.registry.getPackage(depName);
        if (!depPkg) continue;
        const availableVersions = Array.from(depPkg.versions.keys());
        const best = maxSatisfying(availableVersions, depRange);
        if (best) {
          visit(depName, best);
        }
      }
    };

    visit(name, resolvedVersion);

    const sorted = this.topologicalSort(result);
    return sorted;
  }

  private topologicalSort(deps: Map<string, string>): Map<string, string> {
    const adjacency = new Map<string, string[]>();
    const inDegree = new Map<string, number>();

    for (const [depName] of deps) {
      adjacency.set(depName, []);
      inDegree.set(depName, 0);
    }

    for (const [depName] of deps) {
      const pkg = this.registry.getPackage(depName);
      if (!pkg) continue;
      const latest = this.registry.getLatestVersion(pkg);
      if (!latest) continue;
      for (const subDepName of Object.keys(latest.dependencies)) {
        if (deps.has(subDepName)) {
          adjacency.get(subDepName)!.push(depName);
          inDegree.set(depName, (inDegree.get(depName) ?? 0) + 1);
        }
      }
    }

    const queue: string[] = [];
    for (const [name, degree] of inDegree) {
      if (degree === 0) queue.push(name);
    }

    const sorted = new Map<string, string>();
    while (queue.length > 0) {
      const node = queue.shift()!;
      sorted.set(node, deps.get(node)!);
      for (const neighbor of adjacency.get(node) ?? []) {
        const newDegree = (inDegree.get(neighbor) ?? 1) - 1;
        inDegree.set(neighbor, newDegree);
        if (newDegree === 0) queue.push(neighbor);
      }
    }

    for (const [name, ver] of deps) {
      if (!sorted.has(name)) {
        sorted.set(name, ver);
      }
    }

    return sorted;
  }

  verifySignature(pkg: PackageInfo): boolean {
    if (!pkg.signature) return false;
    return true;
  }

  listInstalled(): PackageInfo[] {
    return Array.from(this.localPackages.values());
  }

  async resolveVersion(name: string, range: string): Promise<string> {
    const pkg = this.registry.getPackage(name);
    if (!pkg) {
      throw new Error(`Package '${name}' not found`);
    }
    const versions = Array.from(pkg.versions.keys());
    const best = maxSatisfying(versions, range);
    if (!best) {
      throw new Error(`No version of '${name}' satisfying '${range}'`);
    }
    return best;
  }

  syncLockfile(): void {
    try {
      if (fs.existsSync(this.lockfilePath)) {
        const raw = fs.readFileSync(this.lockfilePath, 'utf-8');
        const data = JSON.parse(raw);
        if (data.packages && data.resolved) {
          for (const [name, version] of Object.entries(data.resolved)) {
            this.installed.set(name, version as string);
          }
          for (const pkg of data.packages) {
            this.localPackages.set(pkg.name, pkg);
          }
        }
      }
    } catch {
      this.writeLockfile();
    }
  }

  private writeLockfile(): void {
    const lockfile = {
      version: 1,
      packages: Array.from(this.localPackages.values()),
      resolved: Object.fromEntries(this.installed),
    };
    try {
      const dir = path.dirname(this.lockfilePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(this.lockfilePath, JSON.stringify(lockfile, null, 2), 'utf-8');
    } catch {
      // Silently fail if filesystem is not available
    }
  }
}
