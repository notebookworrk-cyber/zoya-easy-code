import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WorkflowEngine } from '../../src/ai/workflow.js';
import type { WorkflowDefinition, WorkflowNode, WorkflowEdge } from '../../src/ai/workflow.js';

function makeWorkflow(overrides?: Partial<WorkflowDefinition>): WorkflowDefinition {
  return {
    id: 'test-workflow',
    name: 'Test Workflow',
    description: 'A workflow for testing',
    version: '1.0.0',
    nodes: [
      { id: 'start', type: 'start', name: 'Start', config: {}, next: 'step1' },
      { id: 'step1', type: 'action', name: 'Step 1', config: {}, next: 'end' },
      { id: 'end', type: 'end', name: 'End', config: {} },
    ],
    edges: [
      { from: 'start', to: 'step1' },
      { from: 'step1', to: 'end' },
    ],
    variables: { initial: 'value' },
    errorHandling: 'stop',
    ...overrides,
  };
}

describe('WorkflowEngine', () => {
  let engine: WorkflowEngine;

  beforeEach(() => {
    engine = new WorkflowEngine();
  });

  describe('workflow registration and listing', () => {
    it('registers a workflow', () => {
      const wf = makeWorkflow();
      engine.registerWorkflow(wf);
      expect(engine.getWorkflow('test-workflow')).toBeDefined();
    });

    it('throws when registering duplicate workflow', () => {
      engine.registerWorkflow(makeWorkflow());
      expect(() => engine.registerWorkflow(makeWorkflow())).toThrow(
        'Workflow already registered: test-workflow'
      );
    });

    it('throws when workflow has no start node', () => {
      const wf = makeWorkflow({
        id: 'no-start',
        nodes: [{ id: 'n1', type: 'action', name: 'N1', config: {} }],
        edges: [],
      });
      expect(() => engine.registerWorkflow(wf)).toThrow('has no start node');
    });

    it('throws when workflow has multiple start nodes', () => {
      const wf = makeWorkflow({
        id: 'multi-start',
        nodes: [
          { id: 's1', type: 'start', name: 'S1', config: {} },
          { id: 's2', type: 'start', name: 'S2', config: {} },
        ],
        edges: [],
      });
      expect(() => engine.registerWorkflow(wf)).toThrow('multiple start nodes');
    });

    it('throws when workflow has no nodes', () => {
      const wf = makeWorkflow({ id: 'empty', nodes: [], edges: [] });
      expect(() => engine.registerWorkflow(wf)).toThrow('has no nodes');
    });

    it('removes a workflow', () => {
      engine.registerWorkflow(makeWorkflow());
      engine.removeWorkflow('test-workflow');
      expect(engine.getWorkflow('test-workflow')).toBeUndefined();
    });

    it('lists all registered workflows', () => {
      engine.registerWorkflow(makeWorkflow({ id: 'wf1', name: 'WF1' }));
      engine.registerWorkflow(makeWorkflow({ id: 'wf2', name: 'WF2' }));
      const list = engine.listWorkflows();
      expect(list).toHaveLength(2);
      expect(list.map((w) => w.id)).toContain('wf1');
      expect(list.map((w) => w.id)).toContain('wf2');
    });
  });

  describe('simple linear workflow execution', () => {
    it('completes a linear workflow', async () => {
      engine.registerWorkflow(makeWorkflow());
      const execId = await engine.start('test-workflow');
      const exec = engine.getExecution(execId);
      expect(exec).toBeDefined();
      expect(exec!.status).toBe('completed');
    });

    it('records execution history', async () => {
      engine.registerWorkflow(makeWorkflow());
      const execId = await engine.start('test-workflow');
      const exec = engine.getExecution(execId)!;
      expect(exec.history.length).toBeGreaterThan(0);
      expect(exec.history.every((h) => h.status === 'completed')).toBe(true);
    });

    it('generates unique execution IDs', async () => {
      engine.registerWorkflow(makeWorkflow());
      const id1 = await engine.start('test-workflow');
      const id2 = await engine.start('test-workflow');
      expect(id1).not.toBe(id2);
    });
  });

  describe('conditional branching', () => {
    it('follows true branch', async () => {
      const wf = makeWorkflow({
        id: 'conditional',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'check' },
          {
            id: 'check',
            type: 'condition',
            name: 'Check',
            config: {},
            branches: [
              { condition: '${value} === true', target: 'yes' },
              { condition: 'true', target: 'no' },
            ],
          },
          { id: 'yes', type: 'action', name: 'Yes', config: {}, next: 'end' },
          { id: 'no', type: 'action', name: 'No', config: {}, next: 'end' },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'check' },
          { from: 'check', to: 'yes' },
          { from: 'check', to: 'no' },
          { from: 'yes', to: 'end' },
          { from: 'no', to: 'end' },
        ],
        variables: { value: true },
      });
      engine.registerWorkflow(wf);
      const execId = await engine.start('conditional');
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('completed');
    });

    it('falls through when no condition matches', async () => {
      const wf = makeWorkflow({
        id: 'no-match',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'check' },
          {
            id: 'check',
            type: 'condition',
            name: 'Check',
            config: {},
            branches: [
              { condition: '${nonexistent} === true', target: 'target' },
            ],
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [{ from: 'start', to: 'check' }],
      });
      engine.registerWorkflow(wf);
      const execId = await engine.start('no-match');
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('completed');
    });
  });

  describe('variable management', () => {
    it('passes initial variables to execution', async () => {
      engine.registerWorkflow(makeWorkflow());
      const execId = await engine.start('test-workflow', { extra: 'var' });
      const exec = engine.getExecution(execId)!;
      expect(exec.variables.initial).toBe('value');
      expect(exec.variables.extra).toBe('var');
    });

    it('overrides workflow variables with initial variables', async () => {
      engine.registerWorkflow(makeWorkflow({ variables: { key: 'original' } }));
      const execId = await engine.start('test-workflow', { key: 'override' });
      const exec = engine.getExecution(execId)!;
      expect(exec.variables.key).toBe('override');
    });
  });

  describe('error handling in workflows', () => {
    it('sets status to failed on execution error', async () => {
      const wf = makeWorkflow({
        id: 'failing',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'bad' },
          {
            id: 'bad',
            type: 'tool_call',
            name: 'Bad',
            config: { tool: 'nonexistent' },
            next: 'end',
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'bad' },
          { from: 'bad', to: 'end' },
        ],
        errorHandling: 'stop',
      });
      engine.registerWorkflow(wf);
      const execId = await engine.start('failing');
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('failed');
      expect(exec.error).toBeDefined();
    });

    it('continues on error with skip mode', async () => {
      const wf = makeWorkflow({
        id: 'skipping',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'bad' },
          {
            id: 'bad',
            type: 'tool_call',
            name: 'Bad',
            config: { tool: 'nonexistent' },
            next: 'end',
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'bad' },
          { from: 'bad', to: 'end' },
        ],
        errorHandling: 'skip',
      });
      engine.registerWorkflow(wf);
      const execId = await engine.start('skipping');
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('completed');
    });
  });

  describe('pause/resume workflow execution', () => {
    it('pauses execution', async () => {
      const wf = makeWorkflow({
        id: 'pause-test',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'human' },
          {
            id: 'human',
            type: 'human_input',
            name: 'Wait for input',
            config: {},
            next: 'end',
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'human' },
          { from: 'human', to: 'end' },
        ],
      });
      engine.registerWorkflow(wf);

      const execId = await engine.start('pause-test');
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('paused');
    });

    it('resumes paused execution', async () => {
      const wf = makeWorkflow({
        id: 'resume-test',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'human' },
          {
            id: 'human',
            type: 'human_input',
            name: 'Wait',
            config: {},
            next: 'end',
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'human' },
          { from: 'human', to: 'end' },
        ],
      });
      engine.registerWorkflow(wf);

      const execId = await engine.start('resume-test');
      expect(engine.getExecution(execId)!.status).toBe('paused');

      await engine.resume(execId);
      const resumed = engine.getExecution(execId)!;
      expect(resumed.status).toBe('completed');
    });

    it('throws when pausing non-running execution', () => {
      expect(() => engine.pause('nonexistent')).toThrow('Execution not found');
    });

    it('retrieves active executions', async () => {
      const wf = makeWorkflow({
        id: 'active-test',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'human' },
          {
            id: 'human',
            type: 'human_input',
            name: 'Wait',
            config: {},
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'human' },
        ],
      });
      engine.registerWorkflow(wf);
      await engine.start('active-test');

      const active = engine.getActiveExecutions();
      expect(active.length).toBeGreaterThan(0);
      expect(active[0].status).toBe('paused');
    });
  });

  describe('execution management', () => {
    it('returns undefined for unknown execution', () => {
      expect(engine.getExecution('ghost')).toBeUndefined();
    });

    it('cancels running execution', async () => {
      const wf = makeWorkflow();
      engine.registerWorkflow(wf);
      const execId = await engine.start('test-workflow');

      engine.cancel(execId);
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('cancelled');
    });

    it('clears completed executions', async () => {
      engine.registerWorkflow(makeWorkflow({ id: 'wf1' }));
      engine.registerWorkflow(makeWorkflow({ id: 'wf2' }));

      await engine.start('wf1');
      await engine.start('wf2');

      engine.clearCompletedExecutions();
      expect(engine.getCompletedExecutions()).toHaveLength(0);
    });

    it('retrieves completed executions', async () => {
      engine.registerWorkflow(makeWorkflow());
      await engine.start('test-workflow');

      const completed = engine.getCompletedExecutions();
      expect(completed.length).toBeGreaterThan(0);
    });
  });

  describe('tool registration', () => {
    it('registers and uses a tool handler', async () => {
      const handler = vi.fn().mockResolvedValue('tool-output');
      engine.registerTool('greeter', handler);

      const wf = makeWorkflow({
        id: 'tool-workflow',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'tool' },
          {
            id: 'tool',
            type: 'tool_call',
            name: 'Greet',
            config: { tool: 'greeter', args: { name: 'test' } },
            next: 'end',
          },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [
          { from: 'start', to: 'tool' },
          { from: 'tool', to: 'end' },
        ],
      });
      engine.registerWorkflow(wf);
      const execId = await engine.start('tool-workflow', { name: 'test' });
      const exec = engine.getExecution(execId)!;
      expect(exec.status).toBe('completed');
      expect(handler).toHaveBeenCalled();
    });

    it('removes a registered tool', () => {
      const handler = vi.fn();
      engine.registerTool('t1', handler);
      engine.removeTool('t1');
    });
  });

  describe('getActiveExecutions', () => {
    it('returns empty array when no active executions', () => {
      expect(engine.getActiveExecutions()).toEqual([]);
    });

    it('returns immutable copies', async () => {
      const wf = makeWorkflow({
        id: 'immutable-test',
        nodes: [
          { id: 'start', type: 'start', name: 'Start', config: {}, next: 'human' },
          { id: 'human', type: 'human_input', name: 'Human', config: {} },
          { id: 'end', type: 'end', name: 'End', config: {} },
        ],
        edges: [{ from: 'start', to: 'human' }],
      });
      engine.registerWorkflow(wf);
      await engine.start('immutable-test');

      const active = engine.getActiveExecutions();
      active[0].status = 'cancelled';

      const real = engine.getExecution(active[0].id)!;
      expect(real.status).not.toBe('cancelled');
    });
  });
});
