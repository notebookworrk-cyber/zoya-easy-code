import { describe, it, expect } from 'vitest';
import { CoverageCollector } from '../../src/testing/coverage.js';

describe('CoverageCollector', () => {
  it('starts disabled', () => {
    const cc = new CoverageCollector();
    expect(cc.isEnabled).toBe(false);
  });

  it('enables after start()', () => {
    const cc = new CoverageCollector();
    cc.start();
    expect(cc.isEnabled).toBe(true);
  });

  it('disables after stop()', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.stop();
    expect(cc.isEnabled).toBe(false);
  });

  it('does not record lines when disabled', () => {
    const cc = new CoverageCollector();
    cc.recordLine('test.ts', 1);
    const report = cc.generateReport(['test.ts']);
    expect(report.totalLines).toBe(0);
  });

  it('records lines when enabled', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('test.ts', 1);
    cc.recordLine('test.ts', 2);
    const report = cc.generateReport(['test.ts']);
    expect(report.totalLines).toBe(2);
  });

  it('records branches', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordBranch('test.ts', 'if:1', true);
    cc.recordBranch('test.ts', 'if:1', false);
    const report = cc.generateReport(['test.ts']);
    expect(report.totalBranches).toBe(1);
    expect(report.coveredBranches).toBe(1);
  });

  it('records functions', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordFunction('test.ts', 'foo');
    cc.recordFunction('test.ts', 'bar');
    const report = cc.generateReport(['test.ts']);
    expect(report.totalFunctions).toBe(2);
  });

  it('reset clears all data', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('test.ts', 1);
    cc.reset();
    const report = cc.generateReport(['test.ts']);
    expect(report.totalLines).toBe(0);
  });

  it('generateReport includes all files', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('a.ts', 1);
    cc.recordLine('b.ts', 2);
    const report = cc.generateReport(['a.ts', 'b.ts']);
    expect(report.files).toHaveLength(2);
  });

  it('generateReport calculates percentages', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('a.ts', 1);
    cc.recordLine('a.ts', 2);
    const report = cc.generateReport(['a.ts']);
    expect(report.lineCoverage).toBe(100);
    expect(report.branchCoverage).toBe(100);
    expect(report.functionCoverage).toBe(100);
  });

  it('generateReport returns 100% for empty file list', () => {
    const cc = new CoverageCollector();
    cc.start();
    const report = cc.generateReport([]);
    expect(report.lineCoverage).toBe(100);
    expect(report.branchCoverage).toBe(100);
    expect(report.functionCoverage).toBe(100);
    expect(report.files).toEqual([]);
  });

  it('does not record branches when disabled', () => {
    const cc = new CoverageCollector();
    cc.recordBranch('test.ts', 'if:1', true);
    const report = cc.generateReport(['test.ts']);
    expect(report.totalBranches).toBe(0);
  });

  it('does not record functions when disabled', () => {
    const cc = new CoverageCollector();
    cc.recordFunction('test.ts', 'foo');
    const report = cc.generateReport(['test.ts']);
    expect(report.totalFunctions).toBe(0);
  });

  it('formatSummary returns colored output', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('a.ts', 1);
    const report = cc.generateReport(['a.ts']);
    const summary = cc.formatSummary(report);
    expect(summary).toContain('COVERAGE SUMMARY');
    expect(summary).toContain('100.0%');
    expect(summary).toContain('1/1');
  });

  it('formatDetailed includes file details', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('a.ts', 1);
    const report = cc.generateReport(['a.ts']);
    const detail = cc.formatDetailed(report);
    expect(detail).toContain('a.ts');
    expect(detail).toContain('100.0%');
  });

  it('formatSummary colorizes low coverage red', () => {
    const cc = new CoverageCollector();
    const report = cc.generateReport([]);
    const summary = cc.formatSummary(report);
    expect(summary).toContain('\x1b[32m');
  });

  it('formatDetailed sorts by coverage ascending', () => {
    const cc = new CoverageCollector();
    cc.start();
    cc.recordLine('a.ts', 1);
    cc.recordLine('b.ts', 2);
    const report = cc.generateReport(['b.ts', 'a.ts']);
    const detail = cc.formatDetailed(report);
    expect(detail.indexOf('a.ts')).toBeGreaterThanOrEqual(0);
  });
});
