import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AIClient, AI_DEFAULTS } from '../../src/ai/index.js';
import type { ToolDefinition, ChatMessage, ToolCall } from '../../src/ai/index.js';

describe('AIClient', () => {
  let client: AIClient;

  beforeEach(() => {
    client = new AIClient({ apiKey: 'test-key' });
    vi.restoreAllMocks();
  });

  describe('configuration', () => {
    it('applies default config when no arguments given', () => {
      const defaultClient = new AIClient();
      const config = defaultClient.getConfig();
      expect(config.provider).toBe('openai');
      expect(config.model).toBe('gpt-4');
      expect(config.maxTokens).toBe(2048);
    });

    it('merges partial config with defaults', () => {
      const customClient = new AIClient({ model: 'gpt-3.5-turbo', temperature: 0.5 });
      const config = customClient.getConfig();
      expect(config.model).toBe('gpt-3.5-turbo');
      expect(config.temperature).toBe(0.5);
      expect(config.maxTokens).toBe(2048);
    });

    it('updates config via updateConfig', () => {
      client.updateConfig({ temperature: 0.2, maxTokens: 4096 });
      const config = client.getConfig();
      expect(config.temperature).toBe(0.2);
      expect(config.maxTokens).toBe(4096);
    });
  });

  describe('chat message management', () => {
    it('builds conversation history when system prompt set', () => {
      client.setSystemPrompt('You are a helpful assistant.');
      const history = client.getHistory();
      expect(history).toHaveLength(1);
      expect(history[0].role).toBe('system');
      expect(history[0].content).toBe('You are a helpful assistant.');
    });

    it('replaces existing system prompt on second call', () => {
      client.setSystemPrompt('First prompt');
      client.setSystemPrompt('Second prompt');
      const systemMessages = client.getHistory().filter((m) => m.role === 'system');
      expect(systemMessages).toHaveLength(1);
      expect(systemMessages[0].content).toBe('Second prompt');
    });

    it('returns copy of history that cannot be mutated externally', () => {
      client.setSystemPrompt('system');
      const history = client.getHistory();
      history.push({ role: 'user', content: 'injected' });
      expect(client.getHistory()).toHaveLength(1);
    });

    it('clears all history', () => {
      client.setSystemPrompt('system');
      client.clearHistory();
      expect(client.getHistory()).toHaveLength(0);
    });
  });

  describe('tool registration and execution', () => {
    it('registers and executes a tool', async () => {
      const mockHandler = vi.fn().mockResolvedValue('tool result');
      const tool: ToolDefinition = {
        name: 'test_tool',
        description: 'A test tool',
        parameters: { type: 'object', properties: {} },
        handler: mockHandler,
      };

      client.registerTool(tool);

      const toolCall: ToolCall = {
        id: 'call_1',
        type: 'function',
        function: { name: 'test_tool', arguments: '{}' },
      };

      const result = await client.executeToolCall(toolCall);
      expect(result).toBe('tool result');
      expect(mockHandler).toHaveBeenCalledWith({});
    });

    it('throws error for unknown tool', async () => {
      const toolCall: ToolCall = {
        id: 'call_1',
        type: 'function',
        function: { name: 'nonexistent_tool', arguments: '{}' },
      };

      await expect(client.executeToolCall(toolCall)).rejects.toThrow(
        'Tool not found: nonexistent_tool'
      );
    });

    it('removes a registered tool', async () => {
      const tool: ToolDefinition = {
        name: 'removable',
        description: 'Will be removed',
        parameters: { type: 'object', properties: {} },
        handler: async () => 'result',
      };

      client.registerTool(tool);
      client.removeTool('removable');

      const toolCall: ToolCall = {
        id: 'call_1',
        type: 'function',
        function: { name: 'removable', arguments: '{}' },
      };

      await expect(client.executeToolCall(toolCall)).rejects.toThrow(
        'Tool not found: removable'
      );
    });

    it('passes parsed arguments to tool handler', async () => {
      const mockHandler = vi.fn().mockResolvedValue('parsed');
      const tool: ToolDefinition = {
        name: 'arg_tool',
        description: 'Takes arguments',
        parameters: { type: 'object', properties: {} },
        handler: mockHandler,
      };

      client.registerTool(tool);

      const toolCall: ToolCall = {
        id: 'call_2',
        type: 'function',
        function: { name: 'arg_tool', arguments: '{"key": "value"}' },
      };

      await client.executeToolCall(toolCall);
      expect(mockHandler).toHaveBeenCalledWith({ key: 'value' });
    });
  });

  describe('error handling', () => {
    it('throws when API key is missing for non-local provider', async () => {
      const noKeyClient = new AIClient({ provider: 'openai', apiKey: undefined });
      await expect(noKeyClient.chat('hello')).rejects.toThrow(
        'API key required for provider: openai'
      );
    });

    it('throws when API key is missing for anthropic', async () => {
      const noKeyClient = new AIClient({ provider: 'anthropic', apiKey: undefined });
      await expect(noKeyClient.chat('hello')).rejects.toThrow(
        'API key required for provider: anthropic'
      );
    });

    it('does not require API key for local provider', async () => {
      const localClient = new AIClient({ provider: 'local', apiKey: undefined });
      vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('fetch error'));
      await expect(localClient.chat('hello')).rejects.toThrow('fetch error');
    });

    it('times out when request exceeds timeout', async () => {
      vi.useFakeTimers();
      const timeoutClient = new AIClient({ apiKey: 'key', timeout: 100 });

      const fetchPromise = timeoutClient.chat('hello');
      vi.advanceTimersByTime(150);

      await expect(fetchPromise).rejects.toThrow('timed out');

      vi.useRealTimers();
    });

    it('updates tool timeout behavior with config change', () => {
      client.updateConfig({ timeout: 5000 });
      expect(client.getConfig().timeout).toBe(5000);
    });

    it('handles API error response properly', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response('Unauthorized', { status: 401, statusText: 'Unauthorized' })
      );

      await expect(client.chat('hello')).rejects.toThrow('OpenAI API error');
    });
  });

  describe('AI_DEFAULTS', () => {
    it('has correct default values', () => {
      expect(AI_DEFAULTS.provider).toBe('openai');
      expect(AI_DEFAULTS.model).toBe('gpt-4');
      expect(AI_DEFAULTS.maxTokens).toBe(2048);
      expect(AI_DEFAULTS.temperature).toBe(0.7);
      expect(AI_DEFAULTS.topP).toBe(1);
      expect(AI_DEFAULTS.timeout).toBe(30000);
    });
  });
});
