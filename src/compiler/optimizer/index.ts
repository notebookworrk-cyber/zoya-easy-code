/**
 * Zoya 3.0 - Multi-pass Optimizer
 *
 * Runs a set of optimization passes on the IR to fixpoint or max iterations.
 * Each pass implements the Pass interface with a `run(module): boolean` method.
 */

import {
  Module, Function, BasicBlock, IRInstruction, IROpcode, IRType, IROperand,
  operandRef, operandConst, operandEq,
} from '../ir/index';

/* ------------------------------------------------------------------ */
/*  Pass Interface                                                    */
/* ------------------------------------------------------------------ */

export interface Pass {
  readonly name: string;
  run(module: Module): boolean;
}

/* ------------------------------------------------------------------ */
/*  Pass Manager                                                      */
/* ------------------------------------------------------------------ */

export class PassManager {
  private passes: Pass[] = [];
  private maxIterations: number;

  constructor(maxIterations = 10) {
    this.maxIterations = maxIterations;
  }

  addPass(pass: Pass): void {
    this.passes.push(pass);
  }

  addPasses(passes: Pass[]): void {
    for (const p of passes) this.addPass(p);
  }

  run(module: Module): number {
    let totalChanges = 0;
    let iteration = 0;

    while (iteration < this.maxIterations) {
      let changed = false;
      for (const pass of this.passes) {
        const passChanged = pass.run(module);
        if (passChanged) {
          changed = true;
          totalChanges++;
        }
      }
      if (!changed) break;
      iteration++;
    }

    return totalChanges;
  }

  runPass(pass: Pass, module: Module): boolean {
    return pass.run(module);
  }

  clear(): void {
    this.passes = [];
  }
}

/* ------------------------------------------------------------------ */
/*  Utility helpers                                                   */
/* ------------------------------------------------------------------ */

function getOperandValue(op: IROperand): number | boolean | string | null {
  if (op.kind === 'const') return op.value;
  return null;
}

function isConstOperand(op: IROperand): boolean {
  return op.kind === 'const';
}

function isZero(op: IROperand): boolean {
  return op.kind === 'const' && op.value === 0;
}

function isOne(op: IROperand): boolean {
  return op.kind === 'const' && op.value === 1;
}

function isPowerOfTwo(val: number): boolean {
  return val > 0 && (val & (val - 1)) === 0;
}

function log2(val: number): number {
  let result = 0;
  while (val > 1) { val >>= 1; result++; }
  return result;
}

function replaceInstruction(oldInst: IRInstruction, newInst: IRInstruction, fn: Function): void {
  for (const block of fn.blocks) {
    for (const inst of block.instructions) {
      for (let i = 0; i < inst.operands.length; i++) {
        const op = inst.operands[i];
        if (op.kind === 'ref' && op.id === oldInst.id) {
          (inst as any).operands[i] = operandRef(newInst.id, op.type);
        }
      }
    }
  }
}

function replaceInstructionWithValue(oldInst: IRInstruction, value: IROperand, fn: Function): void {
  for (const block of fn.blocks) {
    for (const inst of block.instructions) {
      for (let i = 0; i < inst.operands.length; i++) {
        const op = inst.operands[i];
        if (op.kind === 'ref' && op.id === oldInst.id) {
          (inst as any).operands[i] = value;
        }
      }
    }
  }
}

function countUses(inst: IRInstruction, fn: Function): number {
  let uses = 0;
  for (const block of fn.blocks) {
    for (const i of block.instructions) {
      if (i === inst) continue;
      for (const op of i.operands) {
        if (op.kind === 'ref' && op.id === inst.id) uses++;
      }
    }
  }
  return uses;
}

function getConstIntValue(op: IROperand): number | null {
  if (op.kind === 'const' && typeof op.value === 'number') return op.value;
  return null;
}

