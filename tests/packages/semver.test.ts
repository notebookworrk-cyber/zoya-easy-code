import { describe, it, expect } from 'vitest';
import {
  parseSemver, compareSemver, satisfies, maxSatisfying,
  coerce, formatSemver, SemVer,
} from '../../src/packages/semver';

describe('semver - parseSemver', () => {
  it('parses full version', () => {
    const v = parseSemver('1.2.3');
    expect(v.major).toBe(1);
    expect(v.minor).toBe(2);
    expect(v.patch).toBe(3);
    expect(v.prerelease).toBeUndefined();
    expect(v.build).toBeUndefined();
  });

  it('parses zero version', () => {
    const v = parseSemver('0.0.1');
    expect(v.major).toBe(0);
    expect(v.minor).toBe(0);
    expect(v.patch).toBe(1);
  });

  it('parses version with prerelease', () => {
    const v = parseSemver('1.2.3-alpha');
    expect(v.prerelease).toBe('alpha');
  });

  it('parses version with build', () => {
    const v = parseSemver('1.2.3+build.123');
    expect(v.build).toBe('build.123');
  });

  it('parses version with prerelease and build', () => {
    const v = parseSemver('1.2.3-rc.1+build.456');
    expect(v.prerelease).toBe('rc.1');
    expect(v.build).toBe('build.456');
  });

  it('parses partial version (major.minor)', () => {
    const v = parseSemver('1.2');
    expect(v.major).toBe(1);
    expect(v.minor).toBe(2);
    expect(v.patch).toBe(0);
  });

  it('parses partial version (major only)', () => {
    const v = parseSemver('1');
    expect(v.major).toBe(1);
    expect(v.minor).toBe(0);
    expect(v.patch).toBe(0);
  });

  it('throws on empty string', () => {
    expect(() => parseSemver('')).toThrow('Invalid version');
  });

  it('throws on invalid version', () => {
    expect(() => parseSemver('not-a-version')).toThrow('Invalid version');
  });

  it('throws on garbage string', () => {
    expect(() => parseSemver('abc.def')).toThrow('Invalid version');
  });
});

describe('semver - formatSemver', () => {
  it('formats basic version', () => {
    expect(formatSemver({ major: 1, minor: 2, patch: 3 })).toBe('1.2.3');
  });

  it('formats with prerelease', () => {
    expect(formatSemver({ major: 1, minor: 2, patch: 3, prerelease: 'beta.2' })).toBe('1.2.3-beta.2');
  });

  it('formats with build', () => {
    expect(formatSemver({ major: 1, minor: 2, patch: 3, build: '123' })).toBe('1.2.3+123');
  });
});

describe('semver - compareSemver', () => {
  it('returns 0 for equal versions', () => {
    expect(compareSemver(parseSemver('1.2.3'), parseSemver('1.2.3'))).toBe(0);
  });

  it('returns 1 when a > b (major)', () => {
    expect(compareSemver(parseSemver('2.0.0'), parseSemver('1.9.9'))).toBe(1);
  });

  it('returns -1 when a < b (major)', () => {
    expect(compareSemver(parseSemver('1.9.9'), parseSemver('2.0.0'))).toBe(-1);
  });

  it('returns 1 when a > b (minor)', () => {
    expect(compareSemver(parseSemver('1.3.0'), parseSemver('1.2.9'))).toBe(1);
  });

  it('returns -1 when a < b (patch)', () => {
    expect(compareSemver(parseSemver('1.2.3'), parseSemver('1.2.4'))).toBe(-1);
  });

  it('considers prerelease versions lower', () => {
    expect(compareSemver(parseSemver('1.0.0-alpha'), parseSemver('1.0.0'))).toBe(-1);
  });

  it('considers release higher than prerelease', () => {
    expect(compareSemver(parseSemver('1.0.0'), parseSemver('1.0.0-beta'))).toBe(1);
  });

  it('compares prerelease identifiers numerically when possible', () => {
    expect(compareSemver(parseSemver('1.0.0-2'), parseSemver('1.0.0-10'))).toBe(-1);
  });

  it('compares prerelease identifiers lexically when non-numeric', () => {
    expect(compareSemver(parseSemver('1.0.0-alpha'), parseSemver('1.0.0-beta'))).toBe(-1);
  });
});

