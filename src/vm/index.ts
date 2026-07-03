import { Opcode } from './opcodes';
import { Chunk } from './chunk';
import {
  ZoyaValue, ZoyaObject, ZoyaArray, ZoyaFunction, ZoyaClosure,
  ZoyaNative, ZoyaUpvalue, ZoyaBoolean, ZoyaString, ZoyaNumber,
  ZoyaNull, ZOYA_NIL, ZOYA_TRUE, ZOYA_FALSE,
  isTruthy, isEqual, typeOf, allocateObjectId,
} from '../types';

const MAX_STACK = 256;
const MAX_FRAMES = 64;

interface CallFrame {
  closure: ZoyaClosure | ZoyaFunction;
  ip: number;
  stackBase: number;
  localCount: number;
}

interface TryHandler {
  catchIp: number;
  frameIndex: number;
  stackSize: number;
}

type NativeFn = (...args: ZoyaValue[]) => ZoyaValue;

export class VM {
  private stack: ZoyaValue[] = [];
  private frames: CallFrame[] = [];
  private globals: Map<string, ZoyaValue> = new Map();
  private openUpvalues: ZoyaUpvalue[] = [];
  private modules: Map<string, ZoyaValue> = new Map();
  private strings: Map<string, string> = new Map();
  private chunks: Chunk[] = [];
  private currentChunk: Chunk | null = null;
  private tryHandlers: TryHandler[] = [];
  private debugMode = false;
  private nativeFunctions: Map<string, { arity: number; fn: NativeFn }> = new Map();

  private gcAllocations = 0;
  private gcThreshold = 1000;
  private gcAllocatedObjects: ZoyaObject[] = [];

  constructor() {
    this.defineNative('clock', 0, () => Date.now());
    this.defineNative('print', 1, (val: ZoyaValue) => {
      const s = this.stringify(val);
      return s;
    });
    this.defineNative('str', 1, (val: ZoyaValue) => this.stringify(val));
    this.defineNative('num', 1, (val: ZoyaValue) => {
      if (typeof val === 'string') {
        const n = parseFloat(val);
        return isNaN(n) ? 0 : n;
      }
      if (typeof val === 'boolean') return val ? 1 : 0;
      if (typeof val === 'number') return val;
      return 0;
    });
    this.defineNative('bool', 1, (val: ZoyaValue) => isTruthy(val));
    this.defineNative('type', 1, (val: ZoyaValue) => typeOf(val));
    this.defineNative('len', 1, (val: ZoyaValue) => {
      if (typeof val === 'string') return val.length;
      if (val !== null && typeof val === 'object' && (val as ZoyaArray).__zoya_type === 'array') {
        return (val as ZoyaArray).length;
      }
      return 0;
    });
    this.defineNative('push', 2, (arr: ZoyaValue, val: ZoyaValue) => {
      if (arr !== null && typeof arr === 'object' && (arr as ZoyaArray).__zoya_type === 'array') {
        (arr as ZoyaArray).elements.push(val);
        (arr as ZoyaArray).length++;
      }
      return val;
    });
    this.defineNative('pop', 1, (arr: ZoyaValue) => {
      if (arr !== null && typeof arr === 'object' && (arr as ZoyaArray).__zoya_type === 'array') {
        const a = arr as ZoyaArray;
        if (a.length > 0) {
          a.length--;
          return a.elements.pop()!;
        }
      }
      return ZOYA_NIL;
    });
  }

  interpret(chunk: Chunk): ZoyaValue {
    this.currentChunk = chunk;
    this.chunks.push(chunk);

    const initialStackSize = this.stack.length;

    const fn: ZoyaFunction = {
      __zoya_type: 'function',
      __id: allocateObjectId(),
      name: '<script>',
      arity: 0,
      chunk: {
        code: chunk.getCode(),
        constants: chunk.constants,
      },
    };

    const closure: ZoyaClosure = {
      __zoya_type: 'closure',
      __id: allocateObjectId(),
      function: fn,
      upvalues: [],
    };

    this.push(closure);
    const closureStackSize = this.stack.length;

    const frame: CallFrame = {
      closure,
      ip: 0,
      stackBase: this.stack.length - 1,
      localCount: 0,
    };
    this.frames.push(frame);

    try {
      this.run();
    } catch (e) {
      this.stack.length = initialStackSize;
      throw e;
    }

    let result: ZoyaValue = ZOYA_NIL;
    if (this.stack.length > closureStackSize) {
      result = this.stack.pop()!;
    }

    this.stack.length = initialStackSize;
    return result;
  }

