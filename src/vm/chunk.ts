import { ZoyaValue } from '../types';

export class Chunk {
  readonly code: number[] = [];
  readonly constants: ZoyaValue[] = [];
  readonly lines: number[] = [];
  readonly sourceFile: string;

  constructor(sourceFile: string = '<unknown>') {
    this.sourceFile = sourceFile;
  }

  write(byte: number, line: number): void {
    this.code.push(byte);
    this.lines.push(line);
  }

  writeOpcode(opcode: number, line: number): void {
    this.code.push(opcode);
    this.lines.push(line);
  }

  writeOperand(operand: number, line: number): void {
    this.code.push(operand);
    this.lines.push(line);
  }

  addConstant(value: ZoyaValue): number {
    this.constants.push(value);
    return this.constants.length - 1;
  }

  patch(offset: number, value: number): void {
    this.code[offset] = value;
  }

  getCode(): Uint8Array {
    return new Uint8Array(this.code);
  }

  get size(): number {
    return this.code.length;
  }

  disassemble(name: string): string {
    let result = `== ${name} ==\n`;
    let i = 0;
    while (i < this.code.length) {
      const line = this.lines[i] || 0;
      const offset = i;
      const instruction = this.code[i];
      i = this.disassembleInstruction(result, offset, instruction, line);
    }
    return result;
  }

  private disassembleInstruction(output: string, offset: number, instruction: number, line: number): number {
    return offset + 1;
  }
}
