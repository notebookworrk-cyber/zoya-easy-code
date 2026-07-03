import { describe, it, expect, beforeEach } from 'vitest';
import { StorageService, StorageError } from '../../src/cloud/storage.js';

describe('StorageService', () => {
  let storage: StorageService;

  beforeEach(() => {
    storage = new StorageService('https://api.zoya.dev', 'test-key');
  });

  describe('Upload', () => {
    it('uploads data with default content type', async () => {
      const data = Buffer.from('hello world');
      const result = await storage.upload(data, 'test.txt');
      expect(result.path).toBe('test.txt');
      expect(result.size).toBe(11);
      expect(result.contentType).toBe('application/octet-stream');
      expect(result.etag).toBeDefined();
      expect(result.url).toBeDefined();
      expect(result.uploadedAt).toBeInstanceOf(Date);
    });

    it('uploads with custom content type and metadata', async () => {
      const data = Buffer.from('{"key":"value"}');
      const result = await storage.upload(data, 'config.json', {
        contentType: 'application/json',
        metadata: { author: 'test' },
      });
      expect(result.contentType).toBe('application/json');
      expect(result.size).toBe(15);
    });

    it('uploads with public flag', async () => {
      const data = Buffer.from('public content');
      const result = await storage.upload(data, 'public.txt', { public: true });
      expect(result.url).toBeDefined();
    });
  });

  describe('Download', () => {
    it('downloads previously uploaded data', async () => {
      const original = Buffer.from('download test data');
      await storage.upload(original, 'download.txt');
      const downloaded = await storage.download('download.txt');
      expect(downloaded.toString()).toBe('download test data');
    });

    it('throws on downloading non-existent file', async () => {
      await expect(storage.download('nonexistent.txt')).rejects.toThrow(StorageError);
    });
  });

  describe('File Listing and Deletion', () => {
    it('lists all objects', async () => {
      await storage.upload(Buffer.from('a'), 'file-a.txt');
      await storage.upload(Buffer.from('b'), 'file-b.txt');
      const objects = await storage.list();
      expect(objects.length).toBe(2);
    });

    it('lists with prefix filter', async () => {
      await storage.upload(Buffer.from('img'), 'images/photo.png');
      await storage.upload(Buffer.from('doc'), 'docs/readme.md');
      const images = await storage.list('images/');
      expect(images.length).toBe(1);
      expect(images[0].path).toBe('images/photo.png');
    });

    it('deletes an object', async () => {
      await storage.upload(Buffer.from('delete me'), 'delete-me.txt');
      await storage.delete('delete-me.txt');
      expect(await storage.exists('delete-me.txt')).toBe(false);
    });

    it('throws on deleting non-existent object', async () => {
      await expect(storage.delete('ghost.txt')).rejects.toThrow(StorageError);
    });

    it('batch deletes objects', async () => {
      await storage.upload(Buffer.from('a'), 'batch-a.txt');
      await storage.upload(Buffer.from('b'), 'batch-b.txt');
      await storage.upload(Buffer.from('c'), 'batch-c.txt');
      const count = await storage.deleteBatch([
        'batch-a.txt',
        'batch-b.txt',
        'batch-c.txt',
      ]);
      expect(count).toBe(3);
    });

    it('batch delete handles partial failures', async () => {
      await storage.upload(Buffer.from('a'), 'partial-a.txt');
      const count = await storage.deleteBatch(['partial-a.txt', 'ghost.txt']);
      expect(count).toBe(1);
    });
  });

  describe('Exists and Metadata', () => {
    it('checks object existence', async () => {
      await storage.upload(Buffer.from('exists'), 'exists.txt');
      expect(await storage.exists('exists.txt')).toBe(true);
      expect(await storage.exists('ghost.txt')).toBe(false);
    });

    it('gets object metadata', async () => {
      await storage.upload(Buffer.from('meta'), 'meta.txt', {
        contentType: 'text/plain',
        metadata: { key: 'value' },
      });
      const meta = await storage.getMetadata('meta.txt');
      expect(meta.path).toBe('meta.txt');
      expect(meta.contentType).toBe('text/plain');
      expect(meta.metadata.key).toBe('value');
      expect(meta.size).toBe(4);
      expect(meta.etag).toBeDefined();
      expect(meta.lastModified).toBeInstanceOf(Date);
    });

    it('throws on metadata for non-existent', async () => {
      await expect(storage.getMetadata('ghost.txt')).rejects.toThrow(StorageError);
    });
  });

  describe('Copy and Move', () => {
    it('copies an object', async () => {
      await storage.upload(Buffer.from('copy source'), 'source.txt');
      const dest = await storage.copy('source.txt', 'dest.txt');
      expect(dest).toBe('dest.txt');
      expect(await storage.exists('dest.txt')).toBe(true);
      expect(await storage.exists('source.txt')).toBe(true);
    });

    it('moves an object', async () => {
      await storage.upload(Buffer.from('move source'), 'move-source.txt');
      const dest = await storage.move('move-source.txt', 'move-dest.txt');
      expect(dest).toBe('move-dest.txt');
      expect(await storage.exists('move-source.txt')).toBe(false);
      expect(await storage.exists('move-dest.txt')).toBe(true);
    });
  });

  describe('Signed URLs', () => {
    it('generates a signed URL', async () => {
      await storage.upload(Buffer.from('signed'), 'signed.txt');
      const url = await storage.getSignedUrl('signed.txt', 3600);
      expect(url).toContain('signed.txt');
      expect(url).toContain('token=');
      expect(url).toContain('expires=');
    });

    it('generates public URL', () => {
      const url = storage.getPublicUrl('public.txt');
      expect(url).toContain('public/');
      expect(url).toContain('public.txt');
    });
  });

  describe('Bucket Management', () => {
    it('creates a bucket', async () => {
      await storage.createBucket('my-bucket');
      const buckets = await storage.listBuckets();
      expect(buckets).toContain('my-bucket');
    });

    it('throws on duplicate bucket', async () => {
      await storage.createBucket('dup-bucket');
      await expect(storage.createBucket('dup-bucket')).rejects.toThrow(StorageError);
    });

    it('deletes a bucket', async () => {
      await storage.createBucket('delete-bucket');
      await storage.deleteBucket('delete-bucket');
      const buckets = await storage.listBuckets();
      expect(buckets).not.toContain('delete-bucket');
    });

    it('throws on deleting non-existent bucket', async () => {
      await expect(storage.deleteBucket('ghost-bucket')).rejects.toThrow(StorageError);
    });

    it('lists buckets', async () => {
      await storage.createBucket('bucket-1');
      await storage.createBucket('bucket-2');
      const buckets = await storage.listBuckets();
      expect(buckets.length).toBeGreaterThanOrEqual(2);
    });
  });
});
