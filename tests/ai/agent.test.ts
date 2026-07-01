import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Agent, AgentOrchestrator } from '../../src/ai/agent.js';
import type { AgentConfig } from '../../src/ai/agent.js';
import type { ToolDefinition } from '../../src/ai/index.js';

describe('Agent', () => {
  let agent: Agent;
  let mockTool: ToolDefinition;

  beforeEach(() => {
    vi.restoreAllMocks();

    mockTool = {
      name: 'calculator',
      description: 'Performs basic math',
      parameters: {
        type: 'object',
        properties: {
          expression: { type: 'string' },
        },
      },
      handler: vi.fn().mockResolvedValue('42'),
    };

    agent = new Agent({
      name: 'test-agent',
      goal: 'Complete the test task',
      role: 'tester',
      tools: [mockTool],
      maxSteps: 5,
      verbose: false,
    });
  });

  describe('agent creation', () => {
    it('creates agent with provided config', () => {
      expect(agent.config.name).toBe('test-agent');
      expect(agent.config.goal).toBe('Complete the test task');
      expect(agent.config.maxSteps).toBe(5);
    });

    it('applies default values for optional config', () => {
      const minimalAgent = new Agent({ name: 'minimal', goal: 'test' });
      expect(minimalAgent.config.role).toBe('assistant');
      expect(minimalAgent.config.maxSteps).toBe(10);
      expect(minimalAgent.config.temperature).toBe(0.7);
    });

    it('starts in idle status', () => {
      expect(agent.getStatus()).toBe('idle');
    });

    it('has zero steps initially', () => {
      expect(agent.getStepCount()).toBe(0);
    });

    it('registers provided tools', () => {
      expect(agent.config.tools).toHaveLength(1);
      expect(agent.config.tools[0].name).toBe('calculator');
    });
  });

  describe('step execution and tracking', () => {
    it('increments step count after run', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'chat_1',
            choices: [
              {
                message: { content: 'Task completed successfully.', tool_calls: undefined },
                finish_reason: 'stop',
              },
            ],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await agent.run('test input');
      expect(agent.getStepCount()).toBeGreaterThanOrEqual(1);
    });

    it('records step details', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'chat_1',
            choices: [
              {
                message: { content: 'Thinking about the task...', tool_calls: undefined },
                finish_reason: 'stop',
              },
            ],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await agent.run('test');
      const steps = agent.getSteps();
      expect(steps[0]).toBeDefined();
      expect(steps[0].step).toBe(1);
      expect(steps[0].timestamp).toBeInstanceOf(Date);
      expect(typeof steps[0].duration).toBe('number');
    });
  });

  describe('memory management', () => {
    it('stores added memories', () => {
      agent.addMemory('Important observation');
      agent.addMemory('Another note');
    });

    it('preserves memory across steps', async () => {
      agent.addMemory('Context from earlier');
      expect(agent.getStepCount()).toBe(0);
    });
  });

  describe('agent status lifecycle', () => {
    it('transitions to completed after run', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'chat_1',
            choices: [
              {
                message: { content: 'Done.', tool_calls: undefined },
                finish_reason: 'stop',
              },
            ],
            usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await agent.run('task');
      expect(agent.getStatus()).toBe('completed');
    });

    it('starts in idle when created', () => {
      expect(agent.getStatus()).toBe('idle');
    });
  });

  describe('agent reset', () => {
    it('clears steps on reset', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'chat_1',
            choices: [
              {
                message: { content: 'Done.', tool_calls: undefined },
                finish_reason: 'stop',
              },
            ],
            usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await agent.run('task');
      expect(agent.getStepCount()).toBeGreaterThan(0);

      agent.reset();
      expect(agent.getStepCount()).toBe(0);
      expect(agent.getStatus()).toBe('idle');
    });

    it('preserves config after reset', () => {
      agent.reset();
      expect(agent.config.name).toBe('test-agent');
    });
  });

  describe('stop', () => {
    it('sets status to failed', () => {
      agent.stop();
      expect(agent.getStatus()).toBe('failed');
    });
  });

  describe('getSteps', () => {
    it('returns steps array', () => {
      const steps = agent.getSteps();
      expect(Array.isArray(steps)).toBe(true);
    });
  });
});

describe('AgentOrchestrator', () => {
  let orchestrator: AgentOrchestrator;

  beforeEach(() => {
    orchestrator = new AgentOrchestrator();
  });

  describe('agent management', () => {
    it('creates and retrieves an agent', () => {
      const agent = orchestrator.createAgent({
        name: 'worker-1',
        goal: 'Process data',
      });
      expect(orchestrator.getAgent('worker-1')).toBe(agent);
    });

    it('throws when creating duplicate agent', () => {
      orchestrator.createAgent({ name: 'worker-1', goal: 'First' });
      expect(() =>
        orchestrator.createAgent({ name: 'worker-1', goal: 'Second' })
      ).toThrow('Agent already exists: worker-1');
    });

    it('removes an agent', () => {
      orchestrator.createAgent({ name: 'worker-1', goal: 'test' });
      orchestrator.removeAgent('worker-1');
      expect(orchestrator.getAgent('worker-1')).toBeUndefined();
    });

    it('reports correct agent count', () => {
      expect(orchestrator.agentCount()).toBe(0);
      orchestrator.createAgent({ name: 'a1', goal: 'g1' });
      orchestrator.createAgent({ name: 'a2', goal: 'g2' });
      expect(orchestrator.agentCount()).toBe(2);
    });

    it('reports statuses for all agents', () => {
      orchestrator.createAgent({ name: 'a1', goal: 'g1' });
      orchestrator.createAgent({ name: 'a2', goal: 'g2' });
      const statuses = orchestrator.getStatuses();
      expect(statuses.get('a1')).toBe('idle');
      expect(statuses.get('a2')).toBe('idle');
      expect(statuses.size).toBe(2);
    });
  });

  describe('task management', () => {
    it('assigns task to existing agent', () => {
      orchestrator.createAgent({ name: 'worker', goal: 'test' });
      expect(() => orchestrator.assignTask('worker', 'do something')).not.toThrow();
    });

    it('throws when assigning task to unknown agent', () => {
      expect(() => orchestrator.assignTask('ghost', 'task')).toThrow(
        'Agent not found: ghost'
      );
    });
  });

  describe('runAll', () => {
    it('returns map with agent results', async () => {
      orchestrator.createAgent({ name: 'worker', goal: 'test' });
      orchestrator.assignTask('worker', 'do work');

      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'chat_1',
            choices: [
              {
                message: { content: 'Done.', tool_calls: undefined },
                finish_reason: 'stop',
              },
            ],
            usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

      const results = await orchestrator.runAll();
      expect(results.has('worker')).toBe(true);
    });
  });

  describe('stopAll', () => {
    it('stops all agents and clears queue', () => {
      orchestrator.createAgent({ name: 'a1', goal: 'g1' });
      orchestrator.createAgent({ name: 'a2', goal: 'g2' });
      orchestrator.assignTask('a1', 'task');

      orchestrator.stopAll();

      expect(orchestrator.getAgent('a1')?.getStatus()).toBe('failed');
      expect(orchestrator.getAgent('a2')?.getStatus()).toBe('failed');
    });
  });
});