function isInstructionConst(inst: IRInstruction): { isConst: boolean; value: number | boolean | string | null } {
  switch (inst.opcode) {
    case IROpcode.ConstI1: return { isConst: true, value: (inst as any).constValue ?? 0 };
    case IROpcode.ConstI8:
    case IROpcode.ConstI16:
    case IROpcode.ConstI32:
    case IROpcode.ConstI64:
      return { isConst: true, value: (inst as any).constValue ?? 0 };
    default:
      return { isConst: false, value: null };
  }
}

/* ------------------------------------------------------------------ */
/*  1. ConstantFolding                                                */
/* ------------------------------------------------------------------ */

export class ConstantFolding implements Pass {
  readonly name = 'constant-folding';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;
    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        if (inst.isTerminator() || inst.opcode === IROpcode.Phi || inst.opcode === IROpcode.Store) continue;
        if (this.foldInstruction(inst, block, fn)) {
          changed = true;
        }
      }
    }
    return changed;
  }

  private foldInstruction(inst: IRInstruction, block: BasicBlock, fn: Function): boolean {
    if (!inst.isBinary() && inst.opcode !== IROpcode.Neg && inst.opcode !== IROpcode.Not) return false;
    const allConst = inst.operands.every(op => op.kind === 'const');
    if (!allConst) return false;

    const left = getConstIntValue(inst.operands[0]);
    const right = inst.operands.length > 1 ? getConstIntValue(inst.operands[1]) : null;
    if (left === null || (inst.operands.length > 1 && right === null)) return false;

    let result: number | null = null;
    switch (inst.opcode) {
      case IROpcode.Add: result = left + right!; break;
      case IROpcode.Sub: result = left - right!; break;
      case IROpcode.Mul: result = left * right!; break;
      case IROpcode.Div: if (right !== 0) result = Math.trunc(left / right!); break;
      case IROpcode.Mod: if (right !== 0) result = left % right!; break;
      case IROpcode.And: result = left & right!; break;
      case IROpcode.Or: result = left | right!; break;
      case IROpcode.Xor: result = left ^ right!; break;
      case IROpcode.Shl: result = left << right!; break;
      case IROpcode.Shr: result = left >> right!; break;
      case IROpcode.Neg: result = -left; break;
      case IROpcode.Not: result = ~left; break;
    }

    if (result === null) return false;

    const constOp = operandConst(result, inst.type);
    replaceInstructionWithValue(inst, constOp, fn);
    block.instructions.splice(block.instructions.indexOf(inst), 1);
    return true;
  }
}

/* ------------------------------------------------------------------ */
/*  2. DeadCodeElimination                                            */
/* ------------------------------------------------------------------ */

export class DeadCodeElimination implements Pass {
  readonly name = 'dead-code-elimination';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;
    const alive = new Set<IRInstruction>();

    const markAlive = (inst: IRInstruction): void => {
      if (alive.has(inst)) return;
      alive.add(inst);
      for (const op of inst.operands) {
        if (op.kind === 'ref') {
          for (const block of fn.blocks) {
            for (const i of block.instructions) {
              if (i.id === op.id) {
                markAlive(i);
                break;
              }
            }
          }
        }
      }
    };

    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        if (inst.isTerminator() || inst.isSideEffecting() || inst.opcode === IROpcode.Phi) {
          markAlive(inst);
        }
      }
    }

    for (const block of fn.blocks) {
      const toRemove: IRInstruction[] = [];
      for (const inst of block.instructions) {
        if (!alive.has(inst) && !inst.isTerminator()) {
          toRemove.push(inst);
        }
      }
      if (toRemove.length > 0) {
        changed = true;
        for (const inst of toRemove) {
          const idx = block.instructions.indexOf(inst);
          if (idx >= 0) block.instructions.splice(idx, 1);
        }
      }
    }

    return changed;
  }
}

/* ------------------------------------------------------------------ */
/*  3. FunctionInlining                                               */
/* ------------------------------------------------------------------ */

export class FunctionInlining implements Pass {
  readonly name = 'function-inlining';
  private maxInlineInstructions = 10;

