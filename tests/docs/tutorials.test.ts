import { describe, it, expect } from 'vitest';
import { TutorialLibrary, TUTORIALS, Tutorial } from '../../src/docs/tutorials';

describe('TutorialLibrary', () => {
  it('registers and retrieves tutorials', () => {
    const lib = new TutorialLibrary();
    lib.register(TUTORIALS[0]);
    const t = lib.get('getting-started');
    expect(t).toBeDefined();
    expect(t!.title).toBe('Getting Started with Zoya');
  });

  it('returns undefined for unknown tutorial', () => {
    const lib = new TutorialLibrary();
    expect(lib.get('nonexistent')).toBeUndefined();
  });

  it('lists all registered tutorials', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const list = lib.list();
    expect(list.length).toBe(TUTORIALS.length);
  });

  it('lists tutorials by difficulty', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const beginner = lib.listByDifficulty('beginner');
    expect(beginner.length).toBeGreaterThan(0);
    for (const t of beginner) {
      expect(t.difficulty).toBe('beginner');
    }
  });

  it('lists tutorials by category', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const gameTuts = lib.listByCategory('game-development');
    expect(gameTuts.length).toBeGreaterThan(0);
    for (const t of gameTuts) {
      expect(t.category).toBe('game-development');
    }
  });

  it('returns empty list for unknown category', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    expect(lib.listByCategory('nonexistent')).toHaveLength(0);
  });

  it('searches tutorials by title', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const results = lib.search('Getting Started');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].id).toBe('getting-started');
  });

  it('searches tutorials by description', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const results = lib.search('Zoya game engine');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].id).toBe('game-dev');
  });

  it('searches tutorials by tags', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const results = lib.search('ai');
    expect(results.length).toBeGreaterThan(0);
  });

  it('returns empty array for no match', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    expect(lib.search('xyznonexistent')).toHaveLength(0);
  });

  it('generates markdown for a tutorial', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const md = lib.generateMarkdown('getting-started');
    expect(md).toContain('# Getting Started with Zoya');
    expect(md).toContain('print("Hello, World!")');
    expect(md).toContain('Step 1');
    expect(md).toContain('Step 5');
  });

  it('returns empty string for unknown tutorial in markdown', () => {
    const lib = new TutorialLibrary();
    expect(lib.generateMarkdown('nonexistent')).toBe('');
  });

  it('generates markdown with prerequisites', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const md = lib.generateMarkdown('game-dev');
    expect(md).toContain('Prerequisites');
    expect(md).toContain('getting-started');
  });

  it('generates markdown with challenge', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const md = lib.generateMarkdown('getting-started');
    expect(md).toContain('Challenge');
  });

  it('generates markdown with tags', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const md = lib.generateMarkdown('packages');
    expect(md).toContain('packages');
    expect(md).toContain('ecosystem');
  });

  it('generates HTML for a tutorial', () => {
    const lib = new TutorialLibrary();
    for (const t of TUTORIALS) {
      lib.register(t);
    }
    const html = lib.generateHTML('getting-started');
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('Getting Started with Zoya');
    expect(html).toContain('language-zoya');
  });

  it('returns empty string for unknown tutorial in HTML', () => {
    const lib = new TutorialLibrary();
    expect(lib.generateHTML('nonexistent')).toBe('');
  });
});

describe('TUTORIALS', () => {
  it('has all required tutorials', () => {
    const ids = TUTORIALS.map((t) => t.id);
    expect(ids).toContain('getting-started');
    expect(ids).toContain('game-dev');
    expect(ids).toContain('ai-integration');
    expect(ids).toContain('cloud-services');
    expect(ids).toContain('packages');
  });

  it('all tutorials have valid structure', () => {
    for (const t of TUTORIALS) {
      expect(t.title).toBeTruthy();
      expect(t.description).toBeTruthy();
      expect(t.steps.length).toBeGreaterThan(0);
      expect(['beginner', 'intermediate', 'advanced']).toContain(t.difficulty);
      expect(t.estimatedTime).toBeGreaterThan(0);
      expect(t.category).toBeTruthy();
      expect(t.tags.length).toBeGreaterThan(0);
    }
  });

  it('all tutorial steps have titles and content', () => {
    for (const t of TUTORIALS) {
      for (let i = 0; i < t.steps.length; i++) {
        const step = t.steps[i];
        expect(step.title).toBeTruthy();
        expect(step.content).toBeTruthy();
      }
    }
  });

  it('tutorial categories are consistent', () => {
    const validCategories = ['language', 'game-development', 'artificial-intelligence', 'cloud', 'package-management'];
    for (const t of TUTORIALS) {
      expect(validCategories).toContain(t.category);
    }
  });
});
