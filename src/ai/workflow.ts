import type { AIClient } from './index.js';

export type WorkflowNodeType =
  | 'start'
  | 'end'
  | 'action'
  | 'condition'
  | 'loop'
  | 'wait'
  | 'subflow'
  | 'ai_call'
  | 'tool_call'
  | 'human_input';

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  name: string;
  config: Record<string, unknown>;
  next?: string;
  branches?: { condition: string; target: string }[];
  loopConfig?: { variable: string; collection: string };
  timeout?: number;
  retryCount?: number;
}

export interface WorkflowEdge {
  from: string;
  to: string;
  label?: string;
  condition?: string;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  variables: Record<string, unknown>;
  errorHandling: 'stop' | 'skip' | 'retry' | 'fallback';
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  currentNode: string;
  variables: Record<string, unknown>;
  history: ExecutionStep[];
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

export interface ExecutionStep {
  nodeId: string;
  status: 'running' | 'completed' | 'failed' | 'skipped';
  input: unknown;
  output: unknown;
  startedAt: Date;
  completedAt?: Date;
  duration: number;
  error?: string;
  retryCount: number;
}

let executionCounter = 0;

export class WorkflowEngine {
  private workflows: Map<string, WorkflowDefinition>;
  private executions: Map<string, WorkflowExecution>;
  private aiClient?: AIClient;
  private toolRegistry: Map<string, (args: unknown) => Promise<unknown>>;

  constructor(aiClient?: AIClient) {
    this.workflows = new Map();
    this.executions = new Map();
    this.aiClient = aiClient;
    this.toolRegistry = new Map();
  }

  registerWorkflow(definition: WorkflowDefinition): void {
    if (this.workflows.has(definition.id)) {
      throw new Error(`Workflow already registered: ${definition.id}`);
    }

    if (definition.nodes.length === 0) {
      throw new Error(`Workflow "${definition.id}" has no nodes`);
    }

    const startNodes = definition.nodes.filter((n) => n.type === 'start');
    if (startNodes.length === 0) {
      throw new Error(`Workflow "${definition.id}" has no start node`);
    }
    if (startNodes.length > 1) {
      throw new Error(`Workflow "${definition.id}" has multiple start nodes`);
    }

    this.workflows.set(definition.id, definition);
  }

  getWorkflow(id: string): WorkflowDefinition | undefined {
    return this.workflows.get(id);
  }

  removeWorkflow(id: string): void {
    this.workflows.delete(id);
  }

  listWorkflows(): WorkflowDefinition[] {
    return Array.from(this.workflows.values());
  }

  async start(
    workflowId: string,
    initialVariables?: Record<string, unknown>
  ): Promise<string> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }

    const startNode = workflow.nodes.find((n) => n.type === 'start');
    if (!startNode) {
      throw new Error(`No start node in workflow: ${workflowId}`);
    }

    executionCounter++;
    const executionId = `exec_${executionCounter}_${Date.now()}`;

    const execution: WorkflowExecution = {
      id: executionId,
      workflowId,
      status: 'running',
      currentNode: startNode.id,
      variables: { ...workflow.variables, ...initialVariables },
      history: [],
      startedAt: new Date(),
    };

    this.executions.set(executionId, execution);

    try {
      await this.executeNode(execution, startNode);
    } catch (error) {
      execution.status = 'failed';
      execution.error = error instanceof Error ? error.message : String(error);
      execution.completedAt = new Date();
    }