  run(module: Module): boolean {
    let changed = false;
    const inlined = new Set<string>();

    for (const fn of module.functions) {
      if (fn.isNative) continue;
      if (fn.instructionCount() > 0 && fn.instructionCount() <= this.maxInlineInstructions) {
        inlined.add(fn.name);
      }
    }

    for (const fn of module.functions) {
      for (const block of fn.blocks) {
        for (let i = 0; i < block.instructions.length; i++) {
          const inst = block.instructions[i];
          if (inst.opcode === IROpcode.Call) {
            const calleeName = inst.operands[0];
            if (calleeName.kind === 'const' && typeof calleeName.value === 'string' && inlined.has(calleeName.value)) {
              const calleeFn = module.getFunction(calleeName.value);
              if (calleeFn && calleeFn.instructionCount() <= this.maxInlineInstructions) {
                changed = true;
              }
            }
          }
        }
      }
    }

    return changed;
  }
}

/* ------------------------------------------------------------------ */
/*  4. TailCallOptimization                                           */
/* ------------------------------------------------------------------ */

export class TailCallOptimization implements Pass {
  readonly name = 'tail-call-optimization';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      if (fn.isNative) continue;
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;
    for (const block of fn.blocks) {
      const insts = block.instructions;
      if (insts.length < 2) continue;

      const last = insts[insts.length - 1];
      if (last.opcode !== IROpcode.Return) continue;

      const secondLast = insts[insts.length - 2];
      if (secondLast.opcode !== IROpcode.Call) continue;

      const callee = secondLast.operands[0];
      if (callee.kind === 'const' && typeof callee.value === 'string' && callee.value === fn.name) {
        last.opcode = IROpcode.Branch as any;
        changed = true;
      }
    }
    return changed;
  }
}

/* ------------------------------------------------------------------ */
/*  5. LoopOptimization (LICM)                                        */
/* ------------------------------------------------------------------ */

export class LoopOptimization implements Pass {
  readonly name = 'loop-optimization';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;

    const loops = this.findLoops(fn);
    for (const { header, body, preheader } of loops) {
      if (!preheader) continue;
      changed = this.hoistInvariants(header, body, preheader, fn) || changed;
    }

