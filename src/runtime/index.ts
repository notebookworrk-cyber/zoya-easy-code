import { VM } from '../vm/index';
import { Chunk } from '../vm/chunk';
import { ZoyaValue, ZOYA_NIL } from '../types';
import { Lexer, Token } from '../compiler/lexer/index';
import { Parser } from '../compiler/parser/index';
import { SemanticAnalyzer } from '../compiler/semantic/index';
import { IRBuilder } from '../compiler/ir/index';
import { BytecodeGen, BytecodeChunk } from '../compiler/codegen/index';
import * as fs from 'fs';
import * as path from 'path';

export interface RuntimeConfig {
  debugMode: boolean;
  gcThreshold: number;
  maxStackSize: number;
  modulePaths: string[];
}

export class Runtime {
  private vm: VM;
  private config: RuntimeConfig;
  private moduleCache: Map<string, ZoyaValue> = new Map();
  private fileCache: Map<string, string> = new Map();

  constructor(config?: Partial<RuntimeConfig>) {
    this.config = {
      debugMode: false,
      gcThreshold: 1000,
      maxStackSize: 256,
      modulePaths: [],
      ...config,
    };
    this.vm = new VM();
  }

  execute(source: string, filename: string = '<repl>'): ZoyaValue {
    if (this.moduleCache.has(filename)) {
      return this.moduleCache.get(filename)!;
    }

    const lexer = new Lexer(source, filename);
    const tokens = lexer.scanTokens();
    const parser = new Parser(tokens);
    const ast = parser.parse();

    const diagnostics = parser.getDiagnostics();
    if (diagnostics.hasErrors()) {
      const errMsg = diagnostics.errors().map(e => e.message).join('\n');
      throw new Error(`Parse error in ${filename}:\n${errMsg}`);
    }

    const semanticAnalyzer = new SemanticAnalyzer();
    const analysis = semanticAnalyzer.analyze(ast);

    if (analysis.diagnostics.hasErrors()) {
      const errMsg = analysis.diagnostics.errors().map(e => e.message).join('\n');
      throw new Error(`Semantic error in ${filename}:\n${errMsg}`);
    }

    const irBuilder = new IRBuilder();
    const module = irBuilder.build(analysis.ast);

    const bytecodeGen = new BytecodeGen();
    const chunks = bytecodeGen.generate(module);

    if (chunks.length === 0) {
      const chunk = new Chunk(filename);
      const result = this.vm.interpret(chunk);
      this.moduleCache.set(filename, result);
      return result;
    }

    const chunk = this.bytecodeChunkToVmChunk(chunks[0], filename);
    const result = this.vm.interpret(chunk);
    this.moduleCache.set(filename, result);
    return result;
  }

  executeFile(filepath: string): ZoyaValue {
    const resolvedPath = path.resolve(filepath);
    if (this.fileCache.has(resolvedPath)) {
      return this.moduleCache.get(resolvedPath) || ZOYA_NIL;
    }

    if (!fs.existsSync(resolvedPath)) {
      throw new Error(`File not found: ${resolvedPath}`);
    }

    const source = fs.readFileSync(resolvedPath, 'utf-8');
    this.fileCache.set(resolvedPath, source);
    return this.execute(source, resolvedPath);
  }

  defineNative(name: string, arity: number, fn: (...args: ZoyaValue[]) => ZoyaValue): void {
    this.vm.defineNative(name, arity, fn);
  }

  setGlobal(name: string, value: ZoyaValue): void {
    this.vm.setGlobal(name, value);
  }

  getGlobal(name: string): ZoyaValue | undefined {
    return this.vm.getGlobal(name);
  }

  getVM(): VM {
    return this.vm;
  }

  getModuleCache(): ReadonlyMap<string, ZoyaValue> {
    return this.moduleCache;
  }

  clearModuleCache(): void {
    this.moduleCache.clear();
    this.fileCache.clear();
  }

  reset(): void {
    this.vm.reset();
    this.moduleCache.clear();
    this.fileCache.clear();
  }

  private bytecodeChunkToVmChunk(bc: BytecodeChunk, filename: string): Chunk {
    const chunk = new Chunk(filename);
    for (let i = 0; i < bc.code.length; i++) {
      chunk.write(bc.code[i], 1);
    }
    for (const c of bc.constants) {
      const val: ZoyaValue =
        c.value === null ? null :
        typeof c.value === 'boolean' ? c.value :
        typeof c.value === 'number' ? c.value :
        String(c.value);
      chunk.addConstant(val);
    }
    return chunk;
  }
}
