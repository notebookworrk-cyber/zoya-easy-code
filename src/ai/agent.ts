import { AIClient, AI_DEFAULTS } from './index.js';
import type { ToolCall, ChatMessage, ChatCompletion, ToolDefinition } from './index.js';

export interface AgentConfig {
  name: string;
  role: string;
  goal: string;
  tools: ToolDefinition[];
  maxSteps: number;
  verbose: boolean;
  model: string;
  temperature: number;
}

export type AgentStatus = 'idle' | 'thinking' | 'acting' | 'observing' | 'completed' | 'failed';

export interface AgentStep {
  step: number;
  thought: string;
  action?: ToolCall;
  observation?: string;
  result?: string;
  timestamp: Date;
  duration: number;
}

export const DEFAULT_AGENT_CONFIG: Partial<AgentConfig> = {
  role: 'assistant',
  tools: [],
  maxSteps: 10,
  verbose: false,
  model: 'gpt-4',
  temperature: 0.7,
};

export class Agent {
  readonly config: AgentConfig;
  private client: AIClient;
  private status: AgentStatus;
  private steps: AgentStep[];
  private memory: string[];

  constructor(config: Partial<AgentConfig> & { name: string; goal: string }) {
    this.config = {
      ...DEFAULT_AGENT_CONFIG,
      ...config,
      tools: config.tools || [],
    } as AgentConfig;
    this.client = new AIClient({
      provider: 'local',
      model: this.config.model,
      temperature: this.config.temperature,
    });
    this.status = 'idle';
    this.steps = [];
    this.memory = [];

    const systemPrompt = this.buildSystemPrompt();
    this.client.setSystemPrompt(systemPrompt);

    for (const tool of this.config.tools) {
      this.client.registerTool(tool);
    }
  }

  async run(initialInput?: string): Promise<AgentStep[]> {
    this.status = 'thinking';
    this.steps = [];

    const systemPrompt = this.buildSystemPrompt();
    this.client.setSystemPrompt(systemPrompt);

    if (initialInput) {
      this.client.clearHistory();
    }

    while (this.steps.length < this.config.maxSteps) {
      const stepResult = await this.step();
      if (!stepResult) break;

      if ((this.status as string) === 'completed' || (this.status as string) === 'failed') {
        break;
      }
    }

    if (this.steps.length >= this.config.maxSteps) {
      this.status = 'completed';
    }

    return this.steps;
  }

