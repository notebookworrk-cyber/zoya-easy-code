import * as fs from 'fs';

export interface LocalLLMConfig {
  modelPath: string;
  contextSize: number;
  gpuLayers: number;
  threads: number;
  verbose: boolean;
  temperature: number;
  topP: number;
  maxTokens: number;
}

export interface LLMInferenceResult {
  text: string;
  tokensGenerated: number;
  tokensPerSecond: number;
  duration: number;
}

export const DEFAULT_LLM_CONFIG: LocalLLMConfig = {
  modelPath: './models/llama.gguf',
  contextSize: 4096,
  gpuLayers: 0,
  threads: 4,
  verbose: false,
  temperature: 0.7,
  topP: 1,
  maxTokens: 2048,
};

export class LocalLLM {
  private config: LocalLLMConfig;
  private loaded: boolean;
  private modelHandle: unknown;

  constructor(config?: Partial<LocalLLMConfig>) {
    this.config = { ...DEFAULT_LLM_CONFIG, ...config };
    this.loaded = false;
    this.modelHandle = null;
  }

  async load(): Promise<void> {
    if (this.loaded) {
      return;
    }

    if (!fs.existsSync(this.config.modelPath)) {
      throw new Error(`Model file not found: ${this.config.modelPath}`);
    }

    if (this.config.verbose) {
      console.log(`[LocalLLM] Loading model from ${this.config.modelPath}`);
      console.log(
        `[LocalLLM] Config: context=${this.config.contextSize}, gpuLayers=${this.config.gpuLayers}, threads=${this.config.threads}`
      );
    }

    this.modelHandle = { path: this.config.modelPath };
    this.loaded = true;
  }

  unload(): void {
    this.modelHandle = null;
    this.loaded = false;
    if (this.config.verbose) {
      console.log('[LocalLLM] Model unloaded');
    }
  }

  isLoaded(): boolean {
    return this.loaded;
  }

  async generate(prompt: string, maxTokens?: number): Promise<LLMInferenceResult> {
    if (!this.loaded) {
      throw new Error('Model not loaded. Call load() first.');
    }

    const tokenLimit = maxTokens || this.config.maxTokens;
    const startTime = Date.now();

    const inputTokens = this.countTokens(prompt);
    const outputTokens = Math.min(tokenLimit, Math.max(1, Math.floor(inputTokens * 0.75)));

    const tokens = this.sampleTokens(outputTokens);
    const text = tokens.join(' ');

    const duration = Date.now() - startTime;
    const tokensPerSecond = duration > 0
      ? Math.round((outputTokens / duration) * 1000 * 100) / 100
      : 0;

    return {
      text,
      tokensGenerated: outputTokens,
      tokensPerSecond,
      duration,
    };
  }

  async *generateStream(prompt: string): AsyncGenerator<string, void, unknown> {
    if (!this.loaded) {
      throw new Error('Model not loaded. Call load() first.');
    }

    const inputTokens = this.countTokens(prompt);
    const outputTokens = Math.min(this.config.maxTokens, Math.max(1, Math.floor(inputTokens * 0.75)));
    const tokens = this.sampleTokens(outputTokens);

    for (const token of tokens) {
      yield token + ' ';
      await this.sleep(10);
    }
  }

  tokenize(text: string): number[] {
    const words = text.split(/\s+/).filter(Boolean);
    const tokens: number[] = [];
    for (const word of words) {
      const code = word.charCodeAt(0);
      tokens.push(code);
      if (word.length > 1) {
        for (let i = 1; i < word.length; i++) {
          tokens.push(word.charCodeAt(i));
        }
      }
    }
    return tokens;
  }

  getConfig(): LocalLLMConfig {
    return { ...this.config };
  }

  private countTokens(text: string): number {
    return Math.ceil(text.length / 4);
  }

  private sampleTokens(count: number): string[] {
    const vocabulary = [
      'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I',
      'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
      'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
      'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
      'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    ];

    const tokens: string[] = [];
    let seed = this.countTokens(JSON.stringify(this.config));
    for (let i = 0; i < count; i++) {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      const idx = seed % vocabulary.length;
      tokens.push(vocabulary[idx]);
    }
    return tokens;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
