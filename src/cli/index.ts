#!/usr/bin/env node
import { runCommand } from './commands/run';
import { buildCommand } from './commands/build';
import { newCommand } from './commands/new';
import { testCommand } from './commands/test';

async function main() {
  const { default: chalk } = await import('chalk');
  const { Command } = await import('commander');

  const program = new Command();

  program
    .name('zoya')
    .version('3.0.0')
    .description('Zoya 3.0 Programming Language - Compiler, Engine and Ecosystem');

  program
    .command('run <file>')
    .description('Run a Zoya file')
    .option('--profile', 'Show timing breakdown for each compilation phase')
    .option('--verbose', 'Show detailed compilation information')
    .action(async (file: string, options: { profile?: boolean; verbose?: boolean }) => {
      try {
        await runCommand(file, options);
      } catch (err) {
        console.error(chalk.red('Error:'), (err as Error).message);
        process.exit(1);
      }
    });

  program
    .command('build <file>')
    .description('Build (compile to bytecode .zbc)')
    .option('-o, --output <path>', 'Output file path')
    .option('-O, --optimize <level>', 'Optimization level (0-3)', '1')
    .action(async (file: string, options: { output?: string; optimize?: string }) => {
      try {
        await buildCommand(file, options);
      } catch (err) {
        console.error(chalk.red('Error:'), (err as Error).message);
        process.exit(1);
      }
    });

  program
    .command('compile <file>')
    .description('Compile to native binary (stub)')
    .action(async () => {
      console.log(chalk.yellow('\u26A0  Native compilation is a stub.'));
      console.log(chalk.dim('  Use `zoya build` for bytecode compilation.'));
      console.log(chalk.dim('  Full LLVM-based native compilation is planned for Zoya 3.1.'));
    });

  program
    .command('test [file]')
    .description('Run tests')
    .action(async (file?: string) => {
      try {
        await testCommand(file);
      } catch (err) {
        console.error(chalk.red('Error:'), (err as Error).message);
        process.exit(1);
      }
    });

  program
    .command('benchmark [file]')
    .description('Run benchmarks')
    .action(async () => {
      console.log(chalk.yellow('\u26A0  Benchmarking is a stub.'));
      console.log(chalk.dim('  Use `zoya test` to run tests.'));
      console.log(chalk.dim('  Full benchmarking support is planned for Zoya 3.2.'));
    });

  program
    .command('coverage [file]')
    .description('Run coverage analysis')
    .action(async () => {
      console.log(chalk.yellow('\u26A0  Coverage analysis is a stub.'));
      console.log(chalk.dim('  Use a dedicated testing framework for coverage.'));
      console.log(chalk.dim('  Full coverage tooling is planned for Zoya 3.2.'));
    });

  program
    .command('new <template> <name>')
    .description('Create a new Zoya project from a template')
    .action(async (template: string, name: string) => {
      try {
        await newCommand(template, name);
      } catch (err) {
        console.error(chalk.red('Error:'), (err as Error).message);
        process.exit(1);
      }
    });

  program
    .command('add <package>')
    .description('Add a package to the current project')
    .action(async (pkg: string) => {
      console.log(chalk.yellow(`\u26A0  Package management is a stub.`));
      console.log(chalk.dim(`  '${pkg}' was not added. Use zoya publish to publish packages.`));
      console.log(chalk.dim('  Full package registry integration is planned for Zoya 3.1.'));
    });

  program
    .command('remove <package>')
    .description('Remove a package from the current project')
    .action(async (pkg: string) => {
      console.log(chalk.yellow(`\u26A0  Package management is a stub.`));
      console.log(chalk.dim(`  '${pkg}' was not removed.`));
      console.log(chalk.dim('  Full package registry integration is planned for Zoya 3.1.'));
    });

  program
    .command('search <query>')
    .description('Search for packages in the registry')
    .action(async (query: string) => {
      console.log(chalk.yellow('\u26A0  Package registry is a stub.'));
      console.log(chalk.dim(`  No results for '${query}'.`));
      console.log(chalk.dim('  Full package registry integration is planned for Zoya 3.1.'));
    });

  program
    .command('publish')
    .description('Publish a package to the registry')
    .action(async () => {
      console.log(chalk.yellow('\u26A0  Package publishing is a stub.'));
      console.log(chalk.dim('  Use zoya add <package> to add packages.'));
      console.log(chalk.dim('  Full package registry integration is planned for Zoya 3.1.'));
    });

  program
    .command('init')
    .description('Initialize a Zoya project in the current directory')
    .action(async () => {
      const path_ = await import('path');
      const name = path_.basename(process.cwd());
      await newCommand('library', name);
    });

  program
    .command('version')
    .description('Show version information')
    .action(() => {
      console.log(chalk.cyan('Zoya v3.0.0'));
      console.log(chalk.dim('  64-bit, bytecode VM, JIT planned'));
    });

  program
    .command('help')
    .description('Show help information')
    .action(() => {
      program.help();
    });

  if (process.argv.length <= 2) {
    program.help();
  }

  program.parse(process.argv);
}

main().catch((err) => {
  console.error('Fatal error:', (err as Error).message);
  process.exit(1);
});
