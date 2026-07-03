/**
 * Zoya 3.0 - Intermediate Representation (SSA-style IR)
 *
 * Flat SSA-form IR with basic blocks, phi nodes, and a full instruction set
 * suitable for optimization and code generation.
 */

import {
  Program, Statement, Expression, BlockStatement, IfStatement, WhileStatement,
  ForStatement, ReturnStatement, VariableDeclaration, FunctionDeclaration,
  BinaryExpression, UnaryExpression, AssignmentExpression, CallExpression,
  Identifier, Literal, ExpressionStatement, BreakStatement, ContinueStatement,
  LoopStatement, LambdaExpression, MemberExpression, IndexExpression,
} from '../ast/index';

/* ------------------------------------------------------------------ */
/*  IR Types                                                          */
/* ------------------------------------------------------------------ */

export enum IRType {
  I1 = 'i1',
  I8 = 'i8',
  I16 = 'i16',
  I32 = 'i32',
  I64 = 'i64',
  F32 = 'f32',
  F64 = 'f64',
  Ptr = 'ptr',
  Void = 'void',
}

export function irTypeSize(type: IRType): number {
  switch (type) {
    case IRType.I1: return 1;
    case IRType.I8: return 1;
    case IRType.I16: return 2;
    case IRType.I32: return 4;
    case IRType.I64: return 8;
    case IRType.F32: return 4;
    case IRType.F64: return 8;
    case IRType.Ptr: return 8;
    case IRType.Void: return 0;
  }
}

export function irTypeFromName(name: string): IRType {
  switch (name) {
    case 'i1': return IRType.I1;
    case 'i8': return IRType.I8;
    case 'i16': return IRType.I16;
    case 'i32': return IRType.I32;
    case 'i64': return IRType.I64;
    case 'f32': return IRType.F32;
    case 'f64': return IRType.F64;
    case 'ptr': return IRType.Ptr;
    default: return IRType.I64;
  }
}

/* ------------------------------------------------------------------ */
/*  IR Opcodes                                                        */
/* ------------------------------------------------------------------ */

export enum IROpcode {
  Add = 'Add',
  Sub = 'Sub',
  Mul = 'Mul',
  Div = 'Div',
  Mod = 'Mod',
  Neg = 'Neg',
  Not = 'Not',
  And = 'And',
  Or = 'Or',
  Xor = 'Xor',
  Shl = 'Shl',
  Shr = 'Shr',
  Load = 'Load',
  Store = 'Store',
  Alloca = 'Alloca',
  GetElementPtr = 'GetElementPtr',
  Branch = 'Branch',
  BranchIf = 'BranchIf',
  BranchIfNot = 'BranchIfNot',
  Call = 'Call',
  NativeCall = 'NativeCall',
  Return = 'Return',
  ReturnVoid = 'ReturnVoid',
  IntToFloat = 'IntToFloat',
  FloatToInt = 'FloatToInt',
  Trunc = 'Trunc',
  ZExt = 'ZExt',
  SExt = 'SExt',
  Phi = 'Phi',
  Switch = 'Switch',
  Unreachable = 'Unreachable',
  ConstI1 = 'ConstI1',
  ConstI8 = 'ConstI8',
  ConstI16 = 'ConstI16',
  ConstI32 = 'ConstI32',
  ConstI64 = 'ConstI64',
  ConstF32 = 'ConstF32',
  ConstF64 = 'ConstF64',
  ConstStr = 'ConstStr',
}

/* ------------------------------------------------------------------ */
/*  Operands                                                          */
/* ------------------------------------------------------------------ */

export type IROperand =
  | { kind: 'ref'; type: IRType; id: number }
  | { kind: 'const'; type: IRType; value: number | boolean | string };

export function operandRef(id: number, type: IRType): IROperand {
  return { kind: 'ref', type, id };
}

export function operandConst(value: number | boolean | string, type?: IRType): IROperand {
  const t = type ?? (typeof value === 'boolean' ? IRType.I1 :
    typeof value === 'string' ? IRType.Ptr : IRType.I64);
  return { kind: 'const', type: t, value };
}

export function operandEq(a: IROperand, b: IROperand): boolean {
  if (a.kind !== b.kind || a.type !== b.type) return false;
  if (a.kind === 'ref') return (b as typeof a).id === a.id;
  return (b as typeof a).value === a.value;
}

/* ------------------------------------------------------------------ */
/*  IR Instruction                                                    */
/* ------------------------------------------------------------------ */

let nextInstructionId = 1;

export class IRInstruction {
  readonly id: number;
  opcode: IROpcode;
  readonly type: IRType;
  operands: IROperand[];
  block: BasicBlock | null = null;
  metadata: Record<string, unknown> = {};

  constructor(opcode: IROpcode, type: IRType, operands: IROperand[] = []) {
    this.id = nextInstructionId++;
    this.opcode = opcode;
    this.type = type;
    this.operands = operands;
  }

