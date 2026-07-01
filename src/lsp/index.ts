import { Lexer, TokenType, Token } from '../compiler/lexer/index';
import { Parser } from '../compiler/parser/index';
import { SemanticAnalyzer, SymbolInfo, Scope, AnalysisResult } from '../compiler/semantic/index';
import { DiagnosticBag, Span } from '../diagnostics';
import {
  Program, Statement, Expression, FunctionDeclaration, ClassDeclaration,
  VariableDeclaration, InterfaceDeclaration, EnumDeclaration,
  Identifier, Node,
} from '../compiler/ast/index';

export interface LSPPosition {
  line: number;
  character: number;
}

export interface LSPRange {
  start: LSPPosition;
  end: LSPPosition;
}

export interface LSPDiagnostic {
  range: LSPRange;
  severity: 1 | 2 | 3 | 4;
  message: string;
  source: string;
}

export interface LSPCompletionItem {
  label: string;
  kind: number;
  detail?: string;
  documentation?: string;
  insertText?: string;
}

export interface LSPHoverInfo {
  contents: string;
  range?: LSPRange;
}

export interface LSPLocation {
  uri: string;
  range: LSPRange;
}

export interface LSPSymbolInfo {
  name: string;
  kind: number;
  location: LSPLocation;
  containerName?: string;
}

interface DocumentState {
  uri: string;
  text: string;
  diagnostics: LSPDiagnostic[];
  symbols: LSPSymbolInfo[];
  globals: Map<string, SymbolInfo>;
  ast: Program | null;
}

const KEYWORD_COMPLETIONS: LSPCompletionItem[] = [
  { label: 'and', kind: 14, detail: 'keyword', documentation: 'Logical AND operator' },
  { label: 'or', kind: 14, detail: 'keyword', documentation: 'Logical OR operator' },
  { label: 'not', kind: 14, detail: 'keyword', documentation: 'Logical NOT operator' },
  { label: 'if', kind: 14, detail: 'keyword', documentation: 'Conditional statement' },
  { label: 'else', kind: 14, detail: 'keyword', documentation: 'Alternative branch' },
  { label: 'elif', kind: 14, detail: 'keyword', documentation: 'Else-if branch' },
  { label: 'for', kind: 14, detail: 'keyword', documentation: 'For loop' },
  { label: 'while', kind: 14, detail: 'keyword', documentation: 'While loop' },
  { label: 'loop', kind: 14, detail: 'keyword', documentation: 'Infinite loop' },
  { label: 'break', kind: 14, detail: 'keyword', documentation: 'Break out of loop' },
  { label: 'continue', kind: 14, detail: 'keyword', documentation: 'Continue to next iteration' },
  { label: 'return', kind: 14, detail: 'keyword', documentation: 'Return from function' },
  { label: 'fun', kind: 14, detail: 'keyword', documentation: 'Function declaration' },
  { label: 'let', kind: 14, detail: 'keyword', documentation: 'Variable declaration' },
  { label: 'const', kind: 14, detail: 'keyword', documentation: 'Constant declaration' },
  { label: 'class', kind: 14, detail: 'keyword', documentation: 'Class declaration' },
  { label: 'inherits', kind: 14, detail: 'keyword', documentation: 'Class inheritance' },
  { label: 'super', kind: 14, detail: 'keyword', documentation: 'Super keyword' },
  { label: 'this', kind: 14, detail: 'keyword', documentation: 'Current instance' },
  { label: 'import', kind: 14, detail: 'keyword', documentation: 'Import module' },
  { label: 'from', kind: 14, detail: 'keyword', documentation: 'Module source' },
  { label: 'as', kind: 14, detail: 'keyword', documentation: 'Alias' },
  { label: 'export', kind: 14, detail: 'keyword', documentation: 'Export declaration' },
  { label: 'type', kind: 14, detail: 'keyword', documentation: 'Type alias' },
  { label: 'interface', kind: 14, detail: 'keyword', documentation: 'Interface declaration' },
  { label: 'enum', kind: 14, detail: 'keyword', documentation: 'Enum declaration' },
  { label: 'match', kind: 14, detail: 'keyword', documentation: 'Pattern matching' },
  { label: 'case', kind: 14, detail: 'keyword', documentation: 'Match case' },
  { label: 'default', kind: 14, detail: 'keyword', documentation: 'Default case' },
  { label: 'try', kind: 14, detail: 'keyword', documentation: 'Try block' },
  { label: 'catch', kind: 14, detail: 'keyword', documentation: 'Catch clause' },
  { label: 'finally', kind: 14, detail: 'keyword', documentation: 'Finally block' },
  { label: 'throw', kind: 14, detail: 'keyword', documentation: 'Throw exception' },
  { label: 'await', kind: 14, detail: 'keyword', documentation: 'Await expression' },
  { label: 'async', kind: 14, detail: 'keyword', documentation: 'Async modifier' },
  { label: 'yield', kind: 14, detail: 'keyword', documentation: 'Yield expression' },
  { label: 'in', kind: 14, detail: 'keyword', documentation: 'Membership check' },
  { label: 'is', kind: 14, detail: 'keyword', documentation: 'Type check' },
  { label: 'new', kind: 14, detail: 'keyword', documentation: 'Constructor call' },
  { label: 'delete', kind: 14, detail: 'keyword', documentation: 'Delete property' },
  { label: 'true', kind: 14, detail: 'keyword', documentation: 'Boolean true' },
  { label: 'false', kind: 14, detail: 'keyword', documentation: 'Boolean false' },
  { label: 'nil', kind: 14, detail: 'keyword', documentation: 'Null value' },
  { label: 'public', kind: 14, detail: 'keyword', documentation: 'Public access modifier' },
  { label: 'private', kind: 14, detail: 'keyword', documentation: 'Private access modifier' },
  { label: 'protected', kind: 14, detail: 'keyword', documentation: 'Protected access modifier' },
  { label: 'static', kind: 14, detail: 'keyword', documentation: 'Static modifier' },
  { label: 'abstract', kind: 14, detail: 'keyword', documentation: 'Abstract modifier' },
  { label: 'override', kind: 14, detail: 'keyword', documentation: 'Override modifier' },
];

