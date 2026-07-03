import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { Lexer } from '../../compiler/lexer/index';
import { Parser } from '../../compiler/parser/index';
import { SemanticAnalyzer } from '../../compiler/semantic/index';
import { IRBuilder } from '../../compiler/ir/index';
import { PassManager, createDefaultPasses, createFullPasses } from '../../compiler/optimizer/index';
import { BytecodeGen, BytecodeChunk, ConstantPoolEntry } from '../../compiler/codegen/index';
import { Chunk } from '../../vm/chunk';
import { ZoyaValue } from '../../types';

interface BuildOptions {
  output?: string;
  optimize?: string;
}

const ZBC_MAGIC = 0x5A4F5942; // 'ZOBC'
const ZBC_VERSION = 0x00010000;

function writeU32(buffer: number[], value: number): void {
  buffer.push(value & 0xFF);
  buffer.push((value >> 8) & 0xFF);
  buffer.push((value >> 16) & 0xFF);
  buffer.push((value >> 24) & 0xFF);
}

function writeU16(buffer: number[], value: number): void {
  buffer.push(value & 0xFF);
  buffer.push((value >> 8) & 0xFF);
}

function writeString(buffer: number[], str: string): void {
  const encoded = Buffer.from(str, 'utf-8');
  writeU32(buffer, encoded.length);
  for (const b of encoded) {
    buffer.push(b);
  }
}