  isTerminator(): boolean {
    switch (this.opcode) {
      case IROpcode.Branch:
      case IROpcode.BranchIf:
      case IROpcode.BranchIfNot:
      case IROpcode.Return:
      case IROpcode.ReturnVoid:
      case IROpcode.Switch:
      case IROpcode.Unreachable:
        return true;
      default:
        return false;
    }
  }

  isSideEffecting(): boolean {
    switch (this.opcode) {
      case IROpcode.Store:
      case IROpcode.Call:
      case IROpcode.NativeCall:
      case IROpcode.Return:
      case IROpcode.ReturnVoid:
      case IROpcode.Branch:
      case IROpcode.BranchIf:
      case IROpcode.BranchIfNot:
      case IROpcode.Switch:
      case IROpcode.Unreachable:
        return true;
      default:
        return false;
    }
  }

  isBinary(): boolean {
    switch (this.opcode) {
      case IROpcode.Add:
      case IROpcode.Sub:
      case IROpcode.Mul:
      case IROpcode.Div:
      case IROpcode.Mod:
      case IROpcode.And:
      case IROpcode.Or:
      case IROpcode.Xor:
      case IROpcode.Shl:
      case IROpcode.Shr:
        return true;
      default:
        return false;
    }
  }

  clone(): IRInstruction {
    const inst = new IRInstruction(this.opcode, this.type, [...this.operands]);
    inst.metadata = { ...this.metadata };
    return inst;
  }

  toString(): string {
    const ops = this.operands.map(op => {
      if (op.kind === 'ref') return `%${op.id}`;
      return `${op.value}`;
    }).join(', ');
    return `%${this.id} = ${this.opcode} ${this.type} ${ops}`.trim();
  }
}

export function resetInstructionIds(): void {
  nextInstructionId = 1;
}

/* ------------------------------------------------------------------ */
/*  Basic Block                                                       */
/* ------------------------------------------------------------------ */

export class BasicBlock {
  readonly label: string;
  readonly instructions: IRInstruction[] = [];
  readonly predecessors: BasicBlock[] = [];
  readonly successors: BasicBlock[] = [];
  private inserted = false;

  constructor(label: string) {
    this.label = label;
  }

  get terminator(): IRInstruction | null {
    if (this.instructions.length === 0) return null;
    const last = this.instructions[this.instructions.length - 1];
    return last.isTerminator() ? last : null;
  }

  get isTerminated(): boolean {
    return this.terminator !== null;
  }

  get phis(): IRInstruction[] {
    return this.instructions.filter(i => i.opcode === IROpcode.Phi);
  }

  pushInst(inst: IRInstruction): IRInstruction {
    inst.block = this;
    if (this.isTerminated) {
      this.instructions.splice(this.instructions.length - 1, 0, inst);
    } else {
      this.instructions.push(inst);
    }
    return inst;
  }

  insertPhi(type: IRType, incoming: { value: IROperand; block: BasicBlock }[]): IRInstruction {
    const operands: IROperand[] = [];
    for (const inc of incoming) {
      operands.push(inc.value);
    }
    const phi = new IRInstruction(IROpcode.Phi, type, operands);
    phi.block = this;
    this.instructions.splice(this.findPhiEnd(), 0, phi);
    return phi;
  }

  private findPhiEnd(): number {
    for (let i = 0; i < this.instructions.length; i++) {
      if (this.instructions[i].opcode !== IROpcode.Phi) return i;
    }
    return this.instructions.length;
  }

  addSuccessor(block: BasicBlock): void {
    if (!this.successors.includes(block)) {
      this.successors.push(block);
    }
    if (!block.predecessors.includes(this)) {
      block.predecessors.push(this);
    }
  }

  removeSuccessor(block: BasicBlock): void {
    const si = this.successors.indexOf(block);
    if (si >= 0) this.successors.splice(si, 1);
    const pi = block.predecessors.indexOf(this);
    if (pi >= 0) block.predecessors.splice(pi, 1);
  }

  replaceSuccessor(oldBlock: BasicBlock, newBlock: BasicBlock): void {
    if (this.successors.includes(oldBlock)) {
      this.removeSuccessor(oldBlock);
      this.addSuccessor(newBlock);
    }
  }

  dump(): string {
    let s = `\n${this.label}:\n`;
    s += `  ; preds: ${this.predecessors.map(b => b.label).join(', ') || 'none'}\n`;
    for (const inst of this.instructions) {
      s += `  ${inst}\n`;
    }
    return s;
  }
}

/* ------------------------------------------------------------------ */
/*  Function                                                          */
/* ------------------------------------------------------------------ */

export class Function {
  readonly name: string;
  readonly parameters: { name: string; type: IRType }[];
  readonly returnType: IRType;
  readonly blocks: BasicBlock[] = [];
  entry: BasicBlock | null = null;
  isNative = false;

