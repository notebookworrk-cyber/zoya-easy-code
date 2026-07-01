import { describe, it, expect, beforeEach } from 'vitest';
import { DatabaseService, DatabaseError } from '../../src/cloud/database.js';
import type { CollectionSchema, QueryFilter } from '../../src/cloud/database.js';

describe('DatabaseService', () => {
  let db: DatabaseService;

  beforeEach(() => {
    db = new DatabaseService('https://api.zoya.dev', 'test-key');
  });

  describe('CRUD Operations', () => {
    it('creates a document', async () => {
      const result = await db.create('users', { name: 'Alice', age: 30 });
      expect(result.id).toBeDefined();
      expect(result.name).toBe('Alice');
      expect(result.age).toBe(30);
      expect(result.createdAt).toBeInstanceOf(Date);
    });

    it('reads a document by id', async () => {
      const created = await db.create('users', { name: 'Bob', age: 25 });
      const read = await db.read('users', created.id);
      expect(read).not.toBeNull();
      expect((read as Record<string, unknown>).name).toBe('Bob');
    });

    it('returns null for non-existent document', async () => {
      const result = await db.read('users', 'nonexistent');
      expect(result).toBeNull();
    });

    it('updates a document', async () => {
      const created = await db.create('users', { name: 'Charlie', age: 35 });
      const updated = await db.update('users', created.id, { age: 36 });
      expect((updated as Record<string, unknown>).age).toBe(36);
      expect((updated as Record<string, unknown>).name).toBe('Charlie');
    });

    it('throws on update for non-existent document', async () => {
      await expect(db.update('users', 'noid', { name: 'X' })).rejects.toThrow(DatabaseError);
    });

    it('soft deletes a document', async () => {
      const created = await db.create('users', { name: 'DeleteMe' });
      await db.delete('users', created.id, true);
      const read = await db.read('users', created.id);
      expect(read).toBeNull();
    });

    it('hard deletes a document', async () => {
      const created = await db.create('users', { name: 'HardDelete' });
      await db.delete('users', created.id, false);
      const read = await db.read('users', created.id);
      expect(read).toBeNull();
    });

    it('throws on hard delete for non-existent', async () => {
      await expect(db.delete('users', 'nonexistent')).rejects.toThrow(DatabaseError);
    });
  });

  describe('Query with Filters', () => {
    beforeEach(async () => {
      await db.create('products', { name: 'Apple', price: 1.5, category: 'fruit' });
      await db.create('products', { name: 'Banana', price: 0.5, category: 'fruit' });
      await db.create('products', { name: 'Carrot', price: 0.8, category: 'vegetable' });
      await db.create('products', { name: 'Donut', price: 2.0, category: 'bakery' });
    });

    it('filters with equality', async () => {
      const result = await db.query('products', {
        filters: [{ field: 'category', operator: '==', value: 'fruit' }],
      });
      expect(result.data.length).toBe(2);
      expect(result.total).toBe(2);
    });

    it('filters with greater than', async () => {
      const result = await db.query('products', {
        filters: [{ field: 'price', operator: '>', value: 1.0 }],
      });
      expect(result.data.length).toBe(2);
    });

    it('filters with less than or equal', async () => {
      const result = await db.query('products', {
        filters: [{ field: 'price', operator: '<=', value: 0.8 }],
      });
      expect(result.data.length).toBe(2);
    });

    it('filters with contains', async () => {
      const result = await db.query('products', {
        filters: [{ field: 'name', operator: 'contains', value: 'pp' }],
      });
      expect(result.data.length).toBe(1);
      expect((result.data[0] as Record<string, unknown>).name).toBe('Apple');
    });

    it('orders by field ascending', async () => {
      const result = await db.query('products', {
        orders: [{ field: 'price', direction: 'asc' }],
      });
      expect((result.data[0] as Record<string, unknown>).name).toBe('Banana');
      expect((result.data[3] as Record<string, unknown>).name).toBe('Donut');
    });

    it('orders by field descending', async () => {
      const result = await db.query('products', {
        orders: [{ field: 'price', direction: 'desc' }],
      });
      expect((result.data[0] as Record<string, unknown>).name).toBe('Donut');
    });

    it('applies limit and offset', async () => {
      const result = await db.query('products', { limit: 2, offset: 1 });
      expect(result.data.length).toBe(2);
      expect(result.hasMore).toBe(true);
    });

    it('returns correct pagination metadata', async () => {
      const result = await db.query('products', { limit: 2 });
      expect(result.total).toBe(4);
      expect(result.limit).toBe(2);
      expect(result.offset).toBe(0);
      expect(result.hasMore).toBe(true);
    });
  });

  describe('Batch Operations', () => {
    it('batch creates documents', async () => {
      const items = [
        { name: 'Item1', value: 1 },
        { name: 'Item2', value: 2 },
        { name: 'Item3', value: 3 },
      ];
      const results = await db.batchCreate('items', items);
      expect(results.length).toBe(3);
      expect(results[0].id).toBeDefined();
      expect(results[1].name).toBe('Item2');
    });

    it('batch deletes documents', async () => {
      const a = await db.create('batchdel', { x: 1 });
      const b = await db.create('batchdel', { x: 2 });
      const c = await db.create('batchdel', { x: 3 });
      const count = await db.batchDelete('batchdel', [a.id, b.id, c.id]);
      expect(count).toBe(3);
      expect(await db.read('batchdel', a.id)).toBeNull();
    });

    it('batch delete handles partial failures', async () => {
      const a = await db.create('partial', { x: 1 });
      const count = await db.batchDelete('partial', [a.id, 'nonexistent']);
      expect(count).toBe(1);
    });
  });

  describe('Count and Exists', () => {
    it('counts documents in collection', async () => {
      await db.create('counts', { val: 1 });
      await db.create('counts', { val: 2 });
      await db.create('counts', { val: 3 });
      expect(await db.count('counts')).toBe(3);
    });

    it('counts with filter', async () => {
      await db.create('filtered', { type: 'a' });
      await db.create('filtered', { type: 'a' });
      await db.create('filtered', { type: 'b' });
      const count = await db.count('filtered', [
        { field: 'type', operator: '==', value: 'a' },
      ]);
      expect(count).toBe(2);
    });

    it('checks document existence', async () => {
      const created = await db.create('exists', { val: 1 });
      expect(await db.exists('exists', created.id)).toBe(true);
      expect(await db.exists('exists', 'nonexistent')).toBe(false);
    });

    it('returns false for soft-deleted document', async () => {
      const created = await db.create('existsdel', { val: 1 });
      await db.delete('existsdel', created.id, true);
      expect(await db.exists('existsdel', created.id)).toBe(false);
    });
  });

  describe('findByIds and first', () => {
    it('finds multiple documents by ids', async () => {
      const a = await db.create('multi', { val: 'a' });
      const b = await db.create('multi', { val: 'b' });
      const results = await db.findByIds('multi', [a.id, b.id]);
      expect(results.length).toBe(2);
    });

    it('returns empty array for missing ids', async () => {
      const results = await db.findByIds('multi', ['nope']);
      expect(results).toEqual([]);
    });

    it('returns first matching document', async () => {
      await db.create('firsts', { name: 'Alice', age: 30 });
      await db.create('firsts', { name: 'Bob', age: 25 });
      const result = await db.first('firsts', {
        field: 'name',
        operator: '==',
        value: 'Alice',
      });
      expect(result).not.toBeNull();
      expect((result as Record<string, unknown>).name).toBe('Alice');
    });

    it('returns null when no match', async () => {
      const result = await db.first('firsts', {
        field: 'name',
        operator: '==',
        value: 'Nobody',
      });
      expect(result).toBeNull();
    });
  });

  describe('Schema Management', () => {
    it('creates a collection schema', async () => {
      const schema: CollectionSchema = {
        name: 'test_collection',
        fields: { name: 'string', age: 'number' },
        indexes: [['name']],
        timestamps: true,
        softDelete: true,
      };
      await db.createCollection(schema);
      const collections = await db.listCollections();
      expect(collections).toContain('test_collection');
    });

    it('throws on duplicate collection', async () => {
      const schema: CollectionSchema = {
        name: 'dup_collection',
        fields: {},
        indexes: [],
        timestamps: true,
        softDelete: false,
      };
      await db.createCollection(schema);
      await expect(db.createCollection(schema)).rejects.toThrow(DatabaseError);
    });

    it('deletes a collection', async () => {
      const schema: CollectionSchema = {
        name: 'delete_collection',
        fields: {},
        indexes: [],
        timestamps: false,
        softDelete: false,
      };
      await db.createCollection(schema);
      await db.deleteCollection('delete_collection');
      const collections = await db.listCollections();
      expect(collections).not.toContain('delete_collection');
    });

    it('throws on deleting non-existent collection', async () => {
      await expect(db.deleteCollection('phantom')).rejects.toThrow(DatabaseError);
    });
  });

  describe('Transactions', () => {
    it('begins a transaction', async () => {
      const txId = await db.beginTransaction();
      expect(txId).toBeDefined();
    });

    it('commits a transaction', async () => {
      const txId = await db.beginTransaction();
      await expect(db.commitTransaction(txId)).resolves.toBeUndefined();
    });

    it('rolls back a transaction', async () => {
      await db.create('tx_data', { val: 'original' });
      const txId = await db.beginTransaction();
      await db.create('tx_data', { val: 'rolled_back' });
      await db.rollbackTransaction(txId);
      const all = await db.query('tx_data');
      expect(all.data.length).toBe(1);
      expect((all.data[0] as Record<string, unknown>).val).toBe('original');
    });

    it('throws on unknown transaction', async () => {
      await expect(db.commitTransaction('phantom')).rejects.toThrow(DatabaseError);
      await expect(db.rollbackTransaction('phantom')).rejects.toThrow(DatabaseError);
    });
  });

  describe('Error Handling', () => {
    it('throws on update of deleted document', async () => {
      const doc = await db.create('err', { val: 1 });
      await db.delete('err', doc.id, false);
      await expect(db.update('err', doc.id, { val: 2 })).rejects.toThrow(DatabaseError);
    });

    it('creates collection dynamically on write', async () => {
      const result = await db.create('auto_create', { x: 1 });
      expect(result.id).toBeDefined();
      const read = await db.read('auto_create', result.id);
      expect(read).not.toBeNull();
    });
  });
});
