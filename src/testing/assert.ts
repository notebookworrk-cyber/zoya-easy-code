import { ZoyaValue } from '../types';

export class AssertionError extends Error {
  public readonly expected?: unknown;
  public readonly actual?: unknown;

  constructor(message: string, expected?: unknown, actual?: unknown) {
    super(message);
    this.name = 'AssertionError';
    this.expected = expected;
    this.actual = actual;
  }
}

function escapeString(value: unknown): string {
  if (typeof value === 'string') return `"${value}"`;
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function formatAssertMessage(expected: unknown, actual: unknown): string {
  return `Expected ${escapeString(expected)}, but got ${escapeString(actual)}`;
}

function isDeepEqual(a: unknown, b: unknown, visited?: Set<unknown>): boolean {
  if (a === b) return true;
  if (a === null || b === null) return a === b;
  if (a === undefined || b === undefined) return a === b;
  if (typeof a !== typeof b) return false;

  if (typeof a === 'number' && typeof b === 'number') {
    if (Number.isNaN(a) && Number.isNaN(b)) return true;
    return a === b;
  }

  if (typeof a === 'string' || typeof a === 'boolean') return a === b;

  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!isDeepEqual(a[i], b[i], visited)) return false;
    }
    return true;
  }

  if (typeof a === 'object' && typeof b === 'object') {
    if (!visited) visited = new Set<unknown>();
    if (visited.has(a)) return true;
    visited.add(a);

    const aObj = a as Record<string, unknown>;
    const bObj = b as Record<string, unknown>;
    const aKeys = Object.keys(aObj);
    const bKeys = Object.keys(bObj);

    if (aKeys.length !== bKeys.length) return false;

    for (const key of aKeys) {
      if (!Object.prototype.hasOwnProperty.call(bObj, key)) return false;
      if (!isDeepEqual(aObj[key], bObj[key], visited)) return false;
    }
    return true;
  }

  return a === b;
}

function stringify(value: unknown): string {
  if (value === null) return 'nil';
  if (value === undefined) return 'undefined';
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return Number.isInteger(value) ? value.toString() : value.toFixed(4);
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return `[${value.map(stringify).join(', ')}]`;
    }
    try {
      return JSON.stringify(value, (_key, val) => {
        if (typeof val === 'bigint') return val.toString();
        return val;
      });
    } catch {
      return String(value);
    }
  }
  return String(value);
}

interface ZoyaObject {
  readonly __zoya_type: string;
}

function isZoyaObject(value: unknown): value is ZoyaObject {
  return value !== null && typeof value === 'object' && '__zoya_type' in value;
}

