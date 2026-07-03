import { ZoyaObject, ZoyaValue, ZoyaArray, ZoyaClosure, ZoyaFunction, ZoyaUpvalue, allocateObjectId } from '../../types';

enum Color {
  White = 0,
  Gray = 1,
  Black = 2,
}

interface GCObject {
  id: number;
  color: Color;
  obj: ZoyaObject;
  size: number;
}

export class GC {
  private objects: GCObject[] = [];
  private roots: (() => ZoyaValue[])[] = [];
  private allocationCount = 0;
  private threshold: number;
  private collectedTotal = 0;
  private collectionsPerformed = 0;

  constructor(threshold: number = 1000) {
    this.threshold = threshold;
  }

  setThreshold(threshold: number): void {
    this.threshold = threshold;
  }

  getThreshold(): number {
    return this.threshold;
  }

  getObjectCount(): number {
    return this.objects.length;
  }

  getAllocationCount(): number {
    return this.allocationCount;
  }

  getCollectedTotal(): number {
    return this.collectedTotal;
  }

  getCollectionsPerformed(): number {
    return this.collectionsPerformed;
  }

  registerRoot(root: () => ZoyaValue[]): void {
    this.roots.push(root);
  }

  removeRoot(root: () => ZoyaValue[]): void {
    const idx = this.roots.indexOf(root);
    if (idx >= 0) {
      this.roots.splice(idx, 1);
    }
  }

  allocate(obj: ZoyaObject): ZoyaObject {
    this.objects.push({
      id: obj.__id,
      color: Color.White,
      obj,
      size: this.estimateSize(obj),
    });
    this.allocationCount++;

    if (this.allocationCount >= this.threshold) {
      this.collect();
    }

    return obj;
  }

  collect(): void {
    this.collectionsPerformed++;

    for (const gcObj of this.objects) {
      gcObj.color = Color.White;
    }

    for (const rootFn of this.roots) {
      const rootValues = rootFn();
      for (const val of rootValues) {
        this.markValue(val);
      }
    }

    const before = this.objects.length;

    const swept: GCObject[] = [];
    for (const gcObj of this.objects) {
      if (gcObj.color === Color.White) {
        this.collectedTotal += gcObj.size;
      } else {
        swept.push(gcObj);
      }
    }
    this.objects = swept;

    const collected = before - this.objects.length;
    this.allocationCount = 0;

    if (this.objects.length > 0 && collected === 0) {
      this.threshold = Math.min(this.threshold * 2, 100000);
    } else if (collected > 0) {
      this.threshold = Math.max(Math.floor(this.threshold * 0.75), 100);
    }
  }

  private markValue(val: ZoyaValue): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      const gcObj = this.findObject(obj.__id);
      if (!gcObj || gcObj.color !== Color.White) return;

      gcObj.color = Color.Gray;

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.markValue(elem);
        }
      } else if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.markValue(clos.function);
        for (const uv of clos.upvalues) {
          this.markValue(uv);
        }
      } else if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.markValue(c);
        }
      }

      gcObj.color = Color.Black;
    }
  }

  private findObject(id: number): GCObject | undefined {
    return this.objects.find(o => o.id === id);
  }

  private estimateSize(obj: ZoyaObject): number {
    let size = 64;
    if (obj.__zoya_type === 'array') {
      const arr = obj as unknown as ZoyaArray;
      size += arr.elements.length * 8;
    }
    if (obj.__zoya_type === 'closure') {
      const clos = obj as unknown as ZoyaClosure;
      size += clos.upvalues.length * 8;
    }
    if (obj.__zoya_type === 'function') {
      const func = obj as unknown as ZoyaFunction;
      size += func.chunk.code.length + func.chunk.constants.length * 8;
    }
    return size;
  }

  getStats(): GCStats {
    return {
      objectCount: this.objects.length,
      allocationCount: this.allocationCount,
      threshold: this.threshold,
      collectedTotal: this.collectedTotal,
      collectionsPerformed: this.collectionsPerformed,
    };
  }

  reset(): void {
    this.objects = [];
    this.roots = [];
    this.allocationCount = 0;
    this.collectedTotal = 0;
    this.collectionsPerformed = 0;
  }

  createObject(type: string): ZoyaObject {
    const obj: ZoyaObject = {
      __zoya_type: type,
      __id: allocateObjectId(),
    };
    return this.allocate(obj);
  }

  createArray(elements: ZoyaValue[] = []): ZoyaArray {
    const arr: ZoyaArray = {
      __zoya_type: 'array',
      __id: allocateObjectId(),
      elements,
      length: elements.length,
    };
    this.allocate(arr);
    return arr;
  }

  createFunction(name: string, arity: number, code: Uint8Array, constants: ZoyaValue[]): ZoyaFunction {
    const func: ZoyaFunction = {
      __zoya_type: 'function',
      __id: allocateObjectId(),
      name,
      arity,
      chunk: { code, constants },
    };
    this.allocate(func);
    return func;
  }

  createClosure(func: ZoyaFunction, upvalues: ZoyaValue[]): ZoyaClosure {
    const clos: ZoyaClosure = {
      __zoya_type: 'closure',
      __id: allocateObjectId(),
      function: func,
      upvalues,
    };
    this.allocate(clos);
    return clos;
  }
}

export interface GCStats {
  objectCount: number;
  allocationCount: number;
  threshold: number;
  collectedTotal: number;
  collectionsPerformed: number;
}
