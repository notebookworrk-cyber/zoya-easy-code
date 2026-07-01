export type AssetType = 'texture' | 'audio' | 'font' | 'shader' | 'model' | 'animation' | 'tileset' | 'particle';

export interface AssetMetadata {
  name: string;
  type: AssetType;
  path: string;
  size: number;
  loaded: boolean;
  tags: string[];
}

export type AssetLoadCallback = (asset: unknown, error?: Error) => void;

export class AssetManager {
  private assets: Map<string, AssetMetadata>;
  private loadedAssets: Map<string, unknown>;
  private loadQueue: string[];
  private loading: boolean;

  constructor() {
    this.assets = new Map();
    this.loadedAssets = new Map();
    this.loadQueue = [];
    this.loading = false;
  }

  load<T>(path: string, type: AssetType, callback?: AssetLoadCallback): Promise<T> {
    return new Promise((resolve, reject) => {
      const name = this.extractName(path);

      this.assets.set(name, {
        name,
        type,
        path,
        size: 0,
        loaded: false,
        tags: [],
      });

      const mockAsset = { name, type, path } as unknown as T;

      this.loadedAssets.set(name, mockAsset);
      this.assets.get(name)!.loaded = true;
      this.assets.get(name)!.size = 1024;

      if (callback) {
        callback(mockAsset);
      }
      resolve(mockAsset);
    });
  }

  loadBatch(paths: string[], type: AssetType): Promise<Map<string, unknown>> {
    const promises = paths.map(p => this.load(p, type));
    return Promise.all(promises).then(() => {
      const result = new Map<string, unknown>();
      for (const [name] of this.assets) {
        const meta = this.assets.get(name)!;
        if (meta.type === type && meta.loaded) {
          result.set(name, this.loadedAssets.get(name));
        }
      }
      return result;
    });
  }

  get<T>(name: string): T | undefined {
    return this.loadedAssets.get(name) as T | undefined;
  }

  unload(name: string): void {
    this.loadedAssets.delete(name);
    this.assets.delete(name);
  }

  unloadAll(): void {
    this.loadedAssets.clear();
    this.assets.clear();
    this.loadQueue = [];
  }

  isLoaded(name: string): boolean {
    const meta = this.assets.get(name);
    return meta ? meta.loaded : false;
  }

  getMetadata(name: string): AssetMetadata | undefined {
    return this.assets.get(name);
  }

  getLoadedCount(): number {
    return this.loadedAssets.size;
  }

  getTotalCount(): number {
    return this.assets.size;
  }

  hasTag(tag: string): AssetMetadata[] {
    const results: AssetMetadata[] = [];
    for (const meta of this.assets.values()) {
      if (meta.tags.includes(tag)) {
        results.push(meta);
      }
    }
    return results;
  }

  tag(name: string, tags: string[]): void {
    const meta = this.assets.get(name);
    if (meta) {
      for (const tag of tags) {
        if (!meta.tags.includes(tag)) {
          meta.tags.push(tag);
        }
      }
    }
  }

  private extractName(path: string): string {
    const parts = path.replace(/\\/g, '/').split('/');
    const file = parts[parts.length - 1] || 'unknown';
    return file.replace(/\.[^.]+$/, '');
  }
}
