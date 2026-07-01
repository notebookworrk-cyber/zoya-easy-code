import { describe, it, expect } from 'vitest';
import { Lexer } from '../../src/compiler/lexer/index';
import { Parser } from '../../src/compiler/parser/index';
import { DiagnosticBag } from '../../src/diagnostics';

function parse(source: string) {
  const lexer = new Lexer(source, 'test.zoya');
  const tokens = lexer.scanTokens();
  const diagnostics = new DiagnosticBag();
  const parser = new Parser(tokens, diagnostics);
  const program = parser.parse();
  return { program, diagnostics, tokens };
}

describe('Parser', () => {
  describe('empty program', () => {
    it('parses empty source', () => {
      const { program, diagnostics } = parse('');
      expect(program.type).toBe('Program');
      expect(program.body).toHaveLength(0);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('parses only semicolons', () => {
      const { program, diagnostics } = parse(';;;');
      expect(program.body).toHaveLength(0);
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('variable declarations', () => {
    it('parses let declaration without initializer', () => {
      const { program } = parse('let x;');
      const decl = program.body[0];
      expect(decl.type).toBe('VariableDeclaration');
      const vd = decl as import('../../src/compiler/ast/index').VariableDeclaration;
      expect(vd.kind).toBe('let');
      expect(vd.declarations).toHaveLength(1);
      expect(vd.declarations[0].id.name).toBe('x');
      expect(vd.declarations[0].init).toBeUndefined();
    });

    it('parses let declaration with initializer', () => {
      const { program } = parse('let x = 42;');
      const vd = program.body[0] as import('../../src/compiler/ast/index').VariableDeclaration;
      expect(vd.kind).toBe('let');
      expect(vd.declarations[0].id.name).toBe('x');
      expect(vd.declarations[0].init?.type).toBe('Literal');
    });

    it('parses const declaration', () => {
      const { program } = parse('const x = "hello";');
      const vd = program.body[0] as import('../../src/compiler/ast/index').VariableDeclaration;
      expect(vd.kind).toBe('const');
      expect(vd.declarations[0].id.name).toBe('x');
      const lit = vd.declarations[0].init as import('../../src/compiler/ast/index').Literal;
      expect(lit.value).toBe('hello');
    });

    it('parses multiple declarators', () => {
      const { program } = parse('let x, y = 1, z;');
      const vd = program.body[0] as import('../../src/compiler/ast/index').VariableDeclaration;
      expect(vd.declarations).toHaveLength(3);
      expect(vd.declarations[0].id.name).toBe('x');
      expect(vd.declarations[1].id.name).toBe('y');
      expect((vd.declarations[1].init as import('../../src/compiler/ast/index').Literal).value).toBe(1);
      expect(vd.declarations[2].id.name).toBe('z');
    });

    it('parses variable declaration with type annotation', () => {
      const { program } = parse('let x: number = 5;');
      const vd = program.body[0] as import('../../src/compiler/ast/index').VariableDeclaration;
      expect(vd.declarations[0].typeAnnotation?.name).toBe('number');
      expect(vd.declarations[0].id.name).toBe('x');
    });
  });

  describe('function declarations', () => {
    it('parses function with no params', () => {
      const { program } = parse('fun main() { }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      expect(fn.type).toBe('FunctionDeclaration');
      expect(fn.id.name).toBe('main');
      expect(fn.params).toHaveLength(0);
      expect(fn.body.body).toHaveLength(0);
    });

    it('parses function with parameters', () => {
      const { program } = parse('fun add(a, b) { return a + b; }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      expect(fn.id.name).toBe('add');
      expect(fn.params).toHaveLength(2);
      expect(fn.params[0].pattern.type).toBe('Identifier');
      expect((fn.params[0].pattern as import('../../src/compiler/ast/index').Identifier).name).toBe('a');
      expect(fn.body.body).toHaveLength(1);
    });

    it('parses function with return type', () => {
      const { program } = parse('fun greet() -> string { return "hi"; }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      expect(fn.returnType?.name).toBe('string');
    });

    it('parses function with parameter type annotations', () => {
      const { program } = parse('fun add(a: number, b: number) -> number { return a + b; }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      expect(fn.params[0].typeAnnotation?.name).toBe('number');
      expect(fn.params[1].typeAnnotation?.name).toBe('number');
      expect(fn.returnType?.name).toBe('number');
    });

    it('parses function with default parameter values', () => {
      const { program } = parse('fun f(x = 10) { }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      expect(fn.params[0].defaultValue).toBeDefined();
      const dv = fn.params[0].defaultValue as import('../../src/compiler/ast/index').Literal;
      expect(dv.value).toBe(10);
    });
  });

  describe('if/else statements', () => {
    it('parses simple if', () => {
      const { program } = parse('if (true) { let x = 1; }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').IfStatement;
      expect(stmt.type).toBe('IfStatement');
      expect(stmt.test.type).toBe('Literal');
      expect((stmt.test as import('../../src/compiler/ast/index').Literal).value).toBe(true);
      expect(stmt.consequent.type).toBe('BlockStatement');
      expect(stmt.alternate).toBeUndefined();
    });

    it('parses if-else', () => {
      const { program } = parse('if (x) { } else { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').IfStatement;
      expect(stmt.alternate).toBeDefined();
      expect(stmt.alternate?.type).toBe('BlockStatement');
    });

    it('parses if-elif-else chain', () => {
      const { program } = parse('if (a) { } elif (b) { } else { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').IfStatement;
      expect(stmt.alternate).toBeDefined();
      expect(stmt.alternate?.type).toBe('IfStatement');
      const elifStmt = stmt.alternate as import('../../src/compiler/ast/index').IfStatement;
      expect(elifStmt.alternate?.type).toBe('BlockStatement');
    });

    it('parses multiple elifs', () => {
      const { program, diagnostics } = parse('if (a) { } elif (b) { } elif (c) { } else { }');
      expect(diagnostics.hasErrors()).toBe(false);
      const stmt = program.body[0] as import('../../src/compiler/ast/index').IfStatement;
      expect(stmt.alternate?.type).toBe('IfStatement');
      const elif1 = stmt.alternate as import('../../src/compiler/ast/index').IfStatement;
      expect(elif1.alternate?.type).toBe('IfStatement');
    });
  });

  describe('loops', () => {
    it('parses while loop', () => {
      const { program } = parse('while (x < 10) { x = x + 1; }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').WhileStatement;
      expect(stmt.type).toBe('WhileStatement');
      expect(stmt.test.type).toBe('BinaryExpression');
      expect(stmt.body.type).toBe('BlockStatement');
    });

    it('parses for loop with all clauses', () => {
      const { program } = parse('for (let i = 0; i < 10; i = i + 1) { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').ForStatement;
      expect(stmt.type).toBe('ForStatement');
      expect(stmt.init?.type).toBe('VariableDeclaration');
      expect(stmt.test).toBeDefined();
      expect(stmt.update).toBeDefined();
    });

    it('parses for loop without init', () => {
      const { program } = parse('for (; i < 10; i = i + 1) { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').ForStatement;
      expect(stmt.init).toBeUndefined();
      expect(stmt.test).toBeDefined();
      expect(stmt.update).toBeDefined();
    });

    it('parses for loop without test', () => {
      const { program } = parse('for (let i = 0;; i = i + 1) { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').ForStatement;
      expect(stmt.init).toBeDefined();
      expect(stmt.test).toBeUndefined();
      expect(stmt.update).toBeDefined();
    });

    it('parses loop statement', () => {
      const { program } = parse('loop { break; }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').LoopStatement;
      expect(stmt.type).toBe('LoopStatement');
    });

    it('parses break and continue', () => {
      const { program } = parse('loop { break; continue; }');
      const body = (program.body[0] as import('../../src/compiler/ast/index').LoopStatement).body;
      if (body.type === 'BlockStatement') {
        expect(body.body[0].type).toBe('BreakStatement');
        expect(body.body[1].type).toBe('ContinueStatement');
      }
    });
  });

  describe('return statements', () => {
    it('parses return with value', () => {
      const { program } = parse('fun f() { return 42; }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      const ret = fn.body.body[0] as import('../../src/compiler/ast/index').ReturnStatement;
      expect(ret.type).toBe('ReturnStatement');
      expect(ret.argument).toBeDefined();
    });

    it('parses return without value', () => {
      const { program } = parse('fun f() { return; }');
      const fn = program.body[0] as import('../../src/compiler/ast/index').FunctionDeclaration;
      const ret = fn.body.body[0] as import('../../src/compiler/ast/index').ReturnStatement;
      expect(ret.argument).toBeUndefined();
    });
  });

  describe('binary expressions', () => {
    it('parses arithmetic', () => {
      const { program } = parse('let x = 1 + 2 * 3;');
      const vd = program.body[0] as import('../../src/compiler/ast/index').VariableDeclaration;
      const expr = vd.declarations[0].init as import('../../src/compiler/ast/index').BinaryExpression;
      expect(expr.type).toBe('BinaryExpression');
      expect(expr.operator).toBe('+');
      expect((expr.left as import('../../src/compiler/ast/index').Literal).value).toBe(1);
      const right = expr.right as import('../../src/compiler/ast/index').BinaryExpression;
      expect(right.operator).toBe('*');
    });

    it('parses comparison operators', () => {
      const { program } = parse('let x = a < b && c >= d;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('BinaryExpression');
      expect(expr.operator).toBe('&&');
      expect(expr.left.operator).toBe('<');
      expect(expr.right.operator).toBe('>=');
    });

    it('parses equality operators', () => {
      const { program } = parse('let x = a == b;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('==');
      expect(expr.left.name).toBe('a');
      expect(expr.right.name).toBe('b');
    });

    it('parses logical operators', () => {
      const { program } = parse('let x = a || b && c;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('||');
      expect(expr.left.name).toBe('a');
      expect(expr.right.operator).toBe('&&');
    });

    it('parses bitwise operators', () => {
      const { program } = parse('let x = a | b ^ c & d;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('|');
      expect(expr.right.operator).toBe('^');
      expect(expr.right.right.operator).toBe('&');
    });

    it('parses shift operators', () => {
      const { program } = parse('let x = a << b >> c;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('>>');
      expect(expr.left.operator).toBe('<<');
    });

    it('parses in and is operators', () => {
      const { program } = parse('let x = a in b; let y = c is d;');
      const expr1 = (program.body[0] as any).declarations[0].init;
      const expr2 = (program.body[1] as any).declarations[0].init;
      expect(expr1.operator).toBe('in');
      expect(expr2.operator).toBe('is');
    });
  });

  describe('unary expressions', () => {
    it('parses negation', () => {
      const { program } = parse('let x = -5;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('UnaryExpression');
      expect(expr.operator).toBe('-');
      expect(expr.prefix).toBe(true);
    });

    it('parses logical not', () => {
      const { program } = parse('let x = !true;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('!');
    });

    it('parses bitwise not', () => {
      const { program } = parse('let x = ~y;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.operator).toBe('~');
    });

    it('parses increment and decrement', () => {
      const { program } = parse('let x = ++y; let z = --w;');
      const expr1 = (program.body[0] as any).declarations[0].init;
      const expr2 = (program.body[1] as any).declarations[0].init;
      expect(expr1.operator).toBe('++');
      expect(expr2.operator).toBe('--');
    });

    it('parses await', () => {
      const { program } = parse('let x = await y;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('AwaitExpression');
    });
  });

  describe('literals', () => {
    it('parses number literal', () => {
      const { program } = parse('let x = 42;');
      const lit = (program.body[0] as any).declarations[0].init;
      expect(lit.type).toBe('Literal');
      expect(lit.value).toBe(42);
    });

    it('parses string literal', () => {
      const { program } = parse('let x = "hello";');
      const lit = (program.body[0] as any).declarations[0].init;
      expect(lit.value).toBe('hello');
    });

    it('parses boolean literals', () => {
      const { program } = parse('let a = true; let b = false;');
      expect((program.body[0] as any).declarations[0].init.value).toBe(true);
      expect((program.body[1] as any).declarations[0].init.value).toBe(false);
    });

    it('parses nil literal', () => {
      const { program } = parse('let x = nil;');
      const lit = (program.body[0] as any).declarations[0].init;
      expect(lit.value).toBe(null);
    });
  });

  describe('array and object literals', () => {
    it('parses empty array', () => {
      const { program } = parse('let x = [];');
      const arr = (program.body[0] as any).declarations[0].init;
      expect(arr.type).toBe('ArrayLiteral');
      expect(arr.elements).toHaveLength(0);
    });

    it('parses array with elements', () => {
      const { program } = parse('let x = [1, 2, 3];');
      const arr = (program.body[0] as any).declarations[0].init;
      expect(arr.elements).toHaveLength(3);
    });

    it('parses array with trailing comma', () => {
      const { program } = parse('let x = [1, 2,];');
      const arr = (program.body[0] as any).declarations[0].init;
      expect(arr.elements).toHaveLength(2);
    });

    it('parses empty object', () => {
      const { program } = parse('let x = {};');
      const obj = (program.body[0] as any).declarations[0].init;
      expect(obj.type).toBe('ObjectLiteral');
      expect(obj.properties).toHaveLength(0);
    });

    it('parses object with properties', () => {
      const { program } = parse('let x = { a: 1, b: "hello" };');
      const obj = (program.body[0] as any).declarations[0].init;
      expect(obj.properties).toHaveLength(2);
      expect(obj.properties[0].key.name).toBe('a');
      expect(obj.properties[0].value.value).toBe(1);
    });

    it('parses shorthand properties', () => {
      const { program } = parse('let x = { a, b };');
      const obj = (program.body[0] as any).declarations[0].init;
      expect(obj.properties).toHaveLength(2);
      expect(obj.properties[0].shorthand).toBe(true);
    });
  });

  describe('member access and calls', () => {
    it('parses member expression', () => {
      const { program } = parse('let x = obj.prop;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('MemberExpression');
      expect(expr.object.name).toBe('obj');
      expect(expr.property.name).toBe('prop');
    });

    it('parses method call', () => {
      const { program } = parse('let x = obj.method(1, 2);');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('CallExpression');
      expect(expr.callee.type).toBe('MemberExpression');
      expect(expr.arguments).toHaveLength(2);
    });

    it('parses index expression', () => {
      const { program } = parse('let x = arr[0];');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('IndexExpression');
      expect(expr.object.name).toBe('arr');
    });

    it('parses optional chaining', () => {
      const { program } = parse('let x = obj?.prop;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('MemberExpression');
      expect(expr.optional).toBe(true);
    });

    it('parses optional call', () => {
      const { program } = parse('let x = obj?.();');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('CallExpression');
      expect(expr.optional).toBe(true);
    });
  });

  describe('class declarations', () => {
    it('parses empty class', () => {
      const { program } = parse('class Foo { }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      expect(cls.type).toBe('ClassDeclaration');
      expect(cls.id.name).toBe('Foo');
      expect(cls.body.properties).toHaveLength(0);
      expect(cls.body.methods).toHaveLength(0);
    });

    it('parses class with methods', () => {
      const { program } = parse('class Foo { bar() { } baz() { } }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      expect(cls.body.methods).toHaveLength(2);
      expect(cls.body.methods[0].key.name).toBe('bar');
      expect(cls.body.methods[1].key.name).toBe('baz');
    });

    it('parses class with constructor', () => {
      const { program } = parse('class Foo { constructor(x) { this.x = x; } }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      expect(cls.body.methods[0].kind).toBe('constructor');
      expect(cls.body.methods[0].params).toHaveLength(1);
    });

    it('parses class with properties', () => {
      const { program } = parse('class Foo { x = 42; y; }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      expect(cls.body.properties).toHaveLength(2);
    });

    it('parses class with inheritance', () => {
      const { program } = parse('class Foo inherits Bar { }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      expect(cls.superClass?.name).toBe('Bar');
    });
  });

  describe('lambda expressions', () => {
    it('parses lambda with params', () => {
      const { program } = parse('let f = |x, y| -> x + y;');
      const lambda = (program.body[0] as any).declarations[0].init;
      expect(lambda.type).toBe('LambdaExpression');
      expect(lambda.params).toHaveLength(2);
      expect(lambda.expression).toBe(true);
    });

    it('parses lambda with block body', () => {
      const { program } = parse('let f = |x| { return x; };');
      const lambda = (program.body[0] as any).declarations[0].init;
      expect(lambda.params).toHaveLength(1);
      expect(lambda.expression).toBe(false);
      expect(lambda.body.type).toBe('BlockStatement');
    });

    it('parses arrow expression (no param lambda)', () => {
      const { program } = parse('let f = -> 42;');
      const lambda = (program.body[0] as any).declarations[0].init;
      expect(lambda.type).toBe('LambdaExpression');
      expect(lambda.params).toHaveLength(0);
      expect(lambda.expression).toBe(true);
    });

    it('parses lambda with single param', () => {
      const { program } = parse('let f = |x| -> x;');
      const lambda = (program.body[0] as any).declarations[0].init;
      expect(lambda.params).toHaveLength(1);
    });
  });

  describe('import/export', () => {
    it('parses default import', () => {
      const { program } = parse('import foo from "module";');
      expect(program.imports).toHaveLength(1);
      const imp = program.imports[0];
      expect(imp.specifiers[0].imported).toBe('default');
      expect(imp.specifiers[0].local).toBe('foo');
      expect(imp.source).toBe('module');
    });

    it('parses named import', () => {
      const { program } = parse('import { foo, bar as baz } from "module";');
      const imp = program.imports[0];
      expect(imp.specifiers).toHaveLength(2);
      expect(imp.specifiers[0].imported).toBe('foo');
      expect(imp.specifiers[1].imported).toBe('bar');
      expect(imp.specifiers[1].local).toBe('baz');
    });

    it('parses export declaration', () => {
      const { program } = parse('export let x = 5;');
      expect(program.exports).toHaveLength(1);
      const exp = program.exports[0];
      expect(exp.declaration?.type).toBe('VariableDeclaration');
    });

    it('parses export named', () => {
      const { program } = parse('export { x, y as z };');
      expect(program.exports).toHaveLength(1);
      const exp = program.exports[0];
      expect(exp.specifiers).toHaveLength(2);
      expect(exp.specifiers![0].exported).toBe('x');
      expect(exp.specifiers![1].exported).toBe('z');
      expect(exp.specifiers![1].local).toBe('y');
    });
  });

  describe('try/catch/finally', () => {
    it('parses try-catch', () => {
      const { program } = parse('try { } catch (e) { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').TryStatement;
      expect(stmt.type).toBe('TryStatement');
      expect(stmt.handler).toBeDefined();
      expect(stmt.handler?.param.name).toBe('e');
      expect(stmt.finalizer).toBeUndefined();
    });

    it('parses try-finally', () => {
      const { program } = parse('try { } finally { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').TryStatement;
      expect(stmt.handler).toBeUndefined();
      expect(stmt.finalizer).toBeDefined();
    });

    it('parses try-catch-finally', () => {
      const { program } = parse('try { } catch (e) { } finally { }');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').TryStatement;
      expect(stmt.handler).toBeDefined();
      expect(stmt.finalizer).toBeDefined();
    });
  });

  describe('throw and match', () => {
    it('parses throw', () => {
      const { program } = parse('throw "error";');
      const stmt = program.body[0] as import('../../src/compiler/ast/index').ThrowStatement;
      expect(stmt.type).toBe('ThrowStatement');
      expect((stmt.argument as import('../../src/compiler/ast/index').Literal).value).toBe('error');
    });

    it('parses match statement', () => {
      const { program } = parse(`
        match x {
          case 1: doSomething();
          case 2: doOther();
          default: handleDefault();
        }
      `);
      const stmt = program.body[0] as import('../../src/compiler/ast/index').MatchStatement;
      expect(stmt.type).toBe('MatchStatement');
      expect(stmt.cases).toHaveLength(3);
      expect(stmt.discriminant.type).toBe('Identifier');
      expect((stmt.discriminant as import('../../src/compiler/ast/index').Identifier).name).toBe('x');
    });
  });

  describe('new expression', () => {
    it('parses new expression', () => {
      const { program } = parse('let x = new Foo(1, 2);');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('NewExpression');
      expect(expr.callee.name).toBe('Foo');
      expect(expr.arguments).toHaveLength(2);
    });

    it('parses new without args', () => {
      const { program } = parse('let x = new Foo;');
      const expr = (program.body[0] as any).declarations[0].init;
      expect(expr.type).toBe('NewExpression');
      expect(expr.callee.name).toBe('Foo');
      expect(expr.arguments).toHaveLength(0);
    });
  });

  describe('this and super', () => {
    it('parses this expression', () => {
      const { program } = parse('class Foo { bar() { return this; } }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      const method = cls.body.methods[0];
      const ret = method.body.body[0] as import('../../src/compiler/ast/index').ReturnStatement;
      expect(ret.argument?.type).toBe('ThisExpression');
    });

    it('parses super expression', () => {
      const { program } = parse('class Foo inherits Bar { baz() { super.bar(); } }');
      const cls = program.body[0] as import('../../src/compiler/ast/index').ClassDeclaration;
      const method = cls.body.methods[0];
      const exprStmt = method.body.body[0] as import('../../src/compiler/ast/index').ExpressionStatement;
      expect(exprStmt.expression.type).toBe('CallExpression');
      const call = exprStmt.expression as import('../../src/compiler/ast/index').CallExpression;
      expect(call.callee.type).toBe('MemberExpression');
      const member = call.callee as import('../../src/compiler/ast/index').MemberExpression;
      expect(member.object.type).toBe('SuperExpression');
    });
  });

  describe('comments', () => {
    it('handles line comments', () => {
      const { program, diagnostics } = parse(`
        // this is a comment
        let x = 1;
        // another comment
      `);
      expect(program.body).toHaveLength(1);
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('handles block comments', () => {
      const { program, diagnostics } = parse(`
        /* block comment */
        let x = 1;
        /* nested /* comment */ */
        let y = 2;
      `);
      expect(program.body).toHaveLength(2);
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('semicolons', () => {
    it('works without semicolons on newlines', () => {
      const { program, diagnostics } = parse(`
        let x = 1
        let y = 2
        fun f() { return x }
      `);
      expect(program.body).toHaveLength(3);
      expect(diagnostics.hasErrors()).toBe(false);
    });
  });

  describe('interface and enum', () => {
    it('parses interface declaration', () => {
      const { program } = parse('interface Foo { bar(): void; }');
      const decl = program.body[0] as import('../../src/compiler/ast/index').InterfaceDeclaration;
      expect(decl.type).toBe('InterfaceDeclaration');
      expect(decl.id.name).toBe('Foo');
    });

    it('parses enum declaration', () => {
      const { program } = parse('enum Color { Red, Green, Blue = 3 }');
      const decl = program.body[0] as import('../../src/compiler/ast/index').EnumDeclaration;
      expect(decl.type).toBe('EnumDeclaration');
      expect(decl.members).toHaveLength(3);
      expect(decl.members[2].init).toBeDefined();
    });
  });

  describe('type alias', () => {
    it('parses type alias', () => {
      const { program } = parse('type MyType = string;');
      const decl = program.body[0] as import('../../src/compiler/ast/index').TypeAliasDeclaration;
      expect(decl.type).toBe('TypeAliasDeclaration');
      expect(decl.id.name).toBe('MyType');
      expect(decl.annotation.name).toBe('string');
    });
  });

  describe('error handling', () => {
    it('recovers from unexpected token', () => {
      const { diagnostics } = parse('let x = ;');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('handles unterminated block', () => {
      const { diagnostics } = parse('fun f() { let x = 1; ');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('handles missing closing paren', () => {
      const { diagnostics } = parse('if (true { }');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('recovers and continues parsing', () => {
      const { program, diagnostics } = parse('let x = ; let y = 42;');
      expect(diagnostics.hasErrors()).toBe(true);
      expect(program.body.length).toBeGreaterThanOrEqual(1);
    });

    it('reports error for empty parens', () => {
      const { diagnostics } = parse('let x = ();');
      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('handles unexpected character', () => {
      const { diagnostics } = parse('let @x = 1;');
      expect(diagnostics.hasErrors()).toBe(true);
    });
  });

  describe('complex programs', () => {
    it('parses a full program', () => {
      const source = `
        import { assertEquals } from "std/testing";
        import math from "std/math";

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

        export { result };
      `;
      const { program, diagnostics } = parse(source);
      expect(diagnostics.hasErrors()).toBe(false);
      expect(program.body.length).toBeGreaterThan(5);
      expect(program.imports).toHaveLength(2);
      expect(program.exports).toHaveLength(1);
    });
  });
});
