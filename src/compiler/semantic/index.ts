import {
  Program, Statement, Declaration, Expression, VariableDeclaration, FunctionDeclaration,
  ClassDeclaration, InterfaceDeclaration, TypeAliasDeclaration, EnumDeclaration,
  ExpressionStatement, BlockStatement, IfStatement, WhileStatement, ForStatement,
  LoopStatement, BreakStatement, ContinueStatement, ReturnStatement, TryStatement,
  ThrowStatement, MatchStatement, ImportDeclaration, ExportDeclaration,
  AssignmentExpression, BinaryExpression, UnaryExpression, CallExpression,
  MemberExpression, IndexExpression, NewExpression, DeleteExpression,
  AwaitExpression, YieldExpression, LambdaExpression, ObjectLiteral, ArrayLiteral,
  Identifier, Literal, ThisExpression, SuperExpression, TypeAnnotation,
  Parameter, Property, Method, CatchClause, MatchCase, Node, Span,
} from '../ast/index';
import { DiagnosticBag } from '../diagnostics';

export interface SymbolInfo {
  name: string;
  kind: 'variable' | 'function' | 'class' | 'interface' | 'type' | 'enum' | 'import';
  node: Node;
  typeAnnotation?: TypeAnnotation;
  exported: boolean;
  imported: boolean;
  module?: string;
}

export interface Scope {
  symbols: Map<string, SymbolInfo>;
  parent: Scope | null;
}

export interface AnalysisResult {
  ast: Program;
  diagnostics: DiagnosticBag;
  globals: Map<string, SymbolInfo>;
  exports: Map<string, SymbolInfo>;
}

export class SemanticAnalyzer {
  private diagnostics: DiagnosticBag;
  private globalScope: Scope;
  private currentScope: Scope;
  private functionDepth = 0;
  private loopDepth = 0;

  constructor(diagnostics?: DiagnosticBag) {
    this.diagnostics = diagnostics ?? new DiagnosticBag();
    this.globalScope = { symbols: new Map(), parent: null };
    this.currentScope = this.globalScope;
  }

  analyze(program: Program): AnalysisResult {
    for (const imp of program.imports) {
      this.visitImportDeclaration(imp);
    }

    for (const exp of program.exports) {
      this.visitExportDeclaration(exp);
    }

    for (const stmt of program.body) {
      if (stmt.type === 'ImportDeclaration' || stmt.type === 'ExportDeclaration') continue;
      this.visitStatement(stmt);
    }

    const exports = new Map<string, SymbolInfo>();
    for (const [name, sym] of this.globalScope.symbols) {
      if (sym.exported) exports.set(name, sym);
    }

    return {
      ast: program,
      diagnostics: this.diagnostics,
      globals: this.globalScope.symbols,
      exports,
    };
  }

  getDiagnostics(): DiagnosticBag {
    return this.diagnostics;
  }

  private enterScope(): Scope {
    const scope: Scope = { symbols: new Map(), parent: this.currentScope };
    this.currentScope = scope;
    return scope;
  }

  private exitScope(): void {
    if (this.currentScope.parent) {
      this.currentScope = this.currentScope.parent;
    }
  }

  private declareSymbol(name: string, kind: SymbolInfo['kind'], node: Node, typeAnnotation?: TypeAnnotation, exported = false, imported = false, module?: string): boolean {
    if (this.currentScope.symbols.has(name)) {
      this.diagnostics.error(`Duplicate declaration: '${name}' already declared in this scope`, node.span);
      return false;
    }
    this.currentScope.symbols.set(name, {
      name, kind, node, typeAnnotation, exported, imported, module,
    });
    return true;
  }

  private resolveSymbol(name: string, span: Span): SymbolInfo | undefined {
    let scope: Scope | null = this.currentScope;
    while (scope) {
      const sym = scope.symbols.get(name);
      if (sym) return sym;
      scope = scope.parent;
    }
    return undefined;
  }

  private resolveSymbolOrError(name: string, span: Span): SymbolInfo | undefined {
    const sym = this.resolveSymbol(name, span);
    if (!sym) {
      this.diagnostics.error(`Undefined variable: '${name}'`, span);
    }
    return sym;
  }

