/**
 * Zoya 3.0 - Abstract Syntax Tree (AST) Node Types
 */

import { Span as Span_ } from '../diagnostics';
export type Span = Span_;

export type NodeType =
  | 'Program'
  | 'ImportDeclaration'
  | 'ExportDeclaration'
  | 'VariableDeclaration'
  | 'FunctionDeclaration'
  | 'ClassDeclaration'
  | 'InterfaceDeclaration'
  | 'TypeAliasDeclaration'
  | 'EnumDeclaration'
  | 'ExpressionStatement'
  | 'BlockStatement'
  | 'IfStatement'
  | 'WhileStatement'
  | 'ForStatement'
  | 'LoopStatement'
  | 'BreakStatement'
  | 'ContinueStatement'
  | 'ReturnStatement'
  | 'TryStatement'
  | 'ThrowStatement'
  | 'MatchStatement'
  | 'AssignmentExpression'
  | 'BinaryExpression'
  | 'UnaryExpression'
  | 'CallExpression'
  | 'MemberExpression'
  | 'IndexExpression'
  | 'NewExpression'
  | 'DeleteExpression'
  | 'AwaitExpression'
  | 'YieldExpression'
  | 'LambdaExpression'
  | 'ObjectLiteral'
  | 'ArrayLiteral'
  | 'TemplateLiteral'
  | 'Identifier'
  | 'Literal'
  | 'ThisExpression'
  | 'SuperExpression'
  | 'TypeAnnotation'
  | 'Parameter'
  | 'Property'
  | 'Method'
  | 'Decorator'
  | 'MatchCase'
  | 'CatchClause'
  | 'ObjectPattern'
  | 'ArrayPattern'
  | 'RestElement'
  | 'AssignmentPattern'
  | 'TypeParameter';

export interface Node {
  readonly type: NodeType;
  readonly span: Span;
}

export interface Program extends Node {
  type: 'Program';
  body: Statement[];
  imports: ImportDeclaration[];
  exports: ExportDeclaration[];
}

export interface ImportDeclaration extends Node {
  type: 'ImportDeclaration';
  specifiers: ImportSpecifier[];
  source: string;
}

export interface ImportSpecifier {
  readonly imported: string;
  readonly local: string;
}

export interface ExportDeclaration extends Node {
  type: 'ExportDeclaration';
  declaration?: Declaration;
  specifiers?: ExportSpecifier[];
  source?: string;
}

export interface ExportSpecifier {
  readonly exported: string;
  readonly local: string;
}

export type Statement =
  | ImportDeclaration
  | ExportDeclaration
  | VariableDeclaration
  | FunctionDeclaration
  | ClassDeclaration
  | InterfaceDeclaration
  | TypeAliasDeclaration
  | EnumDeclaration
  | ExpressionStatement
  | BlockStatement
  | IfStatement
  | WhileStatement
  | ForStatement
  | LoopStatement
  | BreakStatement
  | ContinueStatement
  | ReturnStatement
  | TryStatement
  | ThrowStatement
  | MatchStatement;

export type Declaration =
  | VariableDeclaration
  | FunctionDeclaration
  | ClassDeclaration
  | InterfaceDeclaration
  | TypeAliasDeclaration
  | EnumDeclaration;

export interface VariableDeclaration extends Node {
  type: 'VariableDeclaration';
  kind: 'let' | 'const';
  declarations: VariableDeclarator[];
}

export interface VariableDeclarator {
  readonly id: Identifier;
  readonly init?: Expression;
  readonly typeAnnotation?: TypeAnnotation;
}

export interface FunctionDeclaration extends Node {
  type: 'FunctionDeclaration';
  id: Identifier;
  params: Parameter[];
  returnType?: TypeAnnotation;
  body: BlockStatement;
  async: boolean;
  generator: boolean;
  decorators: Decorator[];
}

export interface ClassDeclaration extends Node {
  type: 'ClassDeclaration';
  id: Identifier;
  superClass?: Identifier;
  implements: Identifier[];
  body: ClassBody;
  decorators: Decorator[];
  abstract: boolean;
}

export interface ClassBody {
  readonly properties: Property[];
  readonly methods: Method[];
}

export interface InterfaceDeclaration extends Node {
  type: 'InterfaceDeclaration';
  id: Identifier;
  extends: Identifier[];
  body: InterfaceBody;
}

