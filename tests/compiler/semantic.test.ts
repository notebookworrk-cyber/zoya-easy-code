import { describe, it, expect } from 'vitest';
import { Lexer } from '../../src/compiler/lexer/index';
import { Parser } from '../../src/compiler/parser/index';
import { SemanticAnalyzer } from '../../src/compiler/semantic/index';
import { DiagnosticBag } from '../../src/diagnostics';

function analyze(source: string) {
  const lexer = new Lexer(source, 'test.zoya');
  const tokens = lexer.scanTokens();
  const parseDiag = new DiagnosticBag();
  const parser = new Parser(tokens, parseDiag);
  const program = parser.parse();

  const diag = new DiagnosticBag();
  const analyzer = new SemanticAnalyzer(diag);
  const result = analyzer.analyze(program);

  return { result, diagnostics: diag, parseDiagnostics: parseDiag, program };
}

describe('SemanticAnalyzer', () => {
  describe('symbol resolution', () => {
    it('resolves variables in same scope', () => {
      const { result, diagnostics } = analyze('let x = 42; let y = x;');
      expect(diagnostics.hasErrors()).toBe(false);
      const sym = result.globals.get('x');
      expect(sym).toBeDefined();
      expect(sym!.kind).toBe('variable');
      expect(result.globals.get('y')).toBeDefined();
    });

    it('resolves variables in nested scopes', () => {
      const { diagnostics } = analyze(`
        let x = 1;
        if (true) {
          let y = x;
        }
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('resolves variables from outer scope in inner blocks', () => {
      const { diagnostics } = analyze(`
        let x = 1;
        {
          {
            let z = x + 1;
          }
        }
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows inner scope to shadow outer', () => {
      const { diagnostics } = analyze(`
        let x = 1;
        {
          let x = 2;
        }
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('resolves function declarations', () => {
      const { result, diagnostics } = analyze(`
        fun foo() { }
        foo();
      `);
      expect(diagnostics.hasErrors()).toBe(false);
      const sym = result.globals.get('foo');
      expect(sym).toBeDefined();
      expect(sym!.kind).toBe('function');
    });
  });

  describe('undefined variable detection', () => {
    it('reports undefined variable', () => {
      const { diagnostics } = analyze('let x = undefinedVar;');
      expect(diagnostics.hasErrors()).toBe(true);
      expect(diagnostics.all().some(d => d.message.includes('undefinedVar'))).toBe(true);
    });

    it('reports undefined variable in nested scope', () => {
      const { diagnostics } = analyze(`
        if (true) {
          let y = unknownVar;
        }
      `);
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('reports undefined function call', () => {
      const { diagnostics } = analyze('undefinedFunc();');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('reports undefined class reference', () => {
      const { diagnostics } = analyze('let x = new NonExistentClass();');
      expect(diagnostics.hasErrors()).toBe(true);
    });
  });

  describe('duplicate declaration detection', () => {
    it('reports duplicate variable in same scope', () => {
      const { diagnostics } = analyze('let x = 1; let x = 2;');
      expect(diagnostics.hasErrors()).toBe(true);
      expect(diagnostics.all().some(d => d.message.includes('Duplicate'))).toBe(true);
    });

    it('allows duplicate variable in different scopes', () => {
      const { diagnostics } = analyze('let x = 1; { let x = 2; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('reports duplicate function declaration', () => {
      const { diagnostics } = analyze('fun foo() { } fun foo() { }');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('reports duplicate parameter name', () => {
      const { diagnostics } = analyze('fun foo(a, a) { }');
      expect(diagnostics.hasErrors()).toBe(true);
    });
  });

  describe('type checking', () => {
    it('determines literal types', () => {
      const { diagnostics } = analyze('let a = 42; let b = "hi"; let c = true; let d = nil;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows number arithmetic', () => {
      const { diagnostics } = analyze('let x = 1 + 2 * 3;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows string concatenation', () => {
      const { diagnostics } = analyze('let x = "hello" + " world";');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('reports type mismatch in binary operations', () => {
      const { diagnostics } = analyze('let x = "hello" * 5;');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('allows comparison operators', () => {
      const { diagnostics } = analyze('let a = 1; let b = 2; let x = a < b; let y = 3 >= 4; let z = a == b;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows logical operators', () => {
      const { diagnostics } = analyze('let x = true && false || true;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows bitwise operators on numbers', () => {
      const { diagnostics } = analyze('let x = 1 | 2 & 3;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows unary negation on numbers', () => {
      const { diagnostics } = analyze('let x = -42; let y = +7;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows logical not', () => {
      const { diagnostics } = analyze('let x = !true;');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('function validation', () => {
    it('checks function argument count', () => {
      const { diagnostics } = analyze('fun foo(a, b) { } foo(1);');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('accepts correct argument count', () => {
      const { diagnostics } = analyze('fun foo(a, b) { } foo(1, 2);');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('accepts function with no params called with no args', () => {
      const { diagnostics } = analyze('fun foo() { } foo();');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('reports return outside function', () => {
      const { diagnostics } = analyze('return 42;');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('allows return inside function', () => {
      const { diagnostics } = analyze('fun f() { return 42; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('loop validation', () => {
    it('allows break inside loop', () => {
      const { diagnostics } = analyze('loop { break; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows continue inside loop', () => {
      const { diagnostics } = analyze('loop { continue; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('reports break outside loop', () => {
      const { diagnostics } = analyze('break;');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('reports continue outside loop', () => {
      const { diagnostics } = analyze('continue;');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('allows break inside for loop', () => {
      const { diagnostics } = analyze('for (let i = 0; i < 10; i = i + 1) { break; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('allows break inside while loop', () => {
      const { diagnostics } = analyze('while (true) { break; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('class validation', () => {
    it('validates class declaration', () => {
      const { result, diagnostics } = analyze('class Foo { }');
      expect(diagnostics.hasErrors()).toBe(false);
      const sym = result.globals.get('Foo');
      expect(sym).toBeDefined();
      expect(sym!.kind).toBe('class');
    });

    it('reports undefined superclass', () => {
      const { diagnostics } = analyze('class Foo inherits Bar { }');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('validates correct superclass', () => {
      const { diagnostics } = analyze('class Bar { } class Foo inherits Bar { }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('validates class with methods and properties', () => {
      const { diagnostics } = analyze(`
        class Counter {
          value = 0;
          inc() { this.value = this.value + 1; }
        }
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('import and export', () => {
    it('records imports in scope', () => {
      const { result, diagnostics } = analyze('import foo from "module";');
      expect(diagnostics.hasErrors()).toBe(false);
      const sym = result.globals.get('foo');
      expect(sym).toBeDefined();
      expect(sym!.imported).toBe(true);
      expect(sym!.module).toBe('module');
    });

    it('records exports', () => {
      const { result, diagnostics } = analyze('export let x = 5;');
      expect(diagnostics.hasErrors()).toBe(false);
      const sym = result.globals.get('x');
      expect(sym?.exported).toBe(true);
    });

    it('handles named exports', () => {
      const { diagnostics } = analyze('let x = 1; let y = 2; export { x, y };');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('resolves imported name', () => {
      const { diagnostics } = analyze('import foo from "mod"; let x = foo;');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('lambda validation', () => {
    it('validates lambda', () => {
      const { diagnostics } = analyze('let f = |x, y| -> x + y;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('validates lambda with block body', () => {
      const { diagnostics } = analyze('let f = |x| { return x + 1; };');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('validates lambda with parameter type annotations', () => {
      const { diagnostics } = analyze('let f = |x: number| -> x + 1;');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('interface, type alias, enum', () => {
    it('validates interface declaration', () => {
      const { result, diagnostics } = analyze('interface Foo { bar(): void; }');
      expect(diagnostics.hasErrors()).toBe(false);
      expect(result.globals.get('Foo')?.kind).toBe('interface');
    });

    it('validates type alias', () => {
      const { result, diagnostics } = analyze('type MyType = string;');
      expect(diagnostics.hasErrors()).toBe(false);
      expect(result.globals.get('MyType')?.kind).toBe('type');
    });

    it('validates enum declaration', () => {
      const { result, diagnostics } = analyze('enum Color { Red, Green, Blue }');
      expect(diagnostics.hasErrors()).toBe(false);
      expect(result.globals.get('Color')?.kind).toBe('enum');
    });
  });

  describe('try/catch scoping', () => {
    it('catches variable in catch scope', () => {
      const { diagnostics } = analyze('try { } catch (e) { let x = e; }');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('catch variable not accessible outside', () => {
      const { diagnostics } = analyze('try { } catch (e) { } let x = e;');
      expect(diagnostics.hasErrors()).toBe(true);
    });
  });

  describe('for loop scoping', () => {
    it('for loop creates child scope', () => {
      const { diagnostics } = analyze('for (let i = 0; i < 10; i = i + 1) { }');
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('complex program validation', () => {
    it('validates complex program without errors', () => {
      const { diagnostics } = analyze(`
        import { assertEquals } from "std/testing";

        const MAX = 100;

        fun fibonacci(n: number) -> number {
          if (n <= 1) { return n; }
          return fibonacci(n - 1) + fibonacci(n - 2);
        }

        class Counter {
          value = 0;
          inc() {
            this.value = this.value + 1;
          }
          get() -> number {
            return this.value;
          }
        }

        let c = new Counter();
        c.inc();
        c.inc();
        let result = c.get();
        let fib10 = fibonacci(10);
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('detects errors in complex program', () => {
      const { diagnostics } = analyze(`
        let x = undefinedVar;
        fun foo(a, a) { }
        break;
      `);
      expect(diagnostics.hasErrors()).toBe(true);
      const msgs = diagnostics.all().map(d => d.message);
      expect(msgs.some(m => m.includes('undefinedVar'))).toBe(true);
      expect(msgs.some(m => m.includes('Duplicate'))).toBe(true);
      expect(msgs.some(m => m.includes('break') || m.includes('outside'))).toBe(true);
    });
  });

  describe('additional coverage', () => {
    it('handles object literal', () => {
      const { diagnostics } = analyze('let obj = { x: 1, y: "hello" };');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('handles array literal', () => {
      const { diagnostics } = analyze('let arr = [1, 2, 3];');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('handles lambda with default parameter', () => {
      const { diagnostics } = analyze('let f = |x = 42| -> x;');
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('handles await in function', () => {
      const { diagnostics } = analyze(`
        fun gen() {
          let x = await 42;
        }
      `);
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });
});
