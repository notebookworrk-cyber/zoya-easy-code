/**
 * Zoya 3.0 - Source position and error helpers
 */

export interface Position {
  readonly line: number;
  readonly column: number;
  readonly offset: number;
}

export interface Span {
  readonly start: Position;
  readonly end: Position;
  readonly file: string;
}

export class ZoyaError extends Error {
  readonly span?: Span;
  readonly sourceLine?: string;

  constructor(message: string, span?: Span, sourceLine?: string) {
    super(formatMessage(message, span, sourceLine));
    this.name = 'ZoyaError';
    this.span = span;
    this.sourceLine = sourceLine;
  }
}

export interface Diagnostic {
  readonly severity: 'error' | 'warning' | 'info' | 'hint';
  readonly message: string;
  readonly span?: Span;
  readonly source?: string;
}

export class DiagnosticBag {
  private readonly items: Diagnostic[] = [];

  add(severity: Diagnostic['severity'], message: string, span?: Span): void {
    this.items.push({ severity, message, span });
  }

  error(message: string, span?: Span): void {
    this.add('error', message, span);
  }

  warning(message: string, span?: Span): void {
    this.add('warning', message, span);
  }

  info(message: string, span?: Span): void {
    this.add('info', message, span);
  }

  hasErrors(): boolean {
    return this.items.some(d => d.severity === 'error');
  }

  all(): readonly Diagnostic[] {
    return this.items;
  }

  count(): number {
    return this.items.length;
  }

  errors(): readonly Diagnostic[] {
    return this.items.filter(d => d.severity === 'error');
  }
}

function formatMessage(message: string, span?: Span, sourceLine?: string): string {
  if (!span) return message;
  const location = `${span.file}:${span.start.line}:${span.start.column}`;
  if (sourceLine) {
    const caret = ' '.repeat(span.start.column) + '^';
    return `${location}: ${message}\n    ${sourceLine}\n    ${caret}`;
  }
  return `${location}: ${message}`;
}

export function fmtSpan(span: Span): string {
  return `${span.file}:${span.start.line}:${span.start.column}`;
}
