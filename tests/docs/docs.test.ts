import { describe, it, expect } from 'vitest';
import { DocGenerator, DOC_DEFAULTS, ExampleGenerator, TutorialGenerator, generateAPIMarkdown, generateIndexMarkdown, generateTutorialMarkdown } from '../../src/docs/index';
import { DocModule } from '../../src/docs/index';
import { Tutorial } from '../../src/docs/tutorials';

function createMockModule(name: string): DocModule {
  return {
    name,
    description: `Description of ${name}`,
    source: `src/${name}.ts`,
    exports: [{ name: 'export1', type: 'function', description: 'An export', signature: 'fun export1()' }],
    classes: [
      {
        name: 'TestClass',
        description: 'A test class',
        constructor: null,
        properties: [{ name: 'prop1', type: 'string', description: 'A property', optional: false, readonly: false, static: false }],
        methods: [
          {
            name: 'method1',
            description: 'A method',
            signature: 'fun method1(): void',
            params: [],
            returnType: 'void',
            returnDescription: 'Nothing',
            async: false,
            generator: false,
            examples: [],
            since: '3.0.0',
            deprecated: false,
          },
        ],
        events: [],
        extends: [],
        implements: [],
        abstract: false,
        since: '3.0.0',
        deprecated: false,
      },
    ],
    functions: [
      {
        name: 'helper',
        description: 'A helper function',
        signature: 'fun helper(x: number): number',
        params: [{ name: 'x', type: 'number', description: 'Input value', optional: false, rest: false }],
        returnType: 'number',
        returnDescription: 'The result',
        async: false,
        generator: false,
        examples: [],
        since: '3.0.0',
        deprecated: false,
      },
    ],
    variables: [],
    types: [],
    interfaces: [],
    enums: [],
    examples: [{ title: 'Example', code: 'print("hello")', description: 'An example', output: 'hello', language: 'zoya' }],
    since: '3.0.0',
    deprecated: false,
  };
}

describe('DocGenerator', () => {
  it('creates with default config', () => {
    const gen = new DocGenerator();
    expect(gen).toBeDefined();
  });

  it('creates with custom config', () => {
    const gen = new DocGenerator({ title: 'Custom', version: '1.0.0' });
    expect(gen).toBeDefined();
  });

  it('generates module documentation markdown', () => {
    const gen = new DocGenerator({ generateSearchIndex: false, generateTutorials: false, generateExamples: false });
    const mod = createMockModule('test-module');
    const md = gen.generateModuleDoc(mod);
    expect(md).toContain('# test-module');
    expect(md).toContain('Description of test-module');
    expect(md).toContain('TestClass');
    expect(md).toContain('helper');
    expect(md).toContain('print("hello")');
  });

  it('generates HTML for a module', () => {
    const gen = new DocGenerator();
    const mod = createMockModule('test');
    const html = gen.generateHTML(mod);
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('test');
    expect(html).toContain('Zoya 3.0 Documentation');
  });

  it('generates API docs markdown', async () => {
    const gen = new DocGenerator();
    const apiDocs = await gen.generateApiDocs();
    expect(apiDocs).toContain('Zoya 3.0 Documentation');
    expect(apiDocs).toContain('API Reference');
    expect(apiDocs).toContain('3.0.0');
  });

  it('generates search index', async () => {
    const gen = new DocGenerator();
    const index = await gen.generateSearchIndex();
    const parsed = JSON.parse(index);
    expect(parsed).toHaveProperty('version');
    expect(parsed).toHaveProperty('generated');
    expect(parsed).toHaveProperty('entries');
  });

  it('builds navigation from modules', () => {
    const gen = new DocGenerator();
    const modules = [createMockModule('core/math'), createMockModule('core/string')];
    const nav = gen.buildNavigation(modules);
    expect(nav.length).toBeGreaterThan(0);
    expect(nav[0].children.length).toBe(2);
  });

  it('extracts from source file', () => {
    const gen = new DocGenerator();
    const doc = gen.extractFromSource('src/example.ts');
    expect(doc.name).toBe('example');
    expect(doc.source).toBe('src/example.ts');
  });

  it('generates tutorials', async () => {
    const gen = new DocGenerator({ generateTutorials: true, generateExamples: false, generateSearchIndex: false });
    const tutorials = await gen.generateTutorials();
    expect(tutorials.length).toBeGreaterThan(0);
    for (const t of tutorials) {
      expect(typeof t).toBe('string');
      expect(t.length).toBeGreaterThan(0);
    }
  });

  it('generates examples', async () => {
    const gen = new DocGenerator({ generateExamples: true, generateTutorials: false, generateSearchIndex: false });
    const examples = await gen.generateExamples();
    expect(examples.length).toBeGreaterThan(0);
    for (const ex of examples) {
      expect(typeof ex).toBe('string');
    }
  });

  it('generates markdown for deprecated module', () => {
    const gen = new DocGenerator();
    const mod = createMockModule('old-module');
    const deprecated: DocModule = { ...mod, deprecated: true, deprecationMessage: 'Use new-module instead' };
    const md = gen.generateModuleDoc(deprecated);
    expect(md).toContain('Deprecated');
    expect(md).toContain('Use new-module instead');
  });

  it('generates markdown for module with enums', () => {
    const gen = new DocGenerator();
    const mod = createMockModule('enum-module');
    const withEnums: DocModule = {
      ...mod,
      enums: [
        {
          name: 'Color',
          description: 'Color enum',
          members: [
            { name: 'Red', value: 0, description: 'Red color' },
            { name: 'Green', value: 1, description: 'Green color' },
          ],
        },
      ],
    };
    const md = gen.generateModuleDoc(withEnums);
    expect(md).toContain('Color');
    expect(md).toContain('Red');
    expect(md).toContain('Green');
  });
});

