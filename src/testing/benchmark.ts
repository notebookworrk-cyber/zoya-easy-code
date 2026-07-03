import { performance } from 'perf_hooks';

export interface BenchmarkResult {
  name: string;
  iterations: number;
  totalTime: number;
  averageTime: number;
  minTime: number;
  maxTime: number;
  operationsPerSecond: number;
  memoryUsed?: number;
}

export interface BenchmarkSuite {
  name: string;
  benchmarks: Benchmark[];
}

export interface Benchmark {
  name: string;
  fn: () => void;
  iterations?: number;
  setup?: () => void;
  teardown?: () => void;
}

const DEFAULT_ITERATIONS = 1000;
const WARMUP_ITERATIONS = 100;
const MIN_CALIBRATION_TIME = 100;
const MAX_ITERATIONS = 1000000;

export class BenchmarkRunner {
  private suites: BenchmarkSuite[] = [];

  register(suite: BenchmarkSuite): void {
    this.suites.push(suite);
  }

  add(name: string, fn: () => void, iterations?: number): void {
    let suite = this.suites.find(s => s.name === 'default');
    if (!suite) {
      suite = { name: 'default', benchmarks: [] };
      this.suites.push(suite);
    }
    suite.benchmarks.push({ name, fn, iterations });
  }

  async run(): Promise<BenchmarkResult[]> {
    const results: BenchmarkResult[] = [];
    for (const suite of this.suites) {
      const suiteResults = await this.runSuite(suite.name);
      results.push(...suiteResults);
    }
    return results;
  }

  async runSuite(name: string): Promise<BenchmarkResult[]> {
    const suite = this.suites.find(s => s.name === name);
    if (!suite) {
      throw new Error(`Benchmark suite '${name}' not found`);
    }

    const results: BenchmarkResult[] = [];
    for (const benchmark of suite.benchmarks) {
      const result = await this.runBenchmark(benchmark);
      results.push(result);
    }
    return results;
  }

  private async runBenchmark(benchmark: Benchmark): Promise<BenchmarkResult> {
    const iterations = benchmark.iterations ?? this.calibrateIterations(benchmark.fn);

    if (benchmark.setup) {
      benchmark.setup();
    }

    for (let i = 0; i < WARMUP_ITERATIONS; i++) {
      benchmark.fn();
    }

    const times: number[] = [];
    let totalTime = 0;

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      benchmark.fn();
      const elapsed = performance.now() - start;
      times.push(elapsed);
      totalTime += elapsed;
    }

    if (benchmark.teardown) {
      benchmark.teardown();
    }

    const sorted = [...times].sort((a, b) => a - b);
    const averageTime = totalTime / iterations;
    const minTime = sorted[0];
    const maxTime = sorted[sorted.length - 1];
    const operationsPerSecond = averageTime > 0 ? 1000 / averageTime : 0;

    let memoryUsed: number | undefined;
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const mem = process.memoryUsage();
      memoryUsed = mem.heapUsed;
    }

    return {
      name: benchmark.name,
      iterations,
      totalTime,
      averageTime,
      minTime,
      maxTime,
      operationsPerSecond,
      memoryUsed,
    };
  }

  private calibrateIterations(fn: () => void): number {
    const sampleStart = performance.now();
    let count = 0;
    while (performance.now() - sampleStart < MIN_CALIBRATION_TIME && count < 10000) {
      fn();
      count++;
    }
    const sampleTime = performance.now() - sampleStart;
    const estimatedPerOp = sampleTime / Math.max(count, 1);

    if (estimatedPerOp <= 0) return DEFAULT_ITERATIONS;

    const idealCount = Math.floor(2000 / estimatedPerOp);
    return Math.min(Math.max(idealCount, 10), MAX_ITERATIONS);
  }

  formatResults(results: BenchmarkResult[]): string {
    if (results.length === 0) return 'No benchmark results';

    const lines: string[] = [];
    lines.push('='.repeat(90));
    lines.push('  BENCHMARK RESULTS');
    lines.push('='.repeat(90));
    lines.push(
      '  '.padEnd(5) +
      'Name'.padEnd(30) +
      'Iterations'.padEnd(14) +
      'Avg (ms)'.padEnd(12) +
      'Min (ms)'.padEnd(12) +
      'Max (ms)'.padEnd(12) +
      'Ops/sec'.padEnd(14),
    );
    lines.push('-'.repeat(90));

    for (const r of results) {
      lines.push(
        '  '.padEnd(5) +
        r.name.padEnd(30) +
        r.iterations.toString().padEnd(14) +
        r.averageTime.toFixed(4).padEnd(12) +
        r.minTime.toFixed(4).padEnd(12) +
        r.maxTime.toFixed(4).padEnd(12) +
        Math.round(r.operationsPerSecond).toLocaleString().padEnd(14),
      );
    }

    lines.push('-'.repeat(90));
    return lines.join('\n');
  }

  printResults(results: BenchmarkResult[]): void {
    console.log(this.formatResults(results));
  }
}
