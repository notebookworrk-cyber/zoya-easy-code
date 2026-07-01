/**
 * Zoya 3.0 - Lexer (Tokenizer)
 * Transforms source code into a stream of tokens
 */

import { Position, Span, ZoyaError } from '../diagnostics';

export enum TokenType {
  // End of file
  EOF = 'EOF',

  // Literals
  IDENTIFIER = 'IDENTIFIER',
  NUMBER = 'NUMBER',
  STRING = 'STRING',
  INTERPOLATED_STRING = 'INTERPOLATED_STRING',
  TRUE = 'TRUE',
  FALSE = 'FALSE',
  NIL = 'NIL',

  // Keywords
  AND = 'AND',
  OR = 'OR',
  NOT = 'NOT',
  IF = 'IF',
  ELSE = 'ELSE',
  ELIF = 'ELIF',
  FOR = 'FOR',
  WHILE = 'WHILE',
  LOOP = 'LOOP',
  BREAK = 'BREAK',
  CONTINUE = 'CONTINUE',
  RETURN = 'RETURN',
  FUN = 'FUN',
  LET = 'LET',
  CONST = 'CONST',
  CLASS = 'CLASS',
  INHERITS = 'INHERITS',
  SUPER = 'SUPER',
  THIS = 'THIS',
  IMPORT = 'IMPORT',
  FROM = 'FROM',
  AS = 'AS',
  EXPORT = 'EXPORT',
  TYPE = 'TYPE',
  INTERFACE = 'INTERFACE',
  ENUM = 'ENUM',
  MATCH = 'MATCH',
  CASE = 'CASE',
  DEFAULT = 'DEFAULT',
  TRY = 'TRY',
  CATCH = 'CATCH',
  FINALLY = 'FINALLY',
  THROW = 'THROW',
  AWAIT = 'AWAIT',
  ASYNC = 'ASYNC',
  YIELD = 'YIELD',
  IN = 'IN',
  IS = 'IS',
  NEW = 'NEW',
  DELETE = 'DELETE',
  PUBLIC = 'PUBLIC',
  PRIVATE = 'PRIVATE',
  PROTECTED = 'PROTECTED',
  STATIC = 'STATIC',
  ABSTRACT = 'ABSTRACT',
  OVERRIDE = 'OVERRIDE',

  // Operators
  PLUS = 'PLUS',
  MINUS = 'MINUS',
  STAR = 'STAR',
  SLASH = 'SLASH',
  PERCENT = 'PERCENT',
  STAR_STAR = 'STAR_STAR', // **
  PLUS_PLUS = 'PLUS_PLUS',
  MINUS_MINUS = 'MINUS_MINUS',
  PLUS_EQUALS = 'PLUS_EQUALS',
  MINUS_EQUALS = 'MINUS_EQUALS',
  STAR_EQUALS = 'STAR_EQUALS',
  SLASH_EQUALS = 'SLASH_EQUALS',
  PERCENT_EQUALS = 'PERCENT_EQUALS',
  BANG = 'BANG',
  BANG_EQUAL = 'BANG_EQUAL',
  EQUAL = 'EQUAL',
  EQUAL_EQUAL = 'EQUAL_EQUAL',
  GREATER = 'GREATER',
  GREATER_EQUAL = 'GREATER_EQUAL',
  LESS = 'LESS',
  LESS_EQUAL = 'LESS_EQUAL',
  ARROW = 'ARROW',
  FAT_ARROW = 'FAT_ARROW',
  PIPE = 'PIPE',
  PIPE_PIPE = 'PIPE_PIPE',
  AMPERSAND = 'AMPERSAND',
  AMPERSAND_AMPERSAND = 'AMPERSAND_AMPERSAND',
  CARET = 'CARET',
  TILDE = 'TILDE',
  SHIFT_LEFT = 'SHIFT_LEFT',
  SHIFT_RIGHT = 'SHIFT_RIGHT',
  DOT = 'DOT',
  DOT_DOT = 'DOT_DOT',
  DOT_DOT_DOT = 'DOT_DOT_DOT',
  QUESTION = 'QUESTION',
  QUESTION_DOT = 'QUESTION_DOT',
  COLON = 'COLON',
  SEMICOLON = 'SEMICOLON',
  COMMA = 'COMMA',

