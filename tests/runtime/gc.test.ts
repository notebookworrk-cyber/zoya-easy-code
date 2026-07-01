import { describe, it, expect } from 'vitest';
import { GC } from '../../src/runtime/gc/index';
import { ZoyaValue, ZoyaObject, ZoyaArray, allocateObjectId } from '../../src/types';

describe('GC', () => {
  it('starts with zero objects', () => {
    const gc = new GC(1000);
    expect(gc.getObjectCount()).toBe(0);
    expect(gc.getAllocationCount()).toBe(0);
    expect(gc.getCollectionsPerformed()).toBe(0);
    expect(gc.getCollectedTotal()).toBe(0);
  });

  it('tracks object allocations', () => {
    const gc = new GC(1000);
    const obj = gc.createObject('test');
    expect(obj.__zoya_type).toBe('test');
    expect(gc.getObjectCount()).toBe(1);
    expect(gc.getAllocationCount()).toBe(1);
  });

  it('tracks array allocations', () => {
    const gc = new GC(1000);
    const arr = gc.createArray([1, 2, 3]);
    expect(arr.__zoya_type).toBe('array');
    expect(arr.length).toBe(3);
    expect(gc.getObjectCount()).toBe(1);
  });

  it('triggers collection when threshold exceeded', () => {
    const gc = new GC(5);

    const roots: ZoyaValue[] = [];

    for (let i = 0; i < 10; i++) {
      const obj = gc.createObject(`test-${i}`);
      if (i < 3) {
        roots.push(obj);
      }
    }

    expect(gc.getCollectionsPerformed()).toBeGreaterThan(0);
  });

  it('preserves reachable objects after collection', () => {
    const gc = new GC(100);

    const roots: ZoyaValue[] = [];

    const obj1 = gc.createObject('reachable-1');
    roots.push(obj1);

    const obj2 = gc.createObject('reachable-2');
    roots.push(obj2);

    gc.createObject('unreachable-1');
    gc.createObject('unreachable-2');

    gc.registerRoot(() => roots);

    const beforeObjCount = gc.getObjectCount();
    gc.collect();
    const afterObjCount = gc.getObjectCount();

    expect(afterObjCount).toBeLessThan(beforeObjCount);
    expect(afterObjCount).toBe(2);
  });

  it('collects unreachable objects', () => {
    const gc = new GC(100);

    const roots: ZoyaValue[] = [];

    for (let i = 0; i < 5; i++) {
      const obj = gc.createObject(`reachable-${i}`);
      if (i < 3) {
        roots.push(obj);
      }
    }

    gc.registerRoot(() => roots);
    gc.collect();

    const collected = gc.getCollectedTotal();
    expect(collected).toBeGreaterThan(0);
  });

  it('handles stress test with many allocations', () => {
    const gc = new GC(50);

    const roots: ZoyaValue[] = [];

    gc.registerRoot(() => roots);

    for (let round = 0; round < 5; round++) {
      for (let i = 0; i < 20; i++) {
        const obj = gc.createObject(`round-${round}-${i}`);
        if (i < 5) {
          roots.push(obj);
        }
      }
    }

    gc.collect();

    expect(gc.getCollectionsPerformed()).toBeGreaterThan(0);
    expect(gc.getObjectCount()).toBeLessThan(100);
  });

  it('adjusts threshold based on collection results', () => {
    const gc = new GC(50);

    const initialThreshold = gc.getThreshold();

    const roots: ZoyaValue[] = [];
    gc.registerRoot(() => roots);

    for (let i = 0; i < 100; i++) {
      const obj = gc.createObject(`obj-${i}`);
      if (i < 5) {
        roots.push(obj);
      }
    }

    const finalThreshold = gc.getThreshold();
    expect(finalThreshold).toBeGreaterThanOrEqual(100);
  });

  it('creates closures and functions via GC', () => {
    const gc = new GC(100);
    const code = new Uint8Array([0x01, 0x02, 0x03]);
    const func = gc.createFunction('test-fn', 2, code, [1, 'hello']);

    expect(func.__zoya_type).toBe('function');
    expect(func.name).toBe('test-fn');
    expect(func.arity).toBe(2);
    expect(func.chunk.code.length).toBe(3);
    expect(func.chunk.constants.length).toBe(2);

    const closure = gc.createClosure(func, []);
    expect(closure.__zoya_type).toBe('closure');
    expect(closure.function).toBe(func);
    expect(closure.upvalues).toEqual([]);
  });

  it('returns stats', () => {
    const gc = new GC(100);
    gc.createObject('a');
    gc.createObject('b');
    gc.createObject('c');

    const stats = gc.getStats();
    expect(stats.objectCount).toBe(3);
    expect(stats.allocationCount).toBe(3);
    expect(stats.threshold).toBe(100);
    expect(stats.collectionsPerformed).toBe(0);
    expect(stats.collectedTotal).toBe(0);
  });

  it('resets state', () => {
    const gc = new GC(100);
    gc.createObject('a');
    gc.createObject('b');
    expect(gc.getObjectCount()).toBe(2);

    gc.reset();
    expect(gc.getObjectCount()).toBe(0);
    expect(gc.getAllocationCount()).toBe(0);
    expect(gc.getCollectedTotal()).toBe(0);
    expect(gc.getCollectionsPerformed()).toBe(0);
  });

  it('can set threshold dynamically', () => {
    const gc = new GC(500);
    expect(gc.getThreshold()).toBe(500);
    gc.setThreshold(1000);
    expect(gc.getThreshold()).toBe(1000);
  });

  it('registering and removing roots', () => {
    const gc = new GC(100);
    const fn = () => [1, 2, 3] as unknown as ZoyaValue[];
    gc.registerRoot(fn);
    gc.removeRoot(fn);
  });
});
