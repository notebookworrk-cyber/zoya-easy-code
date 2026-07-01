import { randomBytes } from 'crypto';

export interface UploadOptions {
  contentType?: string;
  public?: boolean;
  metadata?: Record<string, string>;
  cacheControl?: string;
  encryptionKey?: string;
}

export interface UploadResult {
  url: string;
  path: string;
  size: number;
  contentType: string;
  etag: string;
  uploadedAt: Date;
}

export interface StorageObject {
  path: string;
  size: number;
  contentType: string;
  etag: string;
  uploadedAt: Date;
  lastModified: Date;
  metadata: Record<string, string>;
}

interface Bucket {
  name: string;
  region: string;
  createdAt: Date;
  objects: Map<string, StorageObject>;
  blobStore: Map<string, Buffer>;
}

class StorageError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'StorageError';
  }
}

function generateEtag(): string {
  return `"${randomBytes(16).toString('hex')}"`;
}

export class StorageService {
  private buckets: Map<string, Bucket> = new Map();

  constructor(private readonly baseUrl: string, private readonly apiKey: string) {
    this.createInternalBucket();
  }

  async upload(
    data: Buffer,
    path: string,
    options?: UploadOptions
  ): Promise<UploadResult> {
    const bucketName = this.resolveBucket(path);
    const bucket = this.getOrCreateBucket(bucketName);
    const objectPath = this.normalizePath(path);
    const now = new Date();

    const object: StorageObject = {
      path: objectPath,
      size: data.length,
      contentType: options?.contentType ?? 'application/octet-stream',
      etag: generateEtag(),
      uploadedAt: now,
      lastModified: now,
      metadata: options?.metadata ?? {},
    };

    bucket.objects.set(objectPath, object);
    bucket.blobStore.set(objectPath, data);

    return {
      url: `${this.baseUrl}/storage/v1/${objectPath}`,
      path: objectPath,
      size: data.length,
      contentType: object.contentType,
      etag: object.etag,
      uploadedAt: now,
    };
  }

  async uploadFromFile(
    filePath: string,
    destPath: string,
    options?: UploadOptions
  ): Promise<UploadResult> {
    const { readFileSync } = await import('fs');
    const data = readFileSync(filePath);
    return this.upload(data, destPath, options);
  }

  async download(path: string): Promise<Buffer> {
    const bucketName = this.resolveBucket(path);
    const bucket = this.getBucket(bucketName);
    const objectPath = this.normalizePath(path);

    const blob = bucket.blobStore.get(objectPath);
    if (!blob) {
      throw new StorageError(`Object not found: ${path}`, 'NOT_FOUND');
    }
    return blob;
  }

  async downloadToFile(path: string, destPath: string): Promise<void> {
    const data = await this.download(path);
    const { writeFile } = await import('fs/promises');
    await writeFile(destPath, data);
  }

  async delete(path: string): Promise<void> {
    const bucketName = this.resolveBucket(path);
    const bucket = this.getBucket(bucketName);
    const objectPath = this.normalizePath(path);

    if (!bucket.objects.has(objectPath)) {
      throw new StorageError(`Object not found: ${path}`, 'NOT_FOUND');
    }

    bucket.objects.delete(objectPath);
    bucket.blobStore.delete(objectPath);
  }

  async deleteBatch(paths: string[]): Promise<number> {
    let count = 0;
    for (const path of paths) {
      try {
        await this.delete(path);
        count++;
      } catch {
        continue;
      }
    }
    return count;
  }

  async exists(path: string): Promise<boolean> {
    try {
      const bucketName = this.resolveBucket(path);
      const bucket = this.getBucket(bucketName);
      const objectPath = this.normalizePath(path);
      return bucket.objects.has(objectPath);
    } catch {
      return false;
    }
  }

  async getMetadata(path: string): Promise<StorageObject> {
    const bucketName = this.resolveBucket(path);
    const bucket = this.getBucket(bucketName);
    const objectPath = this.normalizePath(path);

    const object = bucket.objects.get(objectPath);
    if (!object) {
      throw new StorageError(`Object not found: ${path}`, 'NOT_FOUND');
    }
    return { ...object, metadata: { ...object.metadata } };
  }

  async list(prefix?: string, recursive?: boolean): Promise<StorageObject[]> {
    const results: StorageObject[] = [];
    for (const [, bucket] of this.buckets) {
      for (const [, object] of bucket.objects) {
        if (prefix && !object.path.startsWith(prefix)) {
          continue;
        }
        if (!recursive && prefix) {
          const remaining = object.path.slice(prefix.length);
          if (remaining.includes('/')) {
            continue;
          }
        }
        results.push({ ...object, metadata: { ...object.metadata } });
      }
    }
    return results;
  }

  async copy(source: string, dest: string): Promise<string> {
    const data = await this.download(source);
    const metadata = await this.getMetadata(source);
    await this.upload(data, dest, {
      contentType: metadata.contentType,
      metadata: metadata.metadata,
    });
    return dest;
  }

  async move(source: string, dest: string): Promise<string> {
    await this.copy(source, dest);
    await this.delete(source);
    return dest;
  }

  async getSignedUrl(path: string, expiresIn = 3600): Promise<string> {
    const objectPath = this.normalizePath(path);
    const expiry = new Date(Date.now() + expiresIn * 1000).toISOString();
    const signature = randomBytes(16).toString('hex');
    return `${this.baseUrl}/storage/v1/${objectPath}?token=${signature}&expires=${expiry}`;
  }

  getPublicUrl(path: string): string {
    const objectPath = this.normalizePath(path);
    return `${this.baseUrl}/storage/v1/public/${objectPath}`;
  }

  async createBucket(name: string, region?: string): Promise<void> {
    if (this.buckets.has(name)) {
      throw new StorageError(`Bucket already exists: ${name}`, 'ALREADY_EXISTS');
    }
    this.buckets.set(name, {
      name,
      region: region ?? 'us-east',
      createdAt: new Date(),
      objects: new Map(),
      blobStore: new Map(),
    });
  }

  async deleteBucket(name: string): Promise<void> {
    if (!this.buckets.has(name)) {
      throw new StorageError(`Bucket not found: ${name}`, 'NOT_FOUND');
    }
    this.buckets.delete(name);
  }

  async listBuckets(): Promise<string[]> {
    return [...this.buckets.keys()];
  }

  private createInternalBucket(): void {
    const now = new Date();
    this.buckets.set('default', {
      name: 'default',
      region: 'us-east',
      createdAt: now,
      objects: new Map(),
      blobStore: new Map(),
    });
  }

  private resolveBucket(path: string): string {
    const parts = path.replace(/^\/+/, '').split('/');
    return parts.length > 1 ? parts[0] : 'default';
  }

  private normalizePath(path: string): string {
    return path.replace(/^\/+/, '');
  }

  private getOrCreateBucket(name: string): Bucket {
    if (!this.buckets.has(name)) {
      this.buckets.set(name, {
        name,
        region: 'us-east',
        createdAt: new Date(),
        objects: new Map(),
        blobStore: new Map(),
      });
    }
    return this.buckets.get(name)!;
  }

  private getBucket(name: string): Bucket {
    const bucket = this.buckets.get(name);
    if (!bucket) {
      throw new StorageError(`Bucket not found: ${name}`, 'NOT_FOUND');
    }
    return bucket;
  }
}

export { StorageError };