const BUILTIN_COMPLETIONS: LSPCompletionItem[] = [
  { label: 'print', kind: 3, detail: 'builtin function', documentation: 'Print value to stdout' },
  { label: 'len', kind: 3, detail: 'builtin function', documentation: 'Get length of array or string' },
  { label: 'type', kind: 3, detail: 'builtin function', documentation: 'Get type name of value' },
  { label: 'int', kind: 3, detail: 'builtin function', documentation: 'Convert to integer' },
  { label: 'float', kind: 3, detail: 'builtin function', documentation: 'Convert to float' },
  { label: 'string', kind: 3, detail: 'builtin function', documentation: 'Convert to string' },
  { label: 'bool', kind: 3, detail: 'builtin function', documentation: 'Convert to boolean' },
  { label: 'array', kind: 3, detail: 'builtin function', documentation: 'Create array' },
  { label: 'object', kind: 3, detail: 'builtin function', documentation: 'Create object' },
  { label: 'range', kind: 3, detail: 'builtin function', documentation: 'Create range iterator' },
  { label: 'assert', kind: 3, detail: 'builtin function', documentation: 'Assert condition' },
  { label: 'error', kind: 3, detail: 'builtin function', documentation: 'Create error' },
];

function spanToRange(span: Span): LSPRange {
  return {
    start: { line: Math.max(0, span.start.line - 1), character: Math.max(0, span.start.column - 1) },
    end: { line: Math.max(0, span.end.line - 1), character: Math.max(0, span.end.column - 1) },
  };
}

function positionToOffset(text: string, line: number, character: number): number {
  const lines = text.split('\n');
  let offset = 0;
  for (let i = 0; i < Math.min(line, lines.length); i++) {
    offset += lines[i].length + 1;
  }
  return offset + character;
}

function findTokenAtPosition(tokens: Token[], position: LSPPosition): Token | undefined {
  for (const token of tokens) {
    const startLine = token.span.start.line - 1;
    const endLine = token.span.end.line - 1;
    const startCol = token.span.start.column - 1;
    const endCol = token.span.end.column - 1;
    if (
      (position.line > startLine || (position.line === startLine && position.character >= startCol)) &&
      (position.line < endLine || (position.line === endLine && position.character <= endCol))
    ) {
      return token;
    }
  }
  return undefined;
}

