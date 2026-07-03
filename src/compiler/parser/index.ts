import { TokenType, Token } from '../lexer/index';
import {
  Program, Statement, Declaration, Expression, VariableDeclaration, VariableDeclarator,
  FunctionDeclaration, ClassDeclaration, InterfaceDeclaration, TypeAliasDeclaration,
  EnumDeclaration, ExpressionStatement, BlockStatement, IfStatement, WhileStatement,
  ForStatement, LoopStatement, BreakStatement, ContinueStatement, ReturnStatement,
  TryStatement, ThrowStatement, MatchStatement, MatchCase, CatchClause,
  ImportDeclaration, ExportDeclaration, ExportSpecifier,
  AssignmentExpression, AssignmentOperator, BinaryExpression, BinaryOperator,
  UnaryExpression, UnaryOperator, CallExpression, MemberExpression, IndexExpression,
  NewExpression, DeleteExpression, AwaitExpression, YieldExpression,
  LambdaExpression, ObjectLiteral, ArrayLiteral, Identifier, Literal,
  ThisExpression, SuperExpression, TypeAnnotation, Parameter, Property, Method,
  ClassBody, EnumMember, Decorator, Node, Span,
} from '../ast/index';
import { DiagnosticBag, Position } from '../diagnostics';

export class Parser {
  private tokens: Token[];
  private current = 0;
  private diagnostics: DiagnosticBag;

  constructor(tokens: Token[], diagnostics?: DiagnosticBag) {
    this.tokens = tokens;
    this.diagnostics = diagnostics ?? new DiagnosticBag();
  }

  parse(): Program {
    const body: Statement[] = [];
    const imports: ImportDeclaration[] = [];
    const exports: ExportDeclaration[] = [];

    while (!this.isAtEnd()) {
      const stmt = this.parseStatement();
      if (stmt) {
        body.push(stmt);
        if (stmt.type === 'ImportDeclaration' && !imports.some(i => i.source === (stmt as ImportDeclaration).source)) {
          imports.push(stmt as ImportDeclaration);
        }
        if (stmt.type === 'ExportDeclaration') {
          exports.push(stmt as ExportDeclaration);
        }
      }
    }

    const span = this.tokens.length > 1
      ? this.makeSpan(this.tokens[0], this.tokens[this.tokens.length - 1])
      : this.peek().span;

    return {
      type: 'Program',
      span,
      body,
      imports,
      exports,
    };
  }

  getDiagnostics(): DiagnosticBag {
    return this.diagnostics;
  }

  private parseStatement(): Statement | null {
    try {
      if (this.match(TokenType.IMPORT)) return this.parseImportDeclaration();
      if (this.match(TokenType.EXPORT)) return this.parseExportDeclaration();
      if (this.match(TokenType.LET, TokenType.CONST)) return this.parseVariableDeclaration();
      if (this.match(TokenType.FUN)) return this.parseFunctionDeclaration();
      if (this.match(TokenType.CLASS)) return this.parseClassDeclaration();
      if (this.match(TokenType.INTERFACE)) return this.parseInterfaceDeclaration();
      if (this.match(TokenType.TYPE)) return this.parseTypeAlias();
      if (this.match(TokenType.ENUM)) return this.parseEnumDeclaration();
      if (this.match(TokenType.IF)) return this.parseIfStatement();
      if (this.match(TokenType.WHILE)) return this.parseWhileStatement();
      if (this.match(TokenType.FOR)) return this.parseForStatement();
      if (this.match(TokenType.LOOP)) return this.parseLoopStatement();
      if (this.match(TokenType.BREAK)) return this.parseBreakStatement();
      if (this.match(TokenType.CONTINUE)) return this.parseContinueStatement();
      if (this.match(TokenType.RETURN)) return this.parseReturnStatement();
      if (this.match(TokenType.TRY)) return this.parseTryStatement();
      if (this.match(TokenType.THROW)) return this.parseThrowStatement();
      if (this.match(TokenType.MATCH)) return this.parseMatchStatement();
      if (this.match(TokenType.LEFT_BRACE)) return this.parseBlock(this.previous());
      if (this.match(TokenType.SEMICOLON)) return null;
      if (this.isAtEnd()) return null;

      return this.parseExpressionStatement();
    } catch (e) {
      if (e instanceof ParserPanic) {
        this.synchronize();
        return null;
      }
      throw e;
    }
  }

  private parseImportDeclaration(): ImportDeclaration {
    const start = this.previous();
    const specifiers: { imported: string; local: string }[] = [];

    if (this.match(TokenType.LEFT_BRACE)) {
      while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
        const imported = this.expect(TokenType.IDENTIFIER, "Expected identifier in import specifier").lexeme;
        let local = imported;
        if (this.match(TokenType.AS)) {
          local = this.expect(TokenType.IDENTIFIER, "Expected alias after 'as'").lexeme;
        }
        specifiers.push({ imported, local });
        this.match(TokenType.COMMA);
      }
      this.expect(TokenType.RIGHT_BRACE, "Expected '}' after import specifiers");
    } else if (this.check(TokenType.IDENTIFIER) && !this.checkKeywordAsFrom()) {
      const name = this.advance().lexeme;
      specifiers.push({ imported: 'default', local: name });
    } else {
      this.diagnostics.error("Expected import specifier", this.peek().span);
    }

    this.expect(TokenType.FROM, "Expected 'from' after import specifiers");
    const sourceToken = this.expect(TokenType.STRING, "Expected module path string");
    const source = sourceToken.literal as string;
    this.consumeSemicolon();