    return changed;
  }

  private findLoops(fn: Function): { header: BasicBlock; body: BasicBlock[]; preheader: BasicBlock | null }[] {
    const loops: { header: BasicBlock; body: BasicBlock[]; preheader: BasicBlock | null }[] = [];

    for (const block of fn.blocks) {
      for (const succ of block.successors) {
        if (this.dominates(succ, block, fn)) {
          const body = this.findLoopBody(succ, block, fn);
          const preheader = this.findPreheader(succ, fn);
          if (!loops.some(l => l.header === succ)) {
            loops.push({ header: succ, body, preheader });
          }
        }
      }
    }

    return loops;
  }

  private dominates(a: BasicBlock, b: BasicBlock, fn: Function): boolean {
    if (a === b) return true;
    const visited = new Set<BasicBlock>();
    const worklist = [fn.entry!];
    let foundA = false;
    let reachedBfromA = false;

    while (worklist.length > 0) {
      const block = worklist.pop()!;
      if (visited.has(block)) continue;
      visited.add(block);

      if (block === a) foundA = true;
      if (foundA && block === b) reachedBfromA = true;

      for (const succ of block.successors) {
        worklist.push(succ);
      }
    }

    return foundA && reachedBfromA;
  }

  private findLoopBody(header: BasicBlock, latch: BasicBlock, fn: Function): BasicBlock[] {
    const body = new Set<BasicBlock>();
    const worklist = [latch];

    while (worklist.length > 0) {
      const block = worklist.pop()!;
      if (body.has(block)) continue;
      body.add(block);
      if (block === header) continue;
      for (const pred of block.predecessors) {
        worklist.push(pred);
      }
    }

    return [...body];
  }

  private findPreheader(header: BasicBlock, fn: Function): BasicBlock | null {
    const external: BasicBlock[] = [];
    for (const pred of header.predecessors) {
      if (!this.isBackEdge(pred, header)) {
        external.push(pred);
      }
    }
    if (external.length === 1) return external[0];
    return null;
  }

  private isBackEdge(from: BasicBlock, to: BasicBlock): boolean {
    const visited = new Set<BasicBlock>();
    const worklist = [to];
    while (worklist.length > 0) {
      const block = worklist.pop()!;
      if (block === from) return true;
      if (visited.has(block)) continue;
      visited.add(block);
      for (const succ of block.successors) {
        worklist.push(succ);
      }
    }
    return true;
  }

  private isLoopInvariant(inst: IRInstruction, loopBlocks: Set<BasicBlock>): boolean {
    if (inst.opcode === IROpcode.Store || inst.opcode === IROpcode.Call || inst.opcode === IROpcode.NativeCall) {
      return false;
    }
    if (inst.opcode === IROpcode.Load) {
      for (const op of inst.operands) {
        if (op.kind === 'ref') {
          for (const block of loopBlocks) {
            for (const i of block.instructions) {
              if (i.id === op.id && i.opcode === IROpcode.Alloca) {
                return true;
              }
            }
          }
          return false;
        }
      }
      return false;
    }

    for (const op of inst.operands) {
      if (op.kind === 'ref') {
        const definedInLoop = this.isDefinedInLoop(op.id, loopBlocks);
        if (definedInLoop) return false;
      }
    }
    return true;
  }

  private isDefinedInLoop(id: number, loopBlocks: Set<BasicBlock>): boolean {
    for (const block of loopBlocks) {
      for (const inst of block.instructions) {
        if (inst.id === id) return true;
      }
    }
    return false;
  }

  private hoistInvariants(header: BasicBlock, body: BasicBlock[], preheader: BasicBlock, fn: Function): boolean {
    let changed = false;
    const loopSet = new Set([header, ...body]);

    for (const block of [header, ...body]) {
      const toHoist: IRInstruction[] = [];
      for (const inst of block.instructions) {
        if (inst.isTerminator() || inst.opcode === IROpcode.Store || inst.opcode === IROpcode.Phi) continue;
        if (this.isLoopInvariant(inst, loopSet)) {
          toHoist.push(inst);
        }
      }

      for (const inst of toHoist) {
        const idx = block.instructions.indexOf(inst);
        if (idx >= 0) {
          block.instructions.splice(idx, 1);
          preheader.instructions.splice(preheader.instructions.length - 1, 0, inst);
          inst.block = preheader;
          changed = true;
        }
      }
    }

    return changed;
  }
}

/* ------------------------------------------------------------------ */
/*  6. EscapeAnalysis                                                 */
/* ------------------------------------------------------------------ */

export class EscapeAnalysis implements Pass {
  readonly name = 'escape-analysis';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      for (const block of fn.blocks) {
        for (const inst of block.instructions) {
          if (inst.opcode === IROpcode.Alloca) {
            const escapes = this.doesAllocaEscape(inst, fn);
            if (!escapes) {
              inst.metadata['noescape'] = true;
              changed = true;
            }
          }
        }
      }
    }
    return changed;
  }

  private doesAllocaEscape(alloca: IRInstruction, fn: Function): boolean {
    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        for (const op of inst.operands) {
          if (op.kind === 'ref' && op.id === alloca.id) {
            if (inst.opcode === IROpcode.Store) {
              if (inst.operands.length >= 2 && inst.operands[1].kind === 'ref' && inst.operands[1].id === alloca.id) {
                const valOp = inst.operands[0];
                if (valOp.kind === 'ref') {
                  for (const b of fn.blocks) {
                    for (const i of b.instructions) {
                      if (i.id === valOp.id && i.opcode === IROpcode.Alloca) {
                        continue;
                      }
                    }
                  }
                }
              }
            }
            if (inst.opcode === IROpcode.Call || inst.opcode === IROpcode.NativeCall) {
              if (inst.operands.indexOf(op) > 0) {
                return true;
              }
            }
            if (inst.opcode === IROpcode.Return) {
              return true;
            }
            if (inst.opcode === IROpcode.Store) {
              const ptrOp = inst.operands.length > 1 ? inst.operands[1] : null;
              if (ptrOp && ptrOp.kind === 'ref' && ptrOp.id !== alloca.id) {
                return true;
              }
            }
          }
        }
      }
    }
    return false;
  }
}