function extractDocumentSymbols(program: Program, uri: string): LSPSymbolInfo[] {
  const symbols: LSPSymbolInfo[] = [];
  for (const stmt of program.body) {
    if (stmt.type === 'FunctionDeclaration') {
      const fn = stmt as FunctionDeclaration;
      symbols.push({
        name: fn.id.name,
        kind: 12,
        location: { uri, range: spanToRange(fn.span) },
      });
    } else if (stmt.type === 'ClassDeclaration') {
      const cls = stmt as ClassDeclaration;
      symbols.push({
        name: cls.id.name,
        kind: 5,
        location: { uri, range: spanToRange(cls.span) },
      });
      for (const method of cls.body.methods) {
        symbols.push({
          name: method.key.name,
          kind: 6,
          location: { uri, range: spanToRange(method.span) },
          containerName: cls.id.name,
        });
      }
    } else if (stmt.type === 'VariableDeclaration') {
      const vd = stmt as VariableDeclaration;
      for (const decl of vd.declarations) {
        symbols.push({
          name: decl.id.name,
          kind: 13,
          location: { uri, range: spanToRange(decl.id.span) },
        });
      }
    } else if (stmt.type === 'InterfaceDeclaration') {
      const iface = stmt as InterfaceDeclaration;
      symbols.push({
        name: iface.id.name,
        kind: 11,
        location: { uri, range: spanToRange(iface.span) },
      });
    } else if (stmt.type === 'EnumDeclaration') {
      const enm = stmt as EnumDeclaration;
      symbols.push({
        name: enm.id.name,
        kind: 10,
        location: { uri, range: spanToRange(enm.span) },
      });
    }
  }
  return symbols;
}

function findSymbolInProgram(program: Program, name: string): Node | undefined {
  for (const stmt of program.body) {
    if (stmt.type === 'FunctionDeclaration') {
      const fn = stmt as FunctionDeclaration;
      if (fn.id.name === name) return fn;
    } else if (stmt.type === 'ClassDeclaration') {
      const cls = stmt as ClassDeclaration;
      if (cls.id.name === name) return cls;
      for (const method of cls.body.methods) {
        if (method.key.name === name) return method;
      }
    } else if (stmt.type === 'VariableDeclaration') {
      const vd = stmt as VariableDeclaration;
      for (const decl of vd.declarations) {
        if (decl.id.name === name) return decl.id;
      }
    } else if (stmt.type === 'InterfaceDeclaration') {
      const iface = stmt as InterfaceDeclaration;
      if (iface.id.name === name) return iface;
    } else if (stmt.type === 'EnumDeclaration') {
      const enm = stmt as EnumDeclaration;
      if (enm.id.name === name) return enm;
    }
  }
  return undefined;
}

function findReferencesInProgram(program: Program, name: string): LSPLocation[] {
  const locations: LSPLocation[] = [];
  const uri = program.body.length > 0 ? program.body[0].span.file : '<unknown>';
  visitNodeForReferences(program as unknown as Record<string, unknown>, name, locations);
  return locations;
}

function visitNodeForReferences(node: Record<string, unknown>, name: string, locations: LSPLocation[]): void {
  if (!node || typeof node !== 'object') return;

  if ('type' in node && node.type === 'Identifier' && (node as unknown as Identifier).name === name) {
    const idNode = node as unknown as Identifier;
    locations.push({ uri: idNode.span.file, range: spanToRange(idNode.span) });
  }

  for (const value of Object.values(node)) {
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item && typeof item === 'object') {
          visitNodeForReferences(item as Record<string, unknown>, name, locations);
        }
      }
    } else if (value && typeof value === 'object') {
      visitNodeForReferences(value as Record<string, unknown>, name, locations);
    }
  }
}