  private visitStatement(stmt: Statement): void {
    switch (stmt.type) {
      case 'VariableDeclaration': return this.visitVariableDeclaration(stmt);
      case 'FunctionDeclaration': return this.visitFunctionDeclaration(stmt);
      case 'ClassDeclaration': return this.visitClassDeclaration(stmt);
      case 'InterfaceDeclaration': return this.visitInterfaceDeclaration(stmt);
      case 'TypeAliasDeclaration': return this.visitTypeAlias(stmt);
      case 'EnumDeclaration': return this.visitEnumDeclaration(stmt);
      case 'ExpressionStatement': return this.visitExpressionStatement(stmt);
      case 'BlockStatement': return this.visitBlockStatement(stmt);
      case 'IfStatement': return this.visitIfStatement(stmt);
      case 'WhileStatement': return this.visitWhileStatement(stmt);
      case 'ForStatement': return this.visitForStatement(stmt);
      case 'LoopStatement': return this.visitLoopStatement(stmt);
      case 'BreakStatement': return this.visitBreakStatement(stmt);
      case 'ContinueStatement': return this.visitContinueStatement(stmt);
      case 'ReturnStatement': return this.visitReturnStatement(stmt);
      case 'TryStatement': return this.visitTryStatement(stmt);
      case 'ThrowStatement': return this.visitThrowStatement(stmt);
      case 'MatchStatement': return this.visitMatchStatement(stmt);
    }
  }

  private visitImportDeclaration(decl: ImportDeclaration): void {
    for (const spec of decl.specifiers) {
      this.declareSymbol(spec.local, 'import', decl, undefined, false, true, decl.source);
    }
  }

  private visitExportDeclaration(decl: ExportDeclaration): void {
    if (decl.declaration) {
      this.visitStatement(decl.declaration as Statement);
      if (decl.declaration.type === 'VariableDeclaration') {
        for (const d of decl.declaration.declarations) {
          const existing = this.resolveSymbol(d.id.name, d.id.span);
          if (existing) existing.exported = true;
        }
      } else if ('id' in decl.declaration) {
        const declNode = decl.declaration as FunctionDeclaration | ClassDeclaration;
        const existing = this.resolveSymbol(declNode.id.name, declNode.id.span);
        if (existing) existing.exported = true;
      }
    }
  }

  private visitVariableDeclaration(decl: VariableDeclaration): void {
    for (const d of decl.declarations) {
      this.declareSymbol(d.id.name, 'variable', d.id, d.typeAnnotation);
      if (d.init) {
        this.visitExpression(d.init);
      }
    }
  }

  private visitFunctionDeclaration(decl: FunctionDeclaration): void {
    this.declareSymbol(decl.id.name, 'function', decl, decl.returnType);
    this.enterScope();

    for (const param of decl.params) {
      if (param.pattern.type === 'Identifier') {
        this.declareSymbol(param.pattern.name, 'variable', param.pattern, param.typeAnnotation);
      }
      if (param.defaultValue) {
        this.visitExpression(param.defaultValue);
      }
    }

    this.functionDepth++;
    for (const stmt of decl.body.body) {
      this.visitStatement(stmt);
    }
    this.functionDepth--;
    this.exitScope();
  }

  private visitClassDeclaration(decl: ClassDeclaration): void {
    this.declareSymbol(decl.id.name, 'class', decl);

    if (decl.superClass) {
      const superSym = this.resolveSymbol(decl.superClass.name, decl.superClass.span);
      if (!superSym) {
        this.diagnostics.error(`Undefined class: '${decl.superClass.name}'`, decl.superClass.span);
      } else if (superSym.kind !== 'class') {
        this.diagnostics.error(`'${decl.superClass.name}' is not a class`, decl.superClass.span);
      }
    }

    this.enterScope();
    for (const method of decl.body.methods) {
      this.enterScope();
      for (const param of method.params) {
        if (param.pattern.type === 'Identifier') {
          this.declareSymbol(param.pattern.name, 'variable', param.pattern, param.typeAnnotation);
        }
        if (param.defaultValue) {
          this.visitExpression(param.defaultValue);
        }
      }
      this.functionDepth++;
      for (const stmt of method.body.body) {
        this.visitStatement(stmt);
      }
      this.functionDepth--;
      this.exitScope();
    }

    for (const prop of decl.body.properties) {
      if (prop.value) {
        this.visitExpression(prop.value);
      }
    }
    this.exitScope();
  }

