import { describe, it, expect, beforeEach } from 'vitest';
import { TestRunner, TestSuite, TestReport } from '../../src/testing/index';
import { assert, AssertionError } from '../../src/testing/assert';

describe('TestRunner', () => {
  let runner: TestRunner;

  beforeEach(() => {
    runner = new TestRunner();
  });

  describe('suite registration and running', () => {
    it('registers and runs a passing test', async () => {
      const suite: TestSuite = {
        name: 'MathTests',
        tests: [
          { name: 'adds numbers', fn: () => { assert.equal(1 + 1, 2); }, tags: [], timeout: 5000 },
        ],
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.total).toBe(1);
      expect(report.passed).toBe(1);
      expect(report.failed).toBe(0);
    });

    it('registers and runs a failing test', async () => {
      const suite: TestSuite = {
        name: 'FailingTests',
        tests: [
          { name: 'fails assertion', fn: () => { assert.equal(1, 2); }, tags: [], timeout: 5000 },
        ],
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.failed).toBe(1);
      expect(report.passed).toBe(0);
    });

    it('handles multiple suites', async () => {
      runner.register({
        name: 'Suite A',
        tests: [
          { name: 'test A1', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
          { name: 'test A2', fn: () => { assert.equal(1, 1); }, tags: [], timeout: 5000 },
        ],
      });
      runner.register({
        name: 'Suite B',
        tests: [
          { name: 'test B1', fn: () => { assert.false(false); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run();
      expect(report.total).toBe(3);
      expect(report.passed).toBe(3);
      expect(report.suites).toHaveLength(2);
    });

    it('handles test errors', async () => {
      const suite: TestSuite = {
        name: 'ErrorTests',
        tests: [
          { name: 'throws error', fn: () => { throw new Error('Unexpected error'); }, tags: [], timeout: 5000 },
        ],
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.errors).toBe(1);
      expect(report.passed).toBe(0);
    });
  });

  describe('hooks', () => {
    it('runs beforeEach before each test', async () => {
      let counter = 0;
      const suite: TestSuite = {
        name: 'HookTests',
        tests: [
          { name: 'test 1', fn: () => { assert.equal(counter, 1); }, tags: [], timeout: 5000 },
          { name: 'test 2', fn: () => { assert.equal(counter, 1); }, tags: [], timeout: 5000 },
        ],
        beforeEach: () => { counter = 1; },
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.passed).toBe(2);
    });

    it('runs afterEach after each test', async () => {
      const results: string[] = [];
      const suite: TestSuite = {
        name: 'AfterEachTests',
        tests: [
          { name: 'test 1', fn: () => { results.push('test1'); }, tags: [], timeout: 5000 },
          { name: 'test 2', fn: () => { results.push('test2'); }, tags: [], timeout: 5000 },
        ],
        afterEach: () => { results.push('after'); },
      };
      runner.register(suite);
      await runner.run();
      expect(results).toEqual(['test1', 'after', 'test2', 'after']);
    });

    it('runs beforeAll once before all tests', async () => {
      let initValue = 0;
      const suite: TestSuite = {
        name: 'BeforeAllTests',
        tests: [
          { name: 'test 1', fn: () => { assert.equal(initValue, 42); }, tags: [], timeout: 5000 },
          { name: 'test 2', fn: () => { assert.equal(initValue, 42); }, tags: [], timeout: 5000 },
        ],
        beforeAll: () => { initValue = 42; },
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.passed).toBe(2);
    });

    it('runs afterAll once after all tests', async () => {
      let cleanedUp = false;
      const suite: TestSuite = {
        name: 'AfterAllTests',
        tests: [
          { name: 'test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
        afterAll: () => { cleanedUp = true; },
      };
      runner.register(suite);
      await runner.run();
      expect(cleanedUp).toBe(true);
    });

    it('marks all tests as error when beforeAll fails', async () => {
      const suite: TestSuite = {
        name: 'FailSetupTests',
        tests: [
          { name: 'test 1', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
          { name: 'test 2', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
        beforeAll: () => { throw new Error('Setup failed'); },
      };
      runner.register(suite);
      const report = await runner.run();
      expect(report.errors).toBe(2);
    });
  });

  describe('test filtering', () => {
    it('filters tests by name', async () => {
      runner.register({
        name: 'FilterSuite',
        tests: [
          { name: 'alpha test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
          { name: 'beta test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
          { name: 'gamma test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run('beta');
      expect(report.total).toBe(1);
      expect(report.passed).toBe(1);
    });

    it('returns empty report when no tests match filter', async () => {
      runner.register({
        name: 'EmptyFilterSuite',
        tests: [
          { name: 'only test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run('nonexistent');
      expect(report.total).toBe(0);
    });
  });

  describe('report generation', () => {
    it('generates report with correct structure', async () => {
      runner.register({
        name: 'ReportSuite',
        tests: [
          { name: 'passing', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
          { name: 'failing', fn: () => { assert.false(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run();
      expect(report).toHaveProperty('total', 2);
      expect(report).toHaveProperty('passed', 1);
      expect(report).toHaveProperty('failed', 1);
      expect(report).toHaveProperty('duration');
      expect(report).toHaveProperty('suites');
      expect(report.suites).toHaveLength(1);
    });

    it('includes test results in suite reports', async () => {
      runner.register({
        name: 'DetailSuite',
        tests: [
          { name: 'detail test', fn: () => { assert.equal(1, 1); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run();
      const suite = report.suites[0];
      expect(suite.tests).toHaveLength(1);
      expect(suite.tests[0].name).toBe('detail test');
      expect(suite.tests[0].result).toBe('passed');
      expect(suite.tests[0].duration).toBeGreaterThanOrEqual(0);
    });

    it('includes error message for failed tests', async () => {
      runner.register({
        name: 'ErrorMsgSuite',
        tests: [
          { name: 'failing test', fn: () => { assert.equal(1, 2, 'Values did not match'); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run();
      const test = report.suites[0].tests[0];
      expect(test.error).toContain('Values did not match');
    });
  });

  describe('registerSuite with builder', () => {
    it('registers a suite using the builder pattern', async () => {
      runner.registerSuite('BuilderSuite', (suite) => {
        suite.it('builder test', () => {
          assert.true(true);
        });
      });

      const report = await runner.run();
      expect(report.total).toBe(1);
      expect(report.passed).toBe(1);
    });

    it('supports nested describe blocks', async () => {
      runner.registerSuite('NestedSuite', (suite) => {
        suite.describe('Group A', () => {
          suite.it('test in group', () => {
            assert.equal(1, 1);
          });
        });
      });

      const report = await runner.run();
      expect(report.suites.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('format report', () => {
    it('formats report as string', async () => {
      runner.register({
        name: 'FormatSuite',
        tests: [
          { name: 'test', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.run();
      const formatted = runner.formatReport(report);
      expect(typeof formatted).toBe('string');
      expect(formatted.length).toBeGreaterThan(0);
    });
  });

  describe('runFile', () => {
    it('runs suites matching file name', async () => {
      runner.register({
        name: 'ModuleATest',
        tests: [
          { name: 'test A', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });
      runner.register({
        name: 'ModuleBTest',
        tests: [
          { name: 'test B', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.runFile('ModuleB');
      expect(report.total).toBe(1);
      expect(report.suites[0].name).toBe('ModuleBTest');
    });

    it('returns empty report for missing file', async () => {
      const report = await runner.runFile('nonexistent');
      expect(report.total).toBe(0);
    });
  });

  describe('runAll', () => {
    it('runs all registered suites', async () => {
      runner.register({
        name: 'Suite1',
        tests: [
          { name: 'test1', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });
      runner.register({
        name: 'Suite2',
        tests: [
          { name: 'test2', fn: () => { assert.true(true); }, tags: [], timeout: 5000 },
        ],
      });

      const report = await runner.runAll();
      expect(report.total).toBe(2);
    });
  });

  describe('async tests', () => {
    it('supports async test functions', async () => {
      runner.register({
        name: 'AsyncTests',
        tests: [
          {
            name: 'async test',
            fn: async () => {
              await new Promise(resolve => setTimeout(resolve, 10));
              assert.equal(1, 1);
            },
            tags: [],
            timeout: 5000,
          },
        ],
      });

      const report = await runner.run();
      expect(report.passed).toBe(1);
    });

    it('handles async failures properly', async () => {
      runner.register({
        name: 'AsyncFailTests',
        tests: [
          {
            name: 'async fail',
            fn: async () => {
              await new Promise(resolve => setTimeout(resolve, 10));
              assert.equal(1, 2);
            },
            tags: [],
            timeout: 5000,
          },
        ],
      });

      const report = await runner.run();
      expect(report.failed).toBe(1);
    });
  });
});
