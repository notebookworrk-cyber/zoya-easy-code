import { describe, it, expect } from 'vitest';
import {
  Module, Function, BasicBlock, IRInstruction, IROpcode, IRType,
  operandConst, operandRef, resetInstructionIds,
} from '../../src/compiler/ir/index';
import {
  PassManager, ConstantFolding, DeadCodeElimination, AlgebraicSimplification,
  StrengthReduction, CommonSubexpressionElimination, TailCallOptimization,
  FunctionInlining, LoopOptimization, EscapeAnalysis,
  createDefaultPasses, createFullPasses,
} from '../../src/compiler/optimizer/index';

function makeModule(name?: string): Module {
  resetInstructionIds();
  return new Module(name);
}

function makeFunction(name: string, returnType?: IRType): Function {
  return new Function(name, returnType ?? IRType.I64);
}

function makeBlock(label: string, fn: Function): BasicBlock {
  const block = fn.createBlock(label);
  return block;
}

function addReturn(block: BasicBlock, value?: IRInstruction): void {
  if (value) {
    block.pushInst(new IRInstruction(IROpcode.Return, IRType.Void, [operandRef(value.id, IRType.I64)]));
  } else {
    block.pushInst(new IRInstruction(IROpcode.ReturnVoid, IRType.Void, []));
  }
}

function addAdd(block: BasicBlock, a: number, b: number): IRInstruction {
  const inst = new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(a), operandConst(b)]);
  block.pushInst(inst);
  return inst;
}

function addSub(block: BasicBlock, a: number, b: number): IRInstruction {
  const inst = new IRInstruction(IROpcode.Sub, IRType.I64, [operandConst(a), operandConst(b)]);
  block.pushInst(inst);
  return inst;
}

function addMul(block: BasicBlock, a: IROperand, b: IROperand): IRInstruction {
  const inst = new IRInstruction(IROpcode.Mul, IRType.I64, [a, b]);
  block.pushInst(inst);
  return inst;
}

function addLoad(block: BasicBlock, ptr: IRInstruction): IRInstruction {
  const inst = new IRInstruction(IROpcode.Load, IRType.I64, [operandRef(ptr.id, IRType.Ptr)]);
  block.pushInst(inst);
  return inst;
}

function addStore(block: BasicBlock, ptr: IRInstruction, val: IROperand): void {
  block.pushInst(new IRInstruction(IROpcode.Store, IRType.Void, [val, operandRef(ptr.id, IRType.Ptr)]));
}

function addAlloca(block: BasicBlock): IRInstruction {
  const inst = new IRInstruction(IROpcode.Alloca, IRType.Ptr, [operandConst(8), operandConst(8)]);
  block.pushInst(inst);
  return inst;
}

/* ------------------------------------------------------------------ */
/*  ConstantFolding Tests                                             */
/* ------------------------------------------------------------------ */

describe('ConstantFolding', () => {
  it('folds 1 + 2 into 3', () => {
    resetInstructionIds();
    const mod = makeModule('test');
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const add = addAdd(entry, 1, 2);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new ConstantFolding();
    const changed = pass.run(mod);

    expect(changed).toBe(true);
    expect(entry.instructions.filter(i => i.opcode === IROpcode.Add)).toHaveLength(0);
  });

  it('folds 10 - 3 into 7', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const sub = addSub(entry, 10, 3);
    addReturn(entry, sub);
    mod.addFunction(fn);

    const pass = new ConstantFolding();
    expect(pass.run(mod)).toBe(true);
    expect(entry.instructions.filter(i => i.opcode === IROpcode.Sub)).toHaveLength(0);
  });

  it('does not fold non-constant operands', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const a = new IRInstruction(IROpcode.Alloca, IRType.Ptr);
    entry.pushInst(a);
    const load = addLoad(entry, a);
    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(5)]);
    entry.pushInst(add);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new ConstantFolding();
    expect(pass.run(mod)).toBe(false);
  });

  it('is idempotent after folding', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const add = addAdd(entry, 7, 8);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new ConstantFolding();
    pass.run(mod);
    const changed = pass.run(mod);
    expect(changed).toBe(false);
  });
});

/* ------------------------------------------------------------------ */
/*  DeadCodeElimination Tests                                         */
/* ------------------------------------------------------------------ */