  private visitInterfaceDeclaration(decl: InterfaceDeclaration): void {
    this.declareSymbol(decl.id.name, 'interface', decl);
  }

  private visitTypeAlias(decl: TypeAliasDeclaration): void {
    this.declareSymbol(decl.id.name, 'type', decl);
  }

  private visitEnumDeclaration(decl: EnumDeclaration): void {
    this.declareSymbol(decl.id.name, 'enum', decl);
    for (const member of decl.members) {
      if (member.init) {
        this.visitExpression(member.init);
      }
    }
  }

  private visitExpressionStatement(stmt: ExpressionStatement): void {
    this.visitExpression(stmt.expression);
  }

  private visitBlockStatement(stmt: BlockStatement): void {
    this.enterScope();
    for (const s of stmt.body) {
      this.visitStatement(s);
    }
    this.exitScope();
  }

  private visitIfStatement(stmt: IfStatement): void {
    this.visitExpression(stmt.test);
    this.visitStatement(stmt.consequent);
    if (stmt.alternate) {
      this.visitStatement(stmt.alternate);
    }
  }

  private visitWhileStatement(stmt: WhileStatement): void {
    this.visitExpression(stmt.test);
    this.loopDepth++;
    this.visitStatement(stmt.body);
    this.loopDepth--;
  }

  private visitForStatement(stmt: ForStatement): void {
    this.enterScope();
    if (stmt.init) {
      this.visitStatement(stmt.init);
    }
    if (stmt.test) {
      this.visitExpression(stmt.test);
    }
    if (stmt.update) {
      this.visitExpression(stmt.update);
    }
    this.loopDepth++;
    this.visitStatement(stmt.body);
    this.loopDepth--;
    this.exitScope();
  }

  private visitLoopStatement(stmt: LoopStatement): void {
    this.loopDepth++;
    this.visitStatement(stmt.body);
    this.loopDepth--;
  }

  private visitBreakStatement(stmt: BreakStatement): void {
    if (this.loopDepth === 0) {
      this.diagnostics.error("'break' outside of loop", stmt.span);
    }
    if (stmt.label) {
      this.resolveSymbolOrError(stmt.label.name, stmt.label.span);
    }
  }

  private visitContinueStatement(stmt: ContinueStatement): void {
    if (this.loopDepth === 0) {
      this.diagnostics.error("'continue' outside of loop", stmt.span);
    }
    if (stmt.label) {
      this.resolveSymbolOrError(stmt.label.name, stmt.label.span);
    }
  }

  private visitReturnStatement(stmt: ReturnStatement): void {
    if (this.functionDepth === 0) {
      this.diagnostics.error("'return' outside of function", stmt.span);
    }
    if (stmt.argument) {
      this.visitExpression(stmt.argument);
    }
  }

  private visitTryStatement(stmt: TryStatement): void {
    this.visitBlockStatement(stmt.block);
    if (stmt.handler) {
      this.enterScope();
      this.declareSymbol(stmt.handler.param.name, 'variable', stmt.handler.param);
      for (const s of stmt.handler.body.body) {
        this.visitStatement(s);
      }
      this.exitScope();
    }
    if (stmt.finalizer) {
      this.visitBlockStatement(stmt.finalizer);
    }
  }

  private visitThrowStatement(stmt: ThrowStatement): void {
    this.visitExpression(stmt.argument);
  }

  private visitMatchStatement(stmt: MatchStatement): void {
    this.visitExpression(stmt.discriminant);
    for (const c of stmt.cases) {
      this.visitExpression(c.test);
      this.enterScope();
      for (const s of c.consequent) {
        this.visitStatement(s);
      }
      this.exitScope();
    }
  }