function getTokenTypeAtPosition(
  tokens: Token[],
  position: LSPPosition,
): { token: Token; typeId: number } | undefined {
  const token = findTokenAtPosition(tokens, position);
  if (!token) return undefined;

  switch (token.type) {
    case TokenType.NUMBER:
      return { token, typeId: 19 };
    case TokenType.STRING:
    case TokenType.INTERPOLATED_STRING:
      return { token, typeId: 18 };
    case TokenType.IDENTIFIER:
      return { token, typeId: 8 };
    default:
      if (token.type === TokenType.TRUE || token.type === TokenType.FALSE || token.type === TokenType.NIL) {
        return { token, typeId: 19 };
      }
      const isKeyword = typeof token.type === 'string' &&
        token.type !== 'EOF';
      if (isKeyword) {
        return { token, typeId: 15 };
      }
      return { token, typeId: 21 };
  }
}

export class LanguageServer {
  private documents: Map<string, DocumentState> = new Map();
  private lexerCache: Map<string, Token[]> = new Map();

  openDocument(uri: string, text: string): void {
    const { diagnostics, symbols, globals, ast } = this.analyzeDocument(uri, text);
    this.documents.set(uri, { uri, text, diagnostics, symbols, globals, ast });
  }

  changeDocument(uri: string, text: string): void {
    const { diagnostics, symbols, globals, ast } = this.analyzeDocument(uri, text);
    this.documents.set(uri, { uri, text, diagnostics, symbols, globals, ast });
  }

  closeDocument(uri: string): void {
    this.documents.delete(uri);
    this.lexerCache.delete(uri);
  }

  getDiagnostics(uri: string): LSPDiagnostic[] {
    return this.documents.get(uri)?.diagnostics ?? [];
  }

  getCompletions(uri: string, position: LSPPosition): LSPCompletionItem[] {
    const doc = this.documents.get(uri);
    const completions: LSPCompletionItem[] = [
      ...KEYWORD_COMPLETIONS,
      ...BUILTIN_COMPLETIONS,
    ];

    if (doc) {
      for (const [name, sym] of doc.globals) {
        const kindMap: Record<string, number> = {
          variable: 6,
          function: 3,
          class: 5,
          interface: 11,
          type: 22,
          enum: 10,
          import: 9,
        };
        completions.push({
          label: name,
          kind: kindMap[sym.kind] ?? 8,
          detail: sym.kind,
          documentation: sym.node.type,
        });
      }
    }

    const linePrefix = this.getLinePrefix(uri, position);
    if (linePrefix) {
      const lastDot = linePrefix.lastIndexOf('.');
      if (lastDot >= 0) {
        const objName = linePrefix.substring(0, lastDot).trim();
        const memberCompletions = this.getMemberCompletions(objName, doc);
        return memberCompletions;
      }
    }

    return completions;
  }

  private getLinePrefix(uri: string, position: LSPPosition): string | undefined {
    const doc = this.documents.get(uri);
    if (!doc) return undefined;
    const lines = doc.text.split('\n');
    if (position.line >= lines.length) return undefined;
    return lines[position.line].substring(0, position.character);
  }

  private getMemberCompletions(objName: string, doc: DocumentState | undefined): LSPCompletionItem[] {
    return [
      { label: 'toString', kind: 6, detail: 'method', documentation: 'Convert to string' },
      { label: 'toInt', kind: 6, detail: 'method', documentation: 'Convert to integer' },
      { label: 'toFloat', kind: 6, detail: 'method', documentation: 'Convert to float' },
      { label: 'clone', kind: 6, detail: 'method', documentation: 'Clone object' },
      { label: 'equals', kind: 6, detail: 'method', documentation: 'Equality check' },
    ];
  }