  async step(): Promise<AgentStep | null> {
    if (this.status === 'completed' || this.status === 'failed') {
      return null;
    }

    const stepNumber = this.steps.length + 1;
    const startTime = Date.now();
    const stepStart = new Date();

    this.status = 'thinking';

    const messages = this.buildStepMessages();
    let completion: ChatCompletion;

    try {
      completion = await this.client.chatWithHistory(messages);
    } catch (error) {
      this.status = 'failed';
      const failedStep: AgentStep = {
        step: stepNumber,
        thought: `Error: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: stepStart,
        duration: Date.now() - startTime,
      };
      this.steps.push(failedStep);
      return failedStep;
    }

    const thought = completion.message.content;

    if (completion.message.toolCalls && completion.message.toolCalls.length > 0) {
      this.status = 'acting';

      const stepResults: AgentStep[] = [];

      for (const toolCall of completion.message.toolCalls) {
        const actionStart = Date.now();
        let observation: string;

        try {
          this.status = 'observing';
          observation = await this.client.executeToolCall(toolCall);
        } catch (error) {
          observation = `Error executing tool: ${error instanceof Error ? error.message : String(error)}`;
        }

        const duration = Date.now() - actionStart;
        const agentStep: AgentStep = {
          step: stepNumber,
          thought,
          action: toolCall,
          observation,
          result: observation,
          timestamp: stepStart,
          duration,
        };

        this.steps.push(agentStep);
        stepResults.push(agentStep);
        this.memory.push(`Step ${stepNumber}: ${thought} -> ${observation}`);
      }

      if (this.config.verbose) {
        for (const sr of stepResults) {
          console.log(
            `[Agent ${this.config.name}] Step ${sr.step}: ${sr.thought}`
          );
          if (sr.action) {
            console.log(
              `  Action: ${sr.action.function.name}(${sr.action.function.arguments})`
            );
          }
          if (sr.observation) {
            console.log(`  Observation: ${sr.observation.slice(0, 200)}`);
          }
        }
      }

      this.status = 'thinking';
    } else {
      const agentStep: AgentStep = {
        step: stepNumber,
        thought,
        timestamp: stepStart,
        duration: Date.now() - startTime,
      };

      this.steps.push(agentStep);
      this.memory.push(`Step ${stepNumber}: ${thought}`);

      this.status = 'completed';

      if (this.config.verbose) {
        console.log(`[Agent ${this.config.name}] Completed: ${thought.slice(0, 100)}`);
      }
    }

    return this.steps[this.steps.length - 1];
  }

  addMemory(memory: string): void {
    this.memory.push(memory);
  }

  getStatus(): AgentStatus {
    return this.status;
  }

  getSteps(): AgentStep[] {
    return this.steps.map((s) => ({ ...s }));
  }

  getStepCount(): number {
    return this.steps.length;
  }

  reset(): void {
    this.status = 'idle';
    this.steps = [];
    this.memory = [];
    this.client.clearHistory();

    const systemPrompt = this.buildSystemPrompt();
    this.client.setSystemPrompt(systemPrompt);
  }

  stop(): void {
    this.status = 'failed';
  }

  private buildSystemPrompt(): string {
    return `You are ${this.config.name}, an AI agent with the role: ${this.config.role}.

Your goal is: ${this.config.goal}

You have access to the following tools:
${this.config.tools.length > 0 ? this.config.tools.map((t) => `- ${t.name}: ${t.description}`).join('\n') : 'No tools available.'}

Follow this loop:
1. Think about what to do next
2. Use a tool if needed
3. Observe the result
4. Repeat until the goal is achieved

${this.memory.length > 0 ? `Relevant memories:\n${this.memory.map((m) => `- ${m}`).join('\n')}` : ''}`;
  }

  private buildStepMessages(): ChatMessage[] {
    const messages: ChatMessage[] = [
      { role: 'system', content: this.buildSystemPrompt() },
    ];

    for (const step of this.steps) {
      messages.push({ role: 'assistant', content: step.thought });
      if (step.action) {
        messages.push({
          role: 'assistant',
          content: '',
          toolCalls: [step.action],
        });
      }
      if (step.observation !== undefined) {
        messages.push({
          role: 'tool',
          content: step.observation,
          toolCallId: step.action?.id,
        });
      }
    }

    return messages;
  }
}

export class AgentOrchestrator {
  private agents: Map<string, Agent>;
  private taskQueue: { agent: string; task: string }[];

  constructor() {
    this.agents = new Map();
    this.taskQueue = [];
  }

  createAgent(config: AgentConfig): Agent {
    if (this.agents.has(config.name)) {
      throw new Error(`Agent already exists: ${config.name}`);
    }
    const agent = new Agent(config);
    this.agents.set(config.name, agent);
    return agent;
  }

  getAgent(name: string): Agent | undefined {
    return this.agents.get(name);
  }

  removeAgent(name: string): void {
    this.agents.delete(name);
    this.taskQueue = this.taskQueue.filter((t) => t.agent !== name);
  }

  assignTask(agentName: string, task: string): void {
    if (!this.agents.has(agentName)) {
      throw new Error(`Agent not found: ${agentName}`);
    }
    this.taskQueue.push({ agent: agentName, task });
  }

  async runAll(): Promise<Map<string, AgentStep[]>> {
    const results = new Map<string, AgentStep[]>();

    while (this.taskQueue.length > 0) {
      const task = this.taskQueue.shift()!;
      const agent = this.agents.get(task.agent);
      if (agent) {
        const steps = await agent.run(task.task);
        results.set(task.agent, steps);
      }
    }

    return results;
  }

  getStatuses(): Map<string, AgentStatus> {
    const statuses = new Map<string, AgentStatus>();
    for (const [name, agent] of this.agents) {
      statuses.set(name, agent.getStatus());
    }
    return statuses;
  }

  stopAll(): void {
    for (const agent of this.agents.values()) {
      agent.stop();
    }
    this.taskQueue = [];
  }

  agentCount(): number {
    return this.agents.size;
  }
}
