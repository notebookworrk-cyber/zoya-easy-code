import { performance } from 'perf_hooks';
import { assert, AssertionError } from './assert';
import { BenchmarkRunner } from './benchmark';
import { CoverageCollector, CoverageReport, CoverageFile } from './coverage';

export type TestResult = 'passed' | 'failed' | 'skipped' | 'error';

export interface TestCase {
  name: string;
  fn: () => void | Promise<void>;
  tags: string[];
  timeout: number;
}

export interface TestSuite {
  name: string;
  tests: TestCase[];
  beforeAll?: () => void | Promise<void>;
  afterAll?: () => void | Promise<void>;
  beforeEach?: () => void | Promise<void>;
  afterEach?: () => void | Promise<void>;
}

export interface TestReport {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
  duration: number;
  suites: TestSuiteReport[];
  coverage?: CoverageReport;
}

export interface TestSuiteReport {
  name: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
  duration: number;
  tests: TestResultEntry[];
}

export interface TestResultEntry {
  name: string;
  result: TestResult;
  duration: number;
  error?: string;
  stack?: string;
}

class TestSuiteBuilder {
  private name: string;
  private tests: TestCase[] = [];
  private beforeAllFn?: () => void | Promise<void>;
  private afterAllFn?: () => void | Promise<void>;
  private beforeEachFn?: () => void | Promise<void>;
  private afterEachFn?: () => void | Promise<void>;

  constructor(name: string) {
    this.name = name;
  }

  describe(name: string, fn: () => void): void {
    const subBuilder = new TestSuiteBuilder(`${this.name} > ${name}`);
    fn();
    this.tests.push(...subBuilder.build().tests);
  }

  it(name: string, fn: () => void | Promise<void>, timeout?: number): void {
    this.tests.push({
      name,
      fn,
      tags: [],
      timeout: timeout ?? 5000,
    });
  }

  beforeAll(fn: () => void | Promise<void>): void {
    this.beforeAllFn = fn;
  }

  afterAll(fn: () => void | Promise<void>): void {
    this.afterAllFn = fn;
  }

  beforeEach(fn: () => void | Promise<void>): void {
    this.beforeEachFn = fn;
  }

  afterEach(fn: () => void | Promise<void>): void {
    this.afterEachFn = fn;
  }

  build(): TestSuite {
    return {
      name: this.name,
      tests: this.tests,
      beforeAll: this.beforeAllFn,
      afterAll: this.afterAllFn,
      beforeEach: this.beforeEachFn,
      afterEach: this.afterEachFn,
    };
  }
}

export class TestRunner {
  private suites: TestSuite[] = [];
  private coverageCollector: CoverageCollector;

  constructor() {
    this.coverageCollector = new CoverageCollector();
  }

  register(suite: TestSuite): void {
    this.suites.push(suite);
  }

  registerSuite(name: string, definition: (builder: TestSuiteBuilder) => void): void {
    const builder = new TestSuiteBuilder(name);
    definition(builder);
    this.suites.push(builder.build());
  }

  async run(filter?: string): Promise<TestReport> {
    const start = performance.now();
    const suiteReports: TestSuiteReport[] = [];
    let total = 0;
    let passed = 0;
    let failed = 0;
    let skipped = 0;
    let errors = 0;

    for (const suite of this.suites) {
      const suiteStart = performance.now();
      const suiteReport = await this.runSuite(suite, filter);
      suiteReport.duration = performance.now() - suiteStart;
      suiteReports.push(suiteReport);

      total += suiteReport.total;
      passed += suiteReport.passed;
      failed += suiteReport.failed;
      skipped += suiteReport.skipped;
      errors += suiteReport.errors;
    }

    const duration = performance.now() - start;

    return {
      total,
      passed,
      failed,
      skipped,
      errors,
      duration,
      suites: suiteReports,
    };
  }

  async runFile(file: string): Promise<TestReport> {
    const matching = this.suites.filter(s => {
      const normalized = file.replace(/\\/g, '/').toLowerCase();
      return s.name.toLowerCase().includes(normalized) || normalized.includes(s.name.toLowerCase());
    });

    if (matching.length === 0) {
      return {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        errors: 0,
        duration: 0,
        suites: [],
      };
    }

    const saved = this.suites;
    this.suites = matching;
    const report = await this.run();
    this.suites = saved;
    return report;
  }

  async runAll(): Promise<TestReport> {
    return this.run();
  }

  getReport(): TestReport {
    return {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      errors: 0,
      duration: 0,
      suites: [],
    };
  }

