import { VM } from '../vm/index';
import {
  ZoyaValue, ZoyaObject, ZoyaArray, ZoyaFunction, ZoyaClosure, ZoyaNative,
  ZoyaNull, ZoyaBoolean, ZoyaString, ZoyaNumber, ZOYA_NIL,
} from '../types';

export interface DebugBreakpoint {
  id: number;
  file: string;
  line: number;
  condition?: string;
  enabled: boolean;
  hitCount: number;
}

export interface DebugWatch {
  id: number;
  expression: string;
  value: ZoyaValue;
}

export interface DebugStackFrame {
  id: number;
  functionName: string;
  file: string;
  line: number;
  locals: Map<string, ZoyaValue>;
  stack: ZoyaValue[];
}

export interface DebugState {
  running: boolean;
  paused: boolean;
  stepping: boolean;
  currentFile: string;
  currentLine: number;
  frames: DebugStackFrame[];
  breakpoints: DebugBreakpoint[];
  watches: DebugWatch[];
}

export interface TimelineEvent {
  timestamp: number;
  type: 'function_call' | 'gc_collect' | 'breakpoint_hit' | 'step' | 'exception';
  detail: string;
  duration: number;
}

export interface TimelineData {
  events: TimelineEvent[];
  totalDuration: number;
  functionCalls: number;
  gcCollections: number;
}

type DebugHook = (file: string, line: number, opcode: number) => 'pause' | 'continue' | 'step';

export class Debugger {
  private state: DebugState;
  private readonly vm: VM;
  private readonly history: DebugStackFrame[] = [];
  private readonly maxHistory: number = 100;
  private nextBreakpointId = 1;
  private nextWatchId = 1;
  private nextFrameId = 1;
  private attached = false;
  private originalInterpret: ((chunk: import('../vm/chunk').Chunk) => ZoyaValue) | null = null;
  private debugMode = false;
  private stepDepth = 0;
  private currentFrameDepth = 0;
  private timelineEvents: TimelineEvent[] = [];
  private timelineRecording = false;
  private timelineStart = 0;

  constructor(vm: VM) {
    this.vm = vm;
    this.state = {
      running: false,
      paused: false,
      stepping: false,
      currentFile: '',
      currentLine: 0,
      frames: [],
      breakpoints: [],
      watches: [],
    };
  }

  attach(): void {
    if (this.attached) return;
    this.attached = true;
    this.debugMode = true;
  }

  detach(): void {
    if (!this.attached) return;
    this.attached = false;
    this.debugMode = false;
    this.state.running = false;
    this.state.paused = false;
  }

  pause(): void {
    if (this.state.running && !this.state.paused) {
      this.state.paused = true;
      this.state.stepping = false;
    }
  }

  resume(): void {
    this.state.paused = false;
    this.state.stepping = false;
  }

  stop(): void {
    this.state.running = false;
    this.state.paused = false;
    this.state.stepping = false;
    this.state.frames = [];
    this.state.currentFile = '';
    this.state.currentLine = 0;
  }

  stepOver(): void {
    this.state.stepping = true;
    this.state.paused = false;
    this.currentFrameDepth = this.state.frames.length;
  }

  stepInto(): void {
    this.state.stepping = true;
    this.state.paused = false;
    this.currentFrameDepth = -1;
  }

  stepOut(): void {
    this.state.stepping = true;
    this.state.paused = false;
    this.currentFrameDepth = Math.max(0, this.state.frames.length - 2);
  }

  continue(): void {
    this.state.paused = false;
    this.state.stepping = false;
  }

  onInstruction(file: string, line: number, opcode: number): 'pause' | 'continue' {
    if (!this.attached) return 'continue';

    this.state.currentFile = file;
    this.state.currentLine = line;

    const shouldPause = this.checkBreakpoints(file, line);

    if (shouldPause) {
      this.updateFrames();
      this.updateWatches();
      this.state.paused = true;
      this.recordTimeline('breakpoint_hit', `Breakpoint at ${file}:${line}`, 0);
      return 'pause';
    }

    if (this.state.stepping && !this.state.paused) {
      const frameCount = this.state.frames.length;
      if (this.currentFrameDepth === -1 || frameCount <= this.currentFrameDepth) {
        this.updateFrames();
        this.updateWatches();
        this.state.paused = true;
        this.state.stepping = false;
        this.recordTimeline('step', `Step at ${file}:${line}`, 0);
        return 'pause';
      }
    }

    return 'continue';
  }

  setBreakpoint(file: string, line: number, condition?: string): number {
    const existing = this.state.breakpoints.find(b => b.file === file && b.line === line);
    if (existing) {
      existing.enabled = true;
      return existing.id;
    }

    const bp: DebugBreakpoint = {
      id: this.nextBreakpointId++,
      file,
      line,
      condition,
      enabled: true,
      hitCount: 0,
    };
    this.state.breakpoints.push(bp);
    return bp.id;
  }

  removeBreakpoint(id: number): void {
    const idx = this.state.breakpoints.findIndex(b => b.id === id);
    if (idx >= 0) {
      this.state.breakpoints.splice(idx, 1);
    }
  }

  enableBreakpoint(id: number): void {
    const bp = this.state.breakpoints.find(b => b.id === id);
    if (bp) bp.enabled = true;
  }

  disableBreakpoint(id: number): void {
    const bp = this.state.breakpoints.find(b => b.id === id);
    if (bp) bp.enabled = false;
  }

  listBreakpoints(): DebugBreakpoint[] {
    return [...this.state.breakpoints];
  }

