import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { VectorMemory } from '../../src/ai/vector.js';
import * as fs from 'fs';
import * as path from 'path';

describe('VectorMemory', () => {
  let memory: VectorMemory;
  const DIMENSION = 4;

  function makeVector(...values: number[]): Float32Array {
    return new Float32Array(values);
  }

  beforeEach(() => {
    memory = new VectorMemory(DIMENSION);
  });

  describe('record insertion and retrieval', () => {
    it('inserts and retrieves a record', () => {
      memory.insert('vec1', 'test document', makeVector(1, 0, 0, 0), {
        source: 'test',
      });
      const record = memory.get('vec1');
      expect(record).toBeDefined();
      expect(record!.id).toBe('vec1');
      expect(record!.text).toBe('test document');
      expect(record!.metadata).toEqual({ source: 'test' });
    });

    it('returns undefined for unknown id', () => {
      expect(memory.get('nonexistent')).toBeUndefined();
    });

    it('returns a copy that cannot be mutated externally', () => {
      memory.insert('v1', 'text', makeVector(1, 0, 0, 0));
      const record = memory.get('v1')!;
      record.metadata = { hacked: true };
      expect(memory.get('v1')!.metadata).not.toEqual({ hacked: true });
    });

    it('throws on dimension mismatch', () => {
      expect(() =>
        memory.insert('bad', 'text', makeVector(1, 2, 3), {})
      ).toThrow('Vector dimension mismatch');
    });
  });

  describe('cosine similarity search', () => {
    beforeEach(() => {
      memory.insert('a', 'first', makeVector(1, 0, 0, 0));
      memory.insert('b', 'second', makeVector(0, 1, 0, 0));
      memory.insert('c', 'third', makeVector(0, 0, 1, 0));
      memory.insert('d', 'fourth', makeVector(0, 0, 0, 1));
    });

    it('finds most similar vector', () => {
      const results = memory.search(makeVector(1, 0, 0, 0), 1);
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('a');
      expect(results[0].score).toBeCloseTo(1, 5);
    });

    it('returns results sorted by similarity descending', () => {
      const results = memory.search(makeVector(1, 1, 0, 0), 4);
      expect(results[0].id).toBe('a');
      expect(results[1].id).toBe('b');
    });

    it('respects topK parameter', () => {
      const results = memory.search(makeVector(1, 0, 0, 0), 2);
      expect(results).toHaveLength(2);
    });

    it('throws on query dimension mismatch', () => {
      expect(() => memory.search(makeVector(1, 2, 3), 5)).toThrow(
        'Query dimension mismatch'
      );
    });

    it('returns zero score when magnitude is zero', () => {
      memory.insert('zero', 'zero vector', makeVector(0, 0, 0, 0));
      const results = memory.search(makeVector(1, 0, 0, 0), 5);
      const zeroResult = results.find((r) => r.id === 'zero');
      expect(zeroResult!.score).toBe(0);
    });
  });

  describe('record update and removal', () => {
    it('updates metadata', () => {
      memory.insert('v1', 'text', makeVector(1, 0, 0, 0), { old: 'data' });
      memory.update('v1', { new: 'data', extra: true });
      const record = memory.get('v1')!;
      expect(record.metadata).toEqual({ old: 'data', new: 'data', extra: true });
    });

    it('throws on update of nonexistent record', () => {
      expect(() => memory.update('ghost', { key: 'value' })).toThrow(
        'Record not found: ghost'
      );
    });

    it('removes a record', () => {
      memory.insert('v1', 'text', makeVector(1, 0, 0, 0));
      expect(memory.size).toBe(1);
      memory.remove('v1');
      expect(memory.size).toBe(0);
      expect(memory.get('v1')).toBeUndefined();
    });

    it('does nothing when removing nonexistent id', () => {
      memory.remove('ghost');
      expect(memory.size).toBe(0);
    });
  });

  describe('batch insert', () => {
    it('inserts multiple records', () => {
      memory.insertMany([
        { id: 'a', text: 'first', vector: makeVector(1, 0, 0, 0) },
        { id: 'b', text: 'second', vector: makeVector(0, 1, 0, 0) },
        { id: 'c', text: 'third', vector: makeVector(0, 0, 1, 0) },
      ]);
      expect(memory.size).toBe(3);
    });

    it('propagates metadata', () => {
      memory.insertMany([
        { id: 'a', text: 'first', vector: makeVector(1, 0, 0, 0), metadata: { tag: 'x' } },
        { id: 'b', text: 'second', vector: makeVector(0, 1, 0, 0), metadata: { tag: 'y' } },
      ]);
      expect(memory.get('a')!.metadata).toEqual({ tag: 'x' });
      expect(memory.get('b')!.metadata).toEqual({ tag: 'y' });
    });
  });

  describe('stats tracking', () => {
    it('returns zero stats for empty memory', () => {
      const stats = memory.getStats();
      expect(stats.totalRecords).toBe(0);
      expect(stats.dimension).toBe(DIMENSION);
      expect(stats.memoryUsage).toBe(0);
    });

    it('reflects inserted records', () => {
      memory.insert('v1', 'doc', makeVector(1, 0, 0, 0));
      const stats = memory.getStats();
      expect(stats.totalRecords).toBe(1);
      expect(stats.dimension).toBe(DIMENSION);
      expect(stats.memoryUsage).toBeGreaterThan(0);
    });
  });

  describe('clear operation', () => {
    it('removes all records', () => {
      memory.insert('v1', 'doc', makeVector(1, 0, 0, 0));
      memory.insert('v2', 'doc2', makeVector(0, 1, 0, 0));
      expect(memory.size).toBe(2);

      memory.clear();
      expect(memory.size).toBe(0);
      expect(memory.get('v1')).toBeUndefined();
      expect(memory.get('v2')).toBeUndefined();
    });
  });

  describe('save/load persistence', () => {
    const testFilePath = path.join(
      require('os').tmpdir(),
      `vector_test_${Date.now()}.json`
    );

    afterEach(() => {
      try {
        if (fs.existsSync(testFilePath)) {
          fs.unlinkSync(testFilePath);
        }
      } catch {
        // cleanup
      }
    });

    it('saves and loads vector store', () => {
      memory.insert('v1', 'doc one', makeVector(1, 0, 0, 0), { key: 'val1' });
      memory.insert('v2', 'doc two', makeVector(0, 1, 0, 0), { key: 'val2' });
      memory.save(testFilePath);

      const loaded = new VectorMemory();
      loaded.load(testFilePath);

      expect(loaded.size).toBe(2);
      expect(loaded.get('v1')!.text).toBe('doc one');
      expect(loaded.get('v2')!.metadata).toEqual({ key: 'val2' });
      expect(loaded.getDimension()).toBe(DIMENSION);
    });

    it('preserves vector values across save/load', () => {
      memory.insert('v1', 'doc', makeVector(0.5, -0.3, 0.8, 0.1));
      memory.save(testFilePath);

      const loaded = new VectorMemory();
      loaded.load(testFilePath);

      const record = loaded.get('v1')!;
      expect(record.vector[0]).toBeCloseTo(0.5, 5);
      expect(record.vector[1]).toBeCloseTo(-0.3, 5);
      expect(record.vector[2]).toBeCloseTo(0.8, 5);
      expect(record.vector[3]).toBeCloseTo(0.1, 5);
    });

    it('throws when loading from nonexistent file', () => {
      const badPath = '/nonexistent/vector_store.json';
      const fresh = new VectorMemory();
      expect(() => fresh.load(badPath)).toThrow('Vector store file not found');
    });
  });

  describe('consolidate', () => {
    it('removes orphaned records from internal array', () => {
      memory.insert('v1', 'doc', makeVector(1, 0, 0, 0));
      memory.insert('v2', 'doc2', makeVector(0, 1, 0, 0));

      memory.remove('v2');

      memory.consolidate();
      expect(memory.size).toBe(1);
    });
  });

  describe('searchByText', () => {
    it('returns results for text query', async () => {
      memory.insert('v1', 'document', makeVector(1, 0, 0, 0));
      memory.insert('v2', 'other', makeVector(0, 1, 0, 0));

      const results = await memory.searchByText('query', 2);
      expect(results).toHaveLength(2);
    });
  });
});