  private async runSuite(suite: TestSuite, filter?: string): Promise<TestSuiteReport> {
    const results: TestResultEntry[] = [];
    const filtered = filter
      ? suite.tests.filter(t => t.name.toLowerCase().includes(filter.toLowerCase()))
      : suite.tests;

    if (filtered.length === 0) {
      return {
        name: suite.name,
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        errors: 0,
        duration: 0,
        tests: [],
      };
    }

    try {
      if (suite.beforeAll) {
        await suite.beforeAll();
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      const errorStack = e instanceof Error ? e.stack : undefined;
      for (const test of filtered) {
        results.push({
          name: test.name,
          result: 'error',
          duration: 0,
          error: `beforeAll failed: ${errorMsg}`,
          stack: errorStack,
        });
      }
      return {
        name: suite.name,
        total: filtered.length,
        passed: 0,
        failed: 0,
        skipped: 0,
        errors: filtered.length,
        duration: 0,
        tests: results,
      };
    }

    for (const test of filtered) {
      const testStart = performance.now();
      let result: TestResult = 'passed';
      let error: string | undefined;
      let stack: string | undefined;

      try {
        if (suite.beforeEach) {
          await suite.beforeEach();
        }
      } catch (e) {
        result = 'error';
        error = `beforeEach failed: ${e instanceof Error ? e.message : String(e)}`;
        stack = e instanceof Error ? e.stack : undefined;
      }

      if (result !== 'error') {
        try {
          const timer = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error(`Test timed out after ${test.timeout}ms`)), test.timeout);
          });

          await Promise.race([Promise.resolve(test.fn()), timer]);
          result = 'passed';
        } catch (e) {
          if (e instanceof AssertionError) {
            result = 'failed';
          } else {
            result = 'error';
          }
          error = e instanceof Error ? e.message : String(e);
          stack = e instanceof Error ? e.stack : undefined;
        }
      }

      if (result === 'passed') {
        try {
          if (suite.afterEach) {
            await suite.afterEach();
          }
        } catch (e) {
          result = 'error';
          error = `afterEach failed: ${e instanceof Error ? e.message : String(e)}`;
          stack = e instanceof Error ? e.stack : undefined;
        }
      }

      const duration = performance.now() - testStart;
      results.push({ name: test.name, result, duration, error, stack });
    }

    try {
      if (suite.afterAll) {
        await suite.afterAll();
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      const errorStack = e instanceof Error ? e.stack : undefined;
      results.push({
        name: '(afterAll)',
        result: 'error',
        duration: 0,
        error: `afterAll failed: ${errorMsg}`,
        stack: errorStack,
      });
    }

    const passed = results.filter(r => r.result === 'passed').length;
    const failed = results.filter(r => r.result === 'failed').length;
    const skipped = results.filter(r => r.result === 'skipped').length;
    const errors = results.filter(r => r.result === 'error').length;

    return {
      name: suite.name,
      total: results.length,
      passed,
      failed,
      skipped,
      errors,
      duration: 0,
      tests: results,
    };
  }

  formatReport(report: TestReport): string {
    const lines: string[] = [];
    const total = report.total;
    const passed = report.passed;
    const failed = report.failed + report.errors;
    const reset = '\x1b[0m';

    lines.push('');
    lines.push('  TEST RESULTS');
    lines.push('  ' + '\u2500'.repeat(56));

    for (const suite of report.suites) {
      const hasFailures = suite.failed > 0 || suite.errors > 0;
      const suiteIcon = hasFailures ? '\u2716' : '\u2714';
      const suiteColor = hasFailures ? '\x1b[31m' : '\x1b[32m';

      lines.push(`  ${suiteColor}${suiteIcon} ${suite.name}${reset}`);
      lines.push(`     ${suite.passed} passed, ${suite.failed} failed, ${suite.skipped} skipped, ${suite.errors} errors`);
      lines.push(`     Duration: ${suite.duration.toFixed(2)}ms`);
      lines.push('');

      for (const test of suite.tests) {
        const icon = test.result === 'passed' ? '\u2714' :
                     test.result === 'failed' ? '\u2716' :
                     test.result === 'skipped' ? '\u25CB' : '\u26A0';
        const color = test.result === 'passed' ? '\x1b[32m' :
                      test.result === 'failed' ? '\x1b[31m' :
                      test.result === 'skipped' ? '\x1b[33m' : '\x1b[35m';

        lines.push(`  ${color}    ${icon} ${test.name} (${test.duration.toFixed(2)}ms)${reset}`);

        if (test.error) {
          const indented = test.error.split('\n').map(l => `        ${l}`).join('\n');
          lines.push(indented);
        }
        if (test.stack) {
          const stackLines = test.stack.split('\n').slice(0, 3).map(l => `        ${l}`).join('\n');
          lines.push(stackLines);
        }
      }
    }

    lines.push('  ' + '\u2500'.repeat(56));

    const overallIcon = failed === 0 ? '\u2714' : '\u2716';
    const overallColor = failed === 0 ? '\x1b[32m' : '\x1b[31m';
    lines.push(`  ${overallColor}${overallIcon} Tests: ${total} total, ${passed} passed, ${failed} failed, ${report.skipped} skipped${reset}`);
    lines.push(`  Time: ${report.duration.toFixed(2)}ms`);
    lines.push('');

    return lines.join('\n');
  }

  printReport(report: TestReport): void {
    console.log(this.formatReport(report));
  }
}

export {
  assert,
  AssertionError,
  BenchmarkRunner,
  CoverageCollector,
  CoverageReport,
  CoverageFile,
  TestSuiteBuilder,
};
