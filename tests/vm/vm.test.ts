import { describe, it, expect } from 'vitest';
import { VM } from '../../src/vm/index';
import { Chunk } from '../../src/vm/chunk';
import { Opcode } from '../../src/vm/opcodes';
import { ZoyaValue, ZOYA_NIL, ZOYA_TRUE, ZOYA_FALSE, allocateObjectId } from '../../src/types';

function makeScriptChunk(...ops: number[]): Chunk {
  const chunk = new Chunk();
  for (const op of ops) {
    chunk.write(op, 1);
  }
  return chunk;
}

function pushConst(chunk: Chunk, value: ZoyaValue): number {
  return chunk.addConstant(value);
}

function pushNumber(chunk: Chunk, n: number): void {
  chunk.write(Opcode.PUSH_NUMBER, 1);
  chunk.write(n, 1);
}

describe('VM', () => {
  it('executes HALT without error returning nil', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBeNull();
  });

  it('pushes nil', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.PUSH_NIL, Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBeNull();
  });

  it('pushes true', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.PUSH_TRUE, Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('pushes false', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.PUSH_FALSE, Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBe(false);
  });

  it('adds two numbers', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 2);
    pushNumber(chunk, 3);
    chunk.write(Opcode.ADD, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(5);
  });

  it('subtracts two numbers', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 3);
    chunk.write(Opcode.SUB, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(7);
  });

  it('multiplies two numbers', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 6);
    pushNumber(chunk, 7);
    chunk.write(Opcode.MUL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(42);
  });

  it('divides two numbers', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 2);
    chunk.write(Opcode.DIV, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(5);
  });

  it('computes modulo', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 3);
    chunk.write(Opcode.MOD, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(1);
  });

  it('negates a number', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 42);
    chunk.write(Opcode.NEG, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(-42);
  });

  it('performs logical NOT on true', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.PUSH_TRUE, Opcode.NOT, Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBe(false);
  });

  it('performs logical NOT on false', () => {
    const vm = new VM();
    const chunk = makeScriptChunk(Opcode.PUSH_FALSE, Opcode.NOT, Opcode.HALT);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares numbers with EQUAL', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 5);
    pushNumber(chunk, 5);
    chunk.write(Opcode.EQUAL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares numbers with NOT_EQUAL', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 5);
    pushNumber(chunk, 3);
    chunk.write(Opcode.NOT_EQUAL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares with LESS', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 3);
    pushNumber(chunk, 5);
    chunk.write(Opcode.LESS, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares with GREATER', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 5);
    chunk.write(Opcode.GREATER, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares with LESS_EQUAL (true)', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 3);
    pushNumber(chunk, 5);
    chunk.write(Opcode.LESS_EQUAL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('compares with GREATER_EQUAL (true)', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 5);
    pushNumber(chunk, 5);
    chunk.write(Opcode.GREATER_EQUAL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(true);
  });

  it('performs unconditional jump', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 1);
    chunk.write(Opcode.JMP, 1);
    chunk.write(2, 1);
    pushNumber(chunk, 99);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(1);
  });

  it('jumps when JMP_IF_FALSE sees false (skips pushing 42)', () => {
    const vm = new VM();
    const chunk = new Chunk();
    chunk.write(Opcode.PUSH_FALSE, 1);
    chunk.write(Opcode.JMP_IF_FALSE, 1);
    chunk.write(4, 1);
    pushNumber(chunk, 42);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(false);
  });

  it('does not jump when JMP_IF_FALSE sees true (pushes 42)', () => {
    const vm = new VM();
    const chunk = new Chunk();
    chunk.write(Opcode.PUSH_TRUE, 1);
    chunk.write(Opcode.JMP_IF_FALSE, 1);
    chunk.write(4, 1);
    pushNumber(chunk, 42);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(42);
  });

  it('pushes and pops values directly', () => {
    const vm = new VM();
    vm.push(1);
    vm.push(2);
    vm.push(3);
    expect(vm.pop()).toBe(3);
    expect(vm.pop()).toBe(2);
    expect(vm.pop()).toBe(1);
  });

  it('peeks at stack values', () => {
    const vm = new VM();
    vm.push(10);
    vm.push(20);
    vm.push(30);
    expect(vm.peek(0)).toBe(30);
    expect(vm.peek(1)).toBe(20);
    expect(vm.peek(2)).toBe(10);
    vm.clearStack();
  });

  it('duplicates top of stack', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 42);
    chunk.write(Opcode.DUP, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(42);
  });

  it('swaps top two values', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 1);
    pushNumber(chunk, 2);
    chunk.write(Opcode.SWAP, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(1);
  });

  it('handles division by zero', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 1);
    pushNumber(chunk, 0);
    chunk.write(Opcode.DIV, 1);
    chunk.write(Opcode.HALT, 1);
    expect(() => vm.interpret(chunk)).toThrow('Division by zero');
  });

  it('handles type error on string arithmetic', () => {
    const vm = new VM();
    const chunk = new Chunk();
    chunk.write(Opcode.PUSH_STRING, 1);
    chunk.write(pushConst(chunk, 'hello'), 1);
    pushNumber(chunk, 5);
    chunk.write(Opcode.SUB, 1);
    chunk.write(Opcode.HALT, 1);
    expect(() => vm.interpret(chunk)).toThrow('Operands must be numbers');
  });

  it('concatenates strings with ADD', () => {
    const vm = new VM();
    const chunk = new Chunk();
    chunk.write(Opcode.PUSH_STRING, 1);
    chunk.write(pushConst(chunk, 'hello'), 1);
    chunk.write(Opcode.PUSH_STRING, 1);
    chunk.write(pushConst(chunk, ' world'), 1);
    chunk.write(Opcode.ADD, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe('hello world');
  });

  it('defines and loads globals', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 42);
    chunk.write(Opcode.DEFINE_GLOBAL, 1);
    chunk.write(pushConst(chunk, 'x'), 1);
    chunk.write(Opcode.GET_GLOBAL, 1);
    chunk.write(pushConst(chunk, 'x'), 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(42);
  });

  it('provides native clock function', () => {
    const vm = new VM();
    const clock = vm.getGlobal('clock');
    expect(clock).toBeDefined();
  });

  it('prevents exceeding max stack', () => {
    const vm = new VM();
    for (let i = 0; i < 256; i++) {
      vm.push(i);
    }
    expect(vm.getStackSize()).toBe(256);
    expect(() => vm.push(256)).toThrow('Stack overflow');
    vm.clearStack();
  });

  it('makes arrays', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 1);
    pushNumber(chunk, 2);
    pushNumber(chunk, 3);
    chunk.write(Opcode.MAKE_ARRAY, 1);
    chunk.write(3, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).not.toBeNull();
    if (result !== null && typeof result === 'object') {
      const zArr = result as { __zoya_type: string; elements: ZoyaValue[]; length: number };
      expect(zArr.__zoya_type).toBe('array');
      expect(zArr.length).toBe(3);
      expect(zArr.elements[0]).toBe(1);
      expect(zArr.elements[1]).toBe(2);
      expect(zArr.elements[2]).toBe(3);
    }
  });

  it('indexes arrays with GET_INDEX', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 20);
    chunk.write(Opcode.MAKE_ARRAY, 1);
    chunk.write(2, 1);
    pushNumber(chunk, 0);
    chunk.write(Opcode.GET_INDEX, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(10);
  });

  it('handles NOP instruction', () => {
    const vm = new VM();
    const chunk = new Chunk();
    chunk.write(Opcode.NOP, 1);
    pushNumber(chunk, 42);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(42);
  });

  it('clears stack on reset', () => {
    const vm = new VM();
    vm.push(1);
    vm.push(2);
    expect(vm.getStackSize()).toBe(2);
    vm.reset();
    expect(vm.getStackSize()).toBe(0);
  });

  it('supports chained arithmetic', () => {
    const vm = new VM();
    const chunk = new Chunk();
    pushNumber(chunk, 10);
    pushNumber(chunk, 5);
    chunk.write(Opcode.ADD, 1);
    pushNumber(chunk, 3);
    chunk.write(Opcode.MUL, 1);
    chunk.write(Opcode.HALT, 1);
    const result = vm.interpret(chunk);
    expect(result).toBe(45);
  });
});