  // Delimiters
  LEFT_PAREN = 'LEFT_PAREN',
  RIGHT_PAREN = 'RIGHT_PAREN',
  LEFT_BRACE = 'LEFT_BRACE',
  RIGHT_BRACE = 'RIGHT_BRACE',
  LEFT_BRACKET = 'LEFT_BRACKET',
  RIGHT_BRACKET = 'RIGHT_BRACKET',

  // Special
  AT = 'AT', // @ for decorators
  HASH = 'HASH', // # for private fields
  DOLLAR = 'DOLLAR', // $ for string interpolation
}

export interface Token {
  readonly type: TokenType;
  readonly lexeme: string;
  readonly literal: unknown;
  readonly span: Span;
}

const KEYWORDS: Map<string, TokenType> = new Map([
  ['and', TokenType.AND],
  ['or', TokenType.OR],
  ['not', TokenType.NOT],
  ['if', TokenType.IF],
  ['else', TokenType.ELSE],
  ['elif', TokenType.ELIF],
  ['for', TokenType.FOR],
  ['while', TokenType.WHILE],
  ['loop', TokenType.LOOP],
  ['break', TokenType.BREAK],
  ['continue', TokenType.CONTINUE],
  ['return', TokenType.RETURN],
  ['fun', TokenType.FUN],
  ['let', TokenType.LET],
  ['const', TokenType.CONST],
  ['class', TokenType.CLASS],
  ['inherits', TokenType.INHERITS],
  ['super', TokenType.SUPER],
  ['this', TokenType.THIS],
  ['import', TokenType.IMPORT],
  ['from', TokenType.FROM],
  ['as', TokenType.AS],
  ['export', TokenType.EXPORT],
  ['type', TokenType.TYPE],
  ['interface', TokenType.INTERFACE],
  ['enum', TokenType.ENUM],
  ['match', TokenType.MATCH],
  ['case', TokenType.CASE],
  ['default', TokenType.DEFAULT],
  ['try', TokenType.TRY],
  ['catch', TokenType.CATCH],
  ['finally', TokenType.FINALLY],
  ['throw', TokenType.THROW],
  ['await', TokenType.AWAIT],
  ['async', TokenType.ASYNC],
  ['yield', TokenType.YIELD],
  ['in', TokenType.IN],
  ['is', TokenType.IS],
  ['new', TokenType.NEW],
  ['delete', TokenType.DELETE],
  ['public', TokenType.PUBLIC],
  ['private', TokenType.PRIVATE],
  ['protected', TokenType.PROTECTED],
  ['static', TokenType.STATIC],
  ['abstract', TokenType.ABSTRACT],
  ['override', TokenType.OVERRIDE],
  ['true', TokenType.TRUE],
  ['false', TokenType.FALSE],
  ['nil', TokenType.NIL],
]);

export class Lexer {
  private readonly source: string;
  private readonly tokens: Token[] = [];
  private start = 0;
  private current = 0;
  private line = 1;
  private column = 1;
  private readonly file: string;

  constructor(source: string, file = '<unknown>') {
    this.source = source;
    this.file = file;
  }

  scanTokens(): Token[] {
    while (!this.isAtEnd()) {
      this.start = this.current;
      this.scanToken();
    }

    this.tokens.push(this.makeToken(TokenType.EOF));
    return this.tokens;
  }

  private isAtEnd(): boolean {
    return this.current >= this.source.length;
  }