    return {
      type: 'ImportDeclaration',
      span: this.makeSpan(start, this.previous()),
      specifiers,
      source,
    };
  }

  private checkKeywordAsFrom(): boolean {
    if (this.current >= this.tokens.length) return false;
    const next = this.tokens[this.current];
    return next.type === TokenType.FROM;
  }

  private parseExportDeclaration(): ExportDeclaration {
    const start = this.previous();

    if (this.match(TokenType.LEFT_BRACE)) {
      const specifiers: ExportSpecifier[] = [];
      while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
        const local = this.expect(TokenType.IDENTIFIER, "Expected identifier in export specifier").lexeme;
        let exported = local;
        if (this.match(TokenType.AS)) {
          exported = this.expect(TokenType.IDENTIFIER, "Expected name after 'as'").lexeme;
        }
        specifiers.push({ local, exported });
        this.match(TokenType.COMMA);
      }
      this.expect(TokenType.RIGHT_BRACE, "Expected '}' after export specifiers");

      let source: string | undefined;
      if (this.match(TokenType.FROM)) {
        source = this.expect(TokenType.STRING, "Expected module path").literal as string;
      }

      this.consumeSemicolon();
      return {
        type: 'ExportDeclaration',
        span: this.makeSpan(start, this.previous()),
        specifiers,
        source,
      };
    }

    const declaration = this.parseDeclaration();
    return {
      type: 'ExportDeclaration',
      span: this.makeSpan(start, this.previous()),
      declaration,
    };
  }

  private parseDeclaration(): Declaration {
    if (this.match(TokenType.LET, TokenType.CONST)) return this.parseVariableDeclaration();
    if (this.match(TokenType.FUN)) return this.parseFunctionDeclaration();
    if (this.match(TokenType.CLASS)) return this.parseClassDeclaration();
    if (this.match(TokenType.INTERFACE)) return this.parseInterfaceDeclaration();
    if (this.match(TokenType.TYPE)) return this.parseTypeAlias();
    if (this.match(TokenType.ENUM)) return this.parseEnumDeclaration();

    const token = this.peek();
    this.diagnostics.error("Expected declaration", token.span);
    throw new ParserPanic();
  }

  private parseVariableDeclaration(): VariableDeclaration {
    const kindToken = this.previous();
    const kind = kindToken.type === TokenType.CONST ? 'const' : 'let' as const;
    const declarations: VariableDeclarator[] = [];

    do {
      const id = this.parseIdentifier();
      let typeAnnotation: TypeAnnotation | undefined;
      if (this.match(TokenType.COLON)) {
        typeAnnotation = this.parseTypeAnnotation();
      }
      let init: Expression | undefined;
      if (this.match(TokenType.EQUAL)) {
        init = this.parseAssignment();
      }
      declarations.push({ id, init, typeAnnotation });
    } while (this.match(TokenType.COMMA));

    this.consumeSemicolon();

    return {
      type: 'VariableDeclaration',
      span: this.makeSpan(kindToken, this.previous()),
      kind,
      declarations,
    };
  }

  private parseFunctionDeclaration(): FunctionDeclaration {
    const funToken = this.previous();
    const id = this.parseIdentifier();
    this.expect(TokenType.LEFT_PAREN, "Expected '(' after function name");
    const params = this.parseParameters();
    this.expect(TokenType.RIGHT_PAREN, "Expected ')' after parameters");

    let returnType: TypeAnnotation | undefined;
    if (this.match(TokenType.ARROW)) {
      returnType = this.parseTypeAnnotation();
    }

    this.expect(TokenType.LEFT_BRACE, "Expected '{' before function body");
    const body = this.parseBlock(this.previous());

    return {
      type: 'FunctionDeclaration',
      span: this.makeSpan(funToken, this.previous()),
      id,
      params,
      returnType,
      body,
      async: false,
      generator: false,
      decorators: [],
    };
  }

  private parseClassDeclaration(): ClassDeclaration {
    const classToken = this.previous();
    const id = this.parseIdentifier();

    let superClass: Identifier | undefined;
    if (this.match(TokenType.INHERITS)) {
      superClass = this.parseIdentifier();
    }

    const implementsList: Identifier[] = [];
    this.expect(TokenType.LEFT_BRACE, "Expected '{' before class body");

    const properties: Property[] = [];
    const methods: Method[] = [];

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      if (this.match(TokenType.SEMICOLON)) continue;

      const decorators = this.parseDecorators();
      const isStatic = this.match(TokenType.STATIC);

      if (this.check(TokenType.IDENTIFIER)) {
        const nameToken = this.advance();
        const isConstructor = nameToken.lexeme === 'constructor';
        const key: Identifier = {
          type: 'Identifier',
          span: nameToken.span,
          name: nameToken.lexeme,
        };

        if (this.check(TokenType.LEFT_PAREN)) {
          this.advance();
          const mParams = this.parseParameters();
          this.expect(TokenType.RIGHT_PAREN, "Expected ')' after method parameters");

          let mReturnType: TypeAnnotation | undefined;
          if (this.match(TokenType.ARROW)) {
            mReturnType = this.parseTypeAnnotation();
          }

          this.expect(TokenType.LEFT_BRACE, "Expected '{' before method body");
          const mBody = this.parseBlock(this.previous());

          methods.push({
            type: 'Method',
            span: this.makeSpan(nameToken, this.previous()),
            key,
            kind: isConstructor ? 'constructor' : 'method',
            static: isStatic,
            async: false,
            generator: false,
            params: mParams,
            returnType: mReturnType,
            body: mBody,
            decorators,
          });
        } else if (this.match(TokenType.EQUAL)) {
          const value = this.parseExpression();
          properties.push({
            type: 'Property',
            span: this.makeSpan(nameToken, this.previous()),
            key,
            value,
            kind: 'init',
            method: false,
            shorthand: false,
            computed: false,
            decorators,
          });
          this.consumeSemicolon();
        } else {
          properties.push({
            type: 'Property',
            span: nameToken.span,
            key,
            value: { type: 'Identifier', span: nameToken.span, name: nameToken.lexeme },
            kind: 'init',
            method: false,
            shorthand: true,
            computed: false,
            decorators,
          });
          this.consumeSemicolon();
        }
      } else {
        this.diagnostics.error("Expected class member", this.peek().span);
        this.advance();
      }
    }

    this.expect(TokenType.RIGHT_BRACE, "Expected '}' after class body");

    return {
      type: 'ClassDeclaration',
      span: this.makeSpan(classToken, this.previous()),
      id,
      superClass,
      implements: implementsList,
      body: { properties, methods },
      decorators: [],
      abstract: false,
    };
  }

  private parseInterfaceDeclaration(): InterfaceDeclaration {
    const start = this.previous();
    const id = this.parseIdentifier();
    const extendsList: Identifier[] = [];

    this.expect(TokenType.LEFT_BRACE, "Expected '{' before interface body");
    const properties: Property[] = [];
    const methods: Method[] = [];

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      if (this.match(TokenType.SEMICOLON)) continue;
      if (this.check(TokenType.IDENTIFIER)) {
        const nameToken = this.advance();
        const key: Identifier = {
          type: 'Identifier',
          span: nameToken.span,
          name: nameToken.lexeme,
        };

        if (this.check(TokenType.LEFT_PAREN)) {
          this.advance();
          const mParams = this.parseParameters();
          this.expect(TokenType.RIGHT_PAREN, "Expected ')' after parameters");
          let mReturnType: TypeAnnotation | undefined;
          if (this.match(TokenType.ARROW)) {
            mReturnType = this.parseTypeAnnotation();
          }
          methods.push({
            type: 'Method',
            span: this.makeSpan(nameToken, this.previous()),
            key,
            kind: 'method',
            static: false,
            async: false,
            generator: false,
            params: mParams,
            returnType: mReturnType,
            body: { type: 'BlockStatement', span: this.previous().span, body: [] },
            decorators: [],
          });
          this.consumeSemicolon();
        } else {
          let value: Expression = { type: 'Identifier', span: key.span, name: key.name };
          if (this.match(TokenType.COLON)) {
            value = { type: 'Identifier', span: this.previous().span, name: this.previous().lexeme };
          }
          properties.push({
            type: 'Property',
            span: key.span,
            key,
            value,
            kind: 'init',
            method: false,
            shorthand: false,
            computed: false,
            decorators: [],
          });
          this.consumeSemicolon();
        }
      } else {
        this.advance();
      }
    }

    this.expect(TokenType.RIGHT_BRACE, "Expected '}' after interface body");

    return {
      type: 'InterfaceDeclaration',
      span: this.makeSpan(start, this.previous()),
      id,
      extends: extendsList,
      body: { properties, methods },
    };
  }

  private parseTypeAlias(): TypeAliasDeclaration {
    const start = this.previous();
    const id = this.parseIdentifier();
    const typeParameters: never[] = [];

    this.expect(TokenType.EQUAL, "Expected '=' in type alias");
    const annotation = this.parseTypeAnnotation();
    this.consumeSemicolon();

    return {
      type: 'TypeAliasDeclaration',
      span: this.makeSpan(start, this.previous()),
      id,
      typeParameters,
      annotation,
    };
  }

  private parseEnumDeclaration(): EnumDeclaration {
    const start = this.previous();
    const id = this.parseIdentifier();
    const members: EnumMember[] = [];

    this.expect(TokenType.LEFT_BRACE, "Expected '{' before enum body");

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      if (this.match(TokenType.SEMICOLON)) continue;
      const memberId = this.parseIdentifier();
      let init: Expression | undefined;
      if (this.match(TokenType.EQUAL)) {
        init = this.parseAssignment();
      }
      members.push({ id: memberId, init });
      this.match(TokenType.COMMA);
    }

    this.expect(TokenType.RIGHT_BRACE, "Expected '}' after enum body");

    return {
      type: 'EnumDeclaration',
      span: this.makeSpan(start, this.previous()),
      id,
      members,
    };
  }

  private parseBlock(openBrace: Token): BlockStatement {
    const body: Statement[] = [];

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      const stmt = this.parseStatement();
      if (stmt) body.push(stmt);
    }

    const closeBrace = this.expect(TokenType.RIGHT_BRACE, "Expected '}' at end of block");

    return {
      type: 'BlockStatement',
      span: this.makeSpan(openBrace, closeBrace),
      body,
    };
  }

  private parseIfStatement(): IfStatement {
    const start = this.previous();
    this.expect(TokenType.LEFT_PAREN, "Expected '(' after 'if'");
    const test = this.parseExpression();
    this.expect(TokenType.RIGHT_PAREN, "Expected ')' after if condition");

    const consequent = this.parseStatement() ?? this.errorStatement(start);

    const alternate = this.parseElseOrElif();

    return {
      type: 'IfStatement',
      span: alternate
        ? this.makeSpan(start, alternate.span.end.line > start.span.end.line ? { span: alternate.span } as Token : start)
        : this.makeSpan(start, { span: this.previous().span } as Token),
      test,
      consequent,
      alternate,
    };
  }

  private parseElseOrElif(): Statement | undefined {
    if (this.match(TokenType.ELIF)) {
      const elifToken = this.previous();
      this.expect(TokenType.LEFT_PAREN, "Expected '(' after 'elif'");
      const test = this.parseExpression();
      this.expect(TokenType.RIGHT_PAREN, "Expected ')' after elif condition");
      const consequent = this.parseStatement() ?? this.errorStatement(elifToken);
      const alternate = this.parseElseOrElif();

      return {
        type: 'IfStatement',
        span: this.makeSpan(elifToken, this.previous()),
        test,
        consequent,
        alternate,
      };
    }

    if (this.match(TokenType.ELSE)) {
      return this.parseStatement() ?? this.errorStatement(this.previous());
    }

    return undefined;
  }

  private parseWhileStatement(): WhileStatement {
    const start = this.previous();
    this.expect(TokenType.LEFT_PAREN, "Expected '(' after 'while'");
    const test = this.parseExpression();
    this.expect(TokenType.RIGHT_PAREN, "Expected ')' after while condition");
    const body = this.parseStatement() ?? this.errorStatement(start);

    return {
      type: 'WhileStatement',
      span: this.makeSpan(start, this.previous()),
      test,
      body,
    };
  }

  private parseForStatement(): ForStatement {
    const start = this.previous();
    this.expect(TokenType.LEFT_PAREN, "Expected '(' after 'for'");

    let init: VariableDeclaration | ExpressionStatement | undefined;
    if (!this.check(TokenType.SEMICOLON)) {
      if (this.match(TokenType.LET, TokenType.CONST)) {
        const kind = this.previous().type === TokenType.CONST ? 'const' : 'let' as const;
        const declarations: VariableDeclarator[] = [];
        do {
          const id = this.parseIdentifier();
          let typeAnnotation: TypeAnnotation | undefined;
          if (this.match(TokenType.COLON)) {
            typeAnnotation = this.parseTypeAnnotation();
          }
          let initExpr: Expression | undefined;
          if (this.match(TokenType.EQUAL)) {
            initExpr = this.parseExpression();
          }
          declarations.push({ id, init: initExpr, typeAnnotation });
        } while (this.match(TokenType.COMMA));
        init = {
          type: 'VariableDeclaration',
          span: this.makeSpan(this.peer(-1), this.previous()),
          kind,
          declarations,
        };
      } else {
        const expr = this.parseAssignment();
        init = {
          type: 'ExpressionStatement',
          span: expr.span,
          expression: expr,
        };
      }
    }

    this.expect(TokenType.SEMICOLON, "Expected ';' in for loop");

    let test: Expression | undefined;
    if (!this.check(TokenType.SEMICOLON)) {
      test = this.parseAssignment();
    }

    this.expect(TokenType.SEMICOLON, "Expected ';' in for loop");

    let update: Expression | undefined;
    if (!this.check(TokenType.RIGHT_PAREN)) {
      update = this.parseAssignment();
    }

    this.expect(TokenType.RIGHT_PAREN, "Expected ')' after for clauses");
    const body = this.parseStatement() ?? this.errorStatement(start);

    return {
      type: 'ForStatement',
      span: this.makeSpan(start, this.previous()),
      init,
      test,
      update,
      body,
    };
  }

  private parseLoopStatement(): LoopStatement {
    const start = this.previous();
    const body = this.parseStatement() ?? this.errorStatement(start);

    return {
      type: 'LoopStatement',
      span: this.makeSpan(start, this.previous()),
      body,
    };
  }

  private parseBreakStatement(): BreakStatement {
    const start = this.previous();
    let label: Identifier | undefined;
    if (this.check(TokenType.IDENTIFIER)) {
      label = this.parseIdentifier();
    }
    this.consumeSemicolon();

    return {
      type: 'BreakStatement',
      span: this.makeSpan(start, this.previous()),
      label,
    };
  }

  private parseContinueStatement(): ContinueStatement {
    const start = this.previous();
    let label: Identifier | undefined;
    if (this.check(TokenType.IDENTIFIER)) {
      label = this.parseIdentifier();
    }
    this.consumeSemicolon();

    return {
      type: 'ContinueStatement',
      span: this.makeSpan(start, this.previous()),
      label,
    };
  }

  private parseReturnStatement(): ReturnStatement {
    const start = this.previous();

    let argument: Expression | undefined;
    if (!this.check(TokenType.SEMICOLON) && !this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      argument = this.parseAssignment();
    }

    this.consumeSemicolon();

    return {
      type: 'ReturnStatement',
      span: this.makeSpan(start, this.previous()),
      argument,
    };
  }

  private parseTryStatement(): TryStatement {
    const start = this.previous();
    this.expect(TokenType.LEFT_BRACE, "Expected '{' after 'try'");
    const block = this.parseBlock(this.previous());

    let handler: CatchClause | undefined;
    if (this.match(TokenType.CATCH)) {
      const catchToken = this.previous();
      let param: Identifier;
      if (this.match(TokenType.LEFT_PAREN)) {
        param = this.parseIdentifier();
        this.expect(TokenType.RIGHT_PAREN, "Expected ')' after catch parameter");
      } else {
        param = {
          type: 'Identifier',
          span: { ...this.peek().span },
          name: '@error',
        };
      }
      this.expect(TokenType.LEFT_BRACE, "Expected '{' after catch");
      const catchBody = this.parseBlock(this.previous());
      handler = {
        type: 'CatchClause',
        span: this.makeSpan(catchToken, this.previous()),
        param,
        body: catchBody,
      };
    }

    let finalizer: BlockStatement | undefined;
    if (this.match(TokenType.FINALLY)) {
      this.expect(TokenType.LEFT_BRACE, "Expected '{' after 'finally'");
      finalizer = this.parseBlock(this.previous());
    }

    if (!handler && !finalizer) {
      this.diagnostics.error("Expected 'catch' or 'finally'", this.peek().span);
    }

    return {
      type: 'TryStatement',
      span: this.makeSpan(start, this.previous()),
      block,
      handler,
      finalizer,
    };
  }

  private parseThrowStatement(): ThrowStatement {
    const start = this.previous();
    const argument = this.parseExpression();
    this.consumeSemicolon();

    return {
      type: 'ThrowStatement',
      span: this.makeSpan(start, this.previous()),
      argument,
    };
  }

  private parseMatchStatement(): MatchStatement {
    const start = this.previous();
    const discriminant = this.parseExpression();

    this.expect(TokenType.LEFT_BRACE, "Expected '{' after match expression");
    const cases: MatchCase[] = [];

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      if (this.match(TokenType.DEFAULT)) {
        this.expect(TokenType.COLON, "Expected ':' after 'default'");
        const consequent: Statement[] = [];
        while (!this.check(TokenType.RIGHT_BRACE) && !this.check(TokenType.DEFAULT) && !this.check(TokenType.CASE) && !this.isAtEnd()) {
          const stmt = this.parseStatement();
          if (stmt) consequent.push(stmt);
        }
        cases.push({
          type: 'MatchCase',
          span: this.makeSpan(start, this.previous()),
          test: { type: 'Identifier' as const, span: this.peek().span, name: 'default' },
          consequent,
        });
      } else if (this.match(TokenType.CASE)) {
        const test = this.parseExpression();
        this.expect(TokenType.COLON, "Expected ':' after case expression");
        const consequent: Statement[] = [];
        while (!this.check(TokenType.RIGHT_BRACE) && !this.check(TokenType.DEFAULT) && !this.check(TokenType.CASE) && !this.isAtEnd()) {
          const stmt = this.parseStatement();
          if (stmt) consequent.push(stmt);
        }
        cases.push({
          type: 'MatchCase',
          span: this.makeSpan(this.previous(), this.previous()),
          test,
          consequent,
        });
      } else {
        this.diagnostics.error("Expected 'case' or 'default' in match", this.peek().span);
        this.advance();
      }
    }

    this.expect(TokenType.RIGHT_BRACE, "Expected '}' after match");

    return {
      type: 'MatchStatement',
      span: this.makeSpan(start, this.previous()),
      discriminant,
      cases,
    };
  }

  private parseExpressionStatement(): ExpressionStatement {
    const expr = this.parseExpression();
    this.consumeSemicolon();

    return {
      type: 'ExpressionStatement',
      span: expr.span,
      expression: expr,
    };
  }

  private parseExpression(): Expression {
    let expr = this.parseAssignment();

    while (this.match(TokenType.COMMA)) {
      const right = this.parseAssignment();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: ',',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseAssignment(): Expression {
    const expr = this.parseLogicalOr();

    const assignmentOps: [TokenType, AssignmentOperator][] = [
      [TokenType.EQUAL, '='],
      [TokenType.PLUS_EQUALS, '+='],
      [TokenType.MINUS_EQUALS, '-='],
      [TokenType.STAR_EQUALS, '*='],
      [TokenType.SLASH_EQUALS, '/='],
      [TokenType.PERCENT_EQUALS, '%='],
    ];

    for (const [tokenType, op] of assignmentOps) {
      if (this.match(tokenType)) {
        const right = this.parseAssignment();
        return {
          type: 'AssignmentExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: op,
          left: expr,
          right,
        };
      }
    }

    return expr;
  }

  private parseLogicalOr(): Expression {
    let expr = this.parseLogicalAnd();

    while (this.match(TokenType.PIPE_PIPE)) {
      const opToken = this.previous();
      const right = this.parseLogicalAnd();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: '||',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseLogicalAnd(): Expression {
    let expr = this.parseBitwiseOr();

    while (this.match(TokenType.AMPERSAND_AMPERSAND)) {
      const right = this.parseBitwiseOr();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: '&&',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseBitwiseOr(): Expression {
    let expr = this.parseBitwiseXor();

    while (this.match(TokenType.PIPE)) {
      const right = this.parseBitwiseXor();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: '|',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseBitwiseXor(): Expression {
    let expr = this.parseBitwiseAnd();

    while (this.match(TokenType.CARET)) {
      const right = this.parseBitwiseAnd();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: '^',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseBitwiseAnd(): Expression {
    let expr = this.parseEquality();

    while (this.match(TokenType.AMPERSAND)) {
      const right = this.parseEquality();
      expr = {
        type: 'BinaryExpression',
        span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
        operator: '&',
        left: expr,
        right,
      };
    }

    return expr;
  }

  private parseEquality(): Expression {
    let expr = this.parseComparison();

    while (true) {
      if (this.match(TokenType.EQUAL_EQUAL)) {
        const right = this.parseComparison();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '==',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.BANG_EQUAL)) {
        const right = this.parseComparison();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '!=',
          left: expr,
          right,
        };
      } else {
        break;
      }
    }

    return expr;
  }

  private parseComparison(): Expression {
    let expr = this.parseShift();

    while (true) {
      if (this.match(TokenType.LESS)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '<',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.LESS_EQUAL)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '<=',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.GREATER)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '>',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.GREATER_EQUAL)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '>=',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.IN)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: 'in',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.IS)) {
        const right = this.parseShift();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: 'is',
          left: expr,
          right,
        };
      } else {
        break;
      }
    }

    return expr;
  }

  private parseShift(): Expression {
    let expr = this.parseAdditive();

    while (true) {
      if (this.match(TokenType.SHIFT_LEFT)) {
        const right = this.parseAdditive();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '<<',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.SHIFT_RIGHT)) {
        const right = this.parseAdditive();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '>>',
          left: expr,
          right,
        };
      } else {
        break;
      }
    }

    return expr;
  }

  private parseAdditive(): Expression {
    let expr = this.parseMultiplicative();

    while (true) {
      if (this.match(TokenType.PLUS)) {
        const right = this.parseMultiplicative();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '+',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.MINUS)) {
        const right = this.parseMultiplicative();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '-',
          left: expr,
          right,
        };
      } else {
        break;
      }
    }

    return expr;
  }

  private parseMultiplicative(): Expression {
    let expr = this.parseUnary();

    while (true) {
      if (this.match(TokenType.STAR)) {
        const right = this.parseUnary();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '*',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.SLASH)) {
        const right = this.parseUnary();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '/',
          left: expr,
          right,
        };
      } else if (this.match(TokenType.PERCENT)) {
        const right = this.parseUnary();
        expr = {
          type: 'BinaryExpression',
          span: this.makeSpan({ span: expr.span } as Token, { span: right.span } as Token),
          operator: '%',
          left: expr,
          right,
        };
      } else {
        break;
      }
    }

    return expr;
  }

  private parseUnary(): Expression {
    const unaryOps: [TokenType, UnaryOperator][] = [
      [TokenType.BANG, '!'],
      [TokenType.MINUS, '-'],
      [TokenType.PLUS, '+'],
      [TokenType.TILDE, '~'],
      [TokenType.PLUS_PLUS, '++'],
      [TokenType.MINUS_MINUS, '--'],
      [TokenType.NOT, '!'],
      [TokenType.DELETE, 'delete'],
      [TokenType.AWAIT, 'await'],
      [TokenType.YIELD, 'yield'],
    ];

    for (const [type, op] of unaryOps) {
      if (this.match(type)) {
        const opToken = this.previous();
        const argument = this.parseUnary();
        let span: Span;
        if ('start' in argument && 'end' in argument) {
          span = this.makeSpan(opToken, { span: (argument as unknown as { span: Span }).span } as Token);
        } else {
          span = opToken.span;
        }

        if (op === 'delete') {
          return {
            type: 'DeleteExpression',
            span,
            argument,
          };
        }
        if (op === 'await') {
          return {
            type: 'AwaitExpression',
            span,
            argument,
          };
        }
        if (op === 'yield') {
          return {
            type: 'YieldExpression',
            span,
            argument,
            delegate: false,
          };
        }

        return {
          type: 'UnaryExpression',
          span,
          operator: op,
          argument,
          prefix: true,
        };
      }
    }

    return this.parsePostfix();
  }

  private parsePostfix(): Expression {
    let expr = this.parsePrimary();

    while (true) {
      if (this.match(TokenType.LEFT_PAREN)) {
        const args = this.parseArguments();
        const closeParen = this.expect(TokenType.RIGHT_PAREN, "Expected ')' after arguments");
        expr = {
          type: 'CallExpression',
          span: this.makeSpan({ span: expr.span } as Token, closeParen),
          callee: expr,
          arguments: args,
          optional: false,
          typeArguments: [],
        };
      } else if (this.match(TokenType.DOT)) {
        const prop = this.expect(TokenType.IDENTIFIER, "Expected property name after '.'");
        const propId: Identifier = {
          type: 'Identifier',
          span: prop.span,
          name: prop.lexeme,
        };
        expr = {
          type: 'MemberExpression',
          span: this.makeSpan({ span: expr.span } as Token, prop),
          object: expr,
          property: propId,
          computed: false,
          optional: false,
        };
      } else if (this.match(TokenType.LEFT_BRACKET)) {
        const index = this.parseExpression();
        const closeBracket = this.expect(TokenType.RIGHT_BRACKET, "Expected ']' after index");
        expr = {
          type: 'IndexExpression',
          span: this.makeSpan({ span: expr.span } as Token, closeBracket),
          object: expr,
          index,
          optional: false,
        };
      } else if (this.match(TokenType.QUESTION_DOT)) {
        if (this.match(TokenType.LEFT_PAREN)) {
          const args = this.parseArguments();
          const closeParen = this.expect(TokenType.RIGHT_PAREN, "Expected ')' after arguments");
          expr = {
            type: 'CallExpression',
            span: this.makeSpan({ span: expr.span } as Token, closeParen),
            callee: expr,
            arguments: args,
            optional: true,
            typeArguments: [],
          };
        } else if (this.check(TokenType.IDENTIFIER)) {
          const prop = this.advance();
          const propId: Identifier = {
            type: 'Identifier',
            span: prop.span,
            name: prop.lexeme,
          };
          expr = {
            type: 'MemberExpression',
            span: this.makeSpan({ span: expr.span } as Token, prop),
            object: expr,
            property: propId,
            computed: false,
            optional: true,
          };
        } else {
          this.diagnostics.error("Expected property or call after '?.'", this.peek().span);
          break;
        }
      } else {
        break;
      }
    }

    return expr;
  }

  private parsePrimary(): Expression {
    if (this.match(TokenType.NUMBER)) {
      const token = this.previous();
      return {
        type: 'Literal',
        span: token.span,
        value: token.literal as number,
        raw: token.lexeme,
      };
    }

    if (this.match(TokenType.STRING)) {
      const token = this.previous();
      return {
        type: 'Literal',
        span: token.span,
        value: token.literal as string,
        raw: token.lexeme,
      };
    }

    if (this.match(TokenType.TRUE)) {
      const token = this.previous();
      return {
        type: 'Literal',
        span: token.span,
        value: true,
        raw: token.lexeme,
      };
    }

    if (this.match(TokenType.FALSE)) {
      const token = this.previous();
      return {
        type: 'Literal',
        span: token.span,
        value: false,
        raw: token.lexeme,
      };
    }

    if (this.match(TokenType.NIL)) {
      const token = this.previous();
      return {
        type: 'Literal',
        span: token.span,
        value: null,
        raw: token.lexeme,
      };
    }

    if (this.match(TokenType.IDENTIFIER)) {
      const token = this.previous();
      return {
        type: 'Identifier',
        span: token.span,
        name: token.lexeme,
      };
    }

    if (this.match(TokenType.LEFT_PAREN)) {
      const expr = this.parseExpression();
      this.expect(TokenType.RIGHT_PAREN, "Expected ')' after expression");
      return expr;
    }

    if (this.match(TokenType.LEFT_BRACKET)) {
      return this.parseArrayLiteral();
    }

    if (this.match(TokenType.LEFT_BRACE)) {
      return this.parseObjectLiteral();
    }

    if (this.match(TokenType.FUN)) {
      return this.parseFunctionExpression();
    }

    if (this.match(TokenType.PIPE)) {
      return this.parseLambdaExpression();
    }

    if (this.match(TokenType.ARROW)) {
      const arrowToken = this.previous();
      const body = this.parseExpression();
      return {
        type: 'LambdaExpression',
        span: this.makeSpan(arrowToken, { span: body.span } as Token),
        params: [],
        body,
        async: false,
        expression: true,
      };
    }

    if (this.match(TokenType.CLASS)) {
      return this.parseAnonymousClass();
    }

    if (this.match(TokenType.NEW)) {
      return this.parseNewExpression();
    }

    if (this.match(TokenType.THIS)) {
      const token = this.previous();
      return {
        type: 'ThisExpression',
        span: token.span,
      };
    }

    if (this.match(TokenType.SUPER)) {
      const token = this.previous();
      return {
        type: 'SuperExpression',
        span: token.span,
      };
    }

    if (this.match(TokenType.SEMICOLON)) {
      this.diagnostics.error("Unexpected semicolon", this.previous().span);
      return { type: 'Literal', span: this.previous().span, value: null, raw: 'null' };
    }

    return this.errorExpression();
  }

  private parseArrayLiteral(): Expression {
    const openBracket = this.previous();
    const elements: Expression[] = [];

    if (!this.check(TokenType.RIGHT_BRACKET)) {
      elements.push(this.parseAssignment());
      while (this.match(TokenType.COMMA)) {
        if (this.check(TokenType.RIGHT_BRACKET)) break;
        elements.push(this.parseAssignment());
      }
    }

    const closeBracket = this.expect(TokenType.RIGHT_BRACKET, "Expected ']' after array elements");

    return {
      type: 'ArrayLiteral',
      span: this.makeSpan(openBracket, closeBracket),
      elements,
    };
  }

  private parseObjectLiteral(): Expression {
    const openBrace = this.previous();
    const properties: Property[] = [];

    if (!this.check(TokenType.RIGHT_BRACE)) {
      properties.push(this.parseProperty());
      while (this.match(TokenType.COMMA)) {
        if (this.check(TokenType.RIGHT_BRACE)) break;
        properties.push(this.parseProperty());
      }
    }

    const closeBrace = this.expect(TokenType.RIGHT_BRACE, "Expected '}' after object properties");

    return {
      type: 'ObjectLiteral',
      span: this.makeSpan(openBrace, closeBrace),
      properties,
    };
  }

  private parseProperty(): Property {
    if (this.match(TokenType.IDENTIFIER)) {
      const keyToken = this.previous();
      const key: Identifier = {
        type: 'Identifier',
        span: keyToken.span,
        name: keyToken.lexeme,
      };

      if (this.match(TokenType.COLON)) {
        const value = this.parseAssignment();
        return {
          type: 'Property',
          span: this.makeSpan(keyToken, { span: value.span } as Token),
          key,
          value,
          kind: 'init',
          method: false,
          shorthand: false,
          computed: false,
          decorators: [],
        };
      }

      return {
        type: 'Property',
        span: keyToken.span,
        key,
        value: { ...key },
        kind: 'init',
        method: false,
        shorthand: true,
        computed: false,
        decorators: [],
      };
    }

    if (this.match(TokenType.STRING)) {
      const keyToken = this.previous();
      const key: Literal = {
        type: 'Literal',
        span: keyToken.span,
        value: keyToken.literal as string,
        raw: keyToken.lexeme,
      };
      this.expect(TokenType.COLON, "Expected ':' after property key");
      const value = this.parseExpression();
      return {
        type: 'Property',
        span: this.makeSpan(keyToken, { span: value.span } as Token),
        key,
        value,
        kind: 'init',
        method: false,
        shorthand: false,
        computed: false,
        decorators: [],
      };
    }

    if (this.match(TokenType.NUMBER)) {
      const keyToken = this.previous();
      const key: Literal = {
        type: 'Literal',
        span: keyToken.span,
        value: keyToken.literal as number,
        raw: keyToken.lexeme,
      };
      this.expect(TokenType.COLON, "Expected ':' after property key");
      const value = this.parseExpression();
      return {
        type: 'Property',
        span: this.makeSpan(keyToken, { span: value.span } as Token),
        key,
        value,
        kind: 'init',
        method: false,
        shorthand: false,
        computed: false,
        decorators: [],
      };
    }

    const token = this.peek();
    this.diagnostics.error("Expected property name", token.span);
    this.advance();
    const dummy: Identifier = { type: 'Identifier', span: token.span, name: '@error' };
    return {
      type: 'Property',
      span: token.span,
      key: dummy,
      value: dummy,
      kind: 'init',
      method: false,
      shorthand: false,
      computed: false,
      decorators: [],
    };
  }

  private parseFunctionExpression(): Expression {
    const funToken = this.previous();
    let id: Identifier | undefined;

    if (this.check(TokenType.IDENTIFIER) && !this.checkLeftParenAfter()) {
      id = this.parseIdentifier();
    }

    this.expect(TokenType.LEFT_PAREN, "Expected '(' after 'fun'");
    const params = this.parseParameters();
    this.expect(TokenType.RIGHT_PAREN, "Expected ')' after parameters");

    let returnType: TypeAnnotation | undefined;
    if (this.match(TokenType.ARROW)) {
      returnType = this.parseTypeAnnotation();
    }

    this.expect(TokenType.LEFT_BRACE, "Expected '{' before function body");
    const body = this.parseBlock(this.previous());

    return {
      type: 'LambdaExpression' as const,
      span: this.makeSpan(funToken, this.previous()),
      params,
      returnType,
      body,
      async: false,
      expression: false,
    } as Expression;
  }

  private checkLeftParenAfter(): boolean {
    for (let i = this.current; i < this.tokens.length; i++) {
      if (this.tokens[i].type === TokenType.LEFT_PAREN) return true;
      if (this.tokens[i].type !== TokenType.IDENTIFIER) return false;
    }
    return false;
  }

  private parseLambdaExpression(): Expression {
    const pipeToken = this.previous();
    const params: Parameter[] = [];

    if (!this.check(TokenType.PIPE)) {
      params.push(...this.parseLambdaParams());
    }

    this.expect(TokenType.PIPE, "Expected '|' after lambda parameters");

    let body: Expression | BlockStatement;
    let expression = false;

    if (this.match(TokenType.ARROW)) {
      body = this.parseExpression();
      expression = true;
    } else if (this.match(TokenType.LEFT_BRACE)) {
      body = this.parseBlock(this.previous());
    } else {
      const token = this.peek();
      this.diagnostics.error("Expected '->' or '{' after lambda '|'", token.span);
      body = {
        type: 'BlockStatement',
        span: token.span,
        body: [],
      };
    }

    return {
      type: 'LambdaExpression',
      span: this.makeSpan(pipeToken, this.previous()),
      params,
      body,
      async: false,
      expression,
    };
  }

  private parseLambdaParams(): Parameter[] {
    const params: Parameter[] = [];

    if (this.check(TokenType.IDENTIFIER)) {
      const idToken = this.advance();
      params.push({
        type: 'Parameter',
        span: idToken.span,
        pattern: { type: 'Identifier', span: idToken.span, name: idToken.lexeme },
        rest: false,
      });
    }

    while (this.match(TokenType.COMMA)) {
      if (this.check(TokenType.PIPE)) break;
      const idToken = this.expect(TokenType.IDENTIFIER, "Expected parameter name");
      params.push({
        type: 'Parameter',
        span: idToken.span,
        pattern: { type: 'Identifier', span: idToken.span, name: idToken.lexeme },
        rest: false,
      });
    }

    return params;
  }

  private parseAnonymousClass(): Expression {
    const classToken = this.previous();
    let id: Identifier | undefined;
    if (this.check(TokenType.IDENTIFIER)) {
      id = this.parseIdentifier();
    }

    let superClass: Identifier | undefined;
    if (this.match(TokenType.INHERITS)) {
      superClass = this.parseIdentifier();
    }

    this.expect(TokenType.LEFT_BRACE, "Expected '{' before class body");

    const properties: Property[] = [];
    const methods: Method[] = [];

    while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
      if (this.match(TokenType.SEMICOLON)) continue;
      if (this.check(TokenType.IDENTIFIER)) {
        const nameToken = this.advance();
        const key: Identifier = { type: 'Identifier', span: nameToken.span, name: nameToken.lexeme };

        if (this.check(TokenType.LEFT_PAREN)) {
          this.advance();
          const mParams = this.parseParameters();
          this.expect(TokenType.RIGHT_PAREN, "Expected ')' after method parameters");
          let mReturnType: TypeAnnotation | undefined;
          if (this.match(TokenType.ARROW)) {
            mReturnType = this.parseTypeAnnotation();
          }
          this.expect(TokenType.LEFT_BRACE, "Expected '{' before method body");
          const mBody = this.parseBlock(this.previous());
          methods.push({
            type: 'Method',
            span: this.makeSpan(nameToken, this.previous()),
            key,
            kind: 'method',
            static: false,
            async: false,
            generator: false,
            params: mParams,
            returnType: mReturnType,
            body: mBody,
            decorators: [],
          });
        } else {
          properties.push({
            type: 'Property',
            span: nameToken.span,
            key,
            value: key,
            kind: 'init',
            method: false,
            shorthand: true,
            computed: false,
            decorators: [],
          });
        }
      } else {
        this.advance();
      }
    }

    this.expect(TokenType.RIGHT_BRACE, "Expected '}' after class body");

    return {
      type: 'ClassDeclaration',
      span: this.makeSpan(classToken, this.previous()),
      id: id ?? { type: 'Identifier', span: classToken.span, name: '@anonymous' },
      superClass,
      implements: [],
      body: { properties, methods },
      decorators: [],
      abstract: false,
    };
  }

  private parseNewExpression(): Expression {
    const newToken = this.previous();
    const callee = this.parsePrimary();
    const args: Expression[] = [];

    if (this.match(TokenType.LEFT_PAREN)) {
      args.push(...this.parseArguments());
      this.expect(TokenType.RIGHT_PAREN, "Expected ')' after constructor arguments");
    }

    return {
      type: 'NewExpression',
      span: this.makeSpan(newToken, this.previous()),
      callee,
      arguments: args,
      typeArguments: [],
    };
  }

  private parseArguments(): Expression[] {
    const args: Expression[] = [];

    if (!this.check(TokenType.RIGHT_PAREN)) {
      args.push(this.parseAssignment());
      while (this.match(TokenType.COMMA)) {
        if (this.check(TokenType.RIGHT_PAREN)) break;
        args.push(this.parseAssignment());
      }
    }

    return args;
  }

  private parseParameters(): Parameter[] {
    const params: Parameter[] = [];

    if (!this.check(TokenType.RIGHT_PAREN)) {
      params.push(this.parseParameter());
      while (this.match(TokenType.COMMA)) {
        if (this.check(TokenType.RIGHT_PAREN)) break;
        params.push(this.parseParameter());
      }
    }

    return params;
  }

  private parseParameter(): Parameter {
    let rest = false;
    if (this.match(TokenType.DOT_DOT_DOT)) {
      rest = true;
    }

    const pattern = this.parsePattern();

    let typeAnnotation: TypeAnnotation | undefined;
    if (this.match(TokenType.COLON)) {
      typeAnnotation = this.parseTypeAnnotation();
    }

    let defaultValue: Expression | undefined;
    if (this.match(TokenType.EQUAL)) {
      defaultValue = this.parseExpression();
    }

    return {
      type: 'Parameter',
      span: pattern.span,
      pattern,
      typeAnnotation,
      defaultValue,
      rest,
    };
  }

  private parsePattern(): import('../ast/index').Pattern {
    if (this.check(TokenType.IDENTIFIER)) {
      const token = this.advance();
      return {
        type: 'Identifier',
        span: token.span,
        name: token.lexeme,
      };
    }
    if (this.match(TokenType.LEFT_BRACE)) {
      const props: Property[] = [];
      const start = this.previous();
      while (!this.check(TokenType.RIGHT_BRACE) && !this.isAtEnd()) {
        const propToken = this.expect(TokenType.IDENTIFIER, "Expected property name in destructuring");
        props.push({
          type: 'Property',
          span: propToken.span,
          key: { type: 'Identifier', span: propToken.span, name: propToken.lexeme },
          value: { type: 'Identifier', span: propToken.span, name: propToken.lexeme },
          kind: 'init',
          method: false,
          shorthand: true,
          computed: false,
          decorators: [],
        });
        this.match(TokenType.COMMA);
      }
      this.expect(TokenType.RIGHT_BRACE, "Expected '}' after destructuring pattern");
      return {
        type: 'ObjectPattern',
        span: this.makeSpan(start, this.previous()),
        properties: props,
      };
    }
    if (this.match(TokenType.LEFT_BRACKET)) {
      const start = this.previous();
      const elements: (import('../ast/index').Pattern | null)[] = [];
      while (!this.check(TokenType.RIGHT_BRACKET) && !this.isAtEnd()) {
        if (this.match(TokenType.COMMA)) {
          elements.push(null);
        } else {
          elements.push(this.parsePattern());
          this.match(TokenType.COMMA);
        }
      }
      this.expect(TokenType.RIGHT_BRACKET, "Expected ']' after destructuring pattern");
      return {
        type: 'ArrayPattern',
        span: this.makeSpan(start, this.previous()),
        elements,
      };
    }

    const token = this.peek();
    this.diagnostics.error("Expected parameter pattern", token.span);
    return { type: 'Identifier', span: token.span, name: '@error' };
  }

  parseTypeAnnotation(): TypeAnnotation {
    const start = this.peek();

    let nullable = false;
    if (this.match(TokenType.QUESTION)) {
      nullable = true;
    }

    const nameToken = this.expect(TokenType.IDENTIFIER, "Expected type name");
    const name = nameToken.lexeme;

    const typeArguments: TypeAnnotation[] = [];
    if (this.match(TokenType.LESS)) {
      typeArguments.push(this.parseTypeAnnotation());
      while (this.match(TokenType.COMMA)) {
        if (this.check(TokenType.GREATER)) break;
        typeArguments.push(this.parseTypeAnnotation());
      }
      this.expect(TokenType.GREATER, "Expected '>' after type arguments");
    }

    let arrayDepth = 0;
    while (this.match(TokenType.LEFT_BRACKET)) {
      this.expect(TokenType.RIGHT_BRACKET, "Expected ']' after array type");
      arrayDepth++;
    }

    let optional = false;
    if (this.match(TokenType.QUESTION)) {
      optional = true;
    }

    const end = this.previous();
    return {
      type: 'TypeAnnotation',
      span: this.makeSpan(start, end),
      name,
      typeArguments,
      optional,
      nullable,
      arrayDepth,
    };
  }

  private parseIdentifier(): Identifier {
    const token = this.expect(TokenType.IDENTIFIER, "Expected identifier");
    return {
      type: 'Identifier',
      span: token.span,
      name: token.lexeme,
    };
  }

  private parseDecorators(): Decorator[] {
    const decorators: Decorator[] = [];
    while (this.match(TokenType.AT)) {
      const atToken = this.previous();
      const expr = this.parsePrimary();
      decorators.push({
        type: 'Decorator',
        span: this.makeSpan(atToken, this.previous()),
        expression: expr,
      });
    }
    return decorators;
  }

  private consumeSemicolon(): void {
    this.match(TokenType.SEMICOLON);
  }

  private peek(): Token {
    return this.tokens[this.current];
  }

  private previous(): Token {
    return this.tokens[this.current - 1];
  }

  private peer(offset: number): Token {
    const idx = this.current + offset;
    if (idx < 0 || idx >= this.tokens.length) return this.tokens[this.tokens.length - 1];
    return this.tokens[idx];
  }

  private advance(): Token {
    if (!this.isAtEnd()) this.current++;
    return this.previous();
  }

  private check(type: TokenType): boolean {
    if (this.isAtEnd()) return false;
    return this.peek().type === type;
  }

  private match(...types: TokenType[]): boolean {
    for (const type of types) {
      if (this.check(type)) {
        this.advance();
        return true;
      }
    }
    return false;
  }

  private expect(type: TokenType, message: string): Token {
    if (this.check(type)) return this.advance();
    this.diagnostics.error(message, this.peek().span);
    throw new ParserPanic();
  }

  private isAtEnd(): boolean {
    return this.peek().type === TokenType.EOF;
  }

  private makeSpan(start: Token, end: Token): Span {
    return {
      start: start.span.start,
      end: end.span.end,
      file: start.span.file,
    };
  }

  private synchronize(): void {
    this.advance();
    while (!this.isAtEnd()) {
      if (this.previous().type === TokenType.SEMICOLON) return;
      switch (this.peek().type) {
        case TokenType.LET:
        case TokenType.CONST:
        case TokenType.FUN:
        case TokenType.CLASS:
        case TokenType.INTERFACE:
        case TokenType.TYPE:
        case TokenType.ENUM:
        case TokenType.IF:
        case TokenType.WHILE:
        case TokenType.FOR:
        case TokenType.LOOP:
        case TokenType.RETURN:
        case TokenType.TRY:
        case TokenType.THROW:
        case TokenType.MATCH:
        case TokenType.IMPORT:
        case TokenType.EXPORT:
        case TokenType.RIGHT_BRACE:
          return;
      }
      this.advance();
    }
  }

  private errorStatement(start: Token): ExpressionStatement {
    const span = this.makeSpan(start, this.previous());
    return {
      type: 'ExpressionStatement',
      span,
      expression: { type: 'Literal', span, value: null, raw: 'null' },
    };
  }

  private errorExpression(): Expression {
    const token = this.peek();
    this.diagnostics.error("Expected expression", token.span);
    if (!this.isAtEnd()) this.advance();
    return { type: 'Literal', span: token.span, value: null, raw: 'null' };
  }
}

class ParserPanic extends Error {
  constructor() {
    super('Parser panic');
    this.name = 'ParserPanic';
  }
}
