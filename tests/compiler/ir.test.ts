import { describe, it, expect } from 'vitest';
import {
  IRType, IROpcode, IRInstruction, BasicBlock, Function, Module,
  IRBuilder, IRPrinter, Verifier,
  operandConst, operandRef, resetInstructionIds,
} from '../../src/compiler/ir/index';

function makeModule(name?: string): Module {
  resetInstructionIds();
  return new Module(name);
}

function makeFunction(name: string, returnType?: IRType): Function {
  return new Function(name, returnType ?? IRType.I64);
}

function makeBlock(label: string): BasicBlock {
  return new BasicBlock(label);
}

describe('IR Instruction', () => {
  it('creates instructions with unique ids', () => {
    resetInstructionIds();
    const a = new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]);
    const b = new IRInstruction(IROpcode.Sub, IRType.I64, [operandConst(3), operandConst(4)]);
    expect(a.id).toBe(1);
    expect(b.id).toBe(2);
    expect(a.type).toBe(IRType.I64);
  });

  it('identifies terminators', () => {
    expect(new IRInstruction(IROpcode.Return, IRType.Void).isTerminator()).toBe(true);
    expect(new IRInstruction(IROpcode.ReturnVoid, IRType.Void).isTerminator()).toBe(true);
    expect(new IRInstruction(IROpcode.Branch, IRType.Void, [operandConst('entry')]).isTerminator()).toBe(true);
    expect(new IRInstruction(IROpcode.BranchIf, IRType.Void).isTerminator()).toBe(true);
    expect(new IRInstruction(IROpcode.Unreachable, IRType.Void).isTerminator()).toBe(true);
    expect(new IRInstruction(IROpcode.Add, IRType.I64).isTerminator()).toBe(false);
  });

  it('identifies side-effecting instructions', () => {
    expect(new IRInstruction(IROpcode.Store, IRType.Void).isSideEffecting()).toBe(true);
    expect(new IRInstruction(IROpcode.Call, IRType.I64).isSideEffecting()).toBe(true);
    expect(new IRInstruction(IROpcode.Return, IRType.Void).isSideEffecting()).toBe(true);
    expect(new IRInstruction(IROpcode.Add, IRType.I64).isSideEffecting()).toBe(false);
    expect(new IRInstruction(IROpcode.Load, IRType.I64).isSideEffecting()).toBe(false);
  });

  it('identifies binary instructions', () => {
    expect(new IRInstruction(IROpcode.Add, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Sub, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Mul, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Div, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Mod, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.And, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Or, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Xor, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Shl, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Shr, IRType.I64).isBinary()).toBe(true);
    expect(new IRInstruction(IROpcode.Store, IRType.Void).isBinary()).toBe(false);
  });
});

describe('BasicBlock', () => {
  it('creates blocks with labels', () => {
    const block = makeBlock('entry');
    expect(block.label).toBe('entry');
    expect(block.instructions).toHaveLength(0);
    expect(block.predecessors).toHaveLength(0);
    expect(block.successors).toHaveLength(0);
  });

  it('pushes instructions and tracks terminators', () => {
    const block = makeBlock('test');
    expect(block.isTerminated).toBe(false);

    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]);
    block.pushInst(add);
    expect(block.isTerminated).toBe(false);

    const ret = new IRInstruction(IROpcode.ReturnVoid, IRType.Void);
    block.pushInst(ret);
    expect(block.isTerminated).toBe(true);
    expect(block.terminator).toBe(ret);
  });

  it('inserts instructions before the terminator', () => {
    const block = makeBlock('test');
    const ret = new IRInstruction(IROpcode.ReturnVoid, IRType.Void);
    block.pushInst(ret);

    const add = new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]);
    block.pushInst(add);
    expect(block.instructions[0]).toBe(add);
    expect(block.instructions[1]).toBe(ret);
  });

  it('manages predecessor/successor relationships', () => {
    const a = makeBlock('a');
    const b = makeBlock('b');
    a.addSuccessor(b);

    expect(a.successors).toContain(b);
    expect(b.predecessors).toContain(a);

    a.removeSuccessor(b);
    expect(a.successors).not.toContain(b);
    expect(b.predecessors).not.toContain(a);
  });
});

