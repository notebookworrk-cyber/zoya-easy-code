export interface Tutorial {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number;
  prerequisites: string[];
  steps: TutorialStep[];
  tags: string[];
  category: string;
}

export interface TutorialStep {
  title: string;
  content: string;
  code?: string;
  expectedOutput?: string;
  tip?: string;
  warning?: string;
  challenge?: string;
}

export class TutorialLibrary {
  private tutorials: Map<string, Tutorial>;

  constructor() {
    this.tutorials = new Map();
  }

  register(tutorial: Tutorial): void {
    this.tutorials.set(tutorial.id, tutorial);
  }

  get(id: string): Tutorial | undefined {
    return this.tutorials.get(id);
  }

  list(): Tutorial[] {
    return Array.from(this.tutorials.values());
  }

  listByDifficulty(difficulty: Tutorial['difficulty']): Tutorial[] {
    return this.list().filter((t) => t.difficulty === difficulty);
  }

  listByCategory(category: string): Tutorial[] {
    return this.list().filter((t) => t.category === category);
  }

  search(query: string): Tutorial[] {
    const lower = query.toLowerCase();
    return this.list().filter(
      (t) =>
        t.title.toLowerCase().includes(lower) ||
        t.description.toLowerCase().includes(lower) ||
        t.tags.some((tag) => tag.toLowerCase().includes(lower)) ||
        t.steps.some((s) => s.title.toLowerCase().includes(lower)),
    );
  }

  generateMarkdown(id: string): string {
    const tutorial = this.tutorials.get(id);
    if (!tutorial) return '';

    const lines: string[] = [];
    lines.push(`# ${tutorial.title}`);
    lines.push('');
    lines.push(tutorial.description);
    lines.push('');
    lines.push(`**Difficulty:** ${tutorial.difficulty}`);
    lines.push('');
    lines.push(`**Estimated Time:** ${tutorial.estimatedTime} minutes`);
    lines.push('');

    if (tutorial.prerequisites.length > 0) {
      lines.push('## Prerequisites');
      lines.push('');
      for (const prereq of tutorial.prerequisites) {
        lines.push(`- [${prereq}](tutorials/${prereq}.md)`);
      }
      lines.push('');
    }

    lines.push('---');
    lines.push('');

    for (let i = 0; i < tutorial.steps.length; i++) {
      const step = tutorial.steps[i];
      lines.push(`## Step ${i + 1}: ${step.title}`);
      lines.push('');
      lines.push(step.content);
      lines.push('');

      if (step.code) {
        lines.push('```zoya');
        lines.push(step.code);
        lines.push('```');
        lines.push('');
      }

      if (step.expectedOutput) {
        lines.push('**Expected Output:**');
        lines.push('');
        lines.push('```');
        lines.push(step.expectedOutput);
        lines.push('```');
        lines.push('');
      }

      if (step.tip) {
        lines.push(`> 💡 **Tip:** ${step.tip}`);
        lines.push('');
      }

      if (step.warning) {
        lines.push(`> ⚠️ **Warning:** ${step.warning}`);
        lines.push('');
      }

      if (step.challenge) {
        lines.push('### Challenge');
        lines.push('');
        lines.push(step.challenge);
        lines.push('');
      }

      lines.push('---');
      lines.push('');
    }

    if (tutorial.tags.length > 0) {
      lines.push('## Tags');
      lines.push('');
      lines.push(tutorial.tags.map((t) => `\`${t}\``).join(' '));
      lines.push('');
    }

    return lines.join('\n');
  }

