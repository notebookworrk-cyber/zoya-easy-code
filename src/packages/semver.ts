const SEMVER_REGEX = /^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$/;
const RANGE_SPLIT = /\s*\|\|\s*/;
const CONDITION_SPLIT = /\s+/;
const HYPHEN_RANGE = /^(\S+)\s*-\s*(\S+)$/;
const CARET = /^\^/;
const TILDE = /^~/;
const GTE = /^>=/;
const LTE = /^<=/;
const GT = /^>/;
const LT = /^</;
const EQ = /^==/;
const WILDCARD = /^[xX*]$/;

export interface SemVer {
  major: number;
  minor: number;
  patch: number;
  prerelease?: string;
  build?: string;
}

export function parseSemver(version: string): SemVer {
  const trimmed = version.trim();
  if (!trimmed) {
    throw new Error(`Invalid version: '${version}'`);
  }
  const m = SEMVER_REGEX.exec(trimmed);
  if (!m) {
    throw new Error(`Invalid version: '${version}'`);
  }
  return {
    major: parseInt(m[1], 10),
    minor: m[2] !== undefined ? parseInt(m[2], 10) : 0,
    patch: m[3] !== undefined ? parseInt(m[3], 10) : 0,
    prerelease: m[4] ?? undefined,
    build: m[5] ?? undefined,
  };
}

export function compareSemver(a: SemVer, b: SemVer): -1 | 0 | 1 {
  for (const key of ['major', 'minor', 'patch'] as const) {
    if (a[key] < b[key]) return -1;
    if (a[key] > b[key]) return 1;
  }
  const aPre = a.prerelease ?? '';
  const bPre = b.prerelease ?? '';
  if (aPre && !bPre) return -1;
  if (!aPre && bPre) return 1;
  if (aPre && bPre) {
    const aParts = aPre.split('.');
    const bParts = bPre.split('.');
    const len = Math.max(aParts.length, bParts.length);
    for (let i = 0; i < len; i++) {
      if (i >= aParts.length) return -1;
      if (i >= bParts.length) return 1;
      const aVal = aParts[i];
      const bVal = bParts[i];
      const aNum = parseInt(aVal, 10);
      const bNum = parseInt(bVal, 10);
      if (!isNaN(aNum) && !isNaN(bNum)) {
        if (aNum < bNum) return -1;
        if (aNum > bNum) return 1;
      } else {
        if (aVal < bVal) return -1;
        if (aVal > bVal) return 1;
      }
    }
  }
  return 0;
}

export function satisfies(version: string, range: string): boolean {
  let ver: SemVer;
  try {
    ver = parseSemver(version);
  } catch {
    return false;
  }
  const orClauses = range.trim().split(RANGE_SPLIT);
  return orClauses.some(clause => {
    if (!clause) return false;
    const hyphMatch = HYPHEN_RANGE.exec(clause.trim());
    if (hyphMatch) {
      const low = parseSemver(hyphMatch[1]);
      const high = parseSemver(hyphMatch[2]);
      return compareSemver(ver, low) >= 0 && compareSemver(ver, high) <= 0;
    }
    const conditions = clause.trim().split(CONDITION_SPLIT);
    return conditions.every(cond => satisfiesCondition(ver, cond));
  });
}

function satisfiesCondition(ver: SemVer, condition: string): boolean {
  const trimmed = condition.trim();
  if (!trimmed) return true;
  if (trimmed === '*' || WILDCARD.test(trimmed)) return true;
  const gteMatch = GTE.exec(trimmed);
  if (gteMatch) return compareSemver(ver, parseSemver(trimmed.substring(2))) >= 0;
  const gtMatch = GT.exec(trimmed);
  if (gtMatch) return compareSemver(ver, parseSemver(trimmed.substring(1))) > 0;
  const lteMatch = LTE.exec(trimmed);
  if (lteMatch) return compareSemver(ver, parseSemver(trimmed.substring(2))) <= 0;
  const ltMatch = LT.exec(trimmed);
  if (ltMatch) return compareSemver(ver, parseSemver(trimmed.substring(1))) < 0;
  const eqMatch = EQ.exec(trimmed);
  if (eqMatch) return compareSemver(ver, parseSemver(trimmed.substring(2))) === 0;
  const caretMatch = CARET.exec(trimmed);
  if (caretMatch) return satisfiesCaret(ver, trimmed.substring(1));
  const tildeMatch = TILDE.exec(trimmed);
  if (tildeMatch) return satisfiesTilde(ver, trimmed.substring(1));
  return satisfiesExactOrWildcard(ver, trimmed);
}

function satisfiesCaret(ver: SemVer, raw: string): boolean {
  const parts = raw.split('.');
  const major = parseInt(parts[0], 10);
  const minor = parts.length > 1 ? parseInt(parts[1], 10) : 0;
  const patch = parts.length > 2 ? parseInt(parts[2], 10) : 0;
  if (major === 0 && parts.length > 1) {
    if (minor === 0 && parts.length > 2) {
      return ver.major === 0 && ver.minor === 0 && ver.patch === patch;
    }
    return ver.major === 0 && ver.minor === minor && ver.patch >= patch;
  }
  if (ver.major !== major) return false;
  if (parts.length === 1) return true;
  if (ver.minor > minor) return true;
  if (ver.minor < minor) return false;
  if (parts.length === 2) return true;
  return ver.patch >= patch;
}

function satisfiesTilde(ver: SemVer, raw: string): boolean {
  const parts = raw.split('.');
  const major = parseInt(parts[0], 10);
  const minor = parts.length > 1 ? parseInt(parts[1], 10) : 0;
  const patch = parts.length > 2 ? parseInt(parts[2], 10) : 0;
  if (parts.length === 1) {
    return ver.major === major;
  }
  if (parts.length === 2) {
    return ver.major === major && ver.minor === minor;
  }
  return ver.major === major && ver.minor === minor && ver.patch >= patch;
}

function satisfiesExactOrWildcard(ver: SemVer, raw: string): boolean {
  const parts = raw.split('.');
  const wildcardIdx = parts.findIndex(p => WILDCARD.test(p));
  if (wildcardIdx === 0) return true;
  if (wildcardIdx === 1) return ver.major === parseInt(parts[0], 10);
  if (wildcardIdx === 2) {
    return ver.major === parseInt(parts[0], 10) && ver.minor === parseInt(parts[1], 10);
  }
  const target = parseSemver(raw);
  return compareSemver(ver, target) === 0;
}

export function maxSatisfying(versions: string[], range: string): string | null {
  let best: string | null = null;
  let bestVer: SemVer | null = null;
  for (const v of versions) {
    let parsed: SemVer;
    try {
      parsed = parseSemver(v);
    } catch {
      continue;
    }
    if (!satisfies(v, range)) continue;
    if (bestVer === null || compareSemver(parsed, bestVer) > 0) {
      best = v;
      bestVer = parsed;
    }
  }
  return best;
}

export function coerce(version: string): SemVer | null {
  const trimmed = version.trim();
  const m = /(\d+)(?:\.(\d+))?(?:\.(\d+))?/.exec(trimmed);
  if (!m) return null;
  try {
    return parseSemver(m[0]);
  } catch {
    return null;
  }
}

export function formatSemver(v: SemVer): string {
  let result = `${v.major}.${v.minor}.${v.patch}`;
  if (v.prerelease) result += `-${v.prerelease}`;
  if (v.build) result += `+${v.build}`;
  return result;
}