  constructor(name: string, returnType: IRType = IRType.Void, parameters: { name: string; type: IRType }[] = []) {
    this.name = name;
    this.returnType = returnType;
    this.parameters = parameters;
  }

  createBlock(label: string): BasicBlock {
    const block = new BasicBlock(label);
    this.blocks.push(block);
    return block;
  }

  setEntryBlock(block: BasicBlock): void {
    this.entry = block;
    if (!this.blocks.includes(block)) {
      this.blocks.unshift(block);
    }
  }

  removeBlock(block: BasicBlock): void {
    const idx = this.blocks.indexOf(block);
    if (idx >= 0) {
      this.blocks.splice(idx, 1);
      for (const pred of [...block.predecessors]) {
        pred.removeSuccessor(block);
      }
      for (const succ of [...block.successors]) {
        block.removeSuccessor(succ);
      }
    }
    if (this.entry === block) {
      this.entry = this.blocks.length > 0 ? this.blocks[0] : null;
    }
  }

  instructionCount(): number {
    let count = 0;
    for (const block of this.blocks) {
      count += block.instructions.length;
    }
    return count;
  }

  dump(): string {
    let s = `\nfun ${this.name}(${this.parameters.map(p => `${p.name}: ${p.type}`).join(', ')}): ${this.returnType}`;
    if (this.isNative) s += ' [native]';
    s += ' {';
    for (const block of this.blocks) {
      s += block.dump();
    }
    s += '\n}\n';
    return s;
  }
}

/* ------------------------------------------------------------------ */
/*  Module                                                            */
/* ------------------------------------------------------------------ */

export class Module {
  readonly functions: Function[] = [];
  readonly globals: Map<string, { type: IRType; init?: IROperand }> = new Map();
  name: string;

  constructor(name = '<module>') {
    this.name = name;
  }

  addFunction(fn: Function): void {
    this.functions.push(fn);
  }

  getFunction(name: string): Function | undefined {
    return this.functions.find(f => f.name === name);
  }

  removeFunction(fn: Function): void {
    const idx = this.functions.indexOf(fn);
    if (idx >= 0) this.functions.splice(idx, 1);
  }

  dump(): string {
    let s = `; Module: ${this.name}\n`;
    for (const fn of this.functions) {
      s += fn.dump();
    }
    return s;
  }
}

/* ------------------------------------------------------------------ */
/*  IR Printer                                                        */
/* ------------------------------------------------------------------ */

export class IRPrinter {
  private output: string[] = [];

  print(module: Module): string {
    this.output = [];
    this.line(`; Zoya 3.0 IR - Module: ${module.name}`);
    this.line('');
    for (const [name, global] of module.globals) {
      this.line(`@${name} = global ${global.type}${global.init ? ` = ${formatOperand(global.init)}` : ''}`);
    }
    if (module.globals.size > 0) this.line('');
    for (const fn of module.functions) {
      this.printFunction(fn);
    }
    return this.output.join('\n');
  }

  printFunction(fn: Function): void {
    const params = fn.parameters.map(p => `${p.name}: ${p.type}`).join(', ');
    this.line(`fun ${fn.name}(${params}): ${fn.returnType} {`);
    for (const block of fn.blocks) {
      this.printBlock(block);
    }
    this.line('}');
    this.line('');
  }

  printBlock(block: BasicBlock): void {
    this.line(`  ${block.label}:`);
    if (block.predecessors.length > 0) {
      this.line(`    ; preds: ${block.predecessors.map(b => b.label).join(', ')}`);
    }
    for (const inst of block.instructions) {
      this.line(`    ${formatInstruction(inst)}`);
    }
  }

  private line(text: string): void {
    this.output.push(text);
  }
}

function formatOperand(op: IROperand): string {
  if (op.kind === 'ref') return `%${op.id}`;
  if (typeof op.value === 'string') return `"${op.value}"`;
  return `${op.value}`;
}

function formatInstruction(inst: IRInstruction): string {
  if (inst.opcode === IROpcode.ReturnVoid) return 'return void';
  if (inst.opcode === IROpcode.Branch) {
    const target = inst.operands[0];
    return `branch ${formatOperand(target)}`;
  }
  if (inst.opcode === IROpcode.BranchIf) {
    return `branch_if ${formatOperand(inst.operands[0])}, ${formatOperand(inst.operands[1])}, ${formatOperand(inst.operands[2])}`;
  }
  if (inst.opcode === IROpcode.BranchIfNot) {
    return `branch_if_not ${formatOperand(inst.operands[0])}, ${formatOperand(inst.operands[1])}, ${formatOperand(inst.operands[2])}`;
  }
  if (inst.opcode === IROpcode.Store) {
    return `store ${formatOperand(inst.operands[0])}, ${formatOperand(inst.operands[1])}`;
  }
  if (inst.opcode === IROpcode.Return) {
    return `return ${formatOperand(inst.operands[0])}`;
  }
  if (inst.opcode === IROpcode.Phi) {
    const vals = inst.operands.map((op, i) => `[ ${formatOperand(op)} ]`).join(', ');
    return `%${inst.id} = phi ${inst.type} ${vals}`;
  }

  const result = inst.type === IRType.Void ? '' : `%${inst.id} = `;
  const ops = inst.operands.map(formatOperand).join(', ');
  return `${result}${inst.opcode} ${inst.type}${ops ? ' ' + ops : ''}`.trim();
}

