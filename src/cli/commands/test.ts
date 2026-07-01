import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { Runtime } from '../../runtime/index';
import { ZoyaValue, ZOYA_NIL } from '../../types';

interface TestResult {
  name: string;
  file: string;
  passed: boolean;
  durationMs: number;
  error?: string;
}

function formatTime(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(1)}µs`;
  if (ms < 1000) return `${ms.toFixed(2)}ms`;
  return `${(ms / 1000).toFixed(3)}s`;
}

function discoverTestFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== 'node_modules') {
      results.push(...discoverTestFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.test.zoya')) {
      results.push(fullPath);
    }
  }
  return results;
}

function runSingleTest(filePath: string): TestResult {
  const start = performance.now();
  const testName = path.basename(filePath, '.test.zoya');

  try {
    const runtime = new Runtime();
    runtime.executeFile(filePath);
    const elapsed = performance.now() - start;
    return {
      name: testName,
      file: filePath,
      passed: true,
      durationMs: elapsed,
    };
  } catch (err) {
    const elapsed = performance.now() - start;
    return {
      name: testName,
      file: filePath,
      passed: false,
      durationMs: elapsed,
      error: (err as Error).message,
    };
  }
}

export async function testCommand(file?: string): Promise<void> {
  const startTotal = performance.now();

  if (file) {
    const filePath = path.resolve(file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`Test file not found: ${filePath}`);
    }
    const testFiles = [filePath];
    await executeTests(testFiles, startTotal);
  } else {
    const searchDirs = [
      path.resolve(process.cwd(), 'tests'),
      path.resolve(process.cwd(), 'src'),
      process.cwd(),
    ];

    let testFiles: string[] = [];
    for (const dir of searchDirs) {
      testFiles = discoverTestFiles(dir);
      if (testFiles.length > 0) break;
    }

    if (testFiles.length === 0) {
      console.log(chalk.yellow('\nNo test files found.'));
      console.log(chalk.dim('  Create a file named *.test.zoya to add tests.'));
      console.log(chalk.dim('  Use: echo \'print("hello")\' > tests/example.test.zoya'));
      return;
    }

    await executeTests(testFiles, startTotal);
  }
}

async function executeTests(testFiles: string[], startTotal: number): Promise<void> {
  const totalFiles = testFiles.length;
  const results: TestResult[] = [];
  let passed = 0;
  let failed = 0;

  console.log(chalk.cyan(`\n  Running ${totalFiles} test file${totalFiles !== 1 ? 's' : ''}...\n`));

  const ora = await import('ora');

  for (let i = 0; i < testFiles.length; i++) {
    const filePath = testFiles[i];
    const relativePath = path.relative(process.cwd(), filePath);
    const spinner = ora.default(`[${i + 1}/${totalFiles}] ${relativePath}`).start();

    const result = runSingleTest(filePath);
    results.push(result);

    if (result.passed) {
      spinner.suffixText = chalk.green(` ${formatTime(result.durationMs)}`);
      spinner.succeed();
      passed++;
    } else {
      spinner.suffixText = chalk.red(` ${formatTime(result.durationMs)}`);
      spinner.fail();
      failed++;
      if (result.error) {
        console.error(`    ${chalk.red(result.error.split('\n')[0])}`);
      }
    }
  }

  const totalTime = performance.now() - startTotal;

  console.log(chalk.dim('\n── Results ──'));
  console.log(`  ${chalk.white('Files:')}     ${chalk.yellow(totalFiles)}`);
  console.log(`  ${chalk.white('Passed:')}    ${chalk.green(passed)}`);
  console.log(`  ${chalk.white('Failed:')}    ${failed > 0 ? chalk.red(failed) : chalk.green(failed)}`);
  console.log(`  ${chalk.white('Time:')}      ${chalk.yellow(formatTime(totalTime))}`);

  if (failed > 0) {
    console.log(chalk.dim('\n── Failed Tests ──'));
    for (const r of results) {
      if (!r.passed && r.error) {
        const relativePath = path.relative(process.cwd(), r.file);
        console.log(`  ${chalk.red('✗')} ${chalk.white(relativePath)}`);
        console.log(`    ${chalk.dim(r.error)}`);
      }
    }
    process.exit(1);
  } else {
    console.log(chalk.green(`\n  ✓ All tests passed\n`));
  }
}
