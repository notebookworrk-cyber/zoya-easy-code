/**
 * Zoya 3.0 - Code Generator
 *
 * Primary: Bytecode generation for the Zoya VM.
 * Stub: Native code generation interface for future LLVM backend.
 */

import {
  Module, Function, BasicBlock, IRInstruction, IROpcode, IRType, IROperand,
} from '../ir/index';

/* ------------------------------------------------------------------ */
/*  Bytecode Opcodes                                                  */
/* ------------------------------------------------------------------ */

export const enum BytecodeOp {
  NOP = 0x00,
  LOAD_CONST = 0x01,
  LOAD_LOCAL = 0x02,
  STORE_LOCAL = 0x03,
  ADD = 0x04,
  SUB = 0x05,
  MUL = 0x06,
  DIV = 0x07,
  MOD = 0x08,
  NEG = 0x09,
  NOT = 0x0A,
  AND = 0x0B,
  OR = 0x0C,
  XOR = 0x0D,
  SHL = 0x0E,
  SHR = 0x0F,
  CMP_EQ = 0x10,
  CMP_NE = 0x11,
  CMP_LT = 0x12,
  CMP_GT = 0x13,
  CMP_LE = 0x14,
  CMP_GE = 0x15,
  BRANCH = 0x16,
  BRANCH_IF = 0x17,
  BRANCH_IF_NOT = 0x18,
  CALL = 0x19,
  NATIVE_CALL = 0x1A,
  RETURN = 0x1B,
  RETURN_VOID = 0x1C,
  ALLOCA = 0x1D,
  LOAD = 0x1E,
  STORE = 0x1F,
  PHI = 0x20,
  SWITCH = 0x21,
  UNREACHABLE = 0x22,
  INT_TO_FLOAT = 0x23,
  FLOAT_TO_INT = 0x24,
  TRUNC = 0x25,
  ZEXT = 0x26,
  SEXT = 0x27,
  GET_ELEMENT_PTR = 0x28,
}

/* ------------------------------------------------------------------ */
/*  Constant Pool                                                     */
/* ------------------------------------------------------------------ */

export interface ConstantPoolEntry {
  type: 'number' | 'string' | 'boolean' | 'null';
  value: number | string | boolean | null;
}

export interface BytecodeChunk {
  code: Uint8Array;
  constants: ConstantPoolEntry[];
  locals: number;
  debug: DebugInfo;
}

export interface DebugInfo {
  sourceMap: Map<number, { line: number; column: number }>;
  functionName: string;
}

/* ------------------------------------------------------------------ */
/*  BytecodeEmitter — instruction stream                               */
/* ------------------------------------------------------------------ */

class BytecodeStream {
  private buffer: number[] = [];
  private position = 0;

  writeByte(b: number): void {
    this.buffer.push(b & 0xFF);
    this.position++;
  }

  writeWord(w: number): void {
    this.writeByte(w & 0xFF);
    this.writeByte((w >> 8) & 0xFF);
  }

  writeDWord(dw: number): void {
    this.writeByte(dw & 0xFF);
    this.writeByte((dw >> 8) & 0xFF);
    this.writeByte((dw >> 16) & 0xFF);
    this.writeByte((dw >> 24) & 0xFF);
  }

  writeBytes(bytes: number[]): void {
    for (const b of bytes) this.writeByte(b);
  }

  currentOffset(): number {
    return this.position;
  }

  patchAt(offset: number, value: number): void {
    this.buffer[offset] = value & 0xFF;
    if (offset + 1 < this.buffer.length) {
      this.buffer[offset + 1] = (value >> 8) & 0xFF;
    }
  }

  toUint8Array(): Uint8Array {
    return new Uint8Array(this.buffer);
  }
}

/* ------------------------------------------------------------------ */
/*  BytecodeGen — IR → Bytecode                                       */
/* ------------------------------------------------------------------ */

export class BytecodeGen {
  private stream = new BytecodeStream();
  private constants: ConstantPoolEntry[] = [];
  private constantMap = new Map<string, number>();
  private localMap = new Map<number, number>();
  private nextLocal = 0;
  private blockLabels = new Map<string, number>();
  private pendingBranches: { block: string; offset: number }[] = [];
  private debug: DebugInfo = { sourceMap: new Map(), functionName: '' };
  private module: Module | null = null;