  private visitExpression(expr: Expression): string | undefined {
    switch (expr.type) {
      case 'Identifier': return this.visitIdentifier(expr);
      case 'Literal': return this.visitLiteral(expr);
      case 'BinaryExpression': return this.visitBinaryExpression(expr);
      case 'UnaryExpression': return this.visitUnaryExpression(expr);
      case 'AssignmentExpression': return this.visitAssignmentExpression(expr);
      case 'CallExpression': return this.visitCallExpression(expr);
      case 'MemberExpression': return this.visitMemberExpression(expr);
      case 'IndexExpression': return this.visitIndexExpression(expr);
      case 'NewExpression': return this.visitNewExpression(expr);
      case 'DeleteExpression': return this.visitDeleteExpression(expr);
      case 'AwaitExpression': return this.visitAwaitExpression(expr);
      case 'YieldExpression': return this.visitYieldExpression(expr);
      case 'LambdaExpression': return this.visitLambdaExpression(expr);
      case 'ObjectLiteral': return this.visitObjectLiteral(expr);
      case 'ArrayLiteral': return this.visitArrayLiteral(expr);
      case 'ThisExpression': return 'object';
      case 'SuperExpression': return 'object';
      default: return 'unknown';
    }
  }

  private visitIdentifier(expr: Identifier): string | undefined {
    const sym = this.resolveSymbol(expr.name, expr.span);
    if (!sym) {
      this.diagnostics.error(`Undefined variable: '${expr.name}'`, expr.span);
      return 'unknown';
    }
    return this.extractTypeName(sym.typeAnnotation);
  }

  private visitLiteral(expr: Literal): string | undefined {
    if (expr.value === null) return 'null';
    if (typeof expr.value === 'boolean') return 'boolean';
    if (typeof expr.value === 'number') return 'number';
    if (typeof expr.value === 'string') return 'string';
    return 'unknown';
  }

  private visitBinaryExpression(expr: BinaryExpression): string | undefined {
    const leftType = this.visitExpression(expr.left);
    const rightType = this.visitExpression(expr.right);

    if (expr.operator === '===' || expr.operator === '!==' ||
        expr.operator === '==' || expr.operator === '!=') {
      return 'boolean';
    }

    if (expr.operator === '<' || expr.operator === '>' ||
        expr.operator === '<=' || expr.operator === '>=' ||
        expr.operator === 'in' || expr.operator === 'is') {
      return 'boolean';
    }

    if (expr.operator === '&&' || expr.operator === '||') {
      return leftType;
    }

    if (expr.operator === ',' || expr.operator === '|' || expr.operator === '^' || expr.operator === '&' ||
        expr.operator === '<<' || expr.operator === '>>') {
      return this.checkBinaryTypes(expr, leftType, rightType, ['number']);
    }

    if (expr.operator === '+' || expr.operator === '-') {
      return this.checkBinaryTypes(expr, leftType, rightType, ['number', 'string']);
    }

    if (expr.operator === '*' || expr.operator === '/' || expr.operator === '%') {
      return this.checkBinaryTypes(expr, leftType, rightType, ['number']);
    }

    return 'unknown';
  }

  private checkBinaryTypes(expr: BinaryExpression, leftType?: string, rightType?: string, allowed?: string[]): string | undefined {
    if (leftType && rightType && leftType !== rightType && leftType !== 'unknown' && rightType !== 'unknown') {
      this.diagnostics.error(
        `Type mismatch: cannot apply '${expr.operator}' to '${leftType}' and '${rightType}'`,
        expr.span,
      );
    }

    if (allowed && leftType && leftType !== 'unknown' && !allowed.includes(leftType)) {
      this.diagnostics.error(
        `Type '${leftType}' not allowed for operator '${expr.operator}'`,
        expr.span,
      );
    }

    return leftType ?? rightType;
  }

  private visitUnaryExpression(expr: UnaryExpression): string | undefined {
    const argType = this.visitExpression(expr.argument);

    if (expr.operator === '!' || expr.operator === '~') {
      return 'boolean';
    }

    if (expr.operator === '-' || expr.operator === '+') {
      if (argType && argType !== 'number') {
        this.diagnostics.error(`Cannot apply '${expr.operator}' to type '${argType}'`, expr.span);
      }
      return 'number';
    }

    if (expr.operator === '++' || expr.operator === '--') {
      if (argType && argType !== 'number') {
        this.diagnostics.error(`Cannot apply '${expr.operator}' to type '${argType}'`, expr.span);
      }
      return 'number';
    }

    if (expr.operator === 'typeof') return 'string';

    return 'unknown';
  }

