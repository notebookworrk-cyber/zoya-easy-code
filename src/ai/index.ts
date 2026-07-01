export interface AIConfig {
  provider: 'openai' | 'anthropic' | 'local' | 'custom';
  apiKey?: string;
  baseUrl?: string;
  model: string;
  maxTokens: number;
  temperature: number;
  topP: number;
  timeout: number;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ChatCompletion {
  id: string;
  message: ChatMessage;
  finishReason: 'stop' | 'length' | 'tool_calls' | 'error';
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  handler: (args: Record<string, unknown>) => Promise<string>;
}

export const AI_DEFAULTS: AIConfig = {
  provider: 'openai',
  model: 'gpt-4',
  maxTokens: 2048,
  temperature: 0.7,
  topP: 1,
  timeout: 30000,
};

export class AIClient {
  private config: AIConfig;
  private tools: Map<string, ToolDefinition>;
  private conversationHistory: ChatMessage[];
  private maxHistoryLength: number;

  constructor(config?: Partial<AIConfig>) {
    this.config = { ...AI_DEFAULTS, ...config };
    this.tools = new Map();
    this.conversationHistory = [];
    this.maxHistoryLength = 50;
  }

  async chat(message: string): Promise<ChatCompletion> {
    const messages: ChatMessage[] = [
      ...this.conversationHistory,
      { role: 'user', content: message },
    ];
    const result = await this.sendRequest(messages);
    if (result.message.role === 'assistant') {
      this.conversationHistory.push({ role: 'user', content: message });
      this.conversationHistory.push(result.message);
      this.trimHistory();
    }
    return result;
  }

  async chatWithHistory(messages: ChatMessage[]): Promise<ChatCompletion> {
    return this.sendRequest(messages);
  }

  async *stream(message: string): AsyncGenerator<string, void, unknown> {
    const messages: ChatMessage[] = [
      ...this.conversationHistory,
      { role: 'user', content: message },
    ];
    const { provider, apiKey, baseUrl, model } = this.config;

    if (!apiKey && provider !== 'local') {
      throw new Error(`API key required for provider: ${provider}`);
    }

    const url =
      provider === 'openai'
        ? `${baseUrl || 'https://api.openai.com/v1'}/chat/completions`
        : provider === 'anthropic'
          ? 'https://api.anthropic.com/v1/messages'
          : `${baseUrl || 'http://localhost:8080/v1'}/chat/completions`;

    if (provider === 'anthropic') {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey!,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model,
          messages: messages.map((m) => ({
            role: m.role === 'tool' ? 'assistant' : m.role,
            content: m.content,
          })),
          max_tokens: this.config.maxTokens,
          stream: true,
        }),
      });
      if (!response.ok) {
        const err = await response.text();
        throw new Error(`Anthropic API error (${response.status}): ${err}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Stream not available');
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') return;
            try {
              const parsed = JSON.parse(data);
              const delta = parsed.delta?.text || parsed.content_block?.text || '';
              if (delta) yield delta;
            } catch {
              // skip malformed chunks
            }
          }
        }
      }
    } else {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          max_tokens: this.config.maxTokens,
          temperature: this.config.temperature,
          top_p: this.config.topP,
          stream: true,
        }),
      });
      if (!response.ok) {
        const err = await response.text();
        throw new Error(`API error (${response.status}): ${err}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Stream not available');
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') return;
            try {
              const parsed = JSON.parse(data);
              const delta =
                parsed.choices?.[0]?.delta?.content ||
                parsed.choices?.[0]?.text ||
                '';
              if (delta) yield delta;
            } catch {
              // skip malformed chunks
            }
          }
        }
      }
    }

    if (this.config.provider !== 'local') {
      this.conversationHistory.push({ role: 'user', content: message });
    }
  }

  registerTool(tool: ToolDefinition): void {
    this.tools.set(tool.name, tool);
  }

  removeTool(name: string): void {
    this.tools.delete(name);
  }

  async executeToolCall(toolCall: ToolCall): Promise<string> {
    const tool = this.tools.get(toolCall.function.name);
    if (!tool) {
      throw new Error(`Tool not found: ${toolCall.function.name}`);
    }
    const args = JSON.parse(toolCall.function.arguments) as Record<string, unknown>;
    return tool.handler(args);
  }

  clearHistory(): void {
    this.conversationHistory = [];
  }

  getHistory(): ChatMessage[] {
    return this.conversationHistory.map((m) => ({ ...m }));
  }

  setSystemPrompt(prompt: string): void {
    this.conversationHistory = this.conversationHistory.filter(
      (m) => m.role !== 'system'
    );
    this.conversationHistory.unshift({ role: 'system', content: prompt });
  }

  updateConfig(config: Partial<AIConfig>): void {
    this.config = { ...this.config, ...config };
  }

  getConfig(): AIConfig {
    return { ...this.config };
  }

  private trimHistory(): void {
    while (this.conversationHistory.length > this.maxHistoryLength) {
      const idx = this.conversationHistory.findIndex(
        (m, i) => i > 0 && m.role !== 'system'
      );
      if (idx > 0) {
        this.conversationHistory.splice(idx, 1);
      } else {
        break;
      }
    }
  }

  private async sendRequest(messages: ChatMessage[]): Promise<ChatCompletion> {
    const { provider, apiKey, timeout } = this.config;

    if (!apiKey && provider !== 'local') {
      throw new Error(`API key required for provider: ${provider}`);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      if (provider === 'openai') {
        return await this.openaiChat(messages, controller.signal);
      } else if (provider === 'anthropic') {
        return await this.anthropicChat(messages, controller.signal);
      } else {
        return await this.customChat(messages, controller.signal);
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private async openaiChat(
    messages: ChatMessage[],
    signal: AbortSignal
  ): Promise<ChatCompletion> {
    const { baseUrl, model, maxTokens, temperature, topP, apiKey } = this.config;
    const url = `${baseUrl || 'https://api.openai.com/v1'}/chat/completions`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
          ...(m.toolCalls ? { tool_calls: m.toolCalls } : {}),
          ...(m.toolCallId ? { tool_call_id: m.toolCallId } : {}),
        })),
        max_tokens: maxTokens,
        temperature,
        top_p: topP,
        tools:
          this.tools.size > 0
            ? Array.from(this.tools.values()).map((t) => ({
                type: 'function' as const,
                function: {
                  name: t.name,
                  description: t.description,
                  parameters: t.parameters,
                },
              }))
            : undefined,
      }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`OpenAI API error (${response.status}): ${errorText}`);
    }

    const data = await response.json() as {
      id: string;
      choices: Array<{
        message: {
          content: string | null;
          tool_calls?: Array<{
            id: string;
            type: string;
            function: { name: string; arguments: string };
          }>;
        };
        finish_reason: string;
      }>;
      usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
    };
    const choice = data.choices[0];

    return {
      id: data.id,
      message: {
        role: 'assistant',
        content: choice.message.content || '',
        toolCalls: choice.message.tool_calls?.map((tc) => ({
          id: tc.id,
          type: 'function' as const,
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        })),
      },
      finishReason: choice.finish_reason === 'stop'
        ? 'stop'
        : choice.finish_reason === 'length'
          ? 'length'
          : choice.finish_reason === 'tool_calls'
            ? 'tool_calls'
            : 'stop',
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    };
  }

  private async anthropicChat(
    messages: ChatMessage[],
    signal: AbortSignal
  ): Promise<ChatCompletion> {
    const { model, maxTokens, apiKey } = this.config;
    const url = 'https://api.anthropic.com/v1/messages';

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey!,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        messages: messages
          .filter((m) => m.role !== 'system')
          .map((m) => ({
            role: m.role === 'tool' ? 'assistant' : m.role,
            content: m.content,
          })),
        system: messages.find((m) => m.role === 'system')?.content,
      }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Anthropic API error (${response.status}): ${errorText}`);
    }

    const data = await response.json() as {
      id: string;
      content: Array<{ type: string; text: string }>;
      stop_reason: string;
      usage: { input_tokens: number; output_tokens: number };
    };
    const textContent = data.content.find((c) => c.type === 'text');

    return {
      id: data.id,
      message: {
        role: 'assistant',
        content: textContent?.text || '',
      },
      finishReason: data.stop_reason === 'end_turn'
        ? 'stop'
        : data.stop_reason === 'max_tokens'
          ? 'length'
          : 'stop',
      usage: {
        promptTokens: data.usage.input_tokens,
        completionTokens: data.usage.output_tokens,
        totalTokens: data.usage.input_tokens + data.usage.output_tokens,
      },
    };
  }

  private async customChat(
    messages: ChatMessage[],
    signal: AbortSignal
  ): Promise<ChatCompletion> {
    const { baseUrl, model, maxTokens, temperature, topP, apiKey } = this.config;
    const url = `${baseUrl || 'http://localhost:8080/v1'}/chat/completions`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model,
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        max_tokens: maxTokens,
        temperature,
        top_p: topP,
      }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Custom API error (${response.status}): ${errorText}`);
    }

    const data = await response.json() as {
      id: string;
      choices: Array<{
        message: { content: string };
        finish_reason: string;
      }>;
      usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
    };
    const choice = data.choices[0];

    return {
      id: data.id,
      message: {
        role: 'assistant',
        content: choice.message.content,
      },
      finishReason: choice.finish_reason === 'stop' ? 'stop' : 'length',
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    };
  }
}
