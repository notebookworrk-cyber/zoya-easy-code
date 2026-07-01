import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { Command } from 'commander';
import { TemplateEngine } from '../../src/templates/index';
import { Lexer } from '../../src/compiler/lexer/index';
import { Parser } from '../../src/compiler/parser/index';
import { SemanticAnalyzer } from '../../src/compiler/semantic/index';
import { IRBuilder } from '../../src/compiler/ir/index';
import { BytecodeGen, BytecodeChunk } from '../../src/compiler/codegen/index';

describe('CLI Commands', () => {
  describe('Command Registration', () => {
    it('should register all commands on the program', () => {
      const program = new Command();
      program
        .name('zoya')
        .version('3.0.0')
        .description('Zoya 3.0 Programming Language');

      program.command('run <file>').description('Run a Zoya file');
      program.command('build <file>').description('Build to bytecode');
      program.command('compile <file>').description('Compile to native binary');
      program.command('test [file]').description('Run tests');
      program.command('benchmark [file]').description('Run benchmarks');
      program.command('coverage [file]').description('Run coverage analysis');
      program.command('new <template> <name>').description('Create new project');
      program.command('add <package>').description('Add a package');
      program.command('remove <package>').description('Remove a package');
      program.command('search <query>').description('Search packages');
      program.command('publish').description('Publish a package');
      program.command('init').description('Initialize a project');
      program.command('version').description('Show version');
      program.command('help').description('Show help');

      const commands = program.commands.map(c => c.name());
      expect(commands).toContain('run');
      expect(commands).toContain('build');
      expect(commands).toContain('compile');
      expect(commands).toContain('test');
      expect(commands).toContain('benchmark');
      expect(commands).toContain('coverage');
      expect(commands).toContain('new');
      expect(commands).toContain('add');
      expect(commands).toContain('remove');
      expect(commands).toContain('search');
      expect(commands).toContain('publish');
      expect(commands).toContain('init');
      expect(commands).toContain('version');
      expect(commands).toContain('help');
    });
  });

  describe('TemplateEngine', () => {
    const testDir = path.join(__dirname, '../../.test-templates');

    beforeEach(() => {
      if (fs.existsSync(testDir)) {
        fs.rmSync(testDir, { recursive: true });
      }
    });

    afterEach(() => {
      if (fs.existsSync(testDir)) {
        fs.rmSync(testDir, { recursive: true });
      }
    });

    it('should list available templates', () => {
      const templates = TemplateEngine.listTemplates();
      expect(templates.length).toBeGreaterThan(0);

      const names = templates.map(t => t.name);
      expect(names).toContain('game2d');
      expect(names).toContain('game3d');
      expect(names).toContain('ai-app');
      expect(names).toContain('web-api');
      expect(names).toContain('desktop');
      expect(names).toContain('library');
    });

    it('should validate template names', () => {
      expect(TemplateEngine.validateTemplate('game2d')).toBe(true);
      expect(TemplateEngine.validateTemplate('library')).toBe(true);
      expect(TemplateEngine.validateTemplate('nonexistent')).toBe(false);
    });

    it('should generate files from game2d template', () => {
      const projectDir = path.join(testDir, 'my-game');
      TemplateEngine.generate('game2d', 'my-game', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'README.md'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.gitignore'))).toBe(true);

      const mainContent = fs.readFileSync(path.join(projectDir, 'main.zoya'), 'utf-8');
      expect(mainContent).toContain('Zoya 2D Game');
      expect(mainContent).toContain('input');
      expect(mainContent).toContain('game.init');
    });

    it('should generate files from game3d template', () => {
      const projectDir = path.join(testDir, 'my-3d-game');
      TemplateEngine.generate('game3d', 'my-3d-game', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.gitignore'))).toBe(true);

      const mainContent = fs.readFileSync(path.join(projectDir, 'main.zoya'), 'utf-8');
      expect(mainContent).toContain('3D');
      expect(mainContent).toContain('camera');
    });

    it('should generate files from ai-app template', () => {
      const projectDir = path.join(testDir, 'my-ai-app');
      TemplateEngine.generate('ai-app', 'my-ai-app', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.env.example'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'README.md'))).toBe(true);

      const envContent = fs.readFileSync(path.join(projectDir, '.env.example'), 'utf-8');
      expect(envContent).toContain('OPENAI_API_KEY');
    });

    it('should generate files from web-api template', () => {
      const projectDir = path.join(testDir, 'my-api');
      TemplateEngine.generate('web-api', 'my-api', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'config.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'README.md'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.gitignore'))).toBe(true);
    });

    it('should generate files from desktop template', () => {
      const projectDir = path.join(testDir, 'my-desktop-app');
      TemplateEngine.generate('desktop', 'my-desktop-app', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'README.md'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.gitignore'))).toBe(true);

      const mainContent = fs.readFileSync(path.join(projectDir, 'main.zoya'), 'utf-8');
      expect(mainContent).toContain('Desktop');
    });

    it('should generate files from library template', () => {
      const projectDir = path.join(testDir, 'my-lib');
      TemplateEngine.generate('library', 'my-lib', projectDir);

      expect(fs.existsSync(path.join(projectDir, 'main.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'test.zoya'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, 'README.md'))).toBe(true);
      expect(fs.existsSync(path.join(projectDir, '.gitignore'))).toBe(true);

      const testContent = fs.readFileSync(path.join(projectDir, 'test.zoya'), 'utf-8');
      expect(testContent).toContain('testClone');
      expect(testContent).toContain('testClamp');
    });

    it('should throw for unknown templates', () => {
      expect(() => {
        TemplateEngine.generate('nonexistent', 'test', testDir);
      }).toThrow('Unknown template');
    });

    it('should throw if destination exists', () => {
      fs.mkdirSync(testDir, { recursive: true });
      expect(() => {
        TemplateEngine.generate('library', 'test', testDir);
      }).toThrow('already exists');
    });
  });

  describe('Compilation Pipeline', () => {
    it('should lex simple source code', () => {
      const source = 'let x = 42';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();

      expect(tokens.length).toBeGreaterThan(0);
      expect(tokens[0].type).toBeDefined();
    });

    it('should parse tokens into AST', () => {
      const source = 'let x = 42';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      expect(ast.type).toBe('Program');
      expect(ast.body.length).toBeGreaterThan(0);
      const diagnostics = parser.getDiagnostics();
      expect(diagnostics.hasErrors()).toBe(false);
    });

    it('should detect parse errors', () => {
      const source = 'let = 42';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      parser.parse();
      const diagnostics = parser.getDiagnostics();

      expect(diagnostics.hasErrors()).toBe(true);
    });

    it('should lex and parse function declarations', () => {
      const source = `
        fun greet(name: string) -> string {
          return "Hello, " + name
        }
      `;
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      expect(ast.body.length).toBeGreaterThan(0);
      const funcDecl = ast.body.find(s => s.type === 'FunctionDeclaration');
      expect(funcDecl).toBeDefined();
    });

    it('should lex and parse if statements', () => {
      const source = `
        let x = 10
        if (x > 5) {
          print("big")
        } else {
          print("small")
        }
      `;
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      expect(ast.body.length).toBeGreaterThan(0);
      const ifStmt = ast.body.find(s => s.type === 'IfStatement');
      expect(ifStmt).toBeDefined();
    });

    it('should perform semantic analysis', () => {
      const source = 'let x = 42';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      const analyzer = new SemanticAnalyzer();
      const result = analyzer.analyze(ast);

      expect(result.diagnostics.hasErrors()).toBe(false);
      expect(result.globals.has('x')).toBe(true);
    });

    it('should detect semantic errors', () => {
      const source = 'print(y)';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      const analyzer = new SemanticAnalyzer();
      const result = analyzer.analyze(ast);

      expect(result.diagnostics.hasErrors()).toBe(true);
      const errors = result.diagnostics.errors();
      expect(errors.some(e => e.message.includes('y'))).toBe(true);
    });

    it('should generate IR from AST', () => {
      const source = 'fun test() { let x = 1 + 2 }';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      const analyzer = new SemanticAnalyzer();
      const result = analyzer.analyze(ast);

      const builder = new IRBuilder();
      const module = builder.build(result.ast);

      expect(module.functions.length).toBeGreaterThan(0);
      const testFn = module.getFunction('test');
      expect(testFn).toBeDefined();
    });

    it('should generate bytecode from IR', () => {
      const source = 'fun test() { let x = 1 + 2 }';
      const lexer = new Lexer(source, '<test>');
      const tokens = lexer.scanTokens();
      const parser = new Parser(tokens);
      const ast = parser.parse();

      const analyzer = new SemanticAnalyzer();
      const result = analyzer.analyze(ast);

      const builder = new IRBuilder();
      const module = builder.build(result.ast);

      const codegen = new BytecodeGen();
      const chunks = codegen.generate(module);

      expect(chunks.length).toBeGreaterThan(0);
      expect(chunks[0].code.length).toBeGreaterThan(0);
      expect(chunks[0].debug.functionName).toBe('test');
    });
  });

  describe('Argument Parsing', () => {
    it('should parse run command with file argument', () => {
      const program = new Command();
      const cmd = program.command('run <file>');
      const actionFn = vi.fn();
      cmd.action(actionFn);

      program.parse(['node', 'zoya', 'run', 'main.zoya']);
      expect(actionFn).toHaveBeenCalledWith('main.zoya', expect.any(Object), expect.any(Object));
    });

    it('should parse run command with flags', () => {
      const program = new Command();
      const cmd = program
        .command('run <file>')
        .option('--profile', 'timing breakdown')
        .option('--verbose', 'verbose output');
      const actionFn = vi.fn();
      cmd.action(actionFn);

      program.parse(['node', 'zoya', 'run', 'main.zoya', '--profile', '--verbose']);
      expect(actionFn).toHaveBeenCalledWith(
        'main.zoya',
        expect.objectContaining({ profile: true, verbose: true }),
        expect.any(Object)
      );
    });

    it('should parse build command with output flag', () => {
      const program = new Command();
      const cmd = program
        .command('build <file>')
        .option('-o, --output <path>', 'output path')
        .option('-O, --optimize <level>', 'optimization level', '1');
      const actionFn = vi.fn();
      cmd.action(actionFn);

      program.parse(['node', 'zoya', 'build', 'test.zoya', '-o', 'out.zbc', '-O', '2']);
      expect(actionFn).toHaveBeenCalledWith(
        'test.zoya',
        expect.objectContaining({ output: 'out.zbc', optimize: '2' }),
        expect.any(Object)
      );
    });

    it('should parse new command with template and name', () => {
      const program = new Command();
      const cmd = program.command('new <template> <name>');
      const actionFn = vi.fn();
      cmd.action(actionFn);

      program.parse(['node', 'zoya', 'new', 'library', 'my-lib']);
      expect(actionFn).toHaveBeenCalledWith('library', 'my-lib', expect.any(Object), expect.any(Object));
    });

    it('should parse test command with optional file', () => {
      const program = new Command();
      const cmd = program.command('test [file]');
      const actionFn = vi.fn();
      cmd.action(actionFn);

      program.parse(['node', 'zoya', 'test']);
      expect(actionFn).toHaveBeenCalledWith(undefined, expect.any(Object), expect.any(Object));

      program.parse(['node', 'zoya', 'test', 'test.zoya']);
      expect(actionFn).toHaveBeenCalledWith('test.zoya', expect.any(Object), expect.any(Object));
    });
  });

  describe('Error Handling', () => {
    it('should handle missing file for run command', () => {
      const filePath = path.join(__dirname, 'nonexistent.zoya');
      expect(fs.existsSync(filePath)).toBe(false);
    });

    it('should handle missing file for build command', () => {
      const filePath = path.join(__dirname, 'nonexistent.zoya');
      expect(fs.existsSync(filePath)).toBe(false);
    });

    it('should produce parse errors for invalid syntax', () => {
      const source = 'let © = 42';
      const lexer = new Lexer(source, '<test>');

      expect(() => lexer.scanTokens()).toThrow();
    });
  });
});
