import * as path from 'path';
import chalk from 'chalk';
import { TemplateEngine } from '../../templates/index';

function formatTime(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(1)}µs`;
  if (ms < 1000) return `${ms.toFixed(2)}ms`;
  return `${(ms / 1000).toFixed(3)}s`;
}

export async function newCommand(template: string, name: string): Promise<void> {
  const dest = path.resolve(process.cwd(), name);
  const startTime = performance.now();

  const ora = await import('ora');
  const spinner = ora.default(`Creating '${name}' from '${template}' template...`).start();

  try {
    TemplateEngine.generate(template, name, dest);
    spinner.stop();

    const elapsed = performance.now() - startTime;

    console.log(chalk.green(`\n✓ Project '${name}' created${chalk.dim(` (${formatTime(elapsed)})`)}`));
    console.log(chalk.cyan(`  Location: ${chalk.bold(dest)}`));
    console.log('');

    const nextSteps = getNextSteps(template, name);
    console.log(chalk.dim('── Next Steps ──'));
    for (const step of nextSteps) {
      console.log(`  ${step}`);
    }
  } catch (err) {
    if (spinner) {
      spinner.stop();
    }
    const error = err as Error;
    console.error(chalk.red(`Error creating project: ${error.message}`));
    process.exit(1);
  }
}

function getNextSteps(template: string, name: string): string[] {
  switch (template) {
    case 'game2d':
    case 'game3d':
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  zoya run main.zoya`),
        chalk.dim('  Edit main.zoya to build your game world.'),
        chalk.dim('  See README.md for the full API reference.'),
      ];
    case 'ai-app':
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  cp .env.example .env`),
        chalk.cyan(`  # Edit .env with your API keys`),
        chalk.cyan(`  zoya run main.zoya`),
        chalk.dim('  See README.md for configuration details.'),
      ];
    case 'web-api':
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  zoya run main.zoya`),
        chalk.cyan(`  # Server starts on http://localhost:8080`),
        chalk.dim('  Edit config.zoya to change port and settings.'),
        chalk.dim('  See README.md for API documentation.'),
      ];
    case 'desktop':
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  zoya run main.zoya`),
        chalk.dim('  Edit main.zoya to build your UI.'),
        chalk.dim('  See README.md for the UI API reference.'),
      ];
    case 'library':
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  zoya test test.zoya`),
        chalk.dim('  Edit main.zoya to implement your library.'),
        chalk.dim('  Edit test.zoya to add more tests.'),
        chalk.dim('  See README.md for documentation guidelines.'),
      ];
    default:
      return [
        chalk.cyan(`  cd ${name}`),
        chalk.cyan(`  zoya run main.zoya`),
      ];
  }
}