describe('Function', () => {
  it('creates functions with blocks', () => {
    const fn = makeFunction('main');
    expect(fn.name).toBe('main');
    expect(fn.blocks).toHaveLength(0);

    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);
    expect(fn.entry).toBe(entry);
    expect(fn.blocks).toHaveLength(1);
  });

  it('counts instructions', () => {
    const fn = makeFunction('test');
    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);

    entry.pushInst(new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]));
    entry.pushInst(new IRInstruction(IROpcode.ReturnVoid, IRType.Void));

    expect(fn.instructionCount()).toBe(2);
  });
});

describe('Module', () => {
  it('manages functions', () => {
    const mod = makeModule('test');
    const fn = makeFunction('main');
    mod.addFunction(fn);
    expect(mod.getFunction('main')).toBe(fn);
    expect(mod.getFunction('nonexistent')).toBeUndefined();

    mod.removeFunction(fn);
    expect(mod.functions).toHaveLength(0);
  });
});

describe('IRPrinter', () => {
  it('prints a simple module', () => {
    resetInstructionIds();
    const mod = makeModule('test');
    const fn = makeFunction('main', IRType.I64);
    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);

    entry.pushInst(new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]));
    entry.pushInst(new IRInstruction(IROpcode.Return, IRType.Void, [operandConst(0)]));
    mod.addFunction(fn);

    const printer = new IRPrinter();
    const output = printer.print(mod);
    expect(output).toContain('Module: test');
    expect(output).toContain('fun main');
    expect(output).toContain('entry:');
    expect(output).toContain('Add');
    expect(output).toContain('return');
  });
});

describe('Verifier', () => {
  it('reports missing entry block', () => {
    const fn = makeFunction('test');
    const mod = makeModule();
    mod.addFunction(fn);

    const v = new Verifier();
    const errors = v.verify(mod);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].message).toContain('no entry block');
  });

  it('reports unterminated blocks', () => {
    resetInstructionIds();
    const fn = makeFunction('test');
    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);
    entry.pushInst(new IRInstruction(IROpcode.Add, IRType.I64, [operandConst(1), operandConst(2)]));

    const mod = makeModule();
    mod.addFunction(fn);

    const v = new Verifier();
    const errors = v.verify(mod);
    expect(errors.some(e => e.message.includes('not terminated'))).toBe(true);
  });

  it('passes for a well-formed function', () => {
    resetInstructionIds();
    const mod = makeModule();
    const fn = makeFunction('main', IRType.I64);
    const entry = fn.createBlock('entry');
    fn.setEntryBlock(entry);

    entry.pushInst(new IRInstruction(IROpcode.Return, IRType.Void, [operandConst(0)]));
    mod.addFunction(fn);

    const v = new Verifier();
    const errors = v.verify(mod);
    expect(errors).toHaveLength(0);
  });
});