  getHover(uri: string, position: LSPPosition): LSPHoverInfo | null {
    const doc = this.documents.get(uri);
    if (!doc) return null;

    const tokens = this.lexerCache.get(uri);
    if (!tokens) return null;

    const tokenInfo = getTokenTypeAtPosition(tokens, position);
    if (!tokenInfo) return null;

    const { token, typeId } = tokenInfo;

    if (token.type === TokenType.IDENTIFIER) {
      const sym = doc.globals.get(token.lexeme);
      if (sym) {
        const typeStr = sym.typeAnnotation
          ? `\n\n**Type:** ${sym.typeAnnotation.name}`
          : '';
        const declKind = sym.imported
          ? `imported from '${sym.module ?? 'unknown'}'`
          : sym.kind;
        return {
          contents: `**${token.lexeme}** — ${declKind}${typeStr}`,
          range: spanToRange(token.span),
        };
      }
      return {
        contents: `\`${token.lexeme}\``,
        range: spanToRange(token.span),
      };
    }

    const keywordDocs: Record<string, string> = {
      fun: '**fun** — Declare a function.\n\n```\nfun name(params): returnType {\n  body\n}\n```',
      let: '**let** — Declare a mutable variable.\n\n```\nlet name = value\n```',
      const: '**const** — Declare an immutable constant.\n\n```\nconst name = value\n```',
      class: '**class** — Declare a class.\n\n```\nclass Name inherits Parent {\n  // members\n}\n```',
      if: '**if** — Conditional execution.\n\n```\nif (condition) {\n  // true branch\n} else {\n  // false branch\n}\n```',
      for: '**for** — For loop.\n\n```\nfor (let i = 0; i < n; i++) {\n  // body\n}\n```',
      while: '**while** — While loop.\n\n```\nwhile (condition) {\n  // body\n}\n```',
      return: '**return** — Return a value from a function.\n\n```\nreturn value\n```',
      import: '**import** — Import symbols from a module.\n\n```\nimport { name } from "module"\n```',
    };

    if (keywordDocs[token.lexeme]) {
      return {
        contents: keywordDocs[token.lexeme],
        range: spanToRange(token.span),
      };
    }

    return {
      contents: `\`${token.lexeme}\``,
      range: spanToRange(token.span),
    };
  }

  getDefinition(uri: string, position: LSPPosition): LSPLocation | null {
    const doc = this.documents.get(uri);
    if (!doc || !doc.ast) return null;

    const tokens = this.lexerCache.get(uri);
    if (!tokens) return null;

    const token = findTokenAtPosition(tokens, position);
    if (!token || token.type !== TokenType.IDENTIFIER) return null;

    const sym = doc.globals.get(token.lexeme);
    if (sym) {
      return {
        uri,
        range: spanToRange(sym.node.span),
      };
    }

    const defNode = findSymbolInProgram(doc.ast, token.lexeme);
    if (defNode) {
      return {
        uri,
        range: spanToRange(defNode.span),
      };
    }

    return null;
  }

  getReferences(uri: string, position: LSPPosition): LSPLocation[] {
    const doc = this.documents.get(uri);
    if (!doc || !doc.ast) return [];

    const tokens = this.lexerCache.get(uri);
    if (!tokens) return [];

    const token = findTokenAtPosition(tokens, position);
    if (!token || token.type !== TokenType.IDENTIFIER) return [];

    return findReferencesInProgram(doc.ast, token.lexeme);
  }

  getDocumentSymbols(uri: string): LSPSymbolInfo[] {
    return this.documents.get(uri)?.symbols ?? [];
  }

  rename(uri: string, position: LSPPosition, newName: string): Map<string, LSPLocation[]> {
    const doc = this.documents.get(uri);
    if (!doc || !doc.ast) return new Map();

    const tokens = this.lexerCache.get(uri);
    if (!tokens) return new Map();

    const token = findTokenAtPosition(tokens, position);
    if (!token || token.type !== TokenType.IDENTIFIER) return new Map();

    const locations = findReferencesInProgram(doc.ast, token.lexeme);
    const result = new Map<string, LSPLocation[]>();
    result.set(uri, locations);
    return result;
  }

