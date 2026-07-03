import { describe, it, expect } from 'vitest';
import { assert, AssertionError } from '../../src/testing/assert';

describe('AssertionError', () => {
  it('creates error with message', () => {
    const err = new AssertionError('test message');
    expect(err.message).toBe('test message');
    expect(err.name).toBe('AssertionError');
  });

  it('stores expected and actual values', () => {
    const err = new AssertionError('mismatch', 42, 'hello');
    expect(err.expected).toBe(42);
    expect(err.actual).toBe('hello');
  });

  it('is instance of Error', () => {
    const err = new AssertionError('test');
    expect(err).toBeInstanceOf(Error);
  });
});

describe('assert.equal', () => {
  it('passes for equal values', () => {
    expect(() => assert.equal(42, 42)).not.toThrow();
    expect(() => assert.equal('hello', 'hello')).not.toThrow();
    expect(() => assert.equal(true, true)).not.toThrow();
    expect(() => assert.equal(null, null)).not.toThrow();
  });

  it('fails for unequal values', () => {
    expect(() => assert.equal(42, 43)).toThrow(AssertionError);
    expect(() => assert.equal('hello', 'world')).toThrow(AssertionError);
    expect(() => assert.equal(true, false)).toThrow(AssertionError);
  });

  it('passes for NaN equality', () => {
    expect(() => assert.equal(NaN, NaN)).not.toThrow();
  });

  it('uses custom message', () => {
    try {
      assert.equal(1, 2, 'Custom message here');
    } catch (e) {
      expect(e).toBeInstanceOf(AssertionError);
      expect((e as AssertionError).message).toContain('Custom message here');
    }
  });
});

describe('assert.notEqual', () => {
  it('passes for unequal values', () => {
    expect(() => assert.notEqual(1, 2)).not.toThrow();
    expect(() => assert.notEqual('a', 'b')).not.toThrow();
  });

  it('fails for equal values', () => {
    expect(() => assert.notEqual(42, 42)).toThrow(AssertionError);
    expect(() => assert.notEqual('x', 'x')).toThrow(AssertionError);
  });
});

describe('assert.true', () => {
  it('passes for true', () => {
    expect(() => assert.true(true)).not.toThrow();
  });

  it('fails for false', () => {
    expect(() => assert.true(false)).toThrow(AssertionError);
  });

  it('fails for non-boolean truthy values', () => {
    expect(() => assert.true(1 as unknown as boolean)).toThrow(AssertionError);
  });
});

describe('assert.false', () => {
  it('passes for false', () => {
    expect(() => assert.false(false)).not.toThrow();
  });

  it('fails for true', () => {
    expect(() => assert.false(true)).toThrow(AssertionError);
  });
});

describe('assert.throws', () => {
  it('passes when function throws', () => {
    expect(() => assert.throws(() => { throw new Error('boom'); })).not.toThrow();
  });

  it('fails when function does not throw', () => {
    expect(() => assert.throws(() => 42)).toThrow(AssertionError);
  });
});

describe('assert.doesNotThrow', () => {
  it('passes when function does not throw', () => {
    expect(() => assert.doesNotThrow(() => 42)).not.toThrow();
  });

  it('fails when function throws', () => {
    expect(() => assert.doesNotThrow(() => { throw new Error('boom'); })).toThrow(AssertionError);
  });
});

describe('assert.near', () => {
  it('passes for values within epsilon', () => {
    expect(() => assert.near(0.1 + 0.2, 0.3)).not.toThrow();
    expect(() => assert.near(1.0, 1.0001, 0.001)).not.toThrow();
  });

  it('fails for values outside epsilon', () => {
    expect(() => assert.near(1.0, 2.0)).toThrow(AssertionError);
  });

  it('uses custom epsilon', () => {
    expect(() => assert.near(100, 105, 10)).not.toThrow();
    expect(() => assert.near(100, 105, 1)).toThrow(AssertionError);
  });
});

describe('assert.greaterThan', () => {
  it('passes when actual > threshold', () => {
    expect(() => assert.greaterThan(10, 5)).not.toThrow();
  });

  it('fails when actual <= threshold', () => {
    expect(() => assert.greaterThan(5, 10)).toThrow(AssertionError);
    expect(() => assert.greaterThan(10, 10)).toThrow(AssertionError);
  });
});

describe('assert.lessThan', () => {
  it('passes when actual < threshold', () => {
    expect(() => assert.lessThan(5, 10)).not.toThrow();
  });

  it('fails when actual >= threshold', () => {
    expect(() => assert.lessThan(10, 5)).toThrow(AssertionError);
    expect(() => assert.lessThan(10, 10)).toThrow(AssertionError);
  });
});

describe('assert.contains', () => {
  it('passes when string contains substring', () => {
    expect(() => assert.contains('hello world', 'world')).not.toThrow();
  });

  it('fails when string does not contain substring', () => {
    expect(() => assert.contains('hello world', 'xyz')).toThrow(AssertionError);
  });

  it('passes when array contains element', () => {
    expect(() => assert.contains([1, 2, 3], 2)).not.toThrow();
  });

  it('fails when array does not contain element', () => {
    expect(() => assert.contains([1, 2, 3], 4)).toThrow(AssertionError);
  });
});