export interface InterfaceBody {
  readonly properties: Property[];
  readonly methods: Method[];
}

export interface TypeAliasDeclaration extends Node {
  type: 'TypeAliasDeclaration';
  id: Identifier;
  typeParameters: TypeParameter[];
  annotation: TypeAnnotation;
}

export interface EnumDeclaration extends Node {
  type: 'EnumDeclaration';
  id: Identifier;
  members: EnumMember[];
}

export interface EnumMember {
  readonly id: Identifier;
  readonly init?: Expression;
}

export interface ExpressionStatement extends Node {
  type: 'ExpressionStatement';
  expression: Expression;
}

export interface BlockStatement extends Node {
  type: 'BlockStatement';
  body: Statement[];
}

export interface IfStatement extends Node {
  type: 'IfStatement';
  test: Expression;
  consequent: Statement;
  alternate?: Statement;
}

export interface WhileStatement extends Node {
  type: 'WhileStatement';
  test: Expression;
  body: Statement;
}

export interface ForStatement extends Node {
  type: 'ForStatement';
  init?: VariableDeclaration | ExpressionStatement;
  test?: Expression;
  update?: Expression;
  body: Statement;
}

export interface LoopStatement extends Node {
  type: 'LoopStatement';
  body: Statement;
}

export interface BreakStatement extends Node {
  type: 'BreakStatement';
  label?: Identifier;
}

export interface ContinueStatement extends Node {
  type: 'ContinueStatement';
  label?: Identifier;
}

export interface ReturnStatement extends Node {
  type: 'ReturnStatement';
  argument?: Expression;
}

export interface TryStatement extends Node {
  type: 'TryStatement';
  block: BlockStatement;
  handler?: CatchClause;
  finalizer?: BlockStatement;
}

export interface CatchClause extends Node {
  type: 'CatchClause';
  param: Identifier;
  body: BlockStatement;
}

export interface ThrowStatement extends Node {
  type: 'ThrowStatement';
  argument: Expression;
}

export interface MatchStatement extends Node {
  type: 'MatchStatement';
  discriminant: Expression;
  cases: MatchCase[];
}

export interface MatchCase extends Node {
  type: 'MatchCase';
  test: Expression;
  consequent: Statement[];
}

export type Expression =
  | AssignmentExpression
  | BinaryExpression
  | UnaryExpression
  | CallExpression
  | MemberExpression
  | IndexExpression
  | NewExpression
  | DeleteExpression
  | AwaitExpression
  | YieldExpression
  | LambdaExpression
  | FunctionDeclaration
  | ClassDeclaration
  | ObjectLiteral
  | ArrayLiteral
  | TemplateLiteral
  | Identifier
  | Literal
  | ThisExpression
  | SuperExpression;

export interface AssignmentExpression extends Node {
  type: 'AssignmentExpression';
  operator: AssignmentOperator;
  left: Expression;
  right: Expression;
}

export type AssignmentOperator =
  | '='
  | '+='
  | '-='
  | '*='
  | '/='
  | '%='
  | '**='
  | '<<='
  | '>>='
  | '&='
  | '^='
  | '|='
  | '??='
  | '||='
  | '&&=';

export interface BinaryExpression extends Node {
  type: 'BinaryExpression';
  operator: BinaryOperator;
  left: Expression;
  right: Expression;
}

export type BinaryOperator =
  | '+'
  | '-'
  | '*'
  | '/'
  | '%'
  | '**'
  | '<<'
  | '>>'
  | '&'
  | '|'
  | '^'
  | ','
  | '=='
  | '!='
  | '==='
  | '!=='
  | '<'
  | '<='
  | '>'
  | '>='
  | 'in'
  | 'instanceof'
  | 'is'
  | '&&'
  | '||'
  | '??';

export interface UnaryExpression extends Node {
  type: 'UnaryExpression';
  operator: UnaryOperator;
  argument: Expression;
  prefix: boolean;
}

export type UnaryOperator =
  | '-'
  | '+'
  | '!'
  | '~'
  | '++'
  | '--'
  | 'typeof'
  | 'delete'
  | 'await'
  | 'yield';

export interface CallExpression extends Node {
  type: 'CallExpression';
  callee: Expression;
  arguments: Expression[];
  optional: boolean;
  typeArguments: TypeAnnotation[];
}

export interface MemberExpression extends Node {
  type: 'MemberExpression';
  object: Expression;
  property: Identifier;
  computed: boolean;
  optional: boolean;
}

