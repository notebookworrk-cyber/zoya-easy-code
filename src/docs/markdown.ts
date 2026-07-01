import { DocModule } from './index';
import { Tutorial } from './tutorials';

export class MarkdownBuilder {
  private lines: string[];

  constructor() {
    this.lines = [];
  }

  h1(text: string): MarkdownBuilder {
    this.lines.push(`# ${text}`, '');
    return this;
  }

  h2(text: string): MarkdownBuilder {
    this.lines.push(`## ${text}`, '');
    return this;
  }

  h3(text: string): MarkdownBuilder {
    this.lines.push(`### ${text}`, '');
    return this;
  }

  h4(text: string): MarkdownBuilder {
    this.lines.push(`#### ${text}`, '');
    return this;
  }

  p(text: string): MarkdownBuilder {
    this.lines.push(text, '');
    return this;
  }

  code(code: string, language?: string): MarkdownBuilder {
    this.lines.push('```' + (language || ''), code, '```', '');
    return this;
  }

  inlineCode(code: string): string {
    return `\`${code}\``;
  }

  blockquote(text: string): MarkdownBuilder {
    const quoted = text
      .split('\n')
      .map((l) => `> ${l}`)
      .join('\n');
    this.lines.push(quoted, '');
    return this;
  }

  ul(items: string[]): MarkdownBuilder {
    for (const item of items) {
      this.lines.push(`- ${item}`);
    }
    this.lines.push('');
    return this;
  }

  ol(items: string[]): MarkdownBuilder {
    for (let i = 0; i < items.length; i++) {
      this.lines.push(`${i + 1}. ${items[i]}`);
    }
    this.lines.push('');
    return this;
  }

  link(text: string, url: string): string {
    return `[${text}](${url})`;
  }

  table(headers: string[], rows: string[][]): MarkdownBuilder {
    this.lines.push('| ' + headers.join(' | ') + ' |');
    this.lines.push('| ' + headers.map(() => '---').join(' | ') + ' |');
    for (const row of rows) {
      this.lines.push('| ' + row.join(' | ') + ' |');
    }
    this.lines.push('');
    return this;
  }

  hr(): MarkdownBuilder {
    this.lines.push('---', '');
    return this;
  }

  bold(text: string): string {
    return `**${text}**`;
  }

  italic(text: string): string {
    return `*${text}*`;
  }

  append(text: string): MarkdownBuilder {
    this.lines.push(text, '');
    return this;
  }

  build(): string {
    return this.lines.join('\n').trimEnd() + '\n';
  }

  save(path: string): void {
    const fs = require('fs');
    fs.writeFileSync(path, this.build(), 'utf-8');
  }
}

export function generateAPIMarkdown(modules: DocModule[]): string {
  const md = new MarkdownBuilder();
  md.h1('API Reference');
  for (const mod of modules) {
    md.h2(mod.name);
    md.p(mod.description);
    if (mod.classes.length > 0) {
      md.h3('Classes');
      for (const cls of mod.classes) {
        md.p(`**${cls.name}**`);
        md.p(cls.description);
      }
    }
    if (mod.functions.length > 0) {
      md.h3('Functions');
      for (const fn of mod.functions) {
        md.p(`**${fn.name}**`);
        md.code(fn.signature, 'zoya');
      }
    }
  }
  return md.build();
}

export function generateTutorialMarkdown(tutorials: Tutorial[]): string {
  const md = new MarkdownBuilder();
  md.h1('Tutorials');
  for (const t of tutorials) {
    md.h2(md.link(t.title, `tutorials/${t.id}.md`));
    md.p(t.description);
    md.p(`*Difficulty: ${t.difficulty} | Estimated: ${t.estimatedTime} min*`);
    if (t.prerequisites.length > 0) {
      md.p('Prerequisites: ' + t.prerequisites.map((p) => md.link(p, `tutorials/${p}.md`)).join(', '));
    }
  }
  return md.build();
}

export function generateIndexMarkdown(modules: DocModule[], tutorials: Tutorial[]): string {
  const md = new MarkdownBuilder();
  md.h1('Zoya Programming Language');
  md.p('Welcome to the Zoya 3.0 documentation.');
  md.h2('Modules');
  for (const mod of modules) {
    md.ul([md.link(mod.name, `modules/${mod.name}.md`) + ' — ' + mod.description]);
  }
  md.h2('Tutorials');
  for (const t of tutorials) {
    md.ul([md.link(t.title, `tutorials/${t.id}.md`) + ` — ${t.description} (${t.difficulty})`]);
  }
  return md.build();
}
