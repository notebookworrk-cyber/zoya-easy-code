import { describe, it, expect, vi } from 'vitest';
import { BenchmarkRunner } from '../../src/testing/benchmark.js';

describe('BenchmarkRunner', () => {
  it('registers a suite', async () => {
    const runner = new BenchmarkRunner();
    runner.register({ name: 'test', benchmarks: [] });
    const results = await runner.run();
    expect(results).toEqual([]);
  });

  it('adds a benchmark to default suite', async () => {
    const runner = new BenchmarkRunner();
    runner.add('empty', () => {});
    const results = await runner.run();
    expect(results).toHaveLength(1);
  });

  it('runs a named suite', async () => {
    const runner = new BenchmarkRunner();
    runner.register({ name: 'math', benchmarks: [{ name: 'add', fn: () => 1 + 1 }] });
    const results = await runner.runSuite('math');
    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('add');
  });

  it('runs all suites', async () => {
    const runner = new BenchmarkRunner();
    runner.register({ name: 'a', benchmarks: [{ name: 'a1', fn: () => {} }] });
    runner.register({ name: 'b', benchmarks: [{ name: 'b1', fn: () => {} }] });
    const results = await runner.run();
    expect(results).toHaveLength(2);
  });

  it('throws for unknown suite', async () => {
    const runner = new BenchmarkRunner();
    await expect(runner.runSuite('nonexistent')).rejects.toThrow("Benchmark suite 'nonexistent' not found");
  });

  it('produces valid BenchmarkResult fields', async () => {
    const runner = new BenchmarkRunner();
    runner.add('fib', () => {
      let a = 0, b = 1;
      for (let i = 0; i < 20; i++) { const t = a + b; a = b; b = t; }
    });
    const results = await runner.run();
    const r = results[0];
    expect(r.name).toBe('fib');
    expect(r.iterations).toBeGreaterThan(0);
    expect(r.totalTime).toBeGreaterThanOrEqual(0);
    expect(r.averageTime).toBeGreaterThanOrEqual(0);
    expect(r.minTime).toBeGreaterThanOrEqual(0);
    expect(r.maxTime).toBeGreaterThanOrEqual(r.minTime);
    expect(r.operationsPerSecond).toBeGreaterThan(0);
  });

  it('runs setup before benchmark', async () => {
    const setup = vi.fn();
    const runner = new BenchmarkRunner();
    runner.register({
      name: 'default',
      benchmarks: [{ name: 's', fn: () => {}, setup }],
    });
    await runner.run();
    expect(setup).toHaveBeenCalled();
  });

  it('runs teardown after benchmark', async () => {
    const teardown = vi.fn();
    const runner = new BenchmarkRunner();
    runner.register({
      name: 'default',
      benchmarks: [{ name: 't', fn: () => {}, teardown }],
    });
    await runner.run();
    expect(teardown).toHaveBeenCalled();
  });

  it('respects explicit iteration count', async () => {
    const runner = new BenchmarkRunner();
    runner.register({
      name: 'default',
      benchmarks: [{ name: 'exact', fn: () => {}, iterations: 50 }],
    });
    const results = await runner.run();
    expect(results[0].iterations).toBe(50);
  });

  it('formatResults returns string', () => {
    const runner = new BenchmarkRunner();
    const formatted = runner.formatResults([]);
    expect(formatted).toBe('No benchmark results');
  });

  it('formatResults with results', () => {
    const runner = new BenchmarkRunner();
    const results = [{
      name: 'test',
      iterations: 100,
      totalTime: 50,
      averageTime: 0.5,
      minTime: 0.1,
      maxTime: 1.2,
      operationsPerSecond: 2000,
    }];
    const formatted = runner.formatResults(results);
    expect(formatted).toContain('BENCHMARK RESULTS');
    expect(formatted).toContain('test');
    expect(formatted).toContain('2000');
  });

  it('printResults calls console.log', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const runner = new BenchmarkRunner();
    runner.printResults([]);
    expect(spy).toHaveBeenCalledWith('No benchmark results');
    spy.mockRestore();
  });

  it('calibrates iterations for fast functions', async () => {
    const runner = new BenchmarkRunner();
    runner.add('fast', () => {});
    const results = await runner.run();
    expect(results[0].iterations).toBeGreaterThanOrEqual(10);
  });

  it('records memory usage if available', async () => {
    const runner = new BenchmarkRunner();
    runner.add('mem', () => {});
    const results = await runner.run();
    expect(results[0].memoryUsed).toBeDefined();
  });
});