describe('DOC_DEFAULTS', () => {
  it('has correct default values', () => {
    expect(DOC_DEFAULTS.title).toBe('Zoya 3.0 Documentation');
    expect(DOC_DEFAULTS.version).toBe('3.0.0');
    expect(DOC_DEFAULTS.generateSearchIndex).toBe(true);
    expect(DOC_DEFAULTS.generateTutorials).toBe(true);
    expect(DOC_DEFAULTS.generateExamples).toBe(true);
  });
});

describe('TutorialGenerator', () => {
  it('generates quick start guide', () => {
    const gen = new TutorialGenerator();
    const guide = gen.generateQuickStart();
    expect(guide).toContain('Quick Start Guide');
    expect(guide).toContain('print("Hello, World!")');
  });

  it('generates language basics', () => {
    const gen = new TutorialGenerator();
    const basics = gen.generateLanguageBasics();
    expect(basics).toContain('Language Basics');
    expect(basics).toContain('let name');
  });

  it('generates game dev guide', () => {
    const gen = new TutorialGenerator();
    const guide = gen.generateGameDevGuide();
    expect(guide).toContain('Game Development Guide');
    expect(guide).toContain('entity');
  });

  it('generates AI dev guide', () => {
    const gen = new TutorialGenerator();
    const guide = gen.generateAIDevGuide();
    expect(guide).toContain('AI Development Guide');
    expect(guide).toContain('gpt-4');
  });

  it('generates cloud guide', () => {
    const gen = new TutorialGenerator();
    const guide = gen.generateCloudGuide();
    expect(guide).toContain('Cloud Services Guide');
    expect(guide).toContain('zoya:cloud');
  });

  it('generates package guide', () => {
    const gen = new TutorialGenerator();
    const guide = gen.generatePackageGuide();
    expect(guide).toContain('Package Management Guide');
    expect(guide).toContain('zoya add');
  });
});

describe('ExampleGenerator', () => {
  it('generates all examples', () => {
    const gen = new ExampleGenerator();
    const examples = gen.generateExamples();
    expect(examples.length).toBe(5);
  });

  it('generates hello world', () => {
    const gen = new ExampleGenerator();
    const ex = gen.generateHelloWorld();
    expect(ex.title).toBe('Hello World');
    expect(ex.code).toContain('print');
    expect(ex.language).toBe('zoya');
  });

  it('generates game example', () => {
    const gen = new ExampleGenerator();
    const ex = gen.generateGameExample();
    expect(ex.title).toBe('Simple Game Loop');
    expect(ex.code).toContain('engine');
  });

  it('generates AI example', () => {
    const gen = new ExampleGenerator();
    const ex = gen.generateAIExample();
    expect(ex.title).toBe('AI Chat Completion');
    expect(ex.code).toContain('zoya:ai');
  });

  it('generates cloud example', () => {
    const gen = new ExampleGenerator();
    const ex = gen.generateCloudExample();
    expect(ex.title).toBe('Cloud Database Query');
    expect(ex.code).toContain('zoya:cloud');
  });

  it('generates package example', () => {
    const gen = new ExampleGenerator();
    const ex = gen.generatePackageExample();
    expect(ex.title).toBe('Using HTTP Package');
    expect(ex.code).toContain('http');
  });
});

describe('generateAPIMarkdown', () => {
  it('generates API reference from modules', () => {
    const modules = [createMockModule('core'), createMockModule('utils')];
    const md = generateAPIMarkdown(modules);
    expect(md).toContain('Zoya API Reference');
    expect(md).toContain('core');
    expect(md).toContain('utils');
  });
});

describe('generateIndexMarkdown', () => {
  it('generates index from modules and tutorials', () => {
    const modules = [createMockModule('core')];
    const tutorials: Tutorial[] = [];
    const md = generateIndexMarkdown(modules, tutorials);
    expect(md).toContain('Zoya Programming Language');
    expect(md).toContain('core');
  });
});

describe('generateTutorialMarkdown', () => {
  it('generates tutorial overview from tutorials', () => {
    const tutorials: Tutorial[] = [];
    const md = generateTutorialMarkdown(tutorials);
    expect(md).toContain('Tutorials');
  });
});
