import * as fs from 'fs';
import * as path from 'path';
import { TEMPLATES } from './content';

export interface TemplateInfo {
  name: string;
  description: string;
  category: 'game' | 'ai' | 'web' | 'desktop' | 'library';
  files: string[];
}

const TEMPLATE_METADATA: Record<string, TemplateInfo> = {
  game2d: {
    name: 'game2d',
    description: '2D game project with sprite loading, input handling, and ECS stub',
    category: 'game',
    files: ['main.zoya', 'README.md', '.gitignore'],
  },
  game3d: {
    name: 'game3d',
    description: '3D game project with camera, lighting, and model loading stub',
    category: 'game',
    files: ['main.zoya', 'README.md', '.gitignore'],
  },
  'ai-app': {
    name: 'ai-app',
    description: 'AI application with chat client and tool calling support',
    category: 'ai',
    files: ['main.zoya', '.env.example', 'README.md'],
  },
  'web-api': {
    name: 'web-api',
    description: 'RESTful web API with routing, middleware, and database models',
    category: 'web',
    files: ['main.zoya', 'config.zoya', 'README.md', '.gitignore'],
  },
  desktop: {
    name: 'desktop',
    description: 'Desktop application with window management and UI components',
    category: 'desktop',
    files: ['main.zoya', 'README.md', '.gitignore'],
  },
  library: {
    name: 'library',
    description: 'Reusable Zoya library with tests and documentation',
    category: 'library',
    files: ['main.zoya', 'test.zoya', 'README.md', '.gitignore'],
  },
};

export class TemplateEngine {
  static listTemplates(): TemplateInfo[] {
    return Object.values(TEMPLATE_METADATA);
  }

  static getTemplate(name: string): TemplateInfo | undefined {
    return TEMPLATE_METADATA[name];
  }

  static validateTemplate(name: string): boolean {
    return name in TEMPLATES;
  }

  static generate(template: string, projectName: string, dest: string): void {
    if (!this.validateTemplate(template)) {
      const available = Object.keys(TEMPLATES).join(', ');
      throw new Error(
        `Unknown template: '${template}'. Available templates: ${available}`
      );
    }

    if (fs.existsSync(dest)) {
      throw new Error(`Directory already exists: ${dest}`);
    }

    const files = TEMPLATES[template];
    fs.mkdirSync(dest, { recursive: true });

    for (const [relativePath, content] of Object.entries(files)) {
      const fullPath = path.join(dest, relativePath);
      fs.mkdirSync(path.dirname(fullPath), { recursive: true });

      let processedContent = content;
      if (typeof content === 'string') {
        processedContent = content.replace(/\$\{projectName\}/g, projectName);
      }

      fs.writeFileSync(fullPath, processedContent, 'utf-8');
    }
  }
}