  private getFn(closure: ZoyaClosure | ZoyaFunction): ZoyaFunction {
    return 'function' in closure ? closure.function : closure;
  }

  private getUpvalues(closure: ZoyaClosure | ZoyaFunction): ZoyaValue[] {
    if ('upvalues' in closure && closure.upvalues) {
      return closure.upvalues;
    }
    return [];
  }

  private run(): void {
    const frame = this.frames[this.frames.length - 1];
    if (!frame) return;

    const fn = 'function' in frame.closure ? frame.closure.function : frame.closure;
    let ip = frame.ip;
    const code = (fn.chunk.code as unknown as number[]);

    this.gcAllocations++;
    if (this.gcAllocations >= this.gcThreshold) {
      this.collectGarbage();
    }

    while (ip < code.length) {
      const opcode = code[ip];
      ip++;

      switch (opcode) {
        case Opcode.HALT:
          ip = code.length;
          break;

        case Opcode.NOP:
          break;

        case Opcode.PUSH_NIL:
          this.push(ZOYA_NIL);
          break;

        case Opcode.PUSH_TRUE:
          this.push(ZOYA_TRUE);
          break;

        case Opcode.PUSH_FALSE:
          this.push(ZOYA_FALSE);
          break;

        case Opcode.PUSH_NUMBER:
        case Opcode.PUSH_INT: {
          const numVal = code[ip];
          ip++;
          this.push(numVal);
          break;
        }

        case Opcode.PUSH_STRING: {
          const strIdx = code[ip];
          ip++;
          const str = fn.chunk.constants[strIdx];
          this.push(str);
          break;
        }

        case Opcode.LOAD_CONST: {
          const constIdx = code[ip];
          ip++;
          const val = fn.chunk.constants[constIdx];
          this.push(val);
          break;
        }

        case Opcode.POP: {
          this.pop();
          break;
        }

        case Opcode.DUP: {
          const val = this.peek(0);
          this.push(val);
          break;
        }

        case Opcode.SWAP: {
          const a = this.pop();
          const b = this.pop();
          this.push(a);
          this.push(b);
          break;
        }

        case Opcode.LOAD_LOCAL: {
          const slot = code[ip];
          ip++;
          const idx = frame.stackBase + slot;
          this.push(this.stack[idx]);
          break;
        }

        case Opcode.STORE_LOCAL: {
          const slot = code[ip];
          ip++;
          const idx = frame.stackBase + slot;
          this.stack[idx] = this.peek(0);
          break;
        }

        case Opcode.LOAD_GLOBAL:
        case Opcode.GET_GLOBAL: {
          const nameIdx = code[ip];
          ip++;
          const name = this.stringify(this.getFn(frame.closure).chunk.constants[nameIdx]);
          const val = this.globals.get(name);
          if (val === undefined) {
            this.push(ZOYA_NIL);
          } else {
            this.push(val);
          }
          break;
        }

        case Opcode.STORE_GLOBAL:
        case Opcode.DEFINE_GLOBAL:
        case Opcode.SET_GLOBAL: {
          const nameIdx = code[ip];
          ip++;
          const name = this.stringify(this.getFn(frame.closure).chunk.constants[nameIdx]);
          this.globals.set(name, this.peek(0));
          break;
        }

        case Opcode.LOAD_UPVALUE: {
          const slot = code[ip];
          ip++;
          const upvalue = this.getUpvalues(frame.closure)[slot];
          if (upvalue !== undefined) {
            this.push(upvalue);
          } else {
            this.push(ZOYA_NIL);
          }
          break;
        }

        case Opcode.STORE_UPVALUE: {
          const slot = code[ip];
          ip++;
          const val = this.peek(0);
          // values stored directly for simplicity
          break;
        }

        case Opcode.ADD: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a + b);
          } else if (typeof a === 'string' || typeof b === 'string') {
            this.push(this.stringify(a) + this.stringify(b));
          } else {
            this.runtimeError('Operands must be numbers or strings for +');
            return;
          }
          break;
        }