export interface IndexExpression extends Node {
  type: 'IndexExpression';
  object: Expression;
  index: Expression;
  optional: boolean;
}

export interface NewExpression extends Node {
  type: 'NewExpression';
  callee: Expression;
  arguments: Expression[];
  typeArguments: TypeAnnotation[];
}

export interface DeleteExpression extends Node {
  type: 'DeleteExpression';
  argument: Expression;
}

export interface AwaitExpression extends Node {
  type: 'AwaitExpression';
  argument: Expression;
}

export interface YieldExpression extends Node {
  type: 'YieldExpression';
  argument?: Expression;
  delegate: boolean;
}

export interface LambdaExpression extends Node {
  type: 'LambdaExpression';
  params: Parameter[];
  returnType?: TypeAnnotation;
  body: Expression | BlockStatement;
  async: boolean;
  expression: boolean;
}

export interface ObjectLiteral extends Node {
  type: 'ObjectLiteral';
  properties: Property[];
}

export interface ArrayLiteral extends Node {
  type: 'ArrayLiteral';
  elements: Expression[];
}

export interface TemplateLiteral extends Node {
  type: 'TemplateLiteral';
  quasis: TemplateElement[];
  expressions: Expression[];
}

export interface TemplateElement {
  readonly value: { raw: string; cooked: string };
  readonly tail: boolean;
}

export interface Identifier extends Node {
  type: 'Identifier';
  name: string;
}

export interface Literal extends Node {
  type: 'Literal';
  value: string | number | boolean | null;
  raw: string;
}

export interface ThisExpression extends Node {
  type: 'ThisExpression';
}

export interface SuperExpression extends Node {
  type: 'SuperExpression';
}

export interface TypeAnnotation extends Node {
  type: 'TypeAnnotation';
  name: string;
  typeArguments: TypeAnnotation[];
  optional: boolean;
  nullable: boolean;
  arrayDepth: number;
}

export interface Parameter extends Node {
  type: 'Parameter';
  pattern: Pattern;
  typeAnnotation?: TypeAnnotation;
  defaultValue?: Expression;
  rest: boolean;
}

export type Pattern = Identifier | ObjectPattern | ArrayPattern | RestElement | AssignmentPattern;

export interface ObjectPattern extends Node {
  type: 'ObjectPattern';
  properties: Property[];
  rest?: RestElement;
}

export interface ArrayPattern extends Node {
  type: 'ArrayPattern';
  elements: (Pattern | null)[];
  rest?: RestElement;
}

export interface RestElement extends Node {
  type: 'RestElement';
  argument: Pattern;
}

export interface AssignmentPattern extends Node {
  type: 'AssignmentPattern';
  left: Pattern;
  right: Expression;
}

export interface Property extends Node {
  type: 'Property';
  key: Identifier | Literal;
  value: Expression;
  kind: 'init' | 'get' | 'set';
  method: boolean;
  shorthand: boolean;
  computed: boolean;
  decorators: Decorator[];
}

export interface Method extends Node {
  type: 'Method';
  key: Identifier;
  kind: 'constructor' | 'method' | 'get' | 'set';
  static: boolean;
  async: boolean;
  generator: boolean;
  params: Parameter[];
  returnType?: TypeAnnotation;
  body: BlockStatement;
  decorators: Decorator[];
}

export interface Decorator extends Node {
  type: 'Decorator';
  expression: Expression;
}

export interface TypeParameter extends Node {
  type: 'TypeParameter';
  name: string;
  constraint?: TypeAnnotation;
  default?: TypeAnnotation;
}

export function createSpan(start: number, end: number, file: string, lines: string[]): Span {
  let line = 1;
  let column = 1;
  for (let i = 0; i < start; i++) {
    if (lines[i] === '\n') {
      line++;
      column = 1;
    } else {
      column++;
    }
  }
  const startPos = { line, column, offset: start };

  line = 1;
  column = 1;
  for (let i = 0; i < end; i++) {
    if (lines[i] === '\n') {
      line++;
      column = 1;
    } else {
      column++;
    }
  }
  const endPos = { line, column, offset: end };

  return { start: startPos, end: endPos, file };
}

export function createNode<T extends Node>(type: T['type'], span: Span, props: Omit<T, 'type' | 'span'>): T {
  return { type, span, ...props } as T;
}