    return executionId;
  }

  pause(executionId: string): void {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`);
    }
    if (execution.status !== 'running') {
      throw new Error(`Cannot pause execution with status: ${execution.status}`);
    }
    execution.status = 'paused';
  }

  async resume(executionId: string): Promise<void> {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`);
    }
    if (execution.status !== 'paused') {
      throw new Error(`Cannot resume execution with status: ${execution.status}`);
    }

    execution.status = 'running';

    const workflow = this.workflows.get(execution.workflowId);
    if (!workflow) {
      execution.status = 'failed';
      execution.error = `Workflow not found: ${execution.workflowId}`;
      execution.completedAt = new Date();
      return;
    }

    let resumeNode = workflow.nodes.find((n) => n.id === execution.currentNode);
    if (!resumeNode) {
      execution.status = 'failed';
      execution.error = `Node not found: ${execution.currentNode}`;
      execution.completedAt = new Date();
      return;
    }

    if (resumeNode.type === 'human_input') {
      const workflowDef = this.workflows.get(execution.workflowId);
      if (workflowDef) {
        resumeNode = this.getNextNode(workflowDef, resumeNode, execution.variables) || resumeNode;
      }
    }

    try {
      await this.executeNode(execution, resumeNode);
    } catch (error) {
      execution.status = 'failed';
      execution.error = error instanceof Error ? error.message : String(error);
      execution.completedAt = new Date();
    }
  }

  cancel(executionId: string): void {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution not found: ${executionId}`);
    }
    execution.status = 'cancelled';
    execution.completedAt = new Date();
  }

  getExecution(executionId: string): WorkflowExecution | undefined {
    const exec = this.executions.get(executionId);
    return exec ? this.cloneExecution(exec) : undefined;
  }

  registerTool(
    name: string,
    handler: (args: unknown) => Promise<unknown>
  ): void {
    this.toolRegistry.set(name, handler);
  }

  removeTool(name: string): void {
    this.toolRegistry.delete(name);
  }

  getActiveExecutions(): WorkflowExecution[] {
    return Array.from(this.executions.values())
      .filter((e) => e.status === 'running' || e.status === 'paused')
      .map((e) => this.cloneExecution(e));
  }

  getCompletedExecutions(): WorkflowExecution[] {
    return Array.from(this.executions.values())
      .filter(
        (e) =>
          e.status === 'completed' || e.status === 'failed' || e.status === 'cancelled'
      )
      .map((e) => this.cloneExecution(e));
  }

  clearCompletedExecutions(): void {
    for (const [id, exec] of this.executions) {
      if (
        exec.status === 'completed' ||
        exec.status === 'failed' ||
        exec.status === 'cancelled'
      ) {
        this.executions.delete(id);
      }
    }
  }

  private async executeNode(
    execution: WorkflowExecution,
    node: WorkflowNode
  ): Promise<void> {
    if (execution.status === 'paused' || execution.status === 'cancelled') {
      return;
    }

    const stepStart = new Date();
    const step: ExecutionStep = {
      nodeId: node.id,
      status: 'running',
      input: node.config,
      output: null,
      startedAt: stepStart,
      duration: 0,
      retryCount: 0,
    };

    execution.currentNode = node.id;
    execution.history.push(step);

    try {
      await this.processNode(execution, node, step);
      step.status = 'completed';
      step.completedAt = new Date();
      step.duration = step.completedAt.getTime() - step.startedAt.getTime();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      step.status = 'failed';
      step.error = errorMessage;
      step.completedAt = new Date();
      step.duration = step.completedAt.getTime() - step.startedAt.getTime();

      const workflow = this.workflows.get(execution.workflowId);
      if (workflow) {
        switch (workflow.errorHandling) {
          case 'stop':
            execution.status = 'failed';
            execution.error = errorMessage;
            execution.completedAt = new Date();
            return;
          case 'skip':
            break;
          case 'retry':
            if (step.retryCount < (node.retryCount || 3)) {
              step.retryCount++;
              step.status = 'running';
              step.error = undefined;
              await this.processNode(execution, node, step);
              step.status = 'completed';
              step.completedAt = new Date();
              step.duration = step.completedAt.getTime() - step.startedAt.getTime();
            } else {
              execution.status = 'failed';
              execution.error = `Max retries exceeded: ${errorMessage}`;
              execution.completedAt = new Date();
              return;
            }
            break;
          case 'fallback':
            const fallbackNode = this.findNextNode(workflow, node.id);
            if (fallbackNode) {
              await this.executeNode(execution, fallbackNode);
            }
            return;
        }
      } else {
        execution.status = 'failed';
        execution.error = errorMessage;
        execution.completedAt = new Date();
        return;
      }
    }

    const currentExecStatus: string = execution.status;
    if (currentExecStatus === 'paused' || currentExecStatus === 'cancelled') {
      return;
    }

    if (node.type === 'end') {
      execution.status = 'completed';
      execution.completedAt = new Date();
      return;
    }

    const workflow = this.workflows.get(execution.workflowId);
    if (!workflow) {
      execution.status = 'failed';
      execution.error = `Workflow not found: ${execution.workflowId}`;
      execution.completedAt = new Date();
      return;
    }

    const nextNode = this.getNextNode(workflow, node, execution.variables);
    if (nextNode) {
      await this.executeNode(execution, nextNode);
    } else {
      execution.status = 'completed';
      execution.completedAt = new Date();
    }
  }

  private async processNode(
    execution: WorkflowExecution,
    node: WorkflowNode,
    _step: ExecutionStep
  ): Promise<void> {
    switch (node.type) {
      case 'start':
      case 'end':
        break;

      case 'action':
        if (typeof node.config.handler === 'string' && this.toolRegistry.has(node.config.handler as string)) {
          const handler = this.toolRegistry.get(node.config.handler as string)!;
          const result = await handler(node.config.args || {});
          execution.variables[`${node.id}_result`] = result;
        }
        break;

      case 'condition': {
        if (!node.branches || node.branches.length === 0) {
          throw new Error(`Condition node "${node.id}" has no branches`);
        }
        break;
      }

      case 'loop': {
        if (!node.loopConfig) {
          throw new Error(`Loop node "${node.id}" has no loopConfig`);
        }
        const { variable, collection } = node.loopConfig;
        const items = execution.variables[collection] as unknown[];
        if (Array.isArray(items)) {
          execution.variables[variable] = items;
        }
        break;
      }

      case 'wait': {
        const duration = (node.config.duration as number) || 1000;
        await this.sleep(duration);
        break;
      }

      case 'ai_call': {
        if (!this.aiClient) {
          throw new Error('AI client not configured for ai_call node');
        }
        const prompt = node.config.prompt as string;
        if (prompt) {
          const resolvedPrompt = this.resolveTemplate(prompt, execution.variables);
          const result = await this.aiClient.chat(resolvedPrompt);
          execution.variables[`${node.id}_result`] = result.message.content;
        }
        break;
      }

      case 'tool_call': {
        const toolName = node.config.tool as string;
        if (!toolName) {
          throw new Error(`Tool call node "${node.id}" has no tool name`);
        }
        const handler = this.toolRegistry.get(toolName);
        if (!handler) {
          throw new Error(`Tool not registered: ${toolName}`);
        }
        const args = node.config.args || {};
        const resolvedArgs = this.resolveVariables(args, execution.variables);
        const result = await handler(resolvedArgs);
        execution.variables[`${node.id}_result`] = result;
        break;
      }

      case 'subflow': {
        const subflowId = node.config.workflowId as string;
        if (!subflowId) {
          throw new Error(`Subflow node "${node.id}" has no workflowId`);
        }
        const subflowEngine = new WorkflowEngine(this.aiClient);
        for (const [name, handler] of this.toolRegistry) {
          subflowEngine.registerTool(name, handler);
        }
        const subflowDef = this.workflows.get(subflowId);
        if (subflowDef) {
          subflowEngine.registerWorkflow(subflowDef);
        }
        const subExecId = await subflowEngine.start(subflowId, execution.variables);
        const subExec = subflowEngine.getExecution(subExecId);
        if (subExec) {
          execution.variables[`${node.id}_result`] = subExec.variables;
        }
        break;
      }

      case 'human_input':
        execution.status = 'paused';
        break;

      default:
        throw new Error(`Unknown node type: ${node.type}`);
    }
  }

  private getNextNode(
    workflow: WorkflowDefinition,
    node: WorkflowNode,
    variables: Record<string, unknown>
  ): WorkflowNode | undefined {
    if (node.type === 'condition' && node.branches && node.branches.length > 0) {
      for (const branch of node.branches) {
        if (this.evaluateCondition(branch.condition, variables)) {
          return workflow.nodes.find((n) => n.id === branch.target);
        }
      }
      return undefined;
    }

    if (node.type === 'loop' && node.next) {
      const loopNode = workflow.nodes.find((n) => n.id === node.next);
      return loopNode;
    }

    if (node.next) {
      return workflow.nodes.find((n) => n.id === node.next);
    }

    const edge = workflow.edges.find((e) => e.from === node.id);
    if (edge) {
      if (!edge.condition || this.evaluateCondition(edge.condition, variables)) {
        return workflow.nodes.find((n) => n.id === edge.to);
      }
    }

    return undefined;
  }

  private findNextNode(
    workflow: WorkflowDefinition,
    fromNodeId: string
  ): WorkflowNode | undefined {
    const edge = workflow.edges.find((e) => e.from === fromNodeId);
    if (edge) {
      return workflow.nodes.find((n) => n.id === edge.to);
    }
    const node = workflow.nodes.find((n) => n.id === fromNodeId);
    if (node && node.next) {
      return workflow.nodes.find((n) => n.id === node.next);
    }
    return undefined;
  }

  private evaluateCondition(
    condition: string,
    variables: Record<string, unknown>
  ): boolean {
    const trimmed = condition.trim();

    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;

    const comparisonMatch = trimmed.match(
      /^\$\{([^}]+)\}\s*(===|!==|>|<|>=|<=|==)\s*(.+)$/
    );
    if (comparisonMatch) {
      const varPath = comparisonMatch[1].trim();
      const operator = comparisonMatch[2];
      const rawValue = comparisonMatch[3].trim();
      const varValue = this.resolveVariablePath(varPath, variables);

      let comparisonValue: unknown = rawValue;
      if (
        (rawValue.startsWith("'") && rawValue.endsWith("'")) ||
        (rawValue.startsWith('"') && rawValue.endsWith('"'))
      ) {
        comparisonValue = rawValue.slice(1, -1);
      } else if (rawValue === 'true') {
        comparisonValue = true;
      } else if (rawValue === 'false') {
        comparisonValue = false;
      } else if (!isNaN(Number(rawValue))) {
        comparisonValue = Number(rawValue);
      }

      switch (operator) {
        case '===':
        case '==':
          return varValue === comparisonValue;
        case '!==':
          return varValue !== comparisonValue;
        case '>':
          return Number(varValue) > Number(comparisonValue);
        case '<':
          return Number(varValue) < Number(comparisonValue);
        case '>=':
          return Number(varValue) >= Number(comparisonValue);
        case '<=':
          return Number(varValue) <= Number(comparisonValue);
      }
    }

    const existsMatch = trimmed.match(/^\$\{([^}]+)\}$/);
    if (existsMatch) {
      const varPath = existsMatch[1].trim();
      const value = this.resolveVariablePath(varPath, variables);
      return value !== undefined && value !== null;
    }

    return false;
  }

  private resolveVariablePath(
    path: string,
    variables: Record<string, unknown>
  ): unknown {
    const parts = path.split('.');
    let current: unknown = variables;
    for (const part of parts) {
      if (current === null || current === undefined) return undefined;
      if (typeof current === 'object' && part in (current as Record<string, unknown>)) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }
    return current;
  }

  private resolveTemplate(
    template: string,
    variables: Record<string, unknown>
  ): string {
    return template.replace(/\$\{([^}]+)\}/g, (match, path) => {
      const value = this.resolveVariablePath(path.trim(), variables);
      return value !== undefined && value !== null ? String(value) : match;
    });
  }

  private resolveVariables(
    obj: unknown,
    variables: Record<string, unknown>
  ): unknown {
    if (typeof obj === 'string') {
      return this.resolveTemplate(obj, variables);
    }
    if (Array.isArray(obj)) {
      return obj.map((item) => this.resolveVariables(item, variables));
    }
    if (obj !== null && typeof obj === 'object') {
      const result: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
        result[key] = this.resolveVariables(value, variables);
      }
      return result;
    }
    return obj;
  }

  private cloneExecution(exec: WorkflowExecution): WorkflowExecution {
    return JSON.parse(JSON.stringify(exec));
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