function buildBytecodeFile(chunks: BytecodeChunk[], sourcePath: string): Uint8Array {
  const buffer: number[] = [];
  writeU32(buffer, ZBC_MAGIC);
  writeU32(buffer, ZBC_VERSION);
  writeString(buffer, path.basename(sourcePath));

  writeU32(buffer, chunks.length);
  for (const chunk of chunks) {
    writeString(buffer, chunk.debug.functionName);
    writeU16(buffer, chunk.locals);
    writeU32(buffer, chunk.code.length);
    for (let i = 0; i < chunk.code.length; i++) {
      buffer.push(chunk.code[i]);
    }
    writeU32(buffer, chunk.constants.length);
    for (const c of chunk.constants) {
      const typeByte: number =
        c.type === 'null' ? 0 :
        c.type === 'boolean' ? 1 :
        c.type === 'number' ? 2 : 3;
      buffer.push(typeByte);
      writeString(buffer, String(c.value));
    }
  }

  return new Uint8Array(buffer);
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatTime(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(1)}µs`;
  if (ms < 1000) return `${ms.toFixed(2)}ms`;
  return `${(ms / 1000).toFixed(3)}s`;
}

export async function buildCommand(file: string, options: BuildOptions): Promise<void> {
  const filePath = path.resolve(file);
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  const optLevel = parseInt(options.optimize || '1', 10);
  const clampedLevel = Math.max(0, Math.min(3, optLevel));

  const source = fs.readFileSync(filePath, 'utf-8');
  const buildStart = performance.now();

  let spinner: any = null;
  const ora = await import('ora');
  spinner = ora.default('Building...').start();

  try {
    const t0 = performance.now();
    const lexer = new Lexer(source, filePath);
    const tokens = lexer.scanTokens();
    const lexTime = performance.now() - t0;

    spinner.text = 'Parsing...';
    const t1 = performance.now();
    const parser = new Parser(tokens);
    const ast = parser.parse();
    const parseDiags = parser.getDiagnostics();
    const parseTime = performance.now() - t1;

    if (parseDiags.hasErrors()) {
      spinner.stop();
      for (const diag of parseDiags.errors()) {
        const loc = diag.span ? `${diag.span.file}:${diag.span.start.line}:${diag.span.start.column}` : '';
        console.error(chalk.red(`error${loc ? ` ${loc}` : ''}: ${diag.message}`));
      }
      process.exit(1);
    }

    spinner.text = 'Analyzing...';
    const t2 = performance.now();
    const semanticAnalyzer = new SemanticAnalyzer();
    const analysis = semanticAnalyzer.analyze(ast);
    const semanticTime = performance.now() - t2;

    if (analysis.diagnostics.hasErrors()) {
      spinner.stop();
      for (const diag of analysis.diagnostics.errors()) {
        const loc = diag.span ? `${diag.span.file}:${diag.span.start.line}:${diag.span.start.column}` : '';
        console.error(chalk.red(`error${loc ? ` ${loc}` : ''}: ${diag.message}`));
      }
      process.exit(1);
    }

    spinner.text = 'Generating IR...';
    const t3 = performance.now();
    const irBuilder = new IRBuilder();
    const module = irBuilder.build(analysis.ast);
    const irTime = performance.now() - t3;

    spinner.text = 'Optimizing...';
    const t4 = performance.now();
    const passManager = new PassManager(5);
    if (clampedLevel >= 1) {
      passManager.addPasses(createDefaultPasses());
    }
    if (clampedLevel >= 2) {
      passManager.addPasses(createFullPasses());
    }
    const optChanges = passManager.run(module);
    const optTime = performance.now() - t4;

    spinner.text = 'Generating bytecode...';
    const t5 = performance.now();
    const bytecodeGen = new BytecodeGen();
    const chunks = bytecodeGen.generate(module);
    const codegenTime = performance.now() - t5;

    spinner.text = 'Writing output...';
    const bytecodeData = buildBytecodeFile(chunks, filePath);

    const outputPath = options.output
      ? path.resolve(options.output)
      : filePath.replace(/\.(zoya|zo)$/, '.zbc');

    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, bytecodeData);

    spinner.stop();

    const buildTime = performance.now() - buildStart;

    const totalInstrs = chunks.reduce((s, c) => s + c.code.length, 0);
    const totalConsts = chunks.reduce((s, c) => s + c.constants.length, 0);
    const totalLocals = chunks.reduce((s, c) => s + c.locals, 0);

    console.log(chalk.green(`\n✓ Build succeeded`));
    console.log(chalk.cyan(`  Output: ${chalk.bold(outputPath)}`));
    console.log(chalk.cyan(`  Size: ${chalk.bold(formatSize(bytecodeData.length))}`));

    console.log(chalk.dim('\n── Build Statistics ──'));
    console.log(`  ${chalk.white('Functions:')}      ${chalk.yellow(chunks.length)}`);
    console.log(`  ${chalk.white('Instructions:')}    ${chalk.yellow(totalInstrs)}`);
    console.log(`  ${chalk.white('Constants:')}       ${chalk.yellow(totalConsts)}`);
    console.log(`  ${chalk.white('Locals:')}          ${chalk.yellow(totalLocals)}`);

    if (clampedLevel > 0) {
      console.log(`  ${chalk.white('Opt level:')}       ${chalk.yellow(`O${clampedLevel}`)}`);
      console.log(`  ${chalk.white('Opt changes:')}     ${chalk.yellow(optChanges)}`);
    } else {
      console.log(`  ${chalk.white('Opt level:')}       ${chalk.dim('none')}`);
    }

    console.log(chalk.dim('\n── Timing ──'));
    console.log(`  ${chalk.white('Lexer:')}            ${chalk.yellow(formatTime(lexTime))}`);
    console.log(`  ${chalk.white('Parser:')}           ${chalk.yellow(formatTime(parseTime))}`);
    console.log(`  ${chalk.white('Semantic:')}         ${chalk.yellow(formatTime(semanticTime))}`);
    console.log(`  ${chalk.white('IR Gen:')}           ${chalk.yellow(formatTime(irTime))}`);
    console.log(`  ${chalk.white('Optimizer:')}        ${chalk.yellow(formatTime(optTime))}`);
    console.log(`  ${chalk.white('Codegen:')}          ${chalk.yellow(formatTime(codegenTime))}`);
    console.log(`  ${chalk.white('Total:')}            ${chalk.bold.yellow(formatTime(buildTime))}`);
  } catch (err) {
    if (spinner) {
      spinner.stop();
    }
    const error = err as Error;
    console.error(chalk.red(`Build error: ${error.message}`));
    process.exit(1);
  }
}