  generate(module: Module): BytecodeChunk[] {
    this.module = module;
    const chunks: BytecodeChunk[] = [];

    for (const fn of module.functions) {
      const chunk = this.generateFunction(fn);
      chunks.push(chunk);
    }

    return chunks;
  }

  private generateFunction(fn: Function): BytecodeChunk {
    this.stream = new BytecodeStream();
    this.constants = [];
    this.constantMap = new Map();
    this.localMap = new Map();
    this.nextLocal = 0;
    this.blockLabels = new Map();
    this.pendingBranches = [];
    this.debug = { sourceMap: new Map(), functionName: fn.name };

    this.allocateLocals(fn);

    for (const param of fn.parameters) {
      this.getOrAllocateLocal(param.name);
    }

    for (const block of fn.blocks) {
      this.blockLabels.set(block.label, this.stream.currentOffset());
      this.emitBlock(block);
    }

    this.resolveBranches();

    return {
      code: this.stream.toUint8Array(),
      constants: this.constants,
      locals: this.nextLocal,
      debug: this.debug,
    };
  }

  private allocateLocals(fn: Function): void {
    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        this.localMap.set(inst.id, this.nextLocal++);
      }
    }
  }

  private getOrAllocateLocal(name: string): number {
    const idx = this.nextLocal++;
    return idx;
  }

  private localSlot(instId: number): number {
    return this.localMap.get(instId) ?? 0;
  }

  private addConstant(value: number | string | boolean | null): number {
    const key = String(value);
    const existing = this.constantMap.get(key);
    if (existing !== undefined) return existing;

    let type: ConstantPoolEntry['type'];
    if (value === null) type = 'null';
    else if (typeof value === 'boolean') type = 'boolean';
    else if (typeof value === 'number') type = 'number';
    else type = 'string';

    const idx = this.constants.length;
    this.constants.push({ type, value });
    this.constantMap.set(key, idx);
    return idx;
  }

  private emitBlock(block: BasicBlock): void {
    for (const inst of block.instructions) {
      this.emitInstruction(inst);
    }
  }

  private emitInstruction(inst: IRInstruction): void {
    switch (inst.opcode) {
      case IROpcode.Add:
        this.stream.writeByte(BytecodeOp.ADD);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Sub:
        this.stream.writeByte(BytecodeOp.SUB);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Mul:
        this.stream.writeByte(BytecodeOp.MUL);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Div:
        this.stream.writeByte(BytecodeOp.DIV);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Mod:
        this.stream.writeByte(BytecodeOp.MOD);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Neg:
        this.stream.writeByte(BytecodeOp.NEG);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.Not:
        this.stream.writeByte(BytecodeOp.NOT);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.And:
        this.stream.writeByte(BytecodeOp.AND);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Or:
        this.stream.writeByte(BytecodeOp.OR);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Xor:
        this.stream.writeByte(BytecodeOp.XOR);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Shl:
        this.stream.writeByte(BytecodeOp.SHL);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Shr:
        this.stream.writeByte(BytecodeOp.SHR);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Alloca:
        this.stream.writeByte(BytecodeOp.ALLOCA);
        this.stream.writeWord(this.localSlot(inst.id));
        break;

      case IROpcode.Load:
        this.stream.writeByte(BytecodeOp.LOAD);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.Store:
        this.stream.writeByte(BytecodeOp.STORE);
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.GetElementPtr:
        this.stream.writeByte(BytecodeOp.GET_ELEMENT_PTR);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        this.emitOperandRef(inst.operands[1]);
        break;

      case IROpcode.Branch: {
        const targetLabel = this.resolveBlockLabel(inst.operands[0]);
        this.stream.writeByte(BytecodeOp.BRANCH);
        const offset = this.stream.currentOffset();
        this.stream.writeWord(0);
        this.pendingBranches.push({ block: targetLabel, offset });
        break;
      }

      case IROpcode.BranchIf: {
        const trueLabel = this.resolveBlockLabel(inst.operands[1]);
        const falseLabel = this.resolveBlockLabel(inst.operands[2]);
        this.stream.writeByte(BytecodeOp.BRANCH_IF);
        this.emitOperandRef(inst.operands[0]);
        const offset1 = this.stream.currentOffset();
        this.stream.writeWord(0);
        const offset2 = this.stream.currentOffset();
        this.stream.writeWord(0);
        this.pendingBranches.push({ block: trueLabel, offset: offset1 });
        this.pendingBranches.push({ block: falseLabel, offset: offset2 });
        break;
      }

      case IROpcode.BranchIfNot: {
        const exitLabel = this.resolveBlockLabel(inst.operands[1]);
        this.stream.writeByte(BytecodeOp.BRANCH_IF_NOT);
        this.emitOperandRef(inst.operands[0]);
        const offset = this.stream.currentOffset();
        this.stream.writeWord(0);
        this.pendingBranches.push({ block: exitLabel, offset });
        break;
      }

      case IROpcode.Call: {
        this.stream.writeByte(BytecodeOp.CALL);
        if (inst.operands[0].kind === 'const' && typeof inst.operands[0].value === 'string') {
          const nameIdx = this.addConstant(inst.operands[0].value);
          this.stream.writeWord(nameIdx);
        } else {
          this.stream.writeWord(0);
        }
        this.stream.writeWord(this.localSlot(inst.id));
        this.stream.writeWord(inst.operands.length - 1);
        for (let i = 1; i < inst.operands.length; i++) {
          this.emitOperandRef(inst.operands[i]);
        }
        break;
      }

      case IROpcode.NativeCall: {
        this.stream.writeByte(BytecodeOp.NATIVE_CALL);
        this.emitOperandRef(inst.operands[0]);
        this.stream.writeWord(inst.operands.length - 1);
        for (let i = 1; i < inst.operands.length; i++) {
          this.emitOperandRef(inst.operands[i]);
        }
        break;
      }

      case IROpcode.Return:
        this.stream.writeByte(BytecodeOp.RETURN);
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.ReturnVoid:
        this.stream.writeByte(BytecodeOp.RETURN_VOID);
        break;

      case IROpcode.Phi: {
        this.stream.writeByte(BytecodeOp.PHI);
        this.stream.writeWord(this.localSlot(inst.id));
        this.stream.writeWord(inst.operands.length);
        for (const op of inst.operands) {
          this.emitOperandRef(op);
        }
        break;
      }

      case IROpcode.Switch:
        this.stream.writeByte(BytecodeOp.SWITCH);
        this.emitOperandRef(inst.operands[0]);
        this.stream.writeWord((inst.operands.length - 1) / 2);
        for (let i = 1; i < inst.operands.length; i++) {
          this.emitOperandRef(inst.operands[i]);
        }
        break;

      case IROpcode.Unreachable:
        this.stream.writeByte(BytecodeOp.UNREACHABLE);
        break;

      case IROpcode.IntToFloat:
        this.stream.writeByte(BytecodeOp.INT_TO_FLOAT);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.FloatToInt:
        this.stream.writeByte(BytecodeOp.FLOAT_TO_INT);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.Trunc:
        this.stream.writeByte(BytecodeOp.TRUNC);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.ZExt:
        this.stream.writeByte(BytecodeOp.ZEXT);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      case IROpcode.SExt:
        this.stream.writeByte(BytecodeOp.SEXT);
        this.stream.writeWord(this.localSlot(inst.id));
        this.emitOperandRef(inst.operands[0]);
        break;

      default:
        this.stream.writeByte(BytecodeOp.NOP);
        break;
    }
  }

  private emitOperandRef(op: IROperand): void {
    if (op.kind === 'ref') {
      this.stream.writeByte(1);
      this.stream.writeWord(this.localSlot(op.id));
    } else {
      this.stream.writeByte(0);
      const constIdx = this.addConstant(
        typeof op.value === 'string' ? op.value :
        typeof op.value === 'boolean' ? op.value :
        op.value as number
      );
      this.stream.writeWord(constIdx);
    }
  }

  private resolveBlockLabel(op: IROperand): string {
    return op.kind === 'const' && typeof op.value === 'string' ? op.value : '';
  }

  private resolveBranches(): void {
    for (const pending of this.pendingBranches) {
      const targetOffset = this.blockLabels.get(pending.block);
      if (targetOffset !== undefined) {
        this.stream.patchAt(pending.offset, targetOffset);
      }
    }
    this.pendingBranches = [];
  }
}