  addWatch(expression: string): number {
    const watch: DebugWatch = {
      id: this.nextWatchId++,
      expression,
      value: ZOYA_NIL,
    };
    this.state.watches.push(watch);
    this.evaluateWatch(watch);
    return watch.id;
  }

  removeWatch(id: number): void {
    const idx = this.state.watches.findIndex(w => w.id === id);
    if (idx >= 0) {
      this.state.watches.splice(idx, 1);
    }
  }

  updateWatch(id: number): void {
    const watch = this.state.watches.find(w => w.id === id);
    if (watch) {
      this.evaluateWatch(watch);
    }
  }

  listWatches(): DebugWatch[] {
    return [...this.state.watches];
  }

  getStackFrames(): DebugStackFrame[] {
    return [...this.state.frames];
  }

  getLocals(frameId: number): Map<string, ZoyaValue> {
    const frame = this.state.frames.find(f => f.id === frameId);
    return frame ? new Map(frame.locals) : new Map();
  }

  getStack(frameId: number): ZoyaValue[] {
    const frame = this.state.frames.find(f => f.id === frameId);
    return frame ? [...frame.stack] : [];
  }

  getCallStack(): string[] {
    return this.state.frames.map(f =>
      `${f.functionName} at ${f.file}:${f.line}`,
    );
  }

  inspectMemory(address: number, length: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < length; i++) {
      result.push(0);
    }
    return result;
  }

  getHeapStats(): { totalObjects: number; totalSize: number; reachableObjects: number } {
    const globals = this.vm.getGlobals();
    const stack = this.vm.getStack();
    const objIds = new Set<number>();

    for (const val of stack) {
      this.collectIds(val, objIds);
    }
    for (const val of globals.values()) {
      this.collectIds(val, objIds);
    }

    return {
      totalObjects: objIds.size,
      totalSize: objIds.size * 64,
      reachableObjects: objIds.size,
    };
  }

  private collectIds(val: ZoyaValue, ids: Set<number>): void {
    if (val === null || val === undefined) return;
    if (typeof val === 'boolean' || typeof val === 'number' || typeof val === 'string') return;
    if (typeof val === 'object') {
      const obj = val as ZoyaObject;
      if (ids.has(obj.__id)) return;
      ids.add(obj.__id);

      if (obj.__zoya_type === 'array') {
        const arr = val as ZoyaArray;
        for (const elem of arr.elements) {
          this.collectIds(elem, ids);
        }
      }
      if (obj.__zoya_type === 'closure') {
        const clos = val as ZoyaClosure;
        this.collectIds(clos.function, ids);
        for (const uv of clos.upvalues) {
          this.collectIds(uv, ids);
        }
      }
      if (obj.__zoya_type === 'function') {
        const func = val as ZoyaFunction;
        for (const c of func.chunk.constants) {
          this.collectIds(c, ids);
        }
      }
    }
  }

  startTimeline(): void {
    this.timelineEvents = [];
    this.timelineRecording = true;
    this.timelineStart = performance.now();
  }

  stopTimeline(): TimelineData {
    this.timelineRecording = false;
    return this.getPerformanceTimeline();
  }

  getPerformanceTimeline(): TimelineData {
    const totalDuration = this.timelineEvents.length > 0
      ? this.timelineEvents[this.timelineEvents.length - 1].timestamp - this.timelineEvents[0].timestamp
      : 0;

    return {
      events: [...this.timelineEvents],
      totalDuration,
      functionCalls: this.timelineEvents.filter(e => e.type === 'function_call').length,
      gcCollections: this.timelineEvents.filter(e => e.type === 'gc_collect').length,
    };
  }

  private recordTimeline(type: TimelineEvent['type'], detail: string, duration: number): void {
    if (!this.timelineRecording) return;
    this.timelineEvents.push({
      timestamp: performance.now() - this.timelineStart,
      type,
      detail,
      duration,
    });
  }

  private checkBreakpoints(file: string, line: number): boolean {
    for (const bp of this.state.breakpoints) {
      if (!bp.enabled) continue;
      if (bp.file !== file && !file.endsWith(bp.file) && !bp.file.endsWith(file)) continue;
      if (bp.line !== line) continue;

      bp.hitCount++;
      return true;
    }
    return false;
  }

  private updateFrames(): void {
    const newFrames: DebugStackFrame[] = [];
    const stack = this.vm.getStack();
    const globals = this.vm.getGlobals();

    const frame: DebugStackFrame = {
      id: this.nextFrameId++,
      functionName: '<script>',
      file: this.state.currentFile || '<unknown>',
      line: this.state.currentLine,
      locals: new Map<string, ZoyaValue>(),
      stack: [...stack],
    };

    for (const [name, val] of globals) {
      frame.locals.set(name, val);
    }

    newFrames.push(frame);

    if (this.history.length >= this.maxHistory) {
      this.history.shift();
    }
    this.history.push(frame);

    this.state.frames = newFrames;
  }

  private evaluateWatch(watch: DebugWatch): void {
    try {
      const globals = this.vm.getGlobals();
      const val = globals.get(watch.expression);
      watch.value = val !== undefined ? val : ZOYA_NIL;
    } catch {
      watch.value = ZOYA_NIL;
    }
  }

  private updateWatches(): void {
    for (const watch of this.state.watches) {
      this.evaluateWatch(watch);
    }
  }

  getState(): Readonly<DebugState> {
    return this.state;
  }

  isPaused(): boolean {
    return this.state.paused;
  }

  isAttached(): boolean {
    return this.attached;
  }
}
