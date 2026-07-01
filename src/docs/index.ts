import * as fs from 'fs';
import * as path from 'path';
import { MarkdownBuilder } from './markdown';
import { TutorialLibrary, TUTORIALS, Tutorial } from './tutorials';

export interface DocConfig {
  title: string;
  description: string;
  version: string;
  outputDir: string;
  sourceDir: string;
  includeModules: string[];
  excludePatterns: string[];
  themes: string;
  generateSearchIndex: boolean;
  generateTutorials: boolean;
  generateExamples: boolean;
  interactive: boolean;
}

export interface DocModule {
  name: string;
  description: string;
  source: string;
  exports: DocExport[];
  classes: DocClass[];
  functions: DocFunction[];
  variables: DocVariable[];
  types: DocType[];
  interfaces: DocInterface[];
  enums: DocEnum[];
  examples: DocExample[];
  since: string;
  deprecated: boolean;
  deprecationMessage?: string;
}

export interface DocExport {
  name: string;
  type: string;
  description: string;
  signature: string;
}

export interface DocClass {
  name: string;
  description: string;
  constructor: DocFunction | null;
  properties: DocProperty[];
  methods: DocFunction[];
  events: DocEvent[];
  extends: string[];
  implements: string[];
  abstract: boolean;
  since: string;
  deprecated: boolean;
}

export interface DocFunction {
  name: string;
  description: string;
  signature: string;
  params: DocParameter[];
  returnType: string;
  returnDescription: string;
  async: boolean;
  generator: boolean;
  examples: DocExample[];
  since: string;
  deprecated: boolean;
}

export interface DocParameter {
  name: string;
  type: string;
  description: string;
  optional: boolean;
  defaultValue?: string;
  rest: boolean;
}

export interface DocProperty {
  name: string;
  type: string;
  description: string;
  optional: boolean;
  readonly: boolean;
  static: boolean;
  defaultValue?: string;
}

export interface DocType {
  name: string;
  definition: string;
  description: string;
  properties: DocProperty[];
}

export interface DocInterface {
  name: string;
  description: string;
  properties: DocProperty[];
  methods: DocFunction[];
  extends: string[];
}

export interface DocEnum {
  name: string;
  description: string;
  members: DocEnumMember[];
}

export interface DocEnumMember {
  name: string;
  value: string | number;
  description: string;
}

export interface DocVariable {
  name: string;
  type: string;
  description: string;
  value: string;
  const: boolean;
}

export interface DocEvent {
  name: string;
  description: string;
  params: DocParameter[];
}

export interface DocExample {
  title: string;
  code: string;
  description: string;
  output?: string;
  language: string;
}

export const DOC_DEFAULTS: DocConfig = {
  title: 'Zoya 3.0 Documentation',
  description: 'Complete documentation for the Zoya programming language',
  version: '3.0.0',
  outputDir: './docs',
  sourceDir: './src',
  includeModules: [],
  excludePatterns: [],
  themes: 'default',
  generateSearchIndex: true,
  generateTutorials: true,
  generateExamples: true,
  interactive: false,
};

export class DocGenerator {
  private config: DocConfig;

  constructor(config?: Partial<DocConfig>) {
    this.config = { ...DOC_DEFAULTS, ...config };
  }