  generateHTML(id: string): string {
    const tutorial = this.tutorials.get(id);
    if (!tutorial) return '';

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(tutorial.title)} — Tutorial</title>
  <link rel="stylesheet" href="../styles/tutorial.css">
</head>
<body>
  <article class="tutorial">
    <header>
      <h1>${escapeHtml(tutorial.title)}</h1>
      <p class="meta">Difficulty: ${tutorial.difficulty} | ${tutorial.estimatedTime} min</p>
    </header>
    <section class="content">
      ${tutorial.steps.map((step, i) => `
        <div class="step">
          <h2>Step ${i + 1}: ${escapeHtml(step.title)}</h2>
          <p>${escapeHtml(step.content)}</p>
          ${step.code ? `<pre><code class="language-zoya">${escapeHtml(step.code)}</code></pre>` : ''}
        </div>
      `).join('\n')}
    </section>
  </article>
</body>
</html>`;
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

export const TUTORIALS: Tutorial[] = [
  {
    id: 'getting-started',
    title: 'Getting Started with Zoya',
    description: 'Learn the basics of the Zoya programming language',
    difficulty: 'beginner',
    estimatedTime: 15,
    prerequisites: [],
    steps: [
      {
        title: 'Hello World',
        content: 'Welcome to Zoya! Let us start with the traditional Hello World program.\n\nIn Zoya, you use the `print()` function to output text to the console.',
        code: 'print("Hello, World!")',
        expectedOutput: 'Hello, World!',
        challenge: 'Try printing your name instead!',
      },
      {
        title: 'Variables',
        content: 'Variables in Zoya are declared with `let` (mutable) or `const` (immutable).\n\nZoya infers types automatically, but you can also specify them explicitly.',
        code: 'let name = "Zoya"\nconst version = 3.0\nlet count: number = 42\n\nprint(name)\nprint(version)\nprint(count)',
        expectedOutput: 'Zoya\n3\n42',
      },
      {
        title: 'Functions',
        content: 'Functions are defined with the `fun` keyword. They can have parameters and return values.\n\nArrow syntax `->` is also supported for simple functions.',
        code: 'fun greet(name: string) {\n    print("Hello, " + name + "!")\n}\n\nfun add(a: number, b: number) -> number {\n    return a + b\n}\n\ngreet("World")\nprint(add(2, 3))',
        expectedOutput: 'Hello, World!\n5',
      },
      {
        title: 'Control Flow',
        content: 'Zoya supports if/elif/else, while, for, and loop statements for control flow.',
        code: 'for i in 1..5 {\n    if i % 2 == 0 {\n        print(i + " is even")\n    } else {\n        print(i + " is odd")\n    }\n}',
        expectedOutput: '1 is odd\n2 is even\n3 is odd\n4 is even\n5 is odd',
      },
      {
        title: 'Lists and Objects',
        content: 'Zoya has built-in support for lists (arrays) and objects (dictionaries/maps).',
        code: 'let fruits = ["apple", "banana", "cherry"]\nfruits.push("date")\n\nfor fruit in fruits {\n    print(fruit)\n}\n\nlet person = {\n    name: "Alice",\n    age: 30,\n    city: "New York"\n}\nprint(person.name)',
        expectedOutput: 'apple\nbanana\ncherry\ndate\nAlice',
      },
    ],
    tags: ['basics', 'beginner'],
    category: 'language',
  },
  {
    id: 'game-dev',
    title: '2D Game Development',
    description: 'Build your first 2D game with the Zoya game engine',
    difficulty: 'intermediate',
    estimatedTime: 30,
    prerequisites: ['getting-started'],
    steps: [
      {
        title: 'Creating a Game',
        content: 'The Zoya game engine makes it easy to create 2D games. Start by creating a game window and a scene.',
        code: 'import { game, scene, sprite } from "engine"\n\nlet myScene = scene {\n    name: "MainMenu",\n    background: "dark_blue"\n}\n\nfun init() {\n    game.init(800, 600, "My Game")\n    game.loadScene(myScene)\n}',
      },
      {
        title: 'Adding Sprites',
        content: 'Sprites are visual elements in your game. You can add them to a scene with position and size.',
        code: 'import { game, entity } from "engine"\n\nfun createPlayer() {\n    let player = entity {\n        sprite: "player.png",\n        position: (x: 400, y: 300),\n        size: (width: 64, height: 64)\n    }\n    return player\n}',
      },
      {
        title: 'Handling Input',
        content: 'Use the input module to handle keyboard, mouse, and touch input.',
        code: 'import { input } from "engine"\n\nfun update(dt: number) {\n    if input.isKeyDown("space") {\n        print("Jump!")\n    }\n    \n    if input.isKeyPressed("escape") {\n        game.quit()\n    }\n}',
      },
    ],
    tags: ['game', '2d', 'engine'],
    category: 'game-development',
  },
  {
    id: 'ai-integration',
    title: 'AI Integration',
    description: 'Integrate AI capabilities into your Zoya applications',
    difficulty: 'intermediate',
    estimatedTime: 20,
    prerequisites: ['getting-started'],
    steps: [
      {
        title: 'Setting up AI',
        content: 'Zoya provides first-class AI support through its AI module. You can create AI clients that connect to various providers.',
        code: 'import { ai } from "zoya:ai"\n\nlet client = ai {\n    provider: "openai",\n    model: "gpt-4",\n    temperature: 0.7\n}\n\nlet response = client.chat("Explain Zoya in one sentence")\nprint(response)',
      },
      {
        title: 'Creating an Agent',
        content: 'AI Agents can autonomously execute tasks using tools.',
        code: 'import { agent } from "zoya:ai"\n\nlet myAgent = agent {\n    name: "Helper",\n    goal: "Answer user questions about Zoya",\n    tools: [searchDocs, runCode]\n}\n\nmyAgent.run("How do I create a game in Zoya?")',
      },
    ],
    tags: ['ai', 'llm', 'agent'],
    category: 'artificial-intelligence',
  },
  {
    id: 'cloud-services',
    title: 'Cloud Services',
    description: 'Use Zoya Cloud for backend services',
    difficulty: 'intermediate',
    estimatedTime: 25,
    prerequisites: ['getting-started'],
    steps: [
      {
        title: 'Connecting to Cloud',
        content: 'Zoya Cloud provides authentication, database, storage, and more.',
        code: 'import { cloud } from "zoya:cloud"\n\nlet app = cloud {\n    project: "my-app",\n    region: "us-east"\n}\n\nawait app.connect()\n\nlet user = await app.auth.login("user@example.com", "password123")\nprint("Welcome, " + user.username)',
      },
    ],
    tags: ['cloud', 'backend', 'database'],
    category: 'cloud',
  },
  {
    id: 'packages',
    title: 'Using Packages',
    description: 'Learn how to use and create Zoya packages',
    difficulty: 'beginner',
    estimatedTime: 10,
    prerequisites: ['getting-started'],
    steps: [
      {
        title: 'Installing Packages',
        content: 'Zoya has a built-in package manager. You can install packages from the registry.',
        code: '# In your terminal:\nzoya add http\nzoya add json\n\n# Then in your code:\nimport { http } from "http"\nimport { json } from "json"',
      },
    ],
    tags: ['packages', 'ecosystem'],
    category: 'package-management',
  },
];