        case Opcode.SUB: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a - b);
          } else {
            this.runtimeError('Operands must be numbers for -');
            return;
          }
          break;
        }

        case Opcode.MUL: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a * b);
          } else {
            this.runtimeError('Operands must be numbers for *');
            return;
          }
          break;
        }

        case Opcode.DIV: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            if (b === 0) {
              this.runtimeError('Division by zero');
              return;
            }
            this.push(a / b);
          } else {
            this.runtimeError('Operands must be numbers for /');
            return;
          }
          break;
        }

        case Opcode.MOD: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            if (b === 0) {
              this.runtimeError('Division by zero');
              return;
            }
            this.push(a % b);
          } else {
            this.runtimeError('Operands must be numbers for %');
            return;
          }
          break;
        }

        case Opcode.NEG: {
          const a = this.pop();
          if (typeof a === 'number') {
            this.push(-a);
          } else {
            this.runtimeError('Operand must be a number for negation');
            return;
          }
          break;
        }

        case Opcode.NOT: {
          const a = this.pop();
          this.push(!isTruthy(a));
          break;
        }

        case Opcode.BIT_NOT: {
          const a = this.pop();
          if (typeof a === 'number') {
            this.push(~a);
          } else {
            this.runtimeError('Operand must be a number for bitwise not');
            return;
          }
          break;
        }

        case Opcode.BIT_AND: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a & b);
          } else {
            this.runtimeError('Operands must be numbers for &');
            return;
          }
          break;
        }

        case Opcode.BIT_OR: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a | b);
          } else {
            this.runtimeError('Operands must be numbers for |');
            return;
          }
          break;
        }

        case Opcode.BIT_XOR: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a ^ b);
          } else {
            this.runtimeError('Operands must be numbers for ^');
            return;
          }
          break;
        }

        case Opcode.SHL: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a << b);
          } else {
            this.runtimeError('Operands must be numbers for <<');
            return;
          }
          break;
        }

        case Opcode.SHR: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a >> b);
          } else {
            this.runtimeError('Operands must be numbers for >>');
            return;
          }
          break;
        }

        case Opcode.EQUAL: {
          const b = this.pop();
          const a = this.pop();
          const eq = isEqual(a, b);
          this.push(eq);
          break;
        }

        case Opcode.NOT_EQUAL: {
          const b = this.pop();
          const a = this.pop();
          this.push(!isEqual(a, b));
          break;
        }

        case Opcode.LESS: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a < b);
          } else if (typeof a === 'string' && typeof b === 'string') {
            this.push(a < b);
          } else {
            this.runtimeError('Operands must be comparable for <');
            return;
          }
          break;
        }

        case Opcode.GREATER: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a > b);
          } else if (typeof a === 'string' && typeof b === 'string') {
            this.push(a > b);
          } else {
            this.runtimeError('Operands must be comparable for >');
            return;
          }
          break;
        }

        case Opcode.LESS_EQUAL: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a <= b);
          } else if (typeof a === 'string' && typeof b === 'string') {
            this.push(a <= b);
          } else {
            this.runtimeError('Operands must be comparable for <=');
            return;
          }
          break;
        }

        case Opcode.GREATER_EQUAL: {
          const b = this.pop();
          const a = this.pop();
          if (typeof a === 'number' && typeof b === 'number') {
            this.push(a >= b);
          } else if (typeof a === 'string' && typeof b === 'string') {
            this.push(a >= b);
          } else {
            this.runtimeError('Operands must be comparable for >=');
            return;
          }
          break;
        }

        case Opcode.JMP: {
          const offset = code[ip];
          ip++;
          ip += offset;
          break;
        }

        case Opcode.JMP_IF_FALSE: {
          const offset = code[ip];
          ip++;
          const val = this.peek(0);
          if (!isTruthy(val)) {
            ip += offset;
          }
          break;
        }

        case Opcode.JMP_IF_TRUE: {
          const offset = code[ip];
          ip++;
          const val = this.peek(0);
          if (isTruthy(val)) {
            ip += offset;
          }
          break;
        }

        case Opcode.LOOP: {
          const offset = code[ip];
          ip++;
          ip -= offset;
          break;
        }

        case Opcode.CALL: {
          const argCount = code[ip];
          ip++;
          const callee = this.stack[this.stack.length - 1 - argCount];

          if (callee !== null && typeof callee === 'object' && '__zoya_type' in callee) {
            const type = (callee as ZoyaObject).__zoya_type;

            if (type === 'function') {
              const func = callee as ZoyaFunction;
              if (func.arity !== argCount && func.arity !== -1) {
                this.runtimeError(`Function '${func.name}' expects ${func.arity} arguments but got ${argCount}`);
                return;
              }
              const closure: ZoyaClosure = {
                __zoya_type: 'closure',
                __id: allocateObjectId(),
                function: func,
                upvalues: [],
              };
              this.stack[this.stack.length - 1 - argCount] = closure;
              this.frames.push({
                closure,
                ip: 0,
                stackBase: this.stack.length - 1 - argCount,
                localCount: argCount,
              });
              ip = this.frames[this.frames.length - 1].ip;
              break;
            }

            if (type === 'closure') {
              const clos = callee as ZoyaClosure;
              if (clos.function.arity !== argCount && clos.function.arity !== -1) {
                this.runtimeError(`Closure '${clos.function.name}' expects ${clos.function.arity} arguments but got ${argCount}`);
                return;
              }
              this.frames.push({
                closure: clos,
                ip: 0,
                stackBase: this.stack.length - 1 - argCount,
                localCount: argCount,
              });
              ip = 0;
              break;
            }

            if (type === 'native') {
              const nat = callee as ZoyaNative;
              if (nat.arity !== argCount && nat.arity !== -1) {
                this.runtimeError(`Native function expects ${nat.arity} arguments but got ${argCount}`);
                return;
              }
              const args: ZoyaValue[] = [];
              for (let i = argCount - 1; i >= 0; i--) {
                args.unshift(this.stack[this.stack.length - 1 - i]);
              }
              for (let i = 0; i <= argCount; i++) {
                this.pop();
              }
              const result = nat.fn(...args);
              this.push(result);
              break;
            }
          }

          this.runtimeError('Can only call functions and closures');
          return;
        }

        case Opcode.CALL_NATIVE: {
          const argCount = code[ip];
          ip++;
          const nameIdx = code[ip];
          ip++;
          const name = this.stringify(this.getFn(frame.closure).chunk.constants[nameIdx]);
          const native = this.nativeFunctions.get(name);
          if (!native) {
            this.runtimeError(`Undefined native function: '${name}'`);
            return;
          }
          const args: ZoyaValue[] = [];
          for (let i = argCount - 1; i >= 0; i--) {
            args.unshift(this.stack[this.stack.length - 1 - i]);
          }
          for (let i = 0; i < argCount; i++) {
            this.pop();
          }
          const result = native.fn(...args);
          this.pop();
          this.push(result);
          break;
        }

        case Opcode.RETURN: {
          const result = this.pop();
          const currentFrame = this.frames.pop()!;
          const stackBase = currentFrame.stackBase;

          while (this.stack.length > stackBase) {
            this.pop();
          }

          if (this.frames.length > 0) {
            this.push(result);
            const newFrame = this.frames[this.frames.length - 1];
            ip = newFrame.ip;
            const codeArr = this.getFn(newFrame.closure).chunk.code as unknown as number[];
            if (ip < 0 || ip >= codeArr.length) {
              return;
            }
            break;
          }
          this.push(result);
          return;
        }

        case Opcode.CLOSURE:
        case Opcode.MAKE_CLOSURE: {
          const funcIdx = code[ip];
          ip++;
          const upvalueCount = code[ip];
          ip++;
          const func = this.getFn(frame.closure).chunk.constants[funcIdx];
          const upvalues: ZoyaValue[] = [];
          for (let i = 0; i < upvalueCount; i++) {
            const isLocal = code[ip];
            ip++;
            const index = code[ip];
            ip++;
            if (isLocal) {
              const captured = this.stack[frame.stackBase + index];
              upvalues.push(captured);
            } else {
              const captured = this.getUpvalues(frame.closure)[index];
              upvalues.push(captured !== undefined ? captured : ZOYA_NIL);
            }
          }
          if (func !== null && typeof func === 'object' && (func as ZoyaObject).__zoya_type === 'function') {
            const closure: ZoyaClosure = {
              __zoya_type: 'closure',
              __id: allocateObjectId(),
              function: func as ZoyaFunction,
              upvalues,
            };
            this.push(closure);
          } else {
            this.push(ZOYA_NIL);
          }
          break;
        }

        case Opcode.CLOSE_UPVALUE: {
          this.pop();
          break;
        }

        case Opcode.MAKE_ARRAY: {
          const count = code[ip];
          ip++;
          const elements: ZoyaValue[] = [];
          for (let i = 0; i < count; i++) {
            elements.unshift(this.pop());
          }
          const arr: ZoyaArray = {
            __zoya_type: 'array',
            __id: allocateObjectId(),
            elements,
            length: count,
          };
          this.gcTrackObject(arr);
          this.push(arr);
          break;
        }

        case Opcode.GET_INDEX: {
          const index = this.pop();
          const obj = this.pop();
          if (obj !== null && typeof obj === 'object' && (obj as ZoyaArray).__zoya_type === 'array') {
            const arr = obj as ZoyaArray;
            if (typeof index === 'number') {
              const idx = Math.floor(index);
              if (idx >= 0 && idx < arr.length) {
                this.push(arr.elements[idx]);
              } else {
                this.push(ZOYA_NIL);
              }
            } else {
              this.push(ZOYA_NIL);
            }
          } else {
            this.runtimeError('Cannot index non-array value');
            return;
          }
          break;
        }

        case Opcode.SET_INDEX: {
          const value = this.pop();
          const index = this.pop();
          const obj = this.pop();
          if (obj !== null && typeof obj === 'object' && (obj as ZoyaArray).__zoya_type === 'array') {
            const arr = obj as ZoyaArray;
            if (typeof index === 'number') {
              const idx = Math.floor(index);
              if (idx >= 0 && idx < arr.length) {
                arr.elements[idx] = value;
              }
            }
          }
          this.push(value);
          break;
        }

        case Opcode.GET_PROPERTY:
        case Opcode.GET_PROPERTY: {
          const nameIdx = code[ip];
          ip++;
          const name = this.stringify(this.getFn(frame.closure).chunk.constants[nameIdx]);
          const obj = this.pop();
          if (obj !== null && typeof obj === 'object') {
            const zObj = obj as ZoyaObject;
            if (zObj.__zoya_type === 'array') {
              if (name === 'length') {
                this.push((zObj as ZoyaArray).length);
                break;
              }
            }
          }
          this.push(ZOYA_NIL);
          break;
        }

        case Opcode.SET_PROPERTY: {
          const nameIdx = code[ip];
          ip++;
          const val = this.peek(0);
          this.pop();
          this.pop();
          this.push(val);
          break;
        }

        case Opcode.PRINT: {
          const val = this.pop();
          const s = this.stringify(val);
          break;
        }

        case Opcode.THROW: {
          const err = this.pop();
          this.runtimeError(this.stringify(err));
          return;
        }

        case Opcode.TRY: {
          const catchOffset = code[ip];
          ip++;
          this.tryHandlers.push({
            catchIp: ip + catchOffset,
            frameIndex: this.frames.length - 1,
            stackSize: this.stack.length,
          });
          break;
        }

        case Opcode.END_TRY: {
          if (this.tryHandlers.length > 0) {
            this.tryHandlers.pop();
          }
          break;
        }

        case Opcode.POP_HANDLER: {
          if (this.tryHandlers.length > 0) {
            this.tryHandlers.pop();
          }
          break;
        }

        case Opcode.SCOPE_ENTER:
          break;

        case Opcode.SCOPE_EXIT:
          break;

        default:
          this.runtimeError(`Unknown opcode: ${opcode}`);
          return;
      }
    }
  }

  push(value: ZoyaValue): void {
    if (this.stack.length >= MAX_STACK) {
      this.runtimeError('Stack overflow');
      return;
    }
    this.stack.push(value);
  }

  pop(): ZoyaValue {
    if (this.stack.length === 0) {
      this.runtimeError('Stack underflow');
      return ZOYA_NIL;
    }
    return this.stack.pop()!;
  }

  peek(distance: number): ZoyaValue {
    const idx = this.stack.length - 1 - distance;
    if (idx < 0) {
      return ZOYA_NIL;
    }
    return this.stack[idx];
  }

  runtimeError(message: string): void {
    const err = new Error(`RuntimeError: ${message}`);
    if (this.frames.length > 0) {
      const frame = this.frames[this.frames.length - 1];
      const name = this.getFn(frame.closure).name;
      const ip = frame.ip;
      err.message = `RuntimeError at ${name}+${ip}: ${message}`;
    }
    throw err;
  }

  defineNative(name: string, arity: number, fn: (...args: ZoyaValue[]) => ZoyaValue): void {
    const native: ZoyaNative = {
      __zoya_type: 'native',
      __id: allocateObjectId(),
      arity,
      fn,
    };
    this.globals.set(name, native);
    this.nativeFunctions.set(name, { arity, fn });
  }

  setGlobal(name: string, value: ZoyaValue): void {
    this.globals.set(name, value);
  }

  getGlobal(name: string): ZoyaValue | undefined {
    return this.globals.get(name);
  }

  private stringify(value: ZoyaValue): string {
    if (value === null) return 'nil';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return value.toString();
      return value.toString();
    }
    if (typeof value === 'string') return value;
    if (typeof value === 'object' && value !== null) {
      const obj = value as ZoyaObject;
      switch (obj.__zoya_type) {
        case 'function': return `<fn ${(value as ZoyaFunction).name}>`;
        case 'closure': return `<fn ${(value as ZoyaClosure).function.name}>`;
        case 'native': return `<native ${(value as ZoyaNative).arity}>`;
        case 'array': {
          const arr = value as ZoyaArray;
          return `[${arr.elements.map((e: ZoyaValue) => this.stringify(e)).join(', ')}]`;
        }
        case 'upvalue': return '<upvalue>';
        default: return `<${obj.__zoya_type}>`;
      }
    }
    return 'nil';
  }

  private gcTrackObject(obj: ZoyaObject): void {
    this.gcAllocatedObjects.push(obj);
    if (this.gcAllocatedObjects.length >= this.gcThreshold) {
      this.collectGarbage();
    }
  }

  private collectGarbage(): void {
    const marked = new Set<number>();

    for (const val of this.stack) {
      this.gcMarkValue(val, marked);
    }

    for (const val of this.globals.values()) {
      this.gcMarkValue(val, marked);
    }

    for (const frame of this.frames) {
      this.gcMarkValue(frame.closure, marked);
    }

    const survivors: ZoyaObject[] = [];
    for (const obj of this.gcAllocatedObjects) {
      if (marked.has(obj.__id)) {
        survivors.push(obj);
      }
    }
    this.gcAllocatedObjects = survivors;
  }

  private gcMarkValue(val: ZoyaValue, marked: Set<number>): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      if (marked.has(obj.__id)) return;
      marked.add(obj.__id);

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.gcMarkValue(elem, marked);
        }
      }
      if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.gcMarkValue(clos.function, marked);
        for (const uv of clos.upvalues) {
          this.gcMarkValue(uv, marked);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.gcMarkValue(c, marked);
        }
      }
    }
  }

  getStack(): readonly ZoyaValue[] {
    return this.stack;
  }

  getGlobals(): ReadonlyMap<string, ZoyaValue> {
    return this.globals;
  }

  getModules(): ReadonlyMap<string, ZoyaValue> {
    return this.modules;
  }

  getStackSize(): number {
    return this.stack.length;
  }

  clearStack(): void {
    this.stack = [];
  }

  reset(): void {
    this.stack = [];
    this.frames = [];
    this.tryHandlers = [];
    this.gcAllocatedObjects = [];
    this.gcAllocations = 0;
  }
}