  private scanToken(): void {
    const c = this.advance();

    switch (c) {
      case '(':
        this.addToken(TokenType.LEFT_PAREN);
        break;
      case ')':
        this.addToken(TokenType.RIGHT_PAREN);
        break;
      case '{':
        this.addToken(TokenType.LEFT_BRACE);
        break;
      case '}':
        this.addToken(TokenType.RIGHT_BRACE);
        break;
      case '[':
        this.addToken(TokenType.LEFT_BRACKET);
        break;
      case ']':
        this.addToken(TokenType.RIGHT_BRACKET);
        break;
      case ',':
        this.addToken(TokenType.COMMA);
        break;
      case '.':
        this.dotOrRange();
        break;
      case '-':
        this.minusOrArrow();
        break;
      case '+':
        this.addToken(this.match('+') ? TokenType.PLUS_PLUS : this.match('=') ? TokenType.PLUS_EQUALS : TokenType.PLUS);
        break;
      case ';':
        this.addToken(TokenType.SEMICOLON);
        break;
      case '*':
        this.addToken(this.match('*') ? TokenType.STAR_STAR : this.match('=') ? TokenType.STAR_EQUALS : TokenType.STAR);
        break;
      case '/':
        if (this.match('/')) {
          while (this.peek() !== '\n' && !this.isAtEnd()) this.advance();
        } else if (this.match('*')) {
          this.blockComment();
        } else {
          this.addToken(this.match('=') ? TokenType.SLASH_EQUALS : TokenType.SLASH);
        }
        break;
      case '%':
        this.addToken(this.match('=') ? TokenType.PERCENT_EQUALS : TokenType.PERCENT);
        break;
      case '!':
        this.addToken(this.match('=') ? TokenType.BANG_EQUAL : TokenType.BANG);
        break;
      case '=':
        this.addToken(this.match('=') ? TokenType.EQUAL_EQUAL : this.match('>') ? TokenType.FAT_ARROW : TokenType.EQUAL);
        break;
      case '<':
        this.addToken(this.match('=') ? TokenType.LESS_EQUAL : this.match('<') ? TokenType.SHIFT_LEFT : TokenType.LESS);
        break;
      case '>':
        this.addToken(this.match('=') ? TokenType.GREATER_EQUAL : this.match('>') ? TokenType.SHIFT_RIGHT : TokenType.GREATER);
        break;
      case ':':
        this.addToken(TokenType.COLON);
        break;
      case '?':
        this.addToken(this.match('.') ? TokenType.QUESTION_DOT : TokenType.QUESTION);
        break;
      case '&':
        this.addToken(this.match('&') ? TokenType.AMPERSAND_AMPERSAND : TokenType.AMPERSAND);
        break;
      case '|':
        this.addToken(this.match('|') ? TokenType.PIPE_PIPE : TokenType.PIPE);
        break;
      case '^':
        this.addToken(TokenType.CARET);
        break;
      case '~':
        this.addToken(TokenType.TILDE);
        break;
      case '@':
        this.addToken(TokenType.AT);
        break;
      case '#':
        this.addToken(TokenType.HASH);
        break;
      case '$':
        this.addToken(TokenType.DOLLAR);
        break;
      case '"':
        this.string();
        break;
      case '\'':
        this.char();
        break;
      case '`':
        this.templateString();
        break;

      case ' ':
      case '\r':
      case '\t':
        break;

      case '\n':
        this.line++;
        this.column = 1;
        break;

      default:
        if (this.isDigit(c)) {
          this.number();
        } else if (this.isAlpha(c)) {
          this.identifier();
        } else {
          this.error(`Unexpected character: '${c}'`);
        }
        break;
    }
  }

  private dotOrRange(): void {
    if (this.match('.')) {
      if (this.match('.')) {
        this.addToken(TokenType.DOT_DOT_DOT);
      } else {
        this.addToken(TokenType.DOT_DOT);
      }
    } else {
      this.addToken(TokenType.DOT);
    }
  }

  private minusOrArrow(): void {
    if (this.match('-')) {
      this.addToken(TokenType.MINUS_MINUS);
    } else if (this.match('=')) {
      this.addToken(TokenType.MINUS_EQUALS);
    } else if (this.match('>')) {
      this.addToken(TokenType.ARROW);
    } else {
      this.addToken(TokenType.MINUS);
    }
  }

  private identifier(): void {
    while (this.isAlphaNumeric(this.peek())) this.advance();

    const text = this.source.substring(this.start, this.current);
    const type = KEYWORDS.get(text) ?? TokenType.IDENTIFIER;
    this.addToken(type, text);
  }

  private number(): void {
    while (this.isDigit(this.peek())) this.advance();

    if (this.peek() === '.' && this.isDigit(this.peekNext())) {
      this.advance();
      while (this.isDigit(this.peek())) this.advance();
    }

    const value = parseFloat(this.source.substring(this.start, this.current));
    this.addToken(TokenType.NUMBER, value);
  }