export const assert = {
  equal<T>(actual: T, expected: T, message?: string): void {
    if (actual !== expected) {
      if (typeof actual === 'number' && typeof expected === 'number' && Number.isNaN(actual) && Number.isNaN(expected)) {
        return;
      }
      throw new AssertionError(
        message ?? formatAssertMessage(expected, actual),
        expected,
        actual,
      );
    }
  },

  notEqual<T>(actual: T, expected: T, message?: string): void {
    if (actual === expected) {
      if (typeof actual === 'number' && typeof expected === 'number' && Number.isNaN(actual) && Number.isNaN(expected)) {
        return;
      }
      throw new AssertionError(
        message ?? `Expected ${escapeString(actual)} to not equal ${escapeString(expected)}`,
        expected,
        actual,
      );
    }
  },

  true(value: boolean, message?: string): void {
    if (value !== true) {
      throw new AssertionError(
        message ?? `Expected true, but got ${escapeString(value)}`,
        true,
        value,
      );
    }
  },

  false(value: boolean, message?: string): void {
    if (value !== false) {
      throw new AssertionError(
        message ?? `Expected false, but got ${escapeString(value)}`,
        false,
        value,
      );
    }
  },

  throws(fn: () => void, message?: string): void {
    let threw = false;
    try {
      fn();
    } catch {
      threw = true;
    }
    if (!threw) {
      throw new AssertionError(
        message ?? 'Expected function to throw, but it did not',
      );
    }
  },

  doesNotThrow(fn: () => void, message?: string): void {
    try {
      fn();
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      throw new AssertionError(
        message ?? `Expected function not to throw, but it threw: ${errMsg}`,
        undefined,
        e,
      );
    }
  },

  near(actual: number, expected: number, epsilon: number = 1e-10, message?: string): void {
    const diff = Math.abs(actual - expected);
    if (diff > epsilon) {
      throw new AssertionError(
        message ?? `Expected ${actual} to be near ${expected} (epsilon: ${epsilon})`,
        expected,
        actual,
      );
    }
  },

  greaterThan(actual: number, threshold: number, message?: string): void {
    if (!(actual > threshold)) {
      throw new AssertionError(
        message ?? `Expected ${actual} to be greater than ${threshold}`,
        threshold,
        actual,
      );
    }
  },

  lessThan(actual: number, threshold: number, message?: string): void {
    if (!(actual < threshold)) {
      throw new AssertionError(
        message ?? `Expected ${actual} to be less than ${threshold}`,
        threshold,
        actual,
      );
    }
  },

  contains(haystack: string | unknown[], needle: unknown, message?: string): void {
    if (typeof haystack === 'string') {
      if (typeof needle !== 'string') {
        throw new AssertionError('When haystack is a string, needle must also be a string');
      }
      if (!haystack.includes(needle)) {
        throw new AssertionError(
          message ?? `Expected "${haystack}" to contain "${needle}"`,
          needle,
          haystack,
        );
      }
    } else if (Array.isArray(haystack)) {
      if (!haystack.includes(needle)) {
        throw new AssertionError(
          message ?? `Expected array to contain ${escapeString(needle)}`,
          needle,
          haystack,
        );
      }
    } else {
      throw new AssertionError('Haystack must be a string or array');
    }
  },

  type(value: unknown, type: string, message?: string): void {
    if (isZoyaObject(value)) {
      const actualType = value.__zoya_type;
      if (actualType !== type) {
        throw new AssertionError(
          message ?? `Expected type "${type}", but got "${actualType}"`,
          type,
          actualType,
        );
      }
      return;
    }

    if (value === null) {
      if (type !== 'null' && type !== 'nil') {
        throw new AssertionError(
          message ?? `Expected type "${type}", but got "null"`,
          type,
          'null',
        );
      }
      return;
    }

    const jsType = typeof value;
    const typeMap: Record<string, string[]> = {
      null: ['null', 'nil'],
      boolean: ['boolean', 'bool'],
      number: ['number', 'num', 'int', 'float', 'i64', 'f64', 'i32', 'f32'],
      string: ['string', 'str'],
      object: ['object', 'array'],
      function: ['function', 'fn', 'closure', 'native'],
    };

    const aliases = typeMap[jsType] ?? [];
    if (!aliases.includes(type)) {
      throw new AssertionError(
        message ?? `Expected type "${type}", but got "${jsType}"`,
        type,
        jsType,
      );
    }
  },

  fail(message?: string): never {
    throw new AssertionError(message ?? 'Test failed');
  },

  isDefined(value: unknown, message?: string): void {
    if (value === undefined || value === null) {
      throw new AssertionError(
        message ?? 'Expected value to be defined, but got nil',
        'defined',
        value,
      );
    }
  },

  isNull(value: unknown, message?: string): void {
    if (value !== null && value !== undefined) {
      throw new AssertionError(
        message ?? `Expected null, but got ${escapeString(value)}`,
        null,
        value,
      );
    }
  },

  match(value: string, regex: RegExp, message?: string): void {
    if (!regex.test(value)) {
      throw new AssertionError(
        message ?? `Expected "${value}" to match ${regex}`,
        regex,
        value,
      );
    }
  },

  deepEqual<T>(actual: T, expected: T, message?: string): void {
    if (!isDeepEqual(actual, expected)) {
      const actualStr = stringify(actual);
      const expectedStr = stringify(expected);
      throw new AssertionError(
        message ?? `Expected deep equality:\n  Expected: ${expectedStr}\n  Actual:   ${actualStr}`,
        expected,
        actual,
      );
    }
  },

  notDeepEqual<T>(actual: T, expected: T, message?: string): void {
    if (isDeepEqual(actual, expected)) {
      throw new AssertionError(
        message ?? `Expected values not to be deeply equal:\n  ${stringify(actual)}`,
        expected,
        actual,
      );
    }
  },
};