  async generate(): Promise<void> {
    const outputDir = this.config.outputDir;
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const modules = this.collectModules();
    const tutorials = new TutorialLibrary();
    for (const t of TUTORIALS) {
      tutorials.register(t);
    }

    const apiDocs = await this.generateApiDocs();
    const apiPath = path.join(outputDir, 'api.md');
    fs.writeFileSync(apiPath, apiDocs, 'utf-8');

    if (this.config.generateTutorials) {
      const tutorialPaths = await this.generateTutorials();
      const tuteDir = path.join(outputDir, 'tutorials');
      if (!fs.existsSync(tuteDir)) {
        fs.mkdirSync(tuteDir, { recursive: true });
      }
      for (const [i, content] of tutorialPaths.entries()) {
        const tute = tutorials.list()[i];
        if (tute) {
          fs.writeFileSync(path.join(tuteDir, `${tute.id}.md`), content, 'utf-8');
        }
      }
    }

    if (this.config.generateExamples) {
      const exampleContents = await this.generateExamples();
      const exDir = path.join(outputDir, 'examples');
      if (!fs.existsSync(exDir)) {
        fs.mkdirSync(exDir, { recursive: true });
      }
      for (let i = 0; i < exampleContents.length; i++) {
        fs.writeFileSync(path.join(exDir, `example-${i + 1}.md`), exampleContents[i], 'utf-8');
      }
    }

    if (this.config.generateSearchIndex) {
      const index = await this.generateSearchIndex();
      fs.writeFileSync(path.join(outputDir, 'search-index.json'), index, 'utf-8');
    }

    for (const mod of modules) {
      const markdown = this.generateMarkdown(mod);
      const modDir = path.join(outputDir, 'modules');
      if (!fs.existsSync(modDir)) {
        fs.mkdirSync(modDir, { recursive: true });
      }
      fs.writeFileSync(path.join(modDir, `${mod.name}.md`), markdown, 'utf-8');
    }
  }

  generateModuleDoc(module: DocModule): string {
    const md = new MarkdownBuilder();
    md.h1(module.name);
    md.p(module.description);

    if (module.deprecated) {
      md.blockquote(`**Deprecated**: ${module.deprecationMessage || 'This module is deprecated.'}`);
    }

    if (module.since) {
      md.p(`*Since: ${module.since}*`);
    }

    if (module.classes.length > 0) {
      md.h2('Classes');
      for (const cls of module.classes) {
        md.h3(cls.name);
        md.p(cls.description);
        if (cls.abstract) {
          md.p('*Abstract class*');
        }
        if (cls.extends.length > 0) {
          md.p(`**Extends:** ${cls.extends.join(', ')}`);
        }
        if (cls.implements.length > 0) {
          md.p(`**Implements:** ${cls.implements.join(', ')}`);
        }
        if (cls.constructor) {
          md.h4('Constructor');
          md.code(cls.constructor.signature, 'zoya');
        }
        if (cls.properties.length > 0) {
          md.h4('Properties');
          const headers = ['Name', 'Type', 'Description'];
          const rows = cls.properties.map((p) => [
            p.name,
            p.type,
            `${p.description}${p.readonly ? ' (readonly)' : ''}${p.optional ? ' (optional)' : ''}`,
          ]);
          md.table(headers, rows);
        }
        if (cls.methods.length > 0) {
          md.h4('Methods');
          for (const method of cls.methods) {
            md.p(`**${method.name}**`);
            md.code(method.signature, 'zoya');
            md.p(method.description);
          }
        }
        if (cls.events.length > 0) {
          md.h4('Events');
          for (const evt of cls.events) {
            md.p(`**${evt.name}**: ${evt.description}`);
          }
        }
      }
    }

    if (module.functions.length > 0) {
      md.h2('Functions');
      for (const fn of module.functions) {
        md.h3(fn.name);
        md.code(fn.signature, 'zoya');
        md.p(fn.description);
        if (fn.params.length > 0) {
          md.h4('Parameters');
          const headers = ['Name', 'Type', 'Description'];
          const rows = fn.params.map((p) => [
            p.name,
            p.type,
            `${p.description}${p.optional ? ' (optional)' : ''}${p.rest ? ' (rest)' : ''}`,
          ]);
          md.table(headers, rows);
        }
        if (fn.returnType) {
          md.p(`**Returns:** \`${fn.returnType}\` — ${fn.returnDescription}`);
        }
      }
    }

    if (module.types.length > 0) {
      md.h2('Types');
      for (const t of module.types) {
        md.h3(t.name);
        md.code(t.definition, 'zoya');
        md.p(t.description);
        if (t.properties.length > 0) {
          const headers = ['Name', 'Type', 'Description'];
          const rows = t.properties.map((p) => [p.name, p.type, p.description]);
          md.table(headers, rows);
        }
      }
    }

    if (module.interfaces.length > 0) {
      md.h2('Interfaces');
      for (const iface of module.interfaces) {
        md.h3(iface.name);
        md.p(iface.description);
        if (iface.extends.length > 0) {
          md.p(`**Extends:** ${iface.extends.join(', ')}`);
        }
        if (iface.properties.length > 0) {
          md.h4('Properties');
          const headers = ['Name', 'Type', 'Description'];
          const rows = iface.properties.map((p) => [p.name, p.type, p.description]);
          md.table(headers, rows);
        }
      }
    }

    if (module.enums.length > 0) {
      md.h2('Enums');
      for (const en of module.enums) {
        md.h3(en.name);
        md.p(en.description);
        if (en.members.length > 0) {
          const headers = ['Name', 'Value', 'Description'];
          const rows = en.members.map((m) => [m.name, String(m.value), m.description]);
          md.table(headers, rows);
        }
      }
    }

    if (module.variables.length > 0) {
      md.h2('Variables');
      for (const v of module.variables) {
        md.p(`**${v.name}**: \`${v.type}\`${v.const ? ' (const)' : ''}`);
        md.p(v.description);
        if (v.value) {
          md.code(v.value, 'zoya');
        }
      }
    }

    if (module.examples.length > 0) {
      md.h2('Examples');
      for (const ex of module.examples) {
        md.h3(ex.title);
        md.p(ex.description);
        md.code(ex.code, ex.language || 'zoya');
        if (ex.output) {
          md.p('**Output:**');
          md.code(ex.output);
        }
      }
    }

    return md.build();
  }

