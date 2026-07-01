import { ZoyaValue, ZoyaObject, ZoyaArray, ZoyaFunction, ZoyaClosure, ZoyaNative, typeOf } from '../../types';
import { GC, GCStats } from '../gc/index';

export interface AllocationRecord {
  type: string;
  count: number;
  totalSize: number;
  averageSize: number;
  minSize: number;
  maxSize: number;
}

export interface MemoryReport {
  totalObjects: number;
  totalEstimatedSize: number;
  allocationsByType: AllocationRecord[];
  gcStats: GCStats;
  collectionEfficiency: number;
}

export class MemoryProfiler {
  private allocations: Map<string, { count: number; totalSize: number; minSize: number; maxSize: number }> = new Map();
  private previousStats: GCStats | null = null;

  trackAllocation(value: ZoyaValue): void {
    const type = typeOf(value);
    const existing = this.allocations.get(type) || { count: 0, totalSize: 0, minSize: Infinity, maxSize: 0 };
    existing.count++;
    existing.totalSize += this.estimateValueSize(value);
    existing.minSize = Math.min(existing.minSize, existing.totalSize);
    existing.maxSize = Math.max(existing.maxSize, existing.totalSize);
    this.allocations.set(type, existing);
  }

  estimateValueSize(value: ZoyaValue): number {
    if (value === null) return 0;
    if (typeof value === 'boolean') return 4;
    if (typeof value === 'number') return 8;
    if (typeof value === 'string') return value.length * 2 + 16;

    if (typeof value === 'object') {
      const obj = value as ZoyaObject;
      let size = 64;
      if (obj.__zoya_type === 'array') {
        const arr = value as ZoyaArray;
        size += arr.elements.length * 8;
        for (const elem of arr.elements) {
          size += this.estimateValueSize(elem);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = value as ZoyaFunction;
        size += func.chunk.code.length + func.chunk.constants.length * 8;
      }
      if (obj.__zoya_type === 'closure') {
        const clos = value as ZoyaClosure;
        size += clos.upvalues.length * 8;
      }
      return size;
    }

    return 0;
  }

  generateReport(gc: GC): MemoryReport {
    const gcStats = gc.getStats();
    const allocationsByType: AllocationRecord[] = [];
    let totalObjects = 0;
    let totalEstimatedSize = 0;

    for (const [type, data] of this.allocations) {
      totalObjects += data.count;
      totalEstimatedSize += data.totalSize;
      allocationsByType.push({
        type,
        count: data.count,
        totalSize: data.totalSize,
        averageSize: data.count > 0 ? Math.round(data.totalSize / data.count) : 0,
        minSize: data.minSize === Infinity ? 0 : data.minSize,
        maxSize: data.maxSize,
      });
    }

    allocationsByType.sort((a, b) => b.totalSize - a.totalSize);

    const collectionEfficiency = this.previousStats
      ? (this.previousStats.collectedTotal / Math.max(this.previousStats.objectCount, 1)) * 100
      : 0;

    this.previousStats = gcStats;

    return {
      totalObjects,
      totalEstimatedSize,
      allocationsByType,
      gcStats,
      collectionEfficiency,
    };
  }

  reset(): void {
    this.allocations.clear();
    this.previousStats = null;
  }
}

export interface LeakRecord {
  objectId: number;
  type: string;
  estimatedSize: number;
  reason: string;
}

export class LeakDetector {
  private previousSnapshot: SnapshotEntry[] = [];

  detectLeaks(gc: GC, currentValues: ZoyaValue[]): LeakRecord[] {
    const currentIds = new Set<number>();
    for (const val of currentValues) {
      this.collectObjectIds(val, currentIds);
    }

    const leaks: LeakRecord[] = [];
    const stats = gc.getStats();

    for (const prev of this.previousSnapshot) {
      if (!currentIds.has(prev.id)) {
        const typeOfVal = typeof prev.value === 'object' && prev.value !== null
          ? (prev.value as ZoyaObject).__zoya_type
          : typeof prev.value;
        leaks.push({
          objectId: prev.id,
          type: typeOfVal,
          estimatedSize: prev.size,
          reason: 'Object is no longer reachable from roots but was not collected',
        });
      }
    }

    this.previousSnapshot = this.takeSnapshot(currentValues);
    return leaks;
  }

  private takeSnapshot(values: ZoyaValue[]): SnapshotEntry[] {
    const entries: SnapshotEntry[] = [];
    const seen = new Set<number>();

    for (const val of values) {
      this.collectSnapshot(val, seen, entries);
    }

    return entries;
  }

  private collectSnapshot(val: ZoyaValue, seen: Set<number>, entries: SnapshotEntry[]): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      if (seen.has(obj.__id)) return;
      seen.add(obj.__id);

      entries.push({
        id: obj.__id,
        value: val,
        size: 64,
      });

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.collectSnapshot(elem, seen, entries);
        }
      }
      if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.collectSnapshot(clos.function, seen, entries);
        for (const uv of clos.upvalues) {
          this.collectSnapshot(uv, seen, entries);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.collectSnapshot(c, seen, entries);
        }
      }
    }
  }

  private collectObjectIds(val: ZoyaValue, ids: Set<number>): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      if (ids.has(obj.__id)) return;
      ids.add(obj.__id);

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.collectObjectIds(elem, ids);
        }
      }
      if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.collectObjectIds(clos.function, ids);
        for (const uv of clos.upvalues) {
          this.collectObjectIds(uv, ids);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.collectObjectIds(c, ids);
        }
      }
    }
  }

  reset(): void {
    this.previousSnapshot = [];
  }
}

interface SnapshotEntry {
  id: number;
  value: ZoyaValue;
  size: number;
}

export class MemorySnapshot {
  readonly timestamp: number;
  readonly entries: SnapshotEntry[];

  constructor(values: ZoyaValue[]) {
    this.timestamp = Date.now();
    this.entries = [];
    const seen = new Set<number>();

    for (const val of values) {
      this.collect(val, seen);
    }
  }

  private collect(val: ZoyaValue, seen: Set<number>): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      if (seen.has(obj.__id)) return;
      seen.add(obj.__id);

      let size = 64;
      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        size += arr.elements.length * 8;
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        size += func.chunk.code.length + func.chunk.constants.length * 8;
      }

      this.entries.push({ id: obj.__id, value: val, size });

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.collect(elem, seen);
        }
      }
      if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.collect(clos.function, seen);
        for (const uv of clos.upvalues) {
          this.collect(uv, seen);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.collect(c, seen);
        }
      }
    }
  }

  getTotalObjects(): number {
    return this.entries.length;
  }

  getTotalEstimatedSize(): number {
    return this.entries.reduce((sum, e) => sum + e.size, 0);
  }
}
