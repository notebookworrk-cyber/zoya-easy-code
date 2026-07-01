import { describe, it, expect } from 'vitest';
import { Chunk } from '../../src/vm/chunk';

describe('Chunk', () => {
  it('creates a chunk with default source file', () => {
    const chunk = new Chunk();
    expect(chunk.sourceFile).toBe('<unknown>');
    expect(chunk.code.length).toBe(0);
    expect(chunk.constants.length).toBe(0);
    expect(chunk.lines.length).toBe(0);
    expect(chunk.size).toBe(0);
  });

  it('creates a chunk with a source file name', () => {
    const chunk = new Chunk('test.zoya');
    expect(chunk.sourceFile).toBe('test.zoya');
  });

  it('writes bytes to the chunk', () => {
    const chunk = new Chunk();
    chunk.write(0x01, 1);
    chunk.write(0x02, 1);
    chunk.write(0x03, 2);

    expect(chunk.code.length).toBe(3);
    expect(chunk.code[0]).toBe(0x01);
    expect(chunk.code[1]).toBe(0x02);
    expect(chunk.code[2]).toBe(0x03);
    expect(chunk.lines[0]).toBe(1);
    expect(chunk.lines[1]).toBe(1);
    expect(chunk.lines[2]).toBe(2);
  });

  it('writes opcodes', () => {
    const chunk = new Chunk();
    chunk.writeOpcode(42, 5);
    expect(chunk.code[0]).toBe(42);
    expect(chunk.lines[0]).toBe(5);
  });

  it('writes operands', () => {
    const chunk = new Chunk();
    chunk.writeOperand(100, 3);
    expect(chunk.code[0]).toBe(100);
    expect(chunk.lines[0]).toBe(3);
  });

  it('adds constants and returns their index', () => {
    const chunk = new Chunk();
    const idx1 = chunk.addConstant(42);
    const idx2 = chunk.addConstant('hello');
    const idx3 = chunk.addConstant(null);

    expect(idx1).toBe(0);
    expect(idx2).toBe(1);
    expect(idx3).toBe(2);
    expect(chunk.constants[0]).toBe(42);
    expect(chunk.constants[1]).toBe('hello');
    expect(chunk.constants[2]).toBeNull();
  });

  it('patches a byte at a specific offset', () => {
    const chunk = new Chunk();
    chunk.write(0x00, 1);
    chunk.write(0x00, 1);
    chunk.write(0x00, 1);

    chunk.patch(1, 0xFF);
    expect(chunk.code[1]).toBe(0xFF);
  });

  it('returns code as Uint8Array', () => {
    const chunk = new Chunk();
    chunk.write(0x01, 1);
    chunk.write(0x02, 1);
    chunk.write(0x03, 1);

    const code = chunk.getCode();
    expect(code).toBeInstanceOf(Uint8Array);
    expect(code.length).toBe(3);
    expect(code[0]).toBe(0x01);
    expect(code[1]).toBe(0x02);
    expect(code[2]).toBe(0x03);
  });

  it('tracks size correctly', () => {
    const chunk = new Chunk();
    expect(chunk.size).toBe(0);

    chunk.write(0x01, 1);
    expect(chunk.size).toBe(1);

    chunk.write(0x02, 1);
    expect(chunk.size).toBe(2);

    chunk.writeOpcode(0x03, 1);
    expect(chunk.size).toBe(3);

    chunk.writeOperand(0x04, 1);
    expect(chunk.size).toBe(4);
  });

  it('handles disassemble gracefully', () => {
    const chunk = new Chunk('test.zoya');
    chunk.write(0x01, 1);
    chunk.write(0x02, 2);

    const output = chunk.disassemble('test');
    expect(output).toContain('== test ==');
  });

  it('stores multiple constants of various types', () => {
    const chunk = new Chunk();
    chunk.addConstant(1);
    chunk.addConstant(2.5);
    chunk.addConstant('string');
    chunk.addConstant(true);
    chunk.addConstant(false);
    chunk.addConstant(null);

    expect(chunk.constants.length).toBe(6);
    expect(chunk.constants[0]).toBe(1);
    expect(chunk.constants[1]).toBe(2.5);
    expect(chunk.constants[2]).toBe('string');
    expect(chunk.constants[3]).toBe(true);
    expect(chunk.constants[4]).toBe(false);
    expect(chunk.constants[5]).toBeNull();
  });

  it('maintains line tracking for each byte', () => {
    const chunk = new Chunk();
    chunk.write(0x01, 1);
    chunk.write(0x02, 1);
    chunk.write(0x03, 5);
    chunk.write(0x04, 10);

    expect(chunk.lines).toEqual([1, 1, 5, 10]);
  });

  it('patches at the first position', () => {
    const chunk = new Chunk();
    chunk.write(0x00, 1);
    chunk.patch(0, 0xAB);
    expect(chunk.code[0]).toBe(0xAB);
  });
});