  private string(): void {
    while (this.peek() !== '"' && !this.isAtEnd()) {
      if (this.peek() === '\n') {
        this.line++;
        this.column = 1;
      }
      this.advance();
    }

    if (this.isAtEnd()) {
      this.error('Unterminated string.');
      return;
    }

    this.advance();
    const value = this.source.substring(this.start + 1, this.current - 1);
    this.addToken(TokenType.STRING, this.unescape(value));
  }

  private char(): void {
    while (this.peek() !== '\'' && !this.isAtEnd()) {
      if (this.peek() === '\n') {
        this.line++;
        this.column = 1;
      }
      this.advance();
    }

    if (this.isAtEnd()) {
      this.error('Unterminated character literal.');
      return;
    }

    this.advance();
    const value = this.source.substring(this.start + 1, this.current - 1);
    this.addToken(TokenType.STRING, this.unescape(value));
  }

  private templateString(): void {
    // Backtick strings support interpolation
    const parts: string[] = [];
    let interpolated = false;

    while (this.peek() !== '`' && !this.isAtEnd()) {
      if (this.peek() === '$' && this.peekNext() === '{') {
        interpolated = true;
        this.advance(); // $
        this.advance(); // {
        // For simplicity, treat as regular string for now
        // Full interpolation would need parser integration
      }
      if (this.peek() === '\n') {
        this.line++;
        this.column = 1;
      }
      this.advance();
    }

    if (this.isAtEnd()) {
      this.error('Unterminated template string.');
      return;
    }

    this.advance();
    const value = this.source.substring(this.start + 1, this.current - 1);
    this.addToken(interpolated ? TokenType.INTERPOLATED_STRING : TokenType.STRING, this.unescape(value));
  }

  private blockComment(): void {
    let depth = 1;
    while (depth > 0 && !this.isAtEnd()) {
      if (this.peek() === '*' && this.peekNext() === '/') {
        this.advance();
        this.advance();
        depth--;
      } else if (this.peek() === '/' && this.peekNext() === '*') {
        this.advance();
        this.advance();
        depth++;
      } else {
        if (this.peek() === '\n') {
          this.line++;
          this.column = 1;
        }
        this.advance();
      }
    }

    if (depth > 0) {
      this.error('Unterminated block comment.');
    }
  }

  private unescape(str: string): string {
    return str
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
      .replace(/\\r/g, '\r')
      .replace(/\\"/g, '"')
      .replace(/\\'/g, "'")
      .replace(/\\\\/g, '\\')
      .replace(/\\u\{([0-9a-fA-F]+)\}/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)));
  }

  private match(expected: string): boolean {
    if (this.isAtEnd()) return false;
    if (this.source[this.current] !== expected) return false;
    this.current++;
    this.column++;
    return true;
  }

  private peek(): string {
    if (this.isAtEnd()) return '\0';
    return this.source[this.current];
  }

  private peekNext(): string {
    if (this.current + 1 >= this.source.length) return '\0';
    return this.source[this.current + 1];
  }

  private isAlpha(c: string): boolean {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_';
  }

  private isDigit(c: string): boolean {
    return c >= '0' && c <= '9';
  }

  private isAlphaNumeric(c: string): boolean {
    return this.isAlpha(c) || this.isDigit(c);
  }

  private advance(): string {
    const c = this.source[this.current++];
    this.column++;
    return c;
  }

  private addToken(type: TokenType, literal?: unknown): void {
    const text = this.source.substring(this.start, this.current);
    this.tokens.push(this.makeToken(type, literal ?? text));
  }

  private makeToken(type: TokenType, literal?: unknown): Token {
    return {
      type,
      lexeme: this.source.substring(this.start, this.current),
      literal,
      span: {
        start: { line: this.line, column: this.column - (this.current - this.start), offset: this.start },
        end: { line: this.line, column: this.column, offset: this.current },
        file: this.file,
      },
    };
  }

  private error(message: string): void {
    const token = this.makeToken(TokenType.EOF); // This would be better with a proper error token
    throw new ZoyaError(message, token.span);
  }
}

function token(type: TokenType): Token {
  return {
    type,
    lexeme: '',
    literal: null,
    span: {
      start: { line: 1, column: 1, offset: 0 },
      end: { line: 1, column: 1, offset: 0 },
      file: '<error>',
    },
  };
}