describe('IRBuilder', () => {
  it('builds empty program', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 1, column: 1, offset: 0 }, file: 'test.zoya' },
      body: [],
      imports: [],
      exports: [],
    });
    expect(mod.functions).toHaveLength(0);
  });

  it('builds simple arithmetic function', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 1, column: 1, offset: 0 }, file: 'test.zoya' },
      body: [
        {
          type: 'FunctionDeclaration',
          span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 5, column: 1, offset: 50 }, file: 'test.zoya' },
          id: { type: 'Identifier', span: { start: { line: 1, column: 5, offset: 5 }, end: { line: 1, column: 8, offset: 8 }, file: 'test.zoya' }, name: 'add' },
          params: [
            {
              type: 'Parameter',
              span: { start: { line: 1, column: 9, offset: 9 }, end: { line: 1, column: 10, offset: 10 }, file: 'test.zoya' },
              pattern: { type: 'Identifier', span: { start: { line: 1, column: 9, offset: 9 }, end: { line: 1, column: 10, offset: 10 }, file: 'test.zoya' }, name: 'a' },
              rest: false,
            },
            {
              type: 'Parameter',
              span: { start: { line: 1, column: 12, offset: 12 }, end: { line: 1, column: 13, offset: 13 }, file: 'test.zoya' },
              pattern: { type: 'Identifier', span: { start: { line: 1, column: 12, offset: 12 }, end: { line: 1, column: 13, offset: 13 }, file: 'test.zoya' }, name: 'b' },
              rest: false,
            },
          ],
          returnType: { type: 'TypeAnnotation', span: { start: { line: 1, column: 16, offset: 16 }, end: { line: 1, column: 19, offset: 19 }, file: 'test.zoya' }, name: 'i64', typeArguments: [], optional: false, nullable: false, arrayDepth: 0 },
          body: {
            type: 'BlockStatement',
            span: { start: { line: 2, column: 1, offset: 20 }, end: { line: 4, column: 1, offset: 49 }, file: 'test.zoya' },
            body: [
              {
                type: 'ReturnStatement',
                span: { start: { line: 3, column: 3, offset: 25 }, end: { line: 3, column: 18, offset: 40 }, file: 'test.zoya' },
                argument: {
                  type: 'BinaryExpression',
                  span: { start: { line: 3, column: 10, offset: 32 }, end: { line: 3, column: 17, offset: 39 }, file: 'test.zoya' },
                  operator: '+',
                  left: { type: 'Identifier', span: { start: { line: 3, column: 10, offset: 32 }, end: { line: 3, column: 11, offset: 33 }, file: 'test.zoya' }, name: 'a' },
                  right: { type: 'Identifier', span: { start: { line: 3, column: 14, offset: 36 }, end: { line: 3, column: 15, offset: 37 }, file: 'test.zoya' }, name: 'b' },
                },
              },
            ],
          },
          async: false,
          generator: false,
          decorators: [],
        },
      ],
      imports: [],
      exports: [],
    });

    expect(mod.functions).toHaveLength(1);
    const fn = mod.getFunction('add')!;
    expect(fn).toBeDefined();
    expect(fn.blocks.length).toBeGreaterThan(0);
    expect(fn.entry).toBeDefined();

    const entry = fn.entry!;
    expect(entry.instructions.length).toBeGreaterThan(0);

    const hasReturn = entry.instructions.some(i => i.opcode === IROpcode.Return);
    expect(hasReturn).toBe(true);
  });

  it('builds if-else with phi nodes', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 10, column: 1, offset: 100 }, file: 'test.zoya' },
      body: [
        {
          type: 'FunctionDeclaration',
          span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 10, column: 1, offset: 100 }, file: 'test.zoya' },
          id: { type: 'Identifier', span: { start: { line: 1, column: 5, offset: 5 }, end: { line: 1, column: 9, offset: 9 }, file: 'test.zoya' }, name: 'test' },
          params: [],
          body: {
            type: 'BlockStatement',
            span: { start: { line: 2, column: 1, offset: 15 }, end: { line: 9, column: 1, offset: 99 }, file: 'test.zoya' },
            body: [
              {
                type: 'VariableDeclaration',
                span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 12, offset: 29 }, file: 'test.zoya' },
                kind: 'let',
                declarations: [
                  {
                    id: { type: 'Identifier', span: { start: { line: 3, column: 7, offset: 24 }, end: { line: 3, column: 8, offset: 25 }, file: 'test.zoya' }, name: 'x' },
                    init: { type: 'Literal', span: { start: { line: 3, column: 11, offset: 28 }, end: { line: 3, column: 12, offset: 29 }, file: 'test.zoya' }, value: 0, raw: '0' },
                  },
                ],
              },
              {
                type: 'IfStatement',
                span: { start: { line: 4, column: 3, offset: 32 }, end: { line: 7, column: 3, offset: 70 }, file: 'test.zoya' },
                test: {
                  type: 'BinaryExpression',
                  span: { start: { line: 4, column: 7, offset: 36 }, end: { line: 4, column: 14, offset: 43 }, file: 'test.zoya' },
                  operator: '>',
                  left: { type: 'Identifier', span: { start: { line: 4, column: 7, offset: 36 }, end: { line: 4, column: 8, offset: 37 }, file: 'test.zoya' }, name: 'x' },
                  right: { type: 'Literal', span: { start: { line: 4, column: 11, offset: 40 }, end: { line: 4, column: 12, offset: 41 }, file: 'test.zoya' }, value: 0, raw: '0' },
                },
                consequent: {
                  type: 'BlockStatement',
                  span: { start: { line: 5, column: 3, offset: 46 }, end: { line: 5, column: 16, offset: 59 }, file: 'test.zoya' },
                  body: [
                    {
                      type: 'ExpressionStatement',
                      span: { start: { line: 5, column: 5, offset: 48 }, end: { line: 5, column: 14, offset: 57 }, file: 'test.zoya' },
                      expression: {
                        type: 'AssignmentExpression',
                        span: { start: { line: 5, column: 5, offset: 48 }, end: { line: 5, column: 14, offset: 57 }, file: 'test.zoya' },
                        operator: '=',
                        left: { type: 'Identifier', span: { start: { line: 5, column: 5, offset: 48 }, end: { line: 5, column: 6, offset: 49 }, file: 'test.zoya' }, name: 'x' },
                        right: { type: 'Literal', span: { start: { line: 5, column: 9, offset: 52 }, end: { line: 5, column: 14, offset: 57 }, file: 'test.zoya' }, value: 42, raw: '42' },
                      },
                    },
                  ],
                },
                alternate: {
                  type: 'BlockStatement',
                  span: { start: { line: 7, column: 3, offset: 63 }, end: { line: 7, column: 16, offset: 70 }, file: 'test.zoya' },
                  body: [
                    {
                      type: 'ExpressionStatement',
                      span: { start: { line: 7, column: 5, offset: 65 }, end: { line: 7, column: 14, offset: 68 }, file: 'test.zoya' },
                      expression: {
                        type: 'AssignmentExpression',
                        span: { start: { line: 7, column: 5, offset: 65 }, end: { line: 7, column: 14, offset: 68 }, file: 'test.zoya' },
                        operator: '=',
                        left: { type: 'Identifier', span: { start: { line: 7, column: 5, offset: 65 }, end: { line: 7, column: 6, offset: 66 }, file: 'test.zoya' }, name: 'x' },
                        right: { type: 'Literal', span: { start: { line: 7, column: 9, offset: 69 }, end: { line: 7, column: 14, offset: 74 }, file: 'test.zoya' }, value: 7, raw: '7' },
                      },
                    },
                  ],
                },
              },
            ],
          },
          async: false,
          generator: false,
          decorators: [],
        },
      ],
      imports: [],
      exports: [],
    });

    expect(mod.functions).toHaveLength(1);
    const fn = mod.getFunction('test')!;
    expect(fn).toBeDefined();
    expect(fn.blocks.length).toBeGreaterThanOrEqual(3);

    const mergeBlock = fn.blocks.find(b => b.label === 'if.merge');
    const thenBlock = fn.blocks.find(b => b.label === 'if.then');
    const elseBlock = fn.blocks.find(b => b.label === 'if.else');

    expect(mergeBlock).toBeDefined();
    expect(thenBlock).toBeDefined();
    expect(elseBlock).toBeDefined();

    expect(thenBlock!.successors.some(s => s.label === 'if.merge')).toBe(true);
    expect(elseBlock!.successors.some(s => s.label === 'if.merge')).toBe(true);

    const hasStore = fn.blocks.some(b => b.instructions.some(i => i.opcode === IROpcode.Store));
    expect(hasStore).toBe(true);
  });

  it('builds while loop with proper CFG', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 8, column: 1, offset: 80 }, file: 'test.zoya' },
      body: [
        {
          type: 'FunctionDeclaration',
          span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 8, column: 1, offset: 80 }, file: 'test.zoya' },
          id: { type: 'Identifier', span: { start: { line: 1, column: 5, offset: 5 }, end: { line: 1, column: 10, offset: 10 }, file: 'test.zoya' }, name: 'loopTest' },
          params: [],
          body: {
            type: 'BlockStatement',
            span: { start: { line: 2, column: 1, offset: 15 }, end: { line: 7, column: 1, offset: 75 }, file: 'test.zoya' },
            body: [
              {
                type: 'VariableDeclaration',
                span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 15, offset: 32 }, file: 'test.zoya' },
                kind: 'let',
                declarations: [
                  {
                    id: { type: 'Identifier', span: { start: { line: 3, column: 7, offset: 24 }, end: { line: 3, column: 8, offset: 25 }, file: 'test.zoya' }, name: 'i' },
                    init: { type: 'Literal', span: { start: { line: 3, column: 11, offset: 28 }, end: { line: 3, column: 12, offset: 29 }, file: 'test.zoya' }, value: 0, raw: '0' },
                  },
                ],
              },
              {
                type: 'WhileStatement',
                span: { start: { line: 4, column: 3, offset: 35 }, end: { line: 6, column: 3, offset: 65 }, file: 'test.zoya' },
                test: {
                  type: 'BinaryExpression',
                  span: { start: { line: 4, column: 10, offset: 42 }, end: { line: 4, column: 16, offset: 48 }, file: 'test.zoya' },
                  operator: '<',
                  left: { type: 'Identifier', span: { start: { line: 4, column: 10, offset: 42 }, end: { line: 4, column: 11, offset: 43 }, file: 'test.zoya' }, name: 'i' },
                  right: { type: 'Literal', span: { start: { line: 4, column: 14, offset: 46 }, end: { line: 4, column: 15, offset: 47 }, file: 'test.zoya' }, value: 10, raw: '10' },
                },
                body: {
                  type: 'BlockStatement',
                  span: { start: { line: 5, column: 3, offset: 51 }, end: { line: 5, column: 19, offset: 63 }, file: 'test.zoya' },
                  body: [
                    {
                      type: 'ExpressionStatement',
                      span: { start: { line: 5, column: 5, offset: 53 }, end: { line: 5, column: 17, offset: 61 }, file: 'test.zoya' },
                      expression: {
                        type: 'AssignmentExpression',
                        span: { start: { line: 5, column: 5, offset: 53 }, end: { line: 5, column: 17, offset: 61 }, file: 'test.zoya' },
                        operator: '+=',
                        left: { type: 'Identifier', span: { start: { line: 5, column: 5, offset: 53 }, end: { line: 5, column: 6, offset: 54 }, file: 'test.zoya' }, name: 'i' },
                        right: { type: 'Literal', span: { start: { line: 5, column: 10, offset: 58 }, end: { line: 5, column: 11, offset: 59 }, file: 'test.zoya' }, value: 1, raw: '1' },
                      },
                    },
                  ],
                },
              },
            ],
          },
          async: false,
          generator: false,
          decorators: [],
        },
      ],
      imports: [],
      exports: [],
    });

    expect(mod.functions).toHaveLength(1);
    const fn = mod.getFunction('loopTest')!;
    expect(fn).toBeDefined();

    const header = fn.blocks.find(b => b.label === 'while.header');
    const body = fn.blocks.find(b => b.label === 'while.body');
    const exit = fn.blocks.find(b => b.label === 'while.exit');

    expect(header).toBeDefined();
    expect(body).toBeDefined();
    expect(exit).toBeDefined();
    expect(header!.successors.length).toBeGreaterThanOrEqual(2);
    expect(header!.successors.some(s => s.label === 'while.body')).toBe(true);
    expect(header!.successors.some(s => s.label === 'while.exit')).toBe(true);
  });

  it('handles function calls', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 5, column: 1, offset: 60 }, file: 'test.zoya' },
      body: [
        {
          type: 'FunctionDeclaration',
          span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 5, column: 1, offset: 60 }, file: 'test.zoya' },
          id: { type: 'Identifier', span: { start: { line: 1, column: 5, offset: 5 }, end: { line: 1, column: 10, offset: 10 }, file: 'test.zoya' }, name: 'caller' },
          params: [],
          body: {
            type: 'BlockStatement',
            span: { start: { line: 2, column: 1, offset: 15 }, end: { line: 4, column: 1, offset: 55 }, file: 'test.zoya' },
            body: [
              {
                type: 'ExpressionStatement',
                span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 22, offset: 39 }, file: 'test.zoya' },
                expression: {
                  type: 'CallExpression',
                  span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 22, offset: 39 }, file: 'test.zoya' },
                  callee: { type: 'Identifier', span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 7, offset: 24 }, file: 'test.zoya' }, name: 'print' },
                  arguments: [
                    { type: 'Literal', span: { start: { line: 3, column: 8, offset: 25 }, end: { line: 3, column: 21, offset: 38 }, file: 'test.zoya' }, value: 'hello', raw: '"hello"' },
                  ],
                  optional: false,
                  typeArguments: [],
                },
              },
            ],
          },
          async: false,
          generator: false,
          decorators: [],
        },
      ],
      imports: [],
      exports: [],
    });

    expect(mod.functions).toHaveLength(1);
    const fn = mod.getFunction('caller')!;
    expect(fn).toBeDefined();

    const hasCall = fn.entry!.instructions.some(i => i.opcode === IROpcode.Call);
    expect(hasCall).toBe(true);
  });

  it('builds for loop', () => {
    const builder = new IRBuilder();
    const mod = builder.build({
      type: 'Program',
      span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 5, column: 1, offset: 60 }, file: 'test.zoya' },
      body: [
        {
          type: 'FunctionDeclaration',
          span: { start: { line: 1, column: 1, offset: 0 }, end: { line: 5, column: 1, offset: 60 }, file: 'test.zoya' },
          id: { type: 'Identifier', span: { start: { line: 1, column: 5, offset: 5 }, end: { line: 1, column: 11, offset: 11 }, file: 'test.zoya' }, name: 'forTest' },
          params: [],
          body: {
            type: 'BlockStatement',
            span: { start: { line: 2, column: 1, offset: 15 }, end: { line: 4, column: 1, offset: 55 }, file: 'test.zoya' },
            body: [
              {
                type: 'ForStatement',
                span: { start: { line: 3, column: 3, offset: 20 }, end: { line: 3, column: 30, offset: 47 }, file: 'test.zoya' },
                body: { type: 'BlockStatement', span: { start: { line: 3, column: 28, offset: 45 }, end: { line: 3, column: 30, offset: 47 }, file: 'test.zoya' }, body: [] },
              },
            ],
          },
          async: false,
          generator: false,
          decorators: [],
        },
      ],
      imports: [],
      exports: [],
    });

    const fn = mod.getFunction('forTest')!;
    expect(fn.blocks.some(b => b.label === 'for.header')).toBe(true);
    expect(fn.blocks.some(b => b.label === 'for.body')).toBe(true);
    expect(fn.blocks.some(b => b.label === 'for.exit')).toBe(true);
    expect(fn.blocks.some(b => b.label === 'for.update')).toBe(true);
  });
});