describe('DeadCodeElimination', () => {
  it('removes unused instruction', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    addAdd(entry, 1, 2);
    addReturn(entry);
    mod.addFunction(fn);

    expect(entry.instructions.length).toBe(2);

    const pass = new DeadCodeElimination();
    const changed = pass.run(mod);

    expect(changed).toBe(true);
    expect(entry.instructions.filter(i => !i.isTerminator())).toHaveLength(0);
  });

  it('keeps used instructions', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const add = addAdd(entry, 1, 2);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new DeadCodeElimination();
    expect(pass.run(mod)).toBe(false);
    expect(entry.instructions.filter(i => i.opcode === IROpcode.Add)).toHaveLength(1);
  });

  it('is idempotent', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    addAdd(entry, 1, 2);
    addReturn(entry);
    mod.addFunction(fn);

    const pass = new DeadCodeElimination();
    pass.run(mod);
    expect(pass.run(mod)).toBe(false);
  });
});

/* ------------------------------------------------------------------ */
/*  AlgebraicSimplification Tests                                     */
/* ------------------------------------------------------------------ */

describe('AlgebraicSimplification', () => {
  it('simplifies x + 0 -> x', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(0)]);
    entry.pushInst(add);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new AlgebraicSimplification();
    expect(pass.run(mod)).toBe(true);
    expect(entry.instructions.filter(i => i.opcode === IROpcode.Add && i.id !== add.id)).toHaveLength(0);
  });

  it('simplifies x * 1 -> x', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = new IRInstruction(IROpcode.Mul, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(1)]);
    entry.pushInst(mul);
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new AlgebraicSimplification();
    expect(pass.run(mod)).toBe(true);
    expect(entry.instructions.filter(i => i.opcode === IROpcode.Mul)).toHaveLength(0);
  });

  it('simplifies x * 0 -> 0', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = new IRInstruction(IROpcode.Mul, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(0)]);
    entry.pushInst(mul);
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new AlgebraicSimplification();
    expect(pass.run(mod)).toBe(true);
    const remaining = entry.instructions.filter(i => i.opcode === IROpcode.Mul);
    expect(remaining).toHaveLength(0);
  });

  it('simplifies x - x -> 0', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const sub = new IRInstruction(IROpcode.Sub, IRType.I64, [operandRef(load.id, IRType.I64), operandRef(load.id, IRType.I64)]);
    entry.pushInst(sub);
    addReturn(entry, sub);
    mod.addFunction(fn);

    const pass = new AlgebraicSimplification();
    expect(pass.run(mod)).toBe(true);
  });

  it('is idempotent', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(0)]);
    entry.pushInst(add);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new AlgebraicSimplification();
    pass.run(mod);
    expect(pass.run(mod)).toBe(false);
  });
});

/* ------------------------------------------------------------------ */
/*  StrengthReduction Tests                                           */
/* ------------------------------------------------------------------ */

describe('StrengthReduction', () => {
  it('reduces x * 2 -> x << 1', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(2));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    expect(pass.run(mod)).toBe(true);
    const hasShl = entry.instructions.some(i => i.opcode === IROpcode.Shl);
    expect(hasShl).toBe(true);
  });

  it('reduces x * 8 -> x << 3', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(8));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    expect(pass.run(mod)).toBe(true);
    const shlInst = entry.instructions.find(i => i.opcode === IROpcode.Shl);
    expect(shlInst).toBeDefined();
    expect(shlInst!.operands[1].kind === 'const' && shlInst!.operands[1].value).toBe(3);
  });

  it('reduces x / 4 -> x >> 2', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const div = new IRInstruction(IROpcode.Div, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(4)]);
    entry.pushInst(div);
    addReturn(entry, div);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    expect(pass.run(mod)).toBe(true);
    const shrInst = entry.instructions.find(i => i.opcode === IROpcode.Shr);
    expect(shrInst).toBeDefined();
  });

  it('reduces x % 8 -> x & 7', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const modInst = new IRInstruction(IROpcode.Mod, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(8)]);
    entry.pushInst(modInst);
    addReturn(entry, modInst);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    expect(pass.run(mod)).toBe(true);
    const andInst = entry.instructions.find(i => i.opcode === IROpcode.And);
    expect(andInst).toBeDefined();
    const hasMod = entry.instructions.some(i => i.opcode === IROpcode.Mod);
    expect(hasMod).toBe(false);
  });

  it('does not reduce non-power-of-two multiplication', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(7));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    expect(pass.run(mod)).toBe(false);
  });

  it('is idempotent', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(2));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const pass = new StrengthReduction();
    pass.run(mod);
    expect(pass.run(mod)).toBe(false);
  });
});

/* ------------------------------------------------------------------ */
/*  CSE Tests                                                         */
/* ------------------------------------------------------------------ */

