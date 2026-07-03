import { describe, it, expect } from 'vitest';
import { Registry, RegistryPackageVersion, PackageEntry } from '../../src/packages/registry';

describe('Registry', () => {
  let registry: Registry;

  beforeEach(() => {
    registry = new Registry();
  });

  it('contains pre-populated stub packages', () => {
    expect(registry.contains('physics')).toBe(true);
    expect(registry.contains('http')).toBe(true);
    expect(registry.contains('json')).toBe(true);
    expect(registry.contains('sqlite')).toBe(true);
    expect(registry.contains('aes')).toBe(true);
    expect(registry.contains('zlib')).toBe(true);
  });

  it('does not contain unknown packages', () => {
    expect(registry.contains('nonexistent')).toBe(false);
  });

  it('retrieves package metadata', () => {
    const pkg = registry.getPackage('physics');
    expect(pkg).toBeDefined();
    expect(pkg!.name).toBe('physics');
    expect(pkg!.description).toContain('physics engine');
    expect(pkg!.author).toBe('Zoya Team');
    expect(pkg!.license).toBe('MIT');
    expect(pkg!.keywords).toContain('physics');
  });

  it('retrieves specific version of a package', () => {
    const ver = registry.getVersion('json', '1.0.0');
    expect(ver).toBeDefined();
    expect(ver!.version).toBe('1.0.0');
    expect(ver!.checksum).toBeTruthy();
    expect(typeof ver!.checksum).toBe('string');
    expect(ver!.checksum.length).toBeGreaterThan(0);
  });

  it('returns undefined for non-existent version', () => {
    const ver = registry.getVersion('json', '9.9.9');
    expect(ver).toBeUndefined();
  });

  it('lists all versions of a package', () => {
    const versions = registry.getAllVersions('aes');
    expect(versions.length).toBe(1);
    expect(versions[0].version).toBe('1.0.0');
  });

  it('returns empty array for unknown package versions', () => {
    const versions = registry.getAllVersions('nonexistent');
    expect(versions).toEqual([]);
  });

  describe('search', () => {
    it('finds packages by name', () => {
      const results = registry.search('physics');
      expect(results.length).toBe(1);
      expect(results[0].name).toBe('physics');
    });

    it('finds packages by keyword', () => {
      const results = registry.search('encryption');
      expect(results.length).toBeGreaterThanOrEqual(1);
      expect(results.some(r => r.name === 'aes')).toBe(true);
    });

    it('finds packages by description', () => {
      const results = registry.search('compression');
      expect(results.length).toBeGreaterThanOrEqual(1);
      expect(results.some(r => r.name === 'zlib')).toBe(true);
    });

    it('is case insensitive', () => {
      const results = registry.search('JSON');
      expect(results.some(r => r.name === 'json')).toBe(true);
    });

    it('returns empty for no matches', () => {
      const results = registry.search('xyznonexistent12345');
      expect(results.length).toBe(0);
    });

    it('returns multiple matches for broad query', () => {
      const results = registry.search('zoya team');
      expect(results.length).toBeGreaterThanOrEqual(6);
    });
  });

  describe('publish', () => {
    it('publishes a new package', () => {
      const entry: PackageEntry = {
        name: 'newpkg',
        version: '1.0.0',
        description: 'A new package',
        author: 'Test',
        license: 'MIT',
        keywords: ['test'],
        dependencies: {},
        entry: 'newpkg.zoya',
      };
      registry.publish(entry);
      expect(registry.contains('newpkg')).toBe(true);
      const ver = registry.getVersion('newpkg', '1.0.0');
      expect(ver).toBeDefined();
      expect(ver!.checksum).toBeTruthy();
    });

    it('adds a new version to existing package', () => {
      const entry: PackageEntry = {
        name: 'physics',
        version: '2.0.0',
        description: 'Updated physics engine',
        author: 'Zoya Team',
        license: 'MIT',
        keywords: ['physics', '2d'],
        dependencies: {},
        entry: 'physics.zoya',
      };
      registry.publish(entry);
      const versions = registry.getAllVersions('physics');
      expect(versions.length).toBe(2);
      const ver = registry.getVersion('physics', '2.0.0');
      expect(ver).toBeDefined();
    });

    it('throws when publishing duplicate version', () => {
      const entry: PackageEntry = {
        name: 'physics',
        version: '1.0.0',
        description: 'Duplicate',
        author: 'Test',
        license: 'MIT',
        keywords: [],
        dependencies: {},
        entry: 'physics.zoya',
      };
      expect(() => registry.publish(entry)).toThrow('already exists');
    });
  });

  describe('dependency resolution', () => {
    it('returns empty dependencies for stub packages', () => {
      const pkg = registry.getPackage('sqlite');
      const latest = registry.getLatestVersion(pkg!);
      expect(latest).toBeDefined();
      expect(Object.keys(latest!.dependencies).length).toBe(0);
    });

    it('resolves latest version', () => {
      const pkg = registry.getPackage('http');
      const latest = registry.getLatestVersion(pkg!);
      expect(latest).toBeDefined();
      expect(latest!.version).toBe('1.0.0');
    });
  });

  describe('verifyChecksum', () => {
    it('verifies correct checksum', () => {
      const result = registry.verifyChecksum('json', '1.0.0', JSON.stringify({
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
      }));
      expect(result).toBe(true);
    });

    it('fails on incorrect checksum', () => {
      const result = registry.verifyChecksum('json', '1.0.0', 'tampered data');
      expect(result).toBe(false);
    });

    it('returns false for non-existent package', () => {
      const result = registry.verifyChecksum('nonexistent', '1.0.0', 'data');
      expect(result).toBe(false);
    });
  });

  describe('toEntry', () => {
    it('converts registry package to entry', () => {
      const pkg = registry.getPackage('zlib');
      const entry = registry.toEntry(pkg!);
      expect(entry).toBeDefined();
      expect(entry!.name).toBe('zlib');
      expect(entry!.version).toBe('1.0.0');
      expect(entry!.entry).toBe('zlib.zoya');
    });

    it('returns undefined for package without versions', () => {
      const emptyPkg = {
        name: 'empty',
        description: '',
        author: '',
        license: '',
        keywords: [],
        versions: new Map<string, RegistryPackageVersion>(),
      };
      const entry = registry.toEntry(emptyPkg);
      expect(entry).toBeUndefined();
    });
  });
});