  private visitAssignmentExpression(expr: AssignmentExpression): string | undefined {
    const rightType = this.visitExpression(expr.right);

    if (expr.left.type === 'Identifier') {
      const sym = this.resolveSymbol(expr.left.name, expr.left.span);
      if (!sym) {
        this.diagnostics.error(`Undefined variable: '${expr.left.name}'`, expr.left.span);
        return 'unknown';
      }
      if (expr.operator !== '=') {
        const symType = this.extractTypeName(sym.typeAnnotation);
        if (symType && rightType && symType !== rightType) {
          this.diagnostics.error(
            `Type mismatch: cannot apply '${expr.operator}' to '${symType}' and '${rightType}'`,
            expr.span,
          );
        }
      }
      return rightType;
    }

    this.visitExpression(expr.left);
    return rightType;
  }

  private visitCallExpression(expr: CallExpression): string | undefined {
    this.visitExpression(expr.callee);
    for (const arg of expr.arguments) {
      this.visitExpression(arg);
    }

    if (expr.callee.type === 'Identifier') {
      const sym = this.resolveSymbol(expr.callee.name, expr.callee.span);
      if (sym && sym.kind === 'function' && 'params' in sym.node) {
        const fnNode = sym.node as FunctionDeclaration;
        if (fnNode.params.length !== expr.arguments.length) {
          this.diagnostics.error(
            `Function '${expr.callee.name}' expects ${fnNode.params.length} arguments but got ${expr.arguments.length}`,
            expr.span,
          );
        }
        return this.extractTypeName(fnNode.returnType);
      }
    }

    return 'unknown';
  }

  private visitMemberExpression(expr: MemberExpression): string | undefined {
    this.visitExpression(expr.object);
    return 'unknown';
  }

  private visitIndexExpression(expr: IndexExpression): string | undefined {
    this.visitExpression(expr.object);
    this.visitExpression(expr.index);
    return 'unknown';
  }

  private visitNewExpression(expr: NewExpression): string | undefined {
    const calleeType = this.visitExpression(expr.callee);

    for (const arg of expr.arguments) {
      this.visitExpression(arg);
    }

    if (expr.callee.type === 'Identifier') {
      const sym = this.resolveSymbol(expr.callee.name, expr.callee.span);
      if (!sym) {
        this.diagnostics.error(`Undefined class: '${expr.callee.name}'`, expr.callee.span);
      } else if (sym.kind !== 'class') {
        this.diagnostics.error(`'${expr.callee.name}' is not a class`, expr.callee.span);
      }
      return expr.callee.name;
    }

    return calleeType ?? 'object';
  }

  private visitDeleteExpression(expr: DeleteExpression): string | undefined {
    this.visitExpression(expr.argument);
    return 'boolean';
  }

  private visitAwaitExpression(expr: AwaitExpression): string | undefined {
    const argType = this.visitExpression(expr.argument);
    if (this.functionDepth === 0) {
      this.diagnostics.error("'await' outside of async function", expr.span);
    }
    return argType;
  }

  private visitYieldExpression(expr: YieldExpression): string | undefined {
    if (expr.argument) {
      return this.visitExpression(expr.argument);
    }
    return 'unknown';
  }

  private visitLambdaExpression(expr: LambdaExpression): string | undefined {
    this.enterScope();
    for (const param of expr.params) {
      if (param.pattern.type === 'Identifier') {
        this.declareSymbol(param.pattern.name, 'variable', param.pattern, param.typeAnnotation);
      }
      if (param.defaultValue) {
        this.visitExpression(param.defaultValue);
      }
    }

    this.functionDepth++;
    if (expr.body.type === 'BlockStatement') {
      for (const stmt of expr.body.body) {
        this.visitStatement(stmt);
      }
    } else {
      this.visitExpression(expr.body);
    }
    this.functionDepth--;

    this.exitScope();
    return 'function';
  }

  private visitObjectLiteral(expr: ObjectLiteral): string | undefined {
    for (const prop of expr.properties) {
      this.visitExpression(prop.value);
    }
    return 'object';
  }

  private visitArrayLiteral(expr: ArrayLiteral): string | undefined {
    for (const elem of expr.elements) {
      this.visitExpression(elem);
    }
    return 'array';
  }

  private extractTypeName(typeAnnotation?: TypeAnnotation): string | undefined {
    if (!typeAnnotation) return undefined;
    return typeAnnotation.name;
  }
}
