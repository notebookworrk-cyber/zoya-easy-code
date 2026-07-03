import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { LocalLLM, DEFAULT_LLM_CONFIG } from '../../src/ai/llm.js';

vi.mock('node:fs', () => ({
  existsSync: vi.fn(() => true),
  readFileSync: vi.fn(() => ''),
  writeFileSync: vi.fn(),
}));

describe('LocalLLM', () => {
  let llm: LocalLLM;

  beforeEach(() => {
    vi.clearAllMocks();
    llm = new LocalLLM({
      modelPath: './models/test.gguf',
      contextSize: 2048,
      threads: 2,
      verbose: false,
    });
  });

  afterEach(() => {
    if (llm && llm.isLoaded()) {
      llm.unload();
    }
  });

  describe('configuration', () => {
    it('applies default config when no arguments given', () => {
      const defaultLlm = new LocalLLM();
      const config = defaultLlm.getConfig();
      expect(config.modelPath).toBe('./models/llama.gguf');
      expect(config.contextSize).toBe(4096);
      expect(config.gpuLayers).toBe(0);
    });

    it('merges partial config with defaults', () => {
      const customLlm = new LocalLLM({ modelPath: './custom.gguf', threads: 8 });
      const config = customLlm.getConfig();
      expect(config.modelPath).toBe('./custom.gguf');
      expect(config.threads).toBe(8);
      expect(config.contextSize).toBe(4096);
    });

    it('returns copy of config that cannot be mutated externally', () => {
      const config = llm.getConfig();
      config.modelPath = '/hacked/path';
      expect(llm.getConfig().modelPath).toBe('./models/test.gguf');
    });
  });

  describe('model lifecycle', () => {
    it('starts not loaded', () => {
      expect(llm.isLoaded()).toBe(false);
    });

    it('loads successfully', async () => {
      await llm.load();
      expect(llm.isLoaded()).toBe(true);
    });

    it('throws when model file does not exist', async () => {
      const fs = await import('node:fs');
      vi.mocked(fs.existsSync).mockReturnValueOnce(false);
      const brokenLlm = new LocalLLM({ modelPath: '/nonexistent/model.gguf' });
      await expect(brokenLlm.load()).rejects.toThrow('Model file not found');
    });

    it('unloads after loading', async () => {
      await llm.load();
      expect(llm.isLoaded()).toBe(true);
      llm.unload();
      expect(llm.isLoaded()).toBe(false);
    });

    it('is idempotent on repeated load calls', async () => {
      await llm.load();
      await llm.load();
      expect(llm.isLoaded()).toBe(true);
    });
  });

  describe('token counting', () => {
    it('tokenizes text into numeric array', () => {
      const tokens = llm.tokenize('hello world');
      expect(Array.isArray(tokens)).toBe(true);
      expect(tokens.length).toBeGreaterThan(0);
      expect(tokens.every((t) => typeof t === 'number')).toBe(true);
    });

    it('handles empty string', () => {
      const tokens = llm.tokenize('');
      expect(tokens).toEqual([]);
    });

    it('handles multi-word input', () => {
      const tokens = llm.tokenize('one two three');
      expect(tokens.length).toBe(11);
    });
  });

  describe('generation', () => {
    it('throws if generating when not loaded', async () => {
      await expect(llm.generate('test')).rejects.toThrow('Model not loaded');
    });

    it('returns inference result after loading', async () => {
      await llm.load();
      const result = await llm.generate('Hello, how are you?');
      expect(result).toBeDefined();
      expect(typeof result.text).toBe('string');
      expect(result.text.length).toBeGreaterThan(0);
      expect(result.tokensGenerated).toBeGreaterThan(0);
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it('respects maxTokens parameter', async () => {
      await llm.load();
      const result = await llm.generate('Short prompt.', 5);
      expect(result.tokensGenerated).toBeLessThanOrEqual(5);
    });

    it('includes tokensPerSecond in result', async () => {
      await llm.load();
      const result = await llm.generate('Test');
      expect(typeof result.tokensPerSecond).toBe('number');
    });
  });

  describe('streaming', () => {
    it('throws if streaming when not loaded', async () => {
      const generator = llm.generateStream('test');
      await expect(generator.next()).rejects.toThrow('Model not loaded');
    });

    it('yields tokens after loading', async () => {
      await llm.load();
      const generator = llm.generateStream('Hello');
      const chunks: string[] = [];
      for await (const chunk of generator) {
        chunks.push(chunk);
      }
      expect(chunks.length).toBeGreaterThan(0);
    });
  });
});