/* ------------------------------------------------------------------ */
/*  Bytecode Disassembler (Debug)                                     */
/* ------------------------------------------------------------------ */

export class BytecodeDisassembler {
  disassemble(chunk: BytecodeChunk): string {
    let output = `=== ${chunk.debug.functionName} ===\n`;
    output += `locals: ${chunk.locals}, constants: ${chunk.constants.length}\n\n`;

    output += 'Constants:\n';
    for (let i = 0; i < chunk.constants.length; i++) {
      const c = chunk.constants[i];
      output += `  ${i}: ${c.type} = ${c.value}\n`;
    }
    output += '\nCode:\n';

    let offset = 0;
    const code = chunk.code;
    while (offset < code.length) {
      const op = code[offset];
      const [text, advance] = this.disassembleOp(op, code, offset, chunk);
      output += `  ${offset.toString(16).padStart(4, '0')}: ${text}\n`;
      offset += advance;
    }

    return output;
  }

  private disassembleOp(op: number, code: Uint8Array, offset: number, chunk: BytecodeChunk): [string, number] {
    const opNames: Record<number, string> = {
      [BytecodeOp.NOP]: 'NOP',
      [BytecodeOp.LOAD_CONST]: 'LOAD_CONST',
      [BytecodeOp.LOAD_LOCAL]: 'LOAD_LOCAL',
      [BytecodeOp.STORE_LOCAL]: 'STORE_LOCAL',
      [BytecodeOp.ADD]: 'ADD',
      [BytecodeOp.SUB]: 'SUB',
      [BytecodeOp.MUL]: 'MUL',
      [BytecodeOp.DIV]: 'DIV',
      [BytecodeOp.MOD]: 'MOD',
      [BytecodeOp.NEG]: 'NEG',
      [BytecodeOp.NOT]: 'NOT',
      [BytecodeOp.AND]: 'AND',
      [BytecodeOp.OR]: 'OR',
      [BytecodeOp.XOR]: 'XOR',
      [BytecodeOp.SHL]: 'SHL',
      [BytecodeOp.SHR]: 'SHR',
      [BytecodeOp.CMP_EQ]: 'CMP_EQ',
      [BytecodeOp.CMP_NE]: 'CMP_NE',
      [BytecodeOp.CMP_LT]: 'CMP_LT',
      [BytecodeOp.CMP_GT]: 'CMP_GT',
      [BytecodeOp.CMP_LE]: 'CMP_LE',
      [BytecodeOp.CMP_GE]: 'CMP_GE',
      [BytecodeOp.BRANCH]: 'BRANCH',
      [BytecodeOp.BRANCH_IF]: 'BRANCH_IF',
      [BytecodeOp.BRANCH_IF_NOT]: 'BRANCH_IF_NOT',
      [BytecodeOp.CALL]: 'CALL',
      [BytecodeOp.NATIVE_CALL]: 'NATIVE_CALL',
      [BytecodeOp.RETURN]: 'RETURN',
      [BytecodeOp.RETURN_VOID]: 'RETURN_VOID',
      [BytecodeOp.ALLOCA]: 'ALLOCA',
      [BytecodeOp.LOAD]: 'LOAD',
      [BytecodeOp.STORE]: 'STORE',
      [BytecodeOp.PHI]: 'PHI',
      [BytecodeOp.SWITCH]: 'SWITCH',
      [BytecodeOp.UNREACHABLE]: 'UNREACHABLE',
      [BytecodeOp.INT_TO_FLOAT]: 'INT_TO_FLOAT',
      [BytecodeOp.FLOAT_TO_INT]: 'FLOAT_TO_INT',
      [BytecodeOp.TRUNC]: 'TRUNC',
      [BytecodeOp.ZEXT]: 'ZEXT',
      [BytecodeOp.SEXT]: 'SEXT',
      [BytecodeOp.GET_ELEMENT_PTR]: 'GET_ELEMENT_PTR',
    };

    const name = opNames[op] ?? `UNKNOWN_${op}`;
    const fmt = (n: number) => `${n}`;

    switch (op) {
      case BytecodeOp.NOP:
      case BytecodeOp.RETURN_VOID:
      case BytecodeOp.UNREACHABLE:
        return [name, 1];

      case BytecodeOp.ADD:
      case BytecodeOp.SUB:
      case BytecodeOp.MUL:
      case BytecodeOp.DIV:
      case BytecodeOp.MOD:
      case BytecodeOp.NEG:
      case BytecodeOp.NOT:
      case BytecodeOp.AND:
      case BytecodeOp.OR:
      case BytecodeOp.XOR:
      case BytecodeOp.SHL:
      case BytecodeOp.SHR:
      case BytecodeOp.INT_TO_FLOAT:
      case BytecodeOp.FLOAT_TO_INT:
      case BytecodeOp.TRUNC:
      case BytecodeOp.ZEXT:
      case BytecodeOp.SEXT:
      case BytecodeOp.ALLOCA:
      case BytecodeOp.LOAD:
      case BytecodeOp.GET_ELEMENT_PTR: {
        const local = (code[offset + 1] | (code[offset + 2] << 8));
        return [`${name} local(${fmt(local)})`, 3];
      }

      case BytecodeOp.BRANCH: {
        const target = (code[offset + 1] | (code[offset + 2] << 8));
        return [`${name} -> ${fmt(target)}`, 3];
      }

      case BytecodeOp.BRANCH_IF:
      case BytecodeOp.BRANCH_IF_NOT: {
        const mode = code[offset + 1];
        let extra = 3;
        let desc = `${name} mode(${mode})`;
        if (mode === 0) {
          extra = 5;
          const ci = code[offset + 2] | (code[offset + 3] << 8);
          const c = chunk.constants[ci];
          desc = `${name} const(${c.value}) -> `;
          const t1 = code[offset + 4] | (code[offset + 5] << 8);
          desc += `${fmt(t1)}`;
          extra = 6;
        } else {
          const local = code[offset + 2] | (code[offset + 3] << 8);
          const target = code[offset + 4] | (code[offset + 5] << 8);
          desc = `${name} local(${fmt(local)}) -> ${fmt(target)}`;
          extra = 6;
        }
        return [desc, extra];
      }

      case BytecodeOp.RETURN: {
        const mode = code[offset + 1];
        if (mode === 0) {
          const ci = code[offset + 2] | (code[offset + 3] << 8);
          const c = chunk.constants[ci];
          return [`${name} const(${c.value})`, 4];
        }
        const local = code[offset + 2] | (code[offset + 3] << 8);
        return [`${name} local(${fmt(local)})`, 4];
      }

      case BytecodeOp.CALL: {
        const ci = code[offset + 1] | (code[offset + 2] << 8);
        const local = code[offset + 3] | (code[offset + 4] << 8);
        const argc = code[offset + 5] | (code[offset + 6] << 8);
        return [`${name} name(${ci}) local(${fmt(local)}) argc(${fmt(argc)})`, 7 + argc * 3];
      }

      case BytecodeOp.PHI: {
        const local = code[offset + 1] | (code[offset + 2] << 8);
        const count = code[offset + 3] | (code[offset + 4] << 8);
        return [`${name} local(${fmt(local)}) count(${fmt(count)})`, 5 + count * 3];
      }

      case BytecodeOp.STORE: {
        return [`${name}`, 1];
      }

      default:
        return [`${name} (size unknown)`, 1];
    }
  }
}

/* ------------------------------------------------------------------ */
/*  Native Codegen Stub                                               */
/* ------------------------------------------------------------------ */

export interface NativeCodegenOptions {
  outputFormat: 'object' | 'shared-library' | 'executable';
  optimizationLevel: 0 | 1 | 2 | 3;
  targetTriple?: string;
}

export interface NativeCodegenResult {
  success: boolean;
  outputPath?: string;
  objectBytes?: Uint8Array;
  errors: string[];
}

export interface NativeCodegen {
  readonly name: string;
  initialize(options: NativeCodegenOptions): boolean;
  generate(module: Module): NativeCodegenResult;
  emitObject(result: NativeCodegenResult, path: string): boolean;
}

export class NativeCodegenStub implements NativeCodegen {
  readonly name = 'stub-native-codegen';
  private options: NativeCodegenOptions = { outputFormat: 'object', optimizationLevel: 0 };

  initialize(options: NativeCodegenOptions): boolean {
    this.options = options;
    return true;
  }

  generate(_module: Module): NativeCodegenResult {
    return {
      success: false,
      errors: ['Native code generation is a stub. Use LLVM backend for actual native code.'],
    };
  }

  emitObject(_result: NativeCodegenResult, _path: string): boolean {
    return false;
  }
}
