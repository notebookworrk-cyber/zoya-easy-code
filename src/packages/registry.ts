import { createHash } from 'crypto';

export interface RegistryPackage {
  name: string;
  description: string;
  author: string;
  license: string;
  repository?: string;
  homepage?: string;
  keywords: string[];
  versions: Map<string, RegistryPackageVersion>;
}

export interface RegistryPackageVersion {
  version: string;
  publishedAt: Date;
  checksum: string;
  dependencies: Record<string, string>;
}

export interface PackageEntry {
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
}

const STUB_PACKAGES: PackageEntry[] = [
  {
    name: 'physics',
    version: '1.0.0',
    description: '2D physics engine with rigid body simulation, collision detection, and constraint solving',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/physics',
    homepage: 'https://zoya.dev/packages/physics',
    keywords: ['physics', '2d', 'simulation', 'collision', 'game'],
    dependencies: {},
    entry: 'physics.zoya',
  },
  {
    name: 'http',
    version: '1.0.0',
    description: 'HTTP/1.1 server and client with routing, middleware, and WebSocket support',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/http',
    homepage: 'https://zoya.dev/packages/http',
    keywords: ['http', 'server', 'client', 'rest', 'api', 'websocket'],
    dependencies: {},
    entry: 'http.zoya',
  },
  {
    name: 'json',
    version: '1.0.0',
    description: 'High-performance JSON parser and serializer with streaming support',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/json',
    homepage: 'https://zoya.dev/packages/json',
    keywords: ['json', 'parser', 'serializer', 'data'],
    dependencies: {},
    entry: 'json.zoya',
  },
  {
    name: 'sqlite',
    version: '1.0.0',
    description: 'SQLite3 database binding with prepared statements, transactions, and connection pooling',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/sqlite',
    homepage: 'https://zoya.dev/packages/sqlite',
    keywords: ['sqlite', 'database', 'sql', 'persistence'],
    dependencies: {},
    entry: 'sqlite.zoya',
  },
  {
    name: 'aes',
    version: '1.0.0',
    description: 'AES-256 encryption and decryption with GCM, CBC, and ECB modes',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/aes',
    homepage: 'https://zoya.dev/packages/aes',
    keywords: ['aes', 'encryption', 'crypto', 'security', 'aes-256'],
    dependencies: {},
    entry: 'aes.zoya',
  },
  {
    name: 'zlib',
    version: '1.0.0',
    description: 'Deflate/gzip compression and decompression with streaming and buffer APIs',
    author: 'Zoya Team',
    license: 'MIT',
    repository: 'https://github.com/zoya/zlib',
    homepage: 'https://zoya.dev/packages/zlib',
    keywords: ['zlib', 'compression', 'deflate', 'gzip', 'archive'],
    dependencies: {},
    entry: 'zlib.zoya',
  },
];

function computeChecksum(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

export class Registry {
  private packages: Map<string, RegistryPackage> = new Map();

  constructor() {
    this.seedStubPackages();
  }

  private seedStubPackages(): void {
    for (const entry of STUB_PACKAGES) {
      const versionData = JSON.stringify(entry);
      const versions = new Map<string, RegistryPackageVersion>();
      versions.set(entry.version, {
        version: entry.version,
        publishedAt: new Date('2025-01-01'),
        checksum: computeChecksum(versionData),
        dependencies: { ...entry.dependencies },
      });
      this.packages.set(entry.name, {
        name: entry.name,
        description: entry.description,
        author: entry.author,
        license: entry.license,
        repository: entry.repository,
        homepage: entry.homepage,
        keywords: [...entry.keywords],
        versions,
      });
    }
  }

  contains(name: string): boolean {
    return this.packages.has(name);
  }

  getPackage(name: string): RegistryPackage | undefined {
    return this.packages.get(name);
  }

  getVersion(name: string, version: string): RegistryPackageVersion | undefined {
    return this.packages.get(name)?.versions.get(version);
  }

  getAllVersions(name: string): RegistryPackageVersion[] {
    const pkg = this.packages.get(name);
    if (!pkg) return [];
    return Array.from(pkg.versions.values())
      .sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));
  }

  search(query: string): PackageEntry[] {
    const lower = query.toLowerCase();
    const results: PackageEntry[] = [];
    for (const pkg of this.packages.values()) {
      const entry = this.toEntry(pkg, this.getLatestVersion(pkg));
      if (!entry) continue;
      if (
        pkg.name.toLowerCase().includes(lower) ||
        pkg.description.toLowerCase().includes(lower) ||
        pkg.author.toLowerCase().includes(lower) ||
        pkg.keywords.some(k => k.toLowerCase().includes(lower))
      ) {
        results.push(entry);
      }
    }
    return results;
  }

  publish(entry: PackageEntry): void {
    const versionData = JSON.stringify(entry);
    const versionInfo: RegistryPackageVersion = {
      version: entry.version,
      publishedAt: new Date(),
      checksum: computeChecksum(versionData),
      dependencies: { ...entry.dependencies },
    };

    const existing = this.packages.get(entry.name);
    if (existing) {
      if (existing.versions.has(entry.version)) {
        throw new Error(`Version ${entry.version} of '${entry.name}' already exists`);
      }
      existing.versions.set(entry.version, versionInfo);
    } else {
      const versions = new Map<string, RegistryPackageVersion>();
      versions.set(entry.version, versionInfo);
      this.packages.set(entry.name, {
        name: entry.name,
        description: entry.description,
        author: entry.author,
        license: entry.license,
        repository: entry.repository,
        homepage: entry.homepage,
        keywords: [...entry.keywords],
        versions,
      });
    }
  }

  toEntry(pkg: RegistryPackage, version?: RegistryPackageVersion): PackageEntry | undefined {
    const ver = version ?? this.getLatestVersion(pkg);
    if (!ver) return undefined;
    return {
      name: pkg.name,
      version: ver.version,
      description: pkg.description,
      author: pkg.author,
      license: pkg.license,
      repository: pkg.repository,
      homepage: pkg.homepage,
      keywords: [...pkg.keywords],
      dependencies: { ...ver.dependencies },
      entry: `${pkg.name}.zoya`,
    };
  }

  getLatestVersion(pkg: RegistryPackage): RegistryPackageVersion | undefined {
    let latest: RegistryPackageVersion | undefined;
    for (const ver of pkg.versions.values()) {
      if (!latest || ver.publishedAt > latest.publishedAt) {
        latest = ver;
      }
    }
    return latest;
  }

  verifyChecksum(name: string, version: string, data: string): boolean {
    const ver = this.getVersion(name, version);
    if (!ver) return false;
    return computeChecksum(data) === ver.checksum;
  }
}
