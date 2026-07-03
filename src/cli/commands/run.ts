import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { Lexer } from '../../compiler/lexer/index';
import { Parser } from '../../compiler/parser/index';
import { SemanticAnalyzer } from '../../compiler/semantic/index';
import { IRBuilder } from '../../compiler/ir/index';
import { PassManager, createDefaultPasses, createFullPasses } from '../../compiler/optimizer/index';
import { BytecodeGen } from '../../compiler/codegen/index';
import { Chunk } from '../../vm/chunk';
import { VM } from '../../vm/index';
import { ZoyaValue, ZOYA_NIL } from '../../types';

interface RunOptions {
  profile?: boolean;
  verbose?: boolean;
}

interface TimingResult {
  phase: string;
  durationMs: number;
}

function formatTime(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(1)}µs`;
  if (ms < 1000) return `${ms.toFixed(2)}ms`;
  return `${(ms / 1000).toFixed(3)}s`;
}

function showSourceError(filePath: string, source: string, message: string, line?: number, column?: number): void {
  const lines = source.split('\n');
  if (line !== undefined && line > 0 && line <= lines.length) {
    const sourceLine = lines[line - 1];
    const gutter = line.toString().padStart(4, ' ');
    console.error(chalk.red(`error: ${message}`));
    console.error(chalk.dim(`  ┌─ ${filePath}:${line}:${column ?? 1}`));
    console.error(chalk.dim(`  │`));
    console.error(chalk.dim(`  ${gutter} │ ${sourceLine}`));
    if (column !== undefined) {
      const caretLine = ' '.repeat(column.toString().length + 2) + ' '.repeat(column - 1) + chalk.green('^');
      console.error(chalk.dim(caretLine));
    }
    console.error(chalk.dim(`  │`));
    console.error(chalk.dim(`  └─ ${message}`));
  } else {
    console.error(chalk.red(`error: ${message}`));
  }
}

function displayVerboseTimings(timings: TimingResult[]): void {
  const total = timings.reduce((s, t) => s + t.durationMs, 0);
  console.log(chalk.cyan('\n┌──────────────────────────────────┐'));
  console.log(chalk.cyan('│ Compilation Profile             │'));
  console.log(chalk.cyan('├──────────────────────────────────┤'));
  for (const t of timings) {
    const pct = total > 0 ? ((t.durationMs / total) * 100).toFixed(1) : '0.0';
    const bar = chalk.green('█'.repeat(Math.round((t.durationMs / total) * 20)));
    const rest = chalk.dim('░'.repeat(Math.max(0, 20 - Math.round((t.durationMs / total) * 20))));
    console.log(`│ ${chalk.white(t.phase.padEnd(18))} ${chalk.yellow(formatTime(t.durationMs).padStart(10))} │`);
    if (total > 0) {
      console.log(`│ ${bar}${rest} ${pct}%${' '.repeat(5)}│`);
    }
  }
  console.log(chalk.cyan('├──────────────────────────────────┤'));
  console.log(`│ ${chalk.white('Total'.padEnd(18))} ${chalk.bold.yellow(formatTime(total).padStart(10))} │`);
  console.log(chalk.cyan('└──────────────────────────────────┘\n'));
}

function displayVerboseOutput(source: string, tokens: unknown[], ast: unknown, ir: unknown, bytecode: Uint8Array): void {
  console.log(chalk.cyan('\n── Compilation Details ──\n'));
  console.log(chalk.magenta('Source:'));
  console.log(chalk.dim(source));
  console.log(chalk.magenta(`\nTokens (${tokens.length}):`));
  const sampleTokens = tokens.slice(0, 10);
  for (const t of sampleTokens) {
    console.log(chalk.dim(`  ${JSON.stringify(t)}`));
  }
  if (tokens.length > 10) {
    console.log(chalk.dim(`  ... and ${tokens.length - 10} more`));
  }
  console.log(chalk.magenta(`\nAST: ${JSON.stringify(ast).substring(0, 500)}...`));
  console.log(chalk.magenta(`\nIR: ${JSON.stringify(ir).substring(0, 500)}...`));
  console.log(chalk.magenta(`\nBytecode (${bytecode.length} bytes):`));
  const hex = Array.from(bytecode.slice(0, 32)).map(b => b.toString(16).padStart(2, '0')).join(' ');
  console.log(chalk.dim(`  ${hex}${bytecode.length > 32 ? '...' : ''}`));
}

export async function runCommand(file: string, options: RunOptions): Promise<void> {
  const filePath = path.resolve(file);
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
  if (!filePath.endsWith('.zoya') && !filePath.endsWith('.zo')) {
    console.warn(chalk.yellow(`Warning: '${path.basename(filePath)}' does not have a .zoya or .zo extension`));
  }

  const source = fs.readFileSync(filePath, 'utf-8');
  const timings: TimingResult[] = [];
  const startTotal = performance.now();

  let spinner: any = null;
  if (!options.profile && !options.verbose) {
    const ora = await import('ora');
    spinner = ora.default('Compiling...').start();
  }

  try {
    const t0 = performance.now();
    const lexer = new Lexer(source, filePath);
    const tokens = lexer.scanTokens();
    timings.push({ phase: 'Lexer', durationMs: performance.now() - t0 });
    if (options.verbose && spinner) {
      spinner.text = 'Tokens scanned';
    }

    const t1 = performance.now();
    const parser = new Parser(tokens);
    const ast = parser.parse();
    const parseDiags = parser.getDiagnostics();
    timings.push({ phase: 'Parser', durationMs: performance.now() - t1 });
    if (options.verbose && spinner) {
      spinner.text = 'AST parsed';
    }

    if (parseDiags.hasErrors()) {
      if (spinner) spinner.stop();
      for (const diag of parseDiags.errors()) {
        showSourceError(filePath, source, diag.message, diag.span?.start.line, diag.span?.start.column);
      }
      process.exit(1);
    }

    const t2 = performance.now();
    const semanticAnalyzer = new SemanticAnalyzer();
    const analysis = semanticAnalyzer.analyze(ast);
    timings.push({ phase: 'Semantic', durationMs: performance.now() - t2 });
    if (options.verbose && spinner) {
      spinner.text = 'Semantic analysis complete';
    }

    if (analysis.diagnostics.hasErrors()) {
      if (spinner) spinner.stop();
      for (const diag of analysis.diagnostics.errors()) {
        showSourceError(filePath, source, diag.message, diag.span?.start.line, diag.span?.start.column);
      }
      process.exit(1);
    }

    const t3 = performance.now();
    const irBuilder = new IRBuilder();
    const module = irBuilder.build(analysis.ast);
    timings.push({ phase: 'IR Gen', durationMs: performance.now() - t3 });
    if (options.verbose && spinner) {
      spinner.text = 'IR generated';
    }

    const t4 = performance.now();
    const passManager = new PassManager(5);
    passManager.addPasses(createDefaultPasses());
    const optChanges = passManager.run(module);
    timings.push({ phase: 'Optimizer', durationMs: performance.now() - t4 });
    if (options.verbose && spinner) {
      spinner.text = `Optimization complete (${optChanges} changes)`;
    }

    const t5 = performance.now();
    const bytecodeGen = new BytecodeGen();
    const chunks = bytecodeGen.generate(module);
    timings.push({ phase: 'Codegen', durationMs: performance.now() - t5 });
    if (options.verbose && spinner) {
      spinner.text = 'Bytecode generated';
    }

    const t6 = performance.now();
    const vm = new VM();
    let result: ZoyaValue = ZOYA_NIL;
    if (chunks.length > 0) {
      const chunk = new Chunk(filePath);
      for (let i = 0; i < chunks[0].code.length; i++) {
        chunk.write(chunks[0].code[i], 1);
      }
      for (const c of chunks[0].constants) {
        const val: ZoyaValue =
          c.value === null ? null :
          typeof c.value === 'boolean' ? c.value :
          typeof c.value === 'number' ? c.value :
          String(c.value);
        chunk.addConstant(val);
      }
      result = vm.interpret(chunk);
    } else {
      const chunk = new Chunk(filePath);
      result = vm.interpret(chunk);
    }
    timings.push({ phase: 'VM Exec', durationMs: performance.now() - t6 });

    const totalTime = performance.now() - startTotal;
    timings.push({ phase: 'Total', durationMs: totalTime });

    if (spinner) {
      spinner.stop();
    }

    console.log(chalk.green('\n✓ Execution completed'));
    if (options.profile) {
      displayVerboseTimings(timings);
    }
    if (options.verbose) {
      displayVerboseOutput(source, tokens, ast, module, chunks.length > 0 ? chunks[0].code : new Uint8Array(0));
    }
    console.log(chalk.cyan(`\nExecution time: ${chalk.bold(formatTime(totalTime))}`));
    if (vm.getStackSize() > 0) {
      console.log(chalk.dim(`Result: ${JSON.stringify(result)}`));
    }
  } catch (err) {
    if (spinner) {
      spinner.stop();
    }

    const error = err as Error;
    const match = error.message.match(/(.+):(\d+):(\d+):\s(.+)/);
    if (match) {
      const line = parseInt(match[2], 10);
      const column = parseInt(match[3], 10);
      showSourceError(filePath, source, match[4].trim(), line, column);
    } else if (error.message.includes('RuntimeError')) {
      console.error(chalk.red(`Runtime error: ${error.message}`));
    } else {
      console.error(chalk.red(`Error: ${error.message}`));
    }
    process.exit(1);
  }
}