/* ------------------------------------------------------------------ */
/*  Verifier                                                          */
/* ------------------------------------------------------------------ */

export interface VerifierError {
  message: string;
  block?: BasicBlock;
  instruction?: IRInstruction;
}

export class Verifier {
  private errors: VerifierError[] = [];

  verify(module: Module): VerifierError[] {
    this.errors = [];
    for (const fn of module.functions) {
      this.verifyFunction(fn);
    }
    return this.errors;
  }

  private error(msg: string, block?: BasicBlock, inst?: IRInstruction): void {
    this.errors.push({ message: msg, block, instruction: inst });
  }

  private verifyFunction(fn: Function): void {
    if (!fn.entry) {
      this.error(`Function '${fn.name}' has no entry block`);
      return;
    }

    if (fn.blocks.length === 0) {
      this.error(`Function '${fn.name}' has no blocks`);
      return;
    }

    if (fn.blocks[0] !== fn.entry) {
      this.error(`Function '${fn.name}' entry block must be first block`);
    }

    const visited = new Set<BasicBlock>();
    const worklist = [fn.entry];

    while (worklist.length > 0) {
      const block = worklist.pop()!;
      if (visited.has(block)) continue;
      visited.add(block);

      if (!block.isTerminated) {
        this.error(`Block '${block.label}' is not terminated`, block);
      }

      for (const succ of block.successors) {
        if (!fn.blocks.includes(succ)) {
          this.error(`Block '${block.label}' has successor '${succ.label}' not in function`, block);
        }
        if (!succ.predecessors.includes(block)) {
          this.error(`Block '${succ.label}' missing predecessor '${block.label}'`, block);
        }
        worklist.push(succ);
      }

      for (const inst of block.instructions) {
        if (inst.block !== block) {
          this.error(`Instruction %${inst.id} block pointer mismatch`, block, inst);
        }
        if (inst.opcode === IROpcode.Phi) {
          const expectedOps = block.predecessors.length;
          if (inst.operands.length !== expectedOps && expectedOps > 0) {
            this.error(`Phi node %${inst.id} in '${block.label}' has ${inst.operands.length} operands but ${expectedOps} predecessors`, block, inst);
          }
        }
      }
    }

    for (const block of fn.blocks) {
      if (!visited.has(block)) {
        this.error(`Block '${block.label}' is unreachable`, block);
      }
    }
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  formatErrors(): string {
    return this.errors.map(e => `  ERROR: ${e.message}`).join('\n');
  }
}

/* ------------------------------------------------------------------ */
/*  IRBuilder — walks AST → IR                                        */
/* ------------------------------------------------------------------ */

type VarScope = Map<string, number>;
type BlockRef = BasicBlock | string;

export class IRBuilder {
  private module: Module = new Module();
  private currentFn: Function | null = null;
  private currentBlock: BasicBlock | null = null;
  private scopes: VarScope[] = [new Map()];
  private breakTargets: BasicBlock[] = [];
  private continueTargets: BasicBlock[] = [];

  build(program: Program): Module {
    resetInstructionIds();
    this.module = new Module();
    for (const stmt of program.body) {
      if (stmt.type === 'FunctionDeclaration') {
        this.buildFunction(stmt);
      }
    }
    return this.module;
  }

  getModule(): Module {
    return this.module;
  }

  /* Scope management */
  private pushScope(): void {
    this.scopes.push(new Map());
  }

  private popScope(): void {
    this.scopes.pop();
  }

  private setVar(name: string, id: number): void {
    for (let i = this.scopes.length - 1; i >= 0; i--) {
      if (this.scopes[i].has(name)) {
        this.scopes[i].set(name, id);
        return;
      }
    }
    this.scopes[this.scopes.length - 1].set(name, id);
  }

  private getVar(name: string): number | undefined {
    for (let i = this.scopes.length - 1; i >= 0; i--) {
      if (this.scopes[i].has(name)) return this.scopes[i].get(name);
    }
    return undefined;
  }

  /* Emit instruction */
  private emit(opcode: IROpcode, type: IRType, operands: IROperand[] = [], metadata?: Record<string, unknown>): IRInstruction {
    const inst = new IRInstruction(opcode, type, operands);
    if (metadata) inst.metadata = metadata;
    if (this.currentBlock) {
      this.currentBlock.pushInst(inst);
    }
    return inst;
  }