  getSemanticTokens(uri: string): number[] {
    const tokens = this.lexerCache.get(uri);
    if (!tokens) return [];

    const semanticTokens: number[] = [];
    let prevLine = 0;
    let prevChar = 0;

    for (const token of tokens) {
      if (token.type === TokenType.EOF) continue;

      let typeId: number;
      switch (token.type) {
        case TokenType.NUMBER:
          typeId = 19;
          break;
        case TokenType.STRING:
        case TokenType.INTERPOLATED_STRING:
          typeId = 18;
          break;
        case TokenType.IDENTIFIER:
          typeId = 8;
          break;
        default:
          if (
            token.type === TokenType.TRUE ||
            token.type === TokenType.FALSE ||
            token.type === TokenType.NIL
          ) {
            typeId = 19;
          } else if (
            token.type === TokenType.PLUS || token.type === TokenType.MINUS ||
            token.type === TokenType.STAR || token.type === TokenType.SLASH ||
            token.type === TokenType.EQUAL || token.type === TokenType.EQUAL_EQUAL ||
            token.type === TokenType.BANG || token.type === TokenType.BANG_EQUAL ||
            token.type === TokenType.GREATER || token.type === TokenType.GREATER_EQUAL ||
            token.type === TokenType.LESS || token.type === TokenType.LESS_EQUAL ||
            token.type === TokenType.AMPERSAND || token.type === TokenType.PIPE ||
            token.type === TokenType.CARET || token.type === TokenType.TILDE ||
            token.type === TokenType.PLUS_PLUS || token.type === TokenType.MINUS_MINUS ||
            token.type === TokenType.PLUS_EQUALS || token.type === TokenType.MINUS_EQUALS ||
            token.type === TokenType.STAR_EQUALS || token.type === TokenType.SLASH_EQUALS ||
            token.type === TokenType.PERCENT || token.type === TokenType.PERCENT_EQUALS ||
            token.type === TokenType.SHIFT_LEFT || token.type === TokenType.SHIFT_RIGHT ||
            token.type === TokenType.ARROW || token.type === TokenType.FAT_ARROW ||
            token.type === TokenType.DOT || token.type === TokenType.DOT_DOT ||
            token.type === TokenType.DOT_DOT_DOT || token.type === TokenType.QUESTION ||
            token.type === TokenType.QUESTION_DOT || token.type === TokenType.COLON
          ) {
            typeId = 21;
          } else {
            typeId = 15;
          }
          break;
      }

      const tokenLine = token.span.start.line - 1;
      const tokenChar = token.span.start.column - 1;
      const tokenLen = token.lexeme.length;

      let deltaLine = tokenLine - prevLine;
      let deltaChar: number;
      if (deltaLine === 0) {
        deltaChar = tokenChar - prevChar;
      } else {
        deltaChar = tokenChar;
      }

      semanticTokens.push(deltaLine, deltaChar, tokenLen, typeId, 0);
      prevLine = tokenLine;
      prevChar = tokenChar + tokenLen;
    }

    return semanticTokens;
  }

  private analyzeDocument(uri: string, text: string): {
    diagnostics: LSPDiagnostic[];
    symbols: LSPSymbolInfo[];
    globals: Map<string, SymbolInfo>;
    ast: Program | null;
  } {
    const lexer = new Lexer(text, uri);
    let tokens: Token[];
    try {
      tokens = lexer.scanTokens();
    } catch {
      tokens = [];
    }
    this.lexerCache.set(uri, tokens);

    const diagBag = new DiagnosticBag();
    const parser = new Parser(tokens, diagBag);
    let program: Program;
    try {
      program = parser.parse();
    } catch {
      program = {
        type: 'Program',
        span: {
          start: { line: 1, column: 1, offset: 0 },
          end: { line: 1, column: 1, offset: 0 },
          file: uri,
        },
        body: [],
        imports: [],
        exports: [],
      };
    }

    const analyzer = new SemanticAnalyzer(diagBag);
    let result: AnalysisResult;
    try {
      result = analyzer.analyze(program);
    } catch {
      result = {
        ast: program,
        diagnostics: diagBag,
        globals: new Map(),
        exports: new Map(),
      };
    }

    const lspDiagnostics: LSPDiagnostic[] = [];
    const severityMap: Record<string, 1 | 2 | 3 | 4> = {
      error: 1,
      warning: 2,
      info: 3,
      hint: 4,
    };
    for (const diag of result.diagnostics.all()) {
      lspDiagnostics.push({
        range: diag.span ? spanToRange(diag.span) : {
          start: { line: 0, character: 0 },
          end: { line: 0, character: 1 },
        },
        severity: severityMap[diag.severity] ?? 2,
        message: diag.message,
        source: 'zoya',
      });
    }

    const symbols = extractDocumentSymbols(program, uri);

    return {
      diagnostics: lspDiagnostics,
      symbols,
      globals: result.globals,
      ast: result.ast,
    };
  }
}