/* ------------------------------------------------------------------ */
/*  7. AlgebraicSimplification                                         */
/* ------------------------------------------------------------------ */

export class AlgebraicSimplification implements Pass {
  readonly name = 'algebraic-simplification';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;
    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        if (this.simplify(inst, block, fn)) {
          changed = true;
        }
      }
    }
    return changed;
  }

  private simplify(inst: IRInstruction, block: BasicBlock, fn: Function): boolean {
    switch (inst.opcode) {
      case IROpcode.Add: {
        if (isZero(inst.operands[0]) || isZero(inst.operands[1])) {
          const other = isZero(inst.operands[0]) ? inst.operands[1] : inst.operands[0];
          replaceInstructionWithValue(inst, other, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Sub: {
        if (isZero(inst.operands[1])) {
          replaceInstructionWithValue(inst, inst.operands[0], fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        if (inst.operands[0].kind === 'ref' && inst.operands[1].kind === 'ref' &&
            inst.operands[0].id === inst.operands[1].id) {
          const zero = operandConst(0, inst.type);
          replaceInstructionWithValue(inst, zero, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Mul: {
        if (isOne(inst.operands[0]) || isOne(inst.operands[1])) {
          const other = isOne(inst.operands[0]) ? inst.operands[1] : inst.operands[0];
          replaceInstructionWithValue(inst, other, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        if (isZero(inst.operands[0]) || isZero(inst.operands[1])) {
          const zero = operandConst(0, inst.type);
          replaceInstructionWithValue(inst, zero, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Div: {
        if (isOne(inst.operands[1])) {
          replaceInstructionWithValue(inst, inst.operands[0], fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.And: {
        if (isZero(inst.operands[0]) || isZero(inst.operands[1])) {
          const zero = operandConst(0, inst.type);
          replaceInstructionWithValue(inst, zero, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Or:
      case IROpcode.Xor: {
        if (isZero(inst.operands[0]) || isZero(inst.operands[1])) {
          const other = isZero(inst.operands[0]) ? inst.operands[1] : inst.operands[0];
          replaceInstructionWithValue(inst, other, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        if (inst.opcode === IROpcode.Xor &&
            inst.operands[0].kind === 'ref' && inst.operands[1].kind === 'ref' &&
            inst.operands[0].id === inst.operands[1].id) {
          const zero = operandConst(0, inst.type);
          replaceInstructionWithValue(inst, zero, fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Shl: {
        if (isZero(inst.operands[1])) {
          replaceInstructionWithValue(inst, inst.operands[0], fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Shr: {
        if (isZero(inst.operands[1])) {
          replaceInstructionWithValue(inst, inst.operands[0], fn);
          block.instructions.splice(block.instructions.indexOf(inst), 1);
          return true;
        }
        return false;
      }
      case IROpcode.Neg: {
        if (inst.operands[0].kind === 'ref') {
          for (const b of fn.blocks) {
            for (const i of b.instructions) {
              if (i.id === inst.operands[0].id && i.opcode === IROpcode.Neg) {
                replaceInstructionWithValue(inst, i.operands[0], fn);
                block.instructions.splice(block.instructions.indexOf(inst), 1);
                return true;
              }
            }
          }
        }
        return false;
      }
      default:
        return false;
    }
  }
}

/* ------------------------------------------------------------------ */
/*  8. StrengthReduction                                              */
/* ------------------------------------------------------------------ */

export class StrengthReduction implements Pass {
  readonly name = 'strength-reduction';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;
    for (const block of fn.blocks) {
      for (const inst of block.instructions) {
        if (this.reduce(inst, block, fn)) {
          changed = true;
        }
      }
    }
    return changed;
  }

  private reduce(inst: IRInstruction, block: BasicBlock, fn: Function): boolean {
    switch (inst.opcode) {
      case IROpcode.Mul: {
        const leftVal = getConstIntValue(inst.operands[0]);
        const rightVal = getConstIntValue(inst.operands[1]);

        if (leftVal !== null && isPowerOfTwo(leftVal)) {
          const shift = log2(leftVal);
          const shiftConst = operandConst(shift, inst.type);
          const shiftInst = new IRInstruction(IROpcode.Shl, inst.type, [inst.operands[1], shiftConst]);
          shiftInst.block = block;
          const idx = block.instructions.indexOf(inst);
          block.instructions.splice(idx, 1, shiftInst);
          replaceInstructionWithValue(inst, operandRef(shiftInst.id, inst.type), fn);
          return true;
        }

        if (rightVal !== null && isPowerOfTwo(rightVal)) {
          const shift = log2(rightVal);
          const shiftConst = operandConst(shift, inst.type);
          inst.opcode = IROpcode.Shl;
          inst.operands = [inst.operands[0], shiftConst];
          return true;
        }
        return false;
      }
      case IROpcode.Div: {
        const rightVal = getConstIntValue(inst.operands[1]);
        if (rightVal !== null && isPowerOfTwo(rightVal)) {
          const shift = log2(rightVal);
          const shiftConst = operandConst(shift, inst.type);
          inst.opcode = IROpcode.Shr;
          inst.operands = [inst.operands[0], shiftConst];
          return true;
        }
        return false;
      }
      case IROpcode.Mod: {
        const rightVal = getConstIntValue(inst.operands[1]);
        if (rightVal !== null && isPowerOfTwo(rightVal)) {
          const mask = rightVal - 1;
          const maskConst = operandConst(mask, inst.type);
          inst.opcode = IROpcode.And;
          inst.operands = [inst.operands[0], maskConst];
          return true;
        }
        return false;
      }
      default:
        return false;
    }
  }
}

/* ------------------------------------------------------------------ */
/*  9. CommonSubexpressionElimination                                 */
/* ------------------------------------------------------------------ */

export class CommonSubexpressionElimination implements Pass {
  readonly name = 'cse';

  run(module: Module): boolean {
    let changed = false;
    for (const fn of module.functions) {
      changed = this.runOnFunction(fn) || changed;
    }
    return changed;
  }

  private runOnFunction(fn: Function): boolean {
    let changed = false;

    for (const block of fn.blocks) {
      const seen = new Map<string, IRInstruction>();

      for (const inst of block.instructions) {
        if (inst.isTerminator() || inst.isSideEffecting() || inst.opcode === IROpcode.Phi || inst.opcode === IROpcode.Alloca) {
          seen.clear();
          continue;
        }

        const key = this.hashInstruction(inst);
        const existing = seen.get(key);
        if (existing) {
          replaceInstructionWithValue(inst, operandRef(existing.id, inst.type), fn);
          const idx = block.instructions.indexOf(inst);
          block.instructions.splice(idx, 1);
          changed = true;
        } else {
          seen.set(key, inst);
        }
      }
    }

    return changed;
  }

  private hashInstruction(inst: IRInstruction): string {
    const parts: string[] = [inst.opcode, inst.type];
    for (const op of inst.operands) {
      if (op.kind === 'ref') parts.push(`%${op.id}`);
      else parts.push(`${op.value}`);
    }
    return parts.join(':');
  }
}

/* ------------------------------------------------------------------ */
/*  Preset Pass Pipelines                                             */
/* ------------------------------------------------------------------ */

export function createDefaultPasses(): Pass[] {
  return [
    new ConstantFolding(),
    new AlgebraicSimplification(),
    new StrengthReduction(),
    new DeadCodeElimination(),
    new CommonSubexpressionElimination(),
  ];
}

export function createFullPasses(): Pass[] {
  return [
    new ConstantFolding(),
    new AlgebraicSimplification(),
    new StrengthReduction(),
    new DeadCodeElimination(),
    new CommonSubexpressionElimination(),
    new FunctionInlining(),
    new TailCallOptimization(),
    new LoopOptimization(),
    new EscapeAnalysis(),
  ];
}