  private emitRef(opcode: IROpcode, type: IRType, operands: IROperand[] = []): IROperand {
    const inst = this.emit(opcode, type, operands);
    return operandRef(inst.id, type);
  }

  /* Basic block creation */
  setInsertionPoint(block: BasicBlock): void {
    this.currentBlock = block;
  }

  currentInsertionPoint(): BasicBlock | null {
    return this.currentBlock;
  }

  /* --- Function building --- */

  buildFunction(fnDecl: FunctionDeclaration): void {
    const params = fnDecl.params.map(p => ({
      name: p.pattern.type === 'Identifier' ? p.pattern.name : '@param',
      type: IRType.I64,
    }));

    const fn = new Function(fnDecl.id.name, IRType.I64, params);
    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);
    this.module.addFunction(fn);

    this.currentFn = fn;
    this.currentBlock = entry;
    this.pushScope();

    for (const [i, param] of fnDecl.params.entries()) {
      if (param.pattern.type === 'Identifier') {
        const pInst = this.emit(IROpcode.Alloca, IRType.Ptr, [operandConst(8), operandConst(8)]);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(pInst.id, IRType.Ptr), operandConst(0)]);
        this.setVar(param.pattern.name, pInst.id);
      }
    }

    this.buildBlockBody(fnDecl.body);

    if (this.currentBlock && !this.currentBlock.isTerminated) {
      this.emit(IROpcode.ReturnVoid, IRType.Void, []);
    }

    this.popScope();
    this.currentFn = null;
    this.currentBlock = null;
  }

  /* --- Statement building --- */

  private buildBlockBody(block: BlockStatement): void {
    this.pushScope();
    for (const stmt of block.body) {
      this.buildStatement(stmt);
    }
    this.popScope();
  }

  private buildStatement(stmt: Statement): void {
    switch (stmt.type) {
      case 'VariableDeclaration': return this.buildVarDecl(stmt);
      case 'ExpressionStatement': return this.buildExprStatement(stmt);
      case 'BlockStatement': return this.buildBlockBody(stmt);
      case 'IfStatement': return this.buildIfStatement(stmt);
      case 'WhileStatement': return this.buildWhileStatement(stmt);
      case 'ForStatement': return this.buildForStatement(stmt);
      case 'ReturnStatement': return this.buildReturnStatement(stmt);
      case 'BreakStatement': return this.buildBreakStatement(stmt);
      case 'ContinueStatement': return this.buildContinueStatement(stmt);
      case 'LoopStatement': return this.buildLoopStatement(stmt);
      case 'FunctionDeclaration': break;
    }
  }

  private buildVarDecl(decl: VariableDeclaration): void {
    for (const d of decl.declarations) {
      const type = d.typeAnnotation ? irTypeFromName(d.typeAnnotation.name) : IRType.I64;
      const alloca = this.emit(IROpcode.Alloca, IRType.Ptr, [operandConst(8), operandConst(type === IRType.I64 ? 8 : 4)]);
      this.setVar(d.id.name, alloca.id);

      if (d.init) {
        const val = this.buildExpression(d.init);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(alloca.id, IRType.Ptr), val]);
      }
    }
  }

  private buildExprStatement(stmt: ExpressionStatement): void {
    this.buildExpression(stmt.expression);
  }

  /* --- Expression building --- */

  private buildExpression(expr: Expression): IROperand {
    switch (expr.type) {
      case 'Literal': return this.buildLiteral(expr);
      case 'Identifier': return this.buildIdentifier(expr);
      case 'BinaryExpression': return this.buildBinary(expr);
      case 'UnaryExpression': return this.buildUnary(expr);
      case 'AssignmentExpression': return this.buildAssignment(expr);
      case 'CallExpression': return this.buildCall(expr);
      case 'MemberExpression': return this.buildMember(expr);
      case 'IndexExpression': return this.buildIndex(expr);
      default: return operandConst(0);
    }
  }

  private buildLiteral(lit: Literal): IROperand {
    if (lit.value === null) return operandConst(0, IRType.I64);
    if (typeof lit.value === 'boolean') return operandConst(lit.value, IRType.I1);
    if (typeof lit.value === 'number') {
      if (Number.isInteger(lit.value)) return operandConst(lit.value, IRType.I64);
      return operandConst(lit.value, IRType.F64);
    }
    return operandConst(lit.value, IRType.Ptr);
  }

  private buildIdentifier(id: Identifier): IROperand {
    const varId = this.getVar(id.name);
    if (varId !== undefined) {
      return this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
    }
    return operandConst(0);
  }

  private buildBinary(bin: BinaryExpression): IROperand {
    const left = this.buildExpression(bin.left);
    const right = this.buildExpression(bin.right);
    const opType = IRType.I64;

    switch (bin.operator) {
      case '+': return this.emitRef(IROpcode.Add, opType, [left, right]);
      case '-': return this.emitRef(IROpcode.Sub, opType, [left, right]);
      case '*': return this.emitRef(IROpcode.Mul, opType, [left, right]);
      case '/': return this.emitRef(IROpcode.Div, opType, [left, right]);
      case '%': return this.emitRef(IROpcode.Mod, opType, [left, right]);
      case '&': return this.emitRef(IROpcode.And, opType, [left, right]);
      case '|': return this.emitRef(IROpcode.Or, opType, [left, right]);
      case '^': return this.emitRef(IROpcode.Xor, opType, [left, right]);
      case '<<': return this.emitRef(IROpcode.Shl, opType, [left, right]);
      case '>>': return this.emitRef(IROpcode.Shr, opType, [left, right]);
      case '==':
      case '===': {
        const cmp = this.emitRef(IROpcode.Sub, opType, [left, right]);
        return this.emitRef(IROpcode.Not, IRType.I1, [cmp]);
      }
      case '!=':
      case '!==': {
        const cmp = this.emitRef(IROpcode.Sub, opType, [left, right]);
        return this.emitRef(IROpcode.Not, IRType.I1, [cmp]);
      }
      case '<': return this.emitRef(IROpcode.Shr, IRType.I1, [left, right]);
      case '>': {
        const rev = this.emitRef(IROpcode.Sub, opType, [right, left]);
        return this.emitRef(IROpcode.Shr, IRType.I1, [left, rev]);
      }
      case '<=': {
        const cmp = this.emitRef(IROpcode.Sub, opType, [left, right]);
        return this.emitRef(IROpcode.Not, IRType.I1, [cmp]);
      }
      case '>=': {
        const cmp = this.emitRef(IROpcode.Sub, opType, [right, left]);
        return this.emitRef(IROpcode.Not, IRType.I1, [cmp]);
      }
      case '&&': {
        const result = this.emit(IROpcode.Alloca, IRType.Ptr, [operandConst(1), operandConst(1)]);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(result.id, IRType.Ptr), left]);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(result.id, IRType.Ptr), right]);
        return this.emitRef(IROpcode.Load, IRType.I64, [operandRef(result.id, IRType.Ptr)]);
      }
      case '||': {
        const result2 = this.emit(IROpcode.Alloca, IRType.Ptr, [operandConst(1), operandConst(1)]);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(result2.id, IRType.Ptr), left]);
        this.emit(IROpcode.Store, IRType.Void, [operandRef(result2.id, IRType.Ptr), right]);
        return this.emitRef(IROpcode.Load, IRType.I64, [operandRef(result2.id, IRType.Ptr)]);
      }
      default:
        return left;
    }
  }

  private buildUnary(un: UnaryExpression): IROperand {
    const arg = this.buildExpression(un.argument);
    switch (un.operator) {
      case '-': return this.emitRef(IROpcode.Neg, IRType.I64, [arg]);
      case '+': return arg;
      case '!': return this.emitRef(IROpcode.Not, IRType.I1, [arg]);
      case '~': return this.emitRef(IROpcode.Not, IRType.I64, [arg]);
      default: return arg;
    }
  }

  private buildAssignment(assign: AssignmentExpression): IROperand {
    if (assign.left.type === 'Identifier') {
      const varId = this.getVar(assign.left.name);
      const val = this.buildExpression(assign.right);

      if (varId !== undefined) {
        switch (assign.operator) {
          case '=':
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), val]);
            break;
          case '+=': {
            const loaded = this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
            const sum = this.emitRef(IROpcode.Add, IRType.I64, [loaded, val]);
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), sum]);
            break;
          }
          case '-=': {
            const loaded2 = this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
            const sub = this.emitRef(IROpcode.Sub, IRType.I64, [loaded2, val]);
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), sub]);
            break;
          }
          case '*=': {
            const loaded3 = this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
            const mul = this.emitRef(IROpcode.Mul, IRType.I64, [loaded3, val]);
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), mul]);
            break;
          }
          case '/=': {
            const loaded4 = this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
            const div = this.emitRef(IROpcode.Div, IRType.I64, [loaded4, val]);
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), div]);
            break;
          }
          default:
            this.emit(IROpcode.Store, IRType.Void, [operandRef(varId, IRType.Ptr), val]);
            break;
        }
        return this.emitRef(IROpcode.Load, IRType.I64, [operandRef(varId, IRType.Ptr)]);
      }
    }

    const val = this.buildExpression(assign.right);
    return val;
  }

  private buildCall(call: CallExpression): IROperand {
    const args: IROperand[] = [];
    for (const arg of call.arguments) {
      args.push(this.buildExpression(arg));
    }

    if (call.callee.type === 'Identifier') {
      return this.emitRef(IROpcode.Call, IRType.I64, [
        operandConst(call.callee.name, IRType.Ptr),
        ...args,
      ]);
    }

    const callee = this.buildExpression(call.callee);
    return this.emitRef(IROpcode.Call, IRType.I64, [callee, ...args]);
  }

  private buildMember(expr: MemberExpression): IROperand {
    const obj = this.buildExpression(expr.object);
    const prop = this.buildExpression({ type: 'Literal', span: expr.span, value: expr.property.name, raw: expr.property.name } as Literal);
    return this.emitRef(IROpcode.GetElementPtr, IRType.Ptr, [obj, prop]);
  }

  private buildIndex(expr: IndexExpression): IROperand {
    const obj = this.buildExpression(expr.object);
    const idx = this.buildExpression(expr.index);
    return this.emitRef(IROpcode.GetElementPtr, IRType.Ptr, [obj, idx]);
  }

  /* --- Control flow --- */

  private buildIfStatement(stmt: IfStatement): void {
    if (!this.currentFn || !this.currentBlock) return;
    const fn = this.currentFn;
    const cond = this.buildExpression(stmt.test);

    const thenBlock = fn.createBlock('if.then');
    const elseBlock = stmt.alternate ? fn.createBlock('if.else') : null;
    const mergeBlock = fn.createBlock('if.merge');

    if (elseBlock) {
      this.emit(IROpcode.BranchIf, IRType.Void, [
        cond,
        operandRef(thenBlock.instructions.length > 0 ? thenBlock.instructions[0].id : 0, IRType.Ptr),
        operandRef(elseBlock.instructions.length > 0 ? elseBlock.instructions[0].id : 0, IRType.Ptr),
      ]);
      this.currentBlock!.addSuccessor(thenBlock);
      this.currentBlock!.addSuccessor(elseBlock);
    } else {
      this.emit(IROpcode.BranchIfNot, IRType.Void, [
        cond,
        operandRef(mergeBlock.instructions.length > 0 ? mergeBlock.instructions[0].id : 0, IRType.Ptr),
      ]);
      this.currentBlock!.addSuccessor(thenBlock);
      this.currentBlock!.addSuccessor(mergeBlock);
    }

    const savedScope = new Map(this.scopes[this.scopes.length - 1]);

    this.currentBlock = thenBlock;
    this.buildStatement(stmt.consequent);
    if (this.currentBlock && !this.currentBlock.isTerminated) {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(mergeBlock.instructions.length > 0 ? mergeBlock.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock.addSuccessor(mergeBlock);
    }

    const thenScope = new Map(this.scopes[this.scopes.length - 1]);
    this.scopes[this.scopes.length - 1] = savedScope;

    if (elseBlock) {
      this.currentBlock = elseBlock;
      this.buildStatement(stmt.alternate!);
      if (this.currentBlock && !this.currentBlock.isTerminated) {
        this.emit(IROpcode.Branch, IRType.Void, [operandRef(mergeBlock.instructions.length > 0 ? mergeBlock.instructions[0].id : 0, IRType.Ptr)]);
        this.currentBlock.addSuccessor(mergeBlock);
      }
      const elseScope = new Map(this.scopes[this.scopes.length - 1]);

      for (const [name, id] of thenScope) {
        const elseId = elseScope.get(name);
        if (elseId !== undefined && elseId !== id) {
          const phi = mergeBlock.insertPhi(IRType.I64, [
            { value: operandRef(id, IRType.I64), block: thenBlock },
            { value: operandRef(elseId, IRType.I64), block: elseBlock },
          ]);
          const alloca = this.emitWithBlock(mergeBlock, IROpcode.Alloca, IRType.Ptr, [operandConst(8), operandConst(8)]);
          this.emitWithBlock(mergeBlock, IROpcode.Store, IRType.Void, [operandRef(alloca.id, IRType.Ptr), operandRef(phi.id, IRType.I64)]);
          this.setVar(name, alloca.id);
        }
      }
    }

    this.currentBlock = mergeBlock;
  }

  private emitWithBlock(block: BasicBlock, opcode: IROpcode, type: IRType, operands: IROperand[]): IRInstruction {
    const saved = this.currentBlock;
    this.currentBlock = block;
    const inst = this.emit(opcode, type, operands);
    this.currentBlock = saved;
    return inst;
  }

  private buildWhileStatement(stmt: WhileStatement): void {
    if (!this.currentFn || !this.currentBlock) return;
    const fn = this.currentFn;

    const headerBlock = fn.createBlock('while.header');
    const bodyBlock = fn.createBlock('while.body');
    const exitBlock = fn.createBlock('while.exit');

    this.emit(IROpcode.Branch, IRType.Void, [operandRef(headerBlock.instructions.length > 0 ? headerBlock.instructions[0].id : 0, IRType.Ptr)]);
    this.currentBlock!.addSuccessor(headerBlock);

    this.currentBlock = headerBlock;
    const cond = this.buildExpression(stmt.test);
    this.emit(IROpcode.BranchIf, IRType.Void, [
      cond,
      operandRef(bodyBlock.instructions.length > 0 ? bodyBlock.instructions[0].id : 0, IRType.Ptr),
      operandRef(exitBlock.instructions.length > 0 ? exitBlock.instructions[0].id : 0, IRType.Ptr),
    ]);
    headerBlock.addSuccessor(bodyBlock);
    headerBlock.addSuccessor(exitBlock);

    this.currentBlock = bodyBlock;
    this.breakTargets.push(exitBlock);
    this.continueTargets.push(headerBlock);
    this.buildStatement(stmt.body);
    this.breakTargets.pop();
    this.continueTargets.pop();

    if (this.currentBlock && !this.currentBlock.isTerminated) {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(headerBlock.instructions.length > 0 ? headerBlock.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock.addSuccessor(headerBlock);
    }

    this.currentBlock = exitBlock;
  }

  private buildForStatement(stmt: ForStatement): void {
    if (!this.currentFn || !this.currentBlock) return;
    const fn = this.currentFn;

    this.pushScope();

    if (stmt.init) {
      this.buildStatement(stmt.init);
    }

    const headerBlock = fn.createBlock('for.header');
    const bodyBlock = fn.createBlock('for.body');
    const exitBlock = fn.createBlock('for.exit');
    const updateBlock = fn.createBlock('for.update');

    this.emit(IROpcode.Branch, IRType.Void, [operandRef(headerBlock.instructions.length > 0 ? headerBlock.instructions[0].id : 0, IRType.Ptr)]);
    this.currentBlock!.addSuccessor(headerBlock);

    this.currentBlock = headerBlock;
    if (stmt.test) {
      const cond = this.buildExpression(stmt.test);
      this.emit(IROpcode.BranchIf, IRType.Void, [
        cond,
        operandRef(bodyBlock.instructions.length > 0 ? bodyBlock.instructions[0].id : 0, IRType.Ptr),
        operandRef(exitBlock.instructions.length > 0 ? exitBlock.instructions[0].id : 0, IRType.Ptr),
      ]);
    } else {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(bodyBlock.instructions.length > 0 ? bodyBlock.instructions[0].id : 0, IRType.Ptr)]);
    }
    headerBlock.addSuccessor(bodyBlock);
    headerBlock.addSuccessor(exitBlock);

    this.currentBlock = bodyBlock;
    this.breakTargets.push(exitBlock);
    this.continueTargets.push(updateBlock);
    this.buildStatement(stmt.body);
    this.breakTargets.pop();
    this.continueTargets.pop();

    if (this.currentBlock && !this.currentBlock.isTerminated) {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(updateBlock.instructions.length > 0 ? updateBlock.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock.addSuccessor(updateBlock);
    }

    this.currentBlock = updateBlock;
    if (stmt.update) {
      this.buildExpression(stmt.update);
    }
    if (!this.currentBlock!.isTerminated) {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(headerBlock.instructions.length > 0 ? headerBlock.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock!.addSuccessor(headerBlock);
    }

    this.popScope();
    this.currentBlock = exitBlock;
  }

  private buildLoopStatement(stmt: LoopStatement): void {
    if (!this.currentFn || !this.currentBlock) return;
    const fn = this.currentFn;

    const bodyBlock = fn.createBlock('loop.body');
    const exitBlock = fn.createBlock('loop.exit');

    this.emit(IROpcode.Branch, IRType.Void, [operandRef(bodyBlock.instructions.length > 0 ? bodyBlock.instructions[0].id : 0, IRType.Ptr)]);
    this.currentBlock!.addSuccessor(bodyBlock);

    this.currentBlock = bodyBlock;
    this.breakTargets.push(exitBlock);
    this.continueTargets.push(bodyBlock);
    this.buildStatement(stmt.body);
    this.breakTargets.pop();
    this.continueTargets.pop();

    if (this.currentBlock && !this.currentBlock.isTerminated) {
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(bodyBlock.instructions.length > 0 ? bodyBlock.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock.addSuccessor(bodyBlock);
    }

    this.currentBlock = exitBlock;
  }

  private buildReturnStatement(stmt: ReturnStatement): void {
    if (stmt.argument) {
      const val = this.buildExpression(stmt.argument);
      this.emit(IROpcode.Return, IRType.Void, [val]);
    } else {
      this.emit(IROpcode.ReturnVoid, IRType.Void, []);
    }
  }

  private buildBreakStatement(_stmt: BreakStatement): void {
    if (this.breakTargets.length > 0) {
      const target = this.breakTargets[this.breakTargets.length - 1];
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(target.instructions.length > 0 ? target.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock!.addSuccessor(target);
    }
  }

  private buildContinueStatement(_stmt: ContinueStatement): void {
    if (this.continueTargets.length > 0) {
      const target = this.continueTargets[this.continueTargets.length - 1];
      this.emit(IROpcode.Branch, IRType.Void, [operandRef(target.instructions.length > 0 ? target.instructions[0].id : 0, IRType.Ptr)]);
      this.currentBlock!.addSuccessor(target);
    }
  }
}