  async generateApiDocs(): Promise<string> {
    const modules = this.collectModules();
    const md = new MarkdownBuilder();
    md.h1(`${this.config.title} — API Reference`);
    md.p(this.config.description);
    md.p(`**Version:** ${this.config.version}`);

    const nav = this.buildNavigation(modules);
    md.h2('Modules');
    for (const section of nav) {
      md.h3(section.title);
      const items = section.children.map((c) => md.link(c.title, c.path));
      md.ul(items);
    }

    for (const mod of modules) {
      md.hr();
      md.append(this.generateModuleDoc(mod));
    }

    return md.build();
  }

  async generateTutorials(): Promise<string[]> {
    const library = new TutorialLibrary();
    for (const t of TUTORIALS) {
      library.register(t);
    }
    return library.list().map((t) => library.generateMarkdown(t.id));
  }

  async generateExamples(): Promise<string[]> {
    const generator = new ExampleGenerator();
    const examples = generator.generateExamples();
    return examples.map((ex) => {
      const md = new MarkdownBuilder();
      md.h1(ex.title);
      md.p(ex.description);
      md.code(ex.code, ex.language || 'zoya');
      if (ex.output) {
        md.h2('Output');
        md.code(ex.output);
      }
      return md.build();
    });
  }

  async generateSearchIndex(): Promise<string> {
    const modules = this.collectModules();
    const entries: { title: string; description: string; content: string; path: string }[] = [];

    for (const mod of modules) {
      entries.push({
        title: mod.name,
        description: mod.description,
        content: this.generateModuleDoc(mod),
        path: `modules/${mod.name}.md`,
      });
    }

    return JSON.stringify(
      {
        version: this.config.version,
        generated: new Date().toISOString(),
        entries,
      },
      null,
      2,
    );
  }

  generateMarkdown(module: DocModule): string {
    return this.generateModuleDoc(module);
  }

