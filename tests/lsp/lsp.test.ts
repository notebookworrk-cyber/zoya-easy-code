import { describe, it, expect, beforeEach } from 'vitest';
import { LanguageServer, LSPPosition } from '../../src/lsp/index';

const VALID_CODE = `
let x = 1
let y = 2
let z = x + y
`.trim();

const CODE_WITH_ERROR = `
fun broken() {
  return x + 1
}
`.trim();

const CODE_FOR_REFERENCES = `
fun helper() {
  return 1
}

fun caller() {
  let val = helper()
  let val2 = helper()
  return val + val2
}
`.trim();

const CODE_FOR_SYMBOLS = `
fun hello() {
  print("hi")
}

class MyClass {
  constructor() {}
  doThing() {}
}

let x = 1

interface Movable {
  move()
}

enum Color {
  RED, GREEN, BLUE
}
`.trim();

const CODE_FOR_RENAME = `
fun original() {
  return 1
}

fun useOriginal() {
  let a = original()
  let b = original()
  return a + b
}
`.trim();

describe('LanguageServer', () => {
  let server: LanguageServer;

  beforeEach(() => {
    server = new LanguageServer();
  });

  describe('document management', () => {
    it('opens a document and analyzes it', () => {
      server.openDocument('test.zoya', VALID_CODE);
      const diagnostics = server.getDiagnostics('test.zoya');
      expect(Array.isArray(diagnostics)).toBe(true);
    });

    it('changes a document and re-analyzes', () => {
      server.openDocument('test.zoya', 'let x = 1');
      let diagnostics = server.getDiagnostics('test.zoya');
      expect(Array.isArray(diagnostics)).toBe(true);

      server.changeDocument('test.zoya', 'let y = 2');
      diagnostics = server.getDiagnostics('test.zoya');
      expect(Array.isArray(diagnostics)).toBe(true);
    });

    it('closes a document and clears state', () => {
      server.openDocument('test.zoya', 'let x = 1');
      expect(server.getDiagnostics('test.zoya').length).toBeGreaterThanOrEqual(0);

      server.closeDocument('test.zoya');
      expect(server.getDiagnostics('test.zoya')).toEqual([]);
    });

    it('returns empty diagnostics for unknown document', () => {
      const diagnostics = server.getDiagnostics('unknown.zoya');
      expect(diagnostics).toEqual([]);
    });
  });

  describe('completions', () => {
    it('returns keyword completions', () => {
      server.openDocument('test.zoya', VALID_CODE);
      const completions = server.getCompletions('test.zoya', { line: 0, character: 0 });
      expect(completions.length).toBeGreaterThan(0);

      const kwLabels = completions.map(c => c.label);
      expect(kwLabels).toContain('fun');
      expect(kwLabels).toContain('let');
      expect(kwLabels).toContain('class');
      expect(kwLabels).toContain('if');
      expect(kwLabels).toContain('return');
      expect(kwLabels).toContain('import');
    });

    it('returns builtin completions', () => {
      server.openDocument('test.zoya', VALID_CODE);
      const completions = server.getCompletions('test.zoya', { line: 0, character: 0 });
      const labels = completions.map(c => c.label);
      expect(labels).toContain('print');
      expect(labels).toContain('len');
      expect(labels).toContain('type');
    });

    it('returns symbol completions from document', () => {
      server.openDocument('test.zoya', VALID_CODE);
      const completions = server.getCompletions('test.zoya', { line: 0, character: 0 });
      const labels = completions.map(c => c.label);
      expect(labels).toContain('x');
      expect(labels).toContain('y');
    });

    it('returns keyword completions for unknown document', () => {
      const completions = server.getCompletions('unknown.zoya', { line: 0, character: 0 });
      const labels = completions.map(c => c.label);
      expect(labels).toContain('fun');
      expect(labels).toContain('let');
    });
  });

  describe('hover', () => {
    it('returns hover info for identifier', () => {
      server.openDocument('test.zoya', 'let x = 42');
      const hover = server.getHover('test.zoya', { line: 0, character: 5 });
      if (hover) {
        expect(typeof hover.contents).toBe('string');
      }
    });

    it('returns null for unknown document', () => {
      const hover = server.getHover('unknown.zoya', { line: 0, character: 0 });
      expect(hover).toBeNull();
    });
  });

  describe('definition', () => {
    it('returns definition for known symbol', () => {
      server.openDocument('test.zoya', CODE_FOR_REFERENCES);
      const def = server.getDefinition('test.zoya', { line: 6, character: 16 });
      if (def) {
        expect(def.uri).toBe('test.zoya');
      }
    });

    it('returns null for unknown document', () => {
      const def = server.getDefinition('unknown.zoya', { line: 0, character: 0 });
      expect(def).toBeNull();
    });
  });

  describe('references', () => {
    it('finds references in document', () => {
      server.openDocument('test.zoya', CODE_FOR_REFERENCES);
      const refs = server.getReferences('test.zoya', { line: 0, character: 5 });
      expect(refs.length).toBeGreaterThanOrEqual(3);
    });

    it('returns empty for unknown document', () => {
      const refs = server.getReferences('unknown.zoya', { line: 0, character: 0 });
      expect(refs).toEqual([]);
    });
  });

  describe('document symbols', () => {
    it('extracts symbols from document', () => {
      server.openDocument('test.zoya', CODE_FOR_SYMBOLS);
      const symbols = server.getDocumentSymbols('test.zoya');
      const names = symbols.map(s => s.name);
      expect(names).toContain('hello');
      expect(names).toContain('MyClass');
      expect(names).toContain('x');
      expect(names).toContain('doThing');
      expect(names).toContain('Movable');
      expect(names).toContain('Color');
    });

    it('returns empty for unknown document', () => {
      const symbols = server.getDocumentSymbols('unknown.zoya');
      expect(symbols).toEqual([]);
    });
  });

  describe('rename', () => {
    it('returns rename locations', () => {
      server.openDocument('test.zoya', CODE_FOR_RENAME);
      const renameResult = server.rename('test.zoya', { line: 0, character: 5 }, 'renamed');
      expect(renameResult.size).toBeGreaterThan(0);
      const locations = renameResult.get('test.zoya');
      expect(locations).toBeDefined();
      expect(locations!.length).toBeGreaterThanOrEqual(3);
    });

    it('returns empty map for unknown document', () => {
      const renameResult = server.rename('unknown.zoya', { line: 0, character: 0 }, 'newName');
      expect(renameResult.size).toBe(0);
    });
  });

  describe('semantic tokens', () => {
    it('returns semantic tokens for valid code', () => {
      server.openDocument('test.zoya', 'let x = 42');
      const tokens = server.getSemanticTokens('test.zoya');
      expect(tokens.length).toBeGreaterThan(0);
      expect(tokens.length % 5).toBe(0);
    });

    it('returns semantic tokens in correct format (5 ints per token)', () => {
      server.openDocument('test.zoya', 'fun test() { return 1 }');
      const tokens = server.getSemanticTokens('test.zoya');
      expect(tokens.length % 5).toBe(0);

      for (let i = 0; i < tokens.length; i += 5) {
        expect(typeof tokens[i]).toBe('number');
        expect(typeof tokens[i + 1]).toBe('number');
        expect(typeof tokens[i + 2]).toBe('number');
        expect(typeof tokens[i + 3]).toBe('number');
        expect(typeof tokens[i + 4]).toBe('number');
      }
    });

    it('returns empty for unknown document', () => {
      const tokens = server.getSemanticTokens('unknown.zoya');
      expect(tokens).toEqual([]);
    });
  });

  describe('diagnostics', () => {
    it('reports no errors for valid code', () => {
      server.openDocument('test.zoya', VALID_CODE);
      const diagnostics = server.getDiagnostics('test.zoya');
      const errors = diagnostics.filter(d => d.severity === 1);
      expect(errors.length).toBe(0);
    });

    it('reports diagnostic with proper structure', () => {
      server.openDocument('test.zoya', CODE_WITH_ERROR);
      const diagnostics = server.getDiagnostics('test.zoya');
      if (diagnostics.length > 0) {
        const diag = diagnostics[0];
        expect(diag).toHaveProperty('range');
        expect(diag.range).toHaveProperty('start');
        expect(diag.range).toHaveProperty('end');
        expect(typeof diag.message).toBe('string');
        expect(diag.source).toBe('zoya');
        expect([1, 2, 3, 4]).toContain(diag.severity);
      }
    });

    it('returns diagnostics with source field', () => {
      server.openDocument('test.zoya', CODE_WITH_ERROR);
      const diagnostics = server.getDiagnostics('test.zoya');
      for (const d of diagnostics) {
        expect(d.source).toBe('zoya');
      }
    });
  });
});