describe('CommonSubexpressionElimination', () => {
  it('eliminates redundant add within same block', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const a = new IRInstruction(IROpcode.Alloca, IRType.Ptr);
    entry.pushInst(a);
    const load = addLoad(entry, a);

    const add1 = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(5)]);
    entry.pushInst(add1);
    const add2 = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(5)]);
    entry.pushInst(add2);
    addReturn(entry, add2);
    mod.addFunction(fn);

    const initialAddCount = entry.instructions.filter(i => i.opcode === IROpcode.Add).length;
    expect(initialAddCount).toBe(2);

    const pass = new CommonSubexpressionElimination();
    const changed = pass.run(mod);

    expect(changed).toBe(true);
    const finalAddCount = entry.instructions.filter(i => i.opcode === IROpcode.Add).length;
    expect(finalAddCount).toBeLessThan(2);
  });

  it('does not eliminate different expressions', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const a = new IRInstruction(IROpcode.Alloca, IRType.Ptr);
    entry.pushInst(a);
    const load = addLoad(entry, a);

    const add1 = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(5)]);
    entry.pushInst(add1);
    const add2 = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(10)]);
    entry.pushInst(add2);
    addReturn(entry, add2);
    mod.addFunction(fn);

    const pass = new CommonSubexpressionElimination();
    expect(pass.run(mod)).toBe(false);
  });

  it('is idempotent', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const a = new IRInstruction(IROpcode.Alloca, IRType.Ptr);
    entry.pushInst(a);
    const load = addLoad(entry, a);
    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandRef(load.id, IRType.I64), operandConst(5)]);
    entry.pushInst(add);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pass = new CommonSubexpressionElimination();
    pass.run(mod);
    expect(pass.run(mod)).toBe(false);
  });
});

/* ------------------------------------------------------------------ */
/*  TailCallOptimization Tests                                        */
/* ------------------------------------------------------------------ */

describe('TailCallOptimization', () => {
  it('converts self-recursive tail call to jump', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('factorial', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const call = new IRInstruction(IROpcode.Call, IRType.I64, [
      operandConst('factorial'),
      operandConst(5),
    ]);
    entry.pushInst(call);
    entry.pushInst(new IRInstruction(IROpcode.Return, IRType.Void, [operandRef(call.id, IRType.I64)]));
    mod.addFunction(fn);

    const pass = new TailCallOptimization();
    const changed = pass.run(mod);

    expect(changed).toBe(true);
  });
});

/* ------------------------------------------------------------------ */
/*  PassManager Tests                                                 */
/* ------------------------------------------------------------------ */

describe('PassManager', () => {
  it('runs passes to fixpoint', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const add = addAdd(entry, 5, 3);
    addReturn(entry, add);
    mod.addFunction(fn);

    const pm = new PassManager(5);
    pm.addPass(new ConstantFolding());
    pm.addPass(new DeadCodeElimination());

    const changes = pm.run(mod);
    expect(changes).toBeGreaterThan(0);

    const hasAdd = entry.instructions.some(i => i.opcode === IROpcode.Add);
    expect(hasAdd).toBe(false);
  });

  it('stops after max iterations', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);
    addReturn(entry);
    mod.addFunction(fn);

    const pm = new PassManager(2);
    pm.addPass(new ConstantFolding());
    expect(() => pm.run(mod)).not.toThrow();
  });

  it('runs default pass pipeline without errors', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const a = new IRInstruction(IROpcode.Alloca, IRType.Ptr);
    entry.pushInst(a);
    const load = addLoad(entry, a);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(2));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const passes = createDefaultPasses();
    const pm = new PassManager(10);
    pm.addPasses(passes);
    expect(() => pm.run(mod)).not.toThrow();
  });

  it('runs full pass pipeline without errors', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    const mul = addMul(entry, operandRef(load.id, IRType.I64), operandConst(8));
    addReturn(entry, mul);
    mod.addFunction(fn);

    const passes = createFullPasses();
    const pm = new PassManager(10);
    pm.addPasses(passes);
    expect(() => pm.run(mod)).not.toThrow();
  });
});

/* ------------------------------------------------------------------ */
/*  EscapeAnalysis Tests                                              */
/* ------------------------------------------------------------------ */

describe('EscapeAnalysis', () => {
  it('marks non-escaping alloca as noescape', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('test', IRType.I64);
    const entry = makeBlock('entry', fn);
    fn.setEntryBlock(entry);

    const alloca = addAlloca(entry);
    const load = addLoad(entry, alloca);
    addReturn(entry, load);
    mod.addFunction(fn);

    const pass = new EscapeAnalysis();
    const changed = pass.run(mod);

    expect(changed).toBe(true);
    expect(alloca.metadata['noescape']).toBe(true);
  });
});