describe('assert.type', () => {
  it('passes for matching primitive types', () => {
    expect(() => assert.type(42, 'number')).not.toThrow();
    expect(() => assert.type('hello', 'string')).not.toThrow();
    expect(() => assert.type(true, 'boolean')).not.toThrow();
    expect(() => assert.type(null, 'null')).not.toThrow();
  });

  it('fails for mismatched types', () => {
    expect(() => assert.type(42, 'string')).toThrow(AssertionError);
  });

  it('accepts type aliases', () => {
    expect(() => assert.type(42, 'num')).not.toThrow();
    expect(() => assert.type(42, 'int')).not.toThrow();
    expect(() => assert.type('hi', 'str')).not.toThrow();
  });
});

describe('assert.fail', () => {
  it('always throws', () => {
    expect(() => assert.fail()).toThrow(AssertionError);
  });

  it('throws with custom message', () => {
    try {
      assert.fail('Custom failure');
    } catch (e) {
      expect((e as AssertionError).message).toContain('Custom failure');
    }
  });
});

describe('assert.isDefined', () => {
  it('passes for defined values', () => {
    expect(() => assert.isDefined(0)).not.toThrow();
    expect(() => assert.isDefined('')).not.toThrow();
    expect(() => assert.isDefined(false)).not.toThrow();
  });

  it('fails for null and undefined', () => {
    expect(() => assert.isDefined(null)).toThrow(AssertionError);
    expect(() => assert.isDefined(undefined)).toThrow(AssertionError);
  });
});

describe('assert.isNull', () => {
  it('passes for null values', () => {
    expect(() => assert.isNull(null)).not.toThrow();
  });

  it('fails for non-null values', () => {
    expect(() => assert.isNull(42)).toThrow(AssertionError);
    expect(() => assert.isNull('hello')).toThrow(AssertionError);
  });
});

describe('assert.match', () => {
  it('passes when regex matches', () => {
    expect(() => assert.match('hello123', /hello/)).not.toThrow();
    expect(() => assert.match('HELLO', /hello/i)).not.toThrow();
  });

  it('fails when regex does not match', () => {
    expect(() => assert.match('hello', /world/)).toThrow(AssertionError);
  });
});

describe('assert.deepEqual', () => {
  it('passes for deeply equal objects', () => {
    expect(() => assert.deepEqual({ a: 1, b: 2 }, { a: 1, b: 2 })).not.toThrow();
    expect(() => assert.deepEqual([1, 2, 3], [1, 2, 3])).not.toThrow();
  });

  it('fails for deeply unequal objects', () => {
    expect(() => assert.deepEqual({ a: 1 }, { a: 2 })).toThrow(AssertionError);
    expect(() => assert.deepEqual([1, 2], [1, 3])).toThrow(AssertionError);
  });

  it('handles nested objects', () => {
    const a = { x: { y: { z: 42 } } };
    const b = { x: { y: { z: 42 } } };
    expect(() => assert.deepEqual(a, b)).not.toThrow();
  });

  it('handles circular references', () => {
    const a: Record<string, unknown> = { name: 'circle' };
    a.self = a;
    const b: Record<string, unknown> = { name: 'circle' };
    b.self = b;
    expect(() => assert.deepEqual(a, b)).not.toThrow();
  });

  it('compares NaN as equal', () => {
    expect(() => assert.deepEqual(NaN, NaN)).not.toThrow();
  });

  it('passes for equal primitives', () => {
    expect(() => assert.deepEqual(42, 42)).not.toThrow();
    expect(() => assert.deepEqual('hello', 'hello')).not.toThrow();
    expect(() => assert.deepEqual(true, true)).not.toThrow();
    expect(() => assert.deepEqual(null, null)).not.toThrow();
  });

  it('fails for arrays of different lengths', () => {
    expect(() => assert.deepEqual([1, 2], [1, 2, 3])).toThrow(AssertionError);
  });

  it('fails for objects with different keys', () => {
    expect(() => assert.deepEqual({ a: 1 }, { b: 1 })).toThrow(AssertionError);
  });
});

describe('assert.notDeepEqual', () => {
  it('passes for deeply unequal values', () => {
    expect(() => assert.notDeepEqual({ a: 1 }, { a: 2 })).not.toThrow();
  });

  it('fails for deeply equal values', () => {
    expect(() => assert.notDeepEqual({ a: 1 }, { a: 1 })).toThrow(AssertionError);
  });
});

describe('edge cases', () => {
  it('handles undefined values', () => {
    expect(() => assert.equal(undefined, undefined)).not.toThrow();
    expect(() => assert.equal(undefined, null)).toThrow(AssertionError);
  });

  it('handles empty string', () => {
    expect(() => assert.equal('', '')).not.toThrow();
    expect(() => assert.equal('', 'a')).toThrow(AssertionError);
  });

  it('handles zero and negative zero', () => {
    expect(() => assert.equal(0, 0)).not.toThrow();
    expect(() => assert.equal(-0, -0)).not.toThrow();
  });

  it('handles boolean edge cases', () => {
    expect(() => assert.true(true)).not.toThrow();
    expect(() => assert.false(false)).not.toThrow();
  });
});