describe('semver - satisfies', () => {
  it('exact version match', () => {
    expect(satisfies('1.2.3', '1.2.3')).toBe(true);
    expect(satisfies('1.2.4', '1.2.3')).toBe(false);
  });

  it('caret range (^)', () => {
    expect(satisfies('1.2.3', '^1.2.3')).toBe(true);
    expect(satisfies('1.9.9', '^1.2.3')).toBe(true);
    expect(satisfies('2.0.0', '^1.2.3')).toBe(false);
    expect(satisfies('0.2.3', '^0.2.3')).toBe(true);
    expect(satisfies('0.3.0', '^0.2.3')).toBe(false);
    expect(satisfies('0.0.3', '^0.0.3')).toBe(true);
    expect(satisfies('0.0.4', '^0.0.3')).toBe(false);
  });

  it('tilde range (~)', () => {
    expect(satisfies('1.2.3', '~1.2.3')).toBe(true);
    expect(satisfies('1.2.4', '~1.2.3')).toBe(true);
    expect(satisfies('1.3.0', '~1.2.3')).toBe(false);
    expect(satisfies('2.0.0', '~1.2.3')).toBe(false);
  });

  it('greater-than-or-equal range (>=)', () => {
    expect(satisfies('1.0.0', '>=1.0.0')).toBe(true);
    expect(satisfies('2.5.0', '>=1.0.0')).toBe(true);
    expect(satisfies('0.5.0', '>=1.0.0')).toBe(false);
  });

  it('less-than-or-equal range (<=)', () => {
    expect(satisfies('1.0.0', '<=1.0.0')).toBe(true);
    expect(satisfies('0.5.0', '<=1.0.0')).toBe(true);
    expect(satisfies('2.0.0', '<=1.0.0')).toBe(false);
  });

  it('compound range', () => {
    expect(satisfies('1.5.0', '>=1.0.0 <2.0.0')).toBe(true);
    expect(satisfies('2.5.0', '>=1.0.0 <2.0.0')).toBe(false);
    expect(satisfies('0.5.0', '>=1.0.0 <2.0.0')).toBe(false);
  });

  it('OR operator (||)', () => {
    expect(satisfies('2.5.0', '>=1.0.0 <2.0.0 || >=3.0.0')).toBe(false);
    expect(satisfies('3.0.0', '>=1.0.0 <2.0.0 || >=3.0.0')).toBe(true);
    expect(satisfies('1.5.0', '>=1.0.0 <2.0.0 || >=3.0.0')).toBe(true);
  });

  it('wildcard ranges (*, x, X)', () => {
    expect(satisfies('1.2.3', '*')).toBe(true);
    expect(satisfies('5.6.7', '*')).toBe(true);
    expect(satisfies('1.2.3', '1.x')).toBe(true);
    expect(satisfies('2.0.0', '1.x')).toBe(false);
    expect(satisfies('1.2.4', '1.2.x')).toBe(true);
    expect(satisfies('1.3.0', '1.2.x')).toBe(false);
  });

  it('hyphen range', () => {
    expect(satisfies('1.5.0', '1.2.3 - 1.5.0')).toBe(true);
    expect(satisfies('1.2.3', '1.2.3 - 1.5.0')).toBe(true);
    expect(satisfies('1.6.0', '1.2.3 - 1.5.0')).toBe(false);
  });

  it('handles invalid version gracefully', () => {
    expect(satisfies('not-a-version', '^1.0.0')).toBe(false);
  });

  it('handles major 0 caret edge cases', () => {
    expect(satisfies('0.1.0', '^0.1.0')).toBe(true);
    expect(satisfies('0.1.2', '^0.1.0')).toBe(true);
    expect(satisfies('0.2.0', '^0.1.0')).toBe(false);
  });
});

describe('semver - maxSatisfying', () => {
  it('returns highest satisfying version', () => {
    const versions = ['1.2.3', '1.2.4', '1.3.0', '2.0.0'];
    expect(maxSatisfying(versions, '^1.2.3')).toBe('1.3.0');
  });

  it('returns null for empty list', () => {
    expect(maxSatisfying([], '^1.0.0')).toBeNull();
  });

  it('respects range constraints', () => {
    const versions = ['2.0.0', '2.1.0', '1.9.9'];
    expect(maxSatisfying(versions, '^1.0.0')).toBe('1.9.9');
    expect(maxSatisfying(versions, '^2.0.0')).toBe('2.1.0');
  });

  it('returns null when no version satisfies', () => {
    const versions = ['3.0.0', '4.0.0'];
    expect(maxSatisfying(versions, '^1.0.0')).toBeNull();
  });

  it('ignores invalid versions in list', () => {
    const versions = ['not-valid', '1.0.0', '1.5.0'];
    expect(maxSatisfying(versions, '^1.0.0')).toBe('1.5.0');
  });
});

describe('semver - coerce', () => {
  it('coerces full version string', () => {
    const v = coerce('1.2.3');
    expect(v).not.toBeNull();
    expect(v!.major).toBe(1);
    expect(v!.minor).toBe(2);
    expect(v!.patch).toBe(3);
  });

  it('coerces partial version', () => {
    const v = coerce('v1.2');
    expect(v).not.toBeNull();
    expect(v!.patch).toBe(0);
  });

  it('returns null for non-version strings', () => {
    expect(coerce('not-a-version')).toBeNull();
  });

  it('returns null for empty string', () => {
    expect(coerce('')).toBeNull();
  });

  it('coerces version with prefix', () => {
    const v = coerce('v1.2.3');
    expect(v).not.toBeNull();
    expect(v!.major).toBe(1);
  });

  it('coerces version embedded in text', () => {
    const v = coerce('version 1.2.3-beta');
    expect(v).not.toBeNull();
    expect(v!.major).toBe(1);
    expect(v!.minor).toBe(2);
    expect(v!.patch).toBe(3);
  });
});