  generateHTML(module: DocModule): string {
    const md = this.generateMarkdown(module);
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(module.name)} — ${escapeHtml(this.config.title)}</title>
  <link rel="stylesheet" href="../styles/${escapeHtml(this.config.themes)}.css">
</head>
<body>
  <nav class="sidebar">
    <h2>${escapeHtml(this.config.title)}</h2>
    <p>Version ${escapeHtml(this.config.version)}</p>
  </nav>
  <main class="content">
    ${escapeHtml(md)}
  </main>
</body>
</html>`;
  }

  extractFromSource(_filePath: string): DocModule {
    return {
      name: path.basename(_filePath, path.extname(_filePath)),
      description: `Documentation extracted from ${_filePath}`,
      source: _filePath,
      exports: [],
      classes: [],
      functions: [],
      variables: [],
      types: [],
      interfaces: [],
      enums: [],
      examples: [],
      since: this.config.version,
      deprecated: false,
    };
  }

  buildNavigation(modules: DocModule[]): { title: string; children: { title: string; path: string }[] }[] {
    const groups = new Map<string, { title: string; path: string }[]>();
    for (const mod of modules) {
      const category = mod.name.includes('/') ? mod.name.split('/')[0] : 'core';
      if (!groups.has(category)) {
        groups.set(category, []);
      }
      groups.get(category)!.push({
        title: mod.name,
        path: `modules/${mod.name}.md`,
      });
    }
    return Array.from(groups.entries()).map(([title, children]) => ({
      title,
      children,
    }));
  }

  private collectModules(): DocModule[] {
    return [];
  }
}

export class TutorialGenerator {
  generateQuickStart(): string {
    const md = new MarkdownBuilder();
    md.h1('Quick Start Guide');
    md.p('Get started with Zoya in minutes.');
    md.h2('Installation');
    md.code('npm install -g zoya', 'bash');
    md.h2('Hello World');
    md.code('print("Hello, World!")', 'zoya');
    md.p('Save this as `hello.zoya` and run:');
    md.code('zoya run hello.zoya', 'bash');
    md.h2('Next Steps');
    md.ul([
      'Read the Language Basics tutorial',
      'Explore the standard library',
      'Try building a game with the engine',
    ]);
    return md.build();
  }

  generateLanguageBasics(): string {
    const md = new MarkdownBuilder();
    md.h1('Language Basics');
    md.h2('Variables');
    md.code('let name = "Zoya"\nconst version = 3.0', 'zoya');
    md.h2('Functions');
    md.code('fun greet(name: string) {\n    print("Hello, " + name + "!")\n}', 'zoya');
    md.h2('Control Flow');
    md.code('if condition {\n    // do something\n} else {\n    // do something else\n}', 'zoya');
    md.h2('Loops');
    md.code('for i in 0..10 {\n    print(i)\n}', 'zoya');
    return md.build();
  }

  generateGameDevGuide(): string {
    const md = new MarkdownBuilder();
    md.h1('Game Development Guide');
    md.p('Build 2D games with the Zoya game engine.');
    md.h2('Creating a Scene');
    md.code(`import { game, scene } from "engine"

let myScene = scene {
    name: "MainMenu",
    background: "dark_blue"
}`, 'zoya');
    md.h2('Adding Entities');
    md.code(`import { entity } from "engine"

let player = entity {
    sprite: "player.png",
    position: (x: 400, y: 300)
}`, 'zoya');
    return md.build();
  }

  generateAIDevGuide(): string {
    const md = new MarkdownBuilder();
    md.h1('AI Development Guide');
    md.p('Integrate AI capabilities into your Zoya applications.');
    md.h2('AI Client Setup');
    md.code(`import { ai } from "zoya:ai"

let client = ai {
    provider: "openai",
    model: "gpt-4"
}`, 'zoya');
    md.h2('Chat Completion');
    md.code('let response = client.chat("Hello!")\nprint(response)', 'zoya');
    return md.build();
  }

  generateCloudGuide(): string {
    const md = new MarkdownBuilder();
    md.h1('Cloud Services Guide');
    md.p('Use Zoya Cloud for backend services.');
    md.h2('Connecting');
    md.code(`import { cloud } from "zoya:cloud"

let app = cloud {
    project: "my-app",
    region: "us-east"
}\nawait app.connect()`, 'zoya');
    return md.build();
  }

  generatePackageGuide(): string {
    const md = new MarkdownBuilder();
    md.h1('Package Management Guide');
    md.p('Learn how to use and create Zoya packages.');
    md.h2('Installing Packages');
    md.code('zoya add http\nzoya add json', 'bash');
    md.h2('Using Packages');
    md.code(`import { http } from "http"
import { json } from "json"`, 'zoya');
    return md.build();
  }
}

export class ExampleGenerator {
  generateExamples(): DocExample[] {
    return [
      this.generateHelloWorld(),
      this.generateGameExample(),
      this.generateAIExample(),
      this.generateCloudExample(),
      this.generatePackageExample(),
    ];
  }

  generateHelloWorld(): DocExample {
    return {
      title: 'Hello World',
      code: 'print("Hello, World!")',
      description: 'The traditional Hello World program in Zoya.',
      output: 'Hello, World!',
      language: 'zoya',
    };
  }

  generateGameExample(): DocExample {
    return {
      title: 'Simple Game Loop',
      code: `import { game, entity, input } from "engine"

let player = entity {
    sprite: "player.png",
    position: (x: 400, y: 300),
    size: (width: 64, height: 64)
}

fun update(dt: number) {
    if input.isKeyDown("space") {
        print("Jump!")
    }
}

game.init(800, 600, "My Game")
game.start()`,
      description: 'A simple game loop with player entity and input handling.',
      language: 'zoya',
    };
  }

  generateAIExample(): DocExample {
    return {
      title: 'AI Chat Completion',
      code: `import { ai } from "zoya:ai"

let client = ai {
    provider: "openai",
    model: "gpt-4",
    temperature: 0.7
}

let response = client.chat("Explain Zoya in one sentence")
print(response)`,
      description: 'Using AI module to get a chat completion from OpenAI.',
      language: 'zoya',
    };
  }

  generateCloudExample(): DocExample {
    return {
      title: 'Cloud Database Query',
      code: `import { cloud } from "zoya:cloud"

let app = cloud {
    project: "my-app",
    region: "us-east"
}

await app.connect()

let users = await app.database.query("users", {
    filter: { active: true },
    limit: 10
})

for user in users {
    print(user.name)
}`,
      description: 'Querying a cloud database for active users.',
      language: 'zoya',
    };
  }

  generatePackageExample(): DocExample {
    return {
      title: 'Using HTTP Package',
      code: `import { http } from "http"

let response = http.get("https://api.example.com/data")
print(response.status)
print(response.body)`,
      description: 'Using the HTTP package to make a GET request.',
      language: 'zoya',
    };
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function generateAPIMarkdown(modules: DocModule[]): string {
  const md = new MarkdownBuilder();
  md.h1('Zoya API Reference');
  for (const mod of modules) {
    md.h2(mod.name);
    md.append(mod.description);
  }
  return md.build();
}

export function generateTutorialMarkdown(tutorials: Tutorial[]): string {
  const md = new MarkdownBuilder();
  md.h1('Tutorials');
  for (const t of tutorials) {
    md.h2(t.title);
    md.p(t.description);
    md.p(`Difficulty: ${t.difficulty} | Time: ${t.estimatedTime} min`);
  }
  return md.build();
}

export function generateIndexMarkdown(modules: DocModule[], tutorials: Tutorial[]): string {
  const md = new MarkdownBuilder();
  md.h1('Zoya Programming Language');
  md.p('Welcome to the Zoya documentation.');
  md.h2('Modules');
  for (const mod of modules) {
    md.ul([md.link(mod.name, `modules/${mod.name}.md`)]);
  }
  md.h2('Tutorials');
  for (const t of tutorials) {
    md.ul([md.link(t.title, `tutorials/${t.id}.md`)]);
  }
  return md.build();
}
