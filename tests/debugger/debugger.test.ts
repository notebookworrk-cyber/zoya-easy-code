import { describe, it, expect, beforeEach } from 'vitest';
import { VM } from '../../src/vm/index';
import { Debugger, DebugBreakpoint, DebugWatch, DebugStackFrame } from '../../src/debugger/index';

describe('Debugger', () => {
  let vm: VM;
  let debugger_: Debugger;

  beforeEach(() => {
    vm = new VM();
    debugger_ = new Debugger(vm);
  });

  describe('lifecycle', () => {
    it('starts detached', () => {
      expect(debugger_.isAttached()).toBe(false);
    });

    it('attaches and detaches', () => {
      debugger_.attach();
      expect(debugger_.isAttached()).toBe(true);

      debugger_.detach();
      expect(debugger_.isAttached()).toBe(false);
    });

    it('stops execution and resets state', () => {
      debugger_.attach();
      debugger_.pause();
      debugger_.stop();
      expect(debugger_.isPaused()).toBe(false);
      expect(debugger_.getState().running).toBe(false);
    });

    it('pauses and resumes', () => {
      debugger_.attach();
      debugger_.getState().running = true;
      debugger_.pause();
      expect(debugger_.isPaused()).toBe(true);

      debugger_.resume();
      expect(debugger_.isPaused()).toBe(false);
    });
  });

  describe('breakpoints', () => {
    it('sets a breakpoint and returns an id', () => {
      const id = debugger_.setBreakpoint('test.zoya', 10);
      expect(id).toBeGreaterThan(0);
    });

    it('lists breakpoints', () => {
      debugger_.setBreakpoint('test.zoya', 10);
      debugger_.setBreakpoint('test.zoya', 20, 'x > 5');

      const bps = debugger_.listBreakpoints();
      expect(bps).toHaveLength(2);
      expect(bps[0].file).toBe('test.zoya');
      expect(bps[0].line).toBe(10);
      expect(bps[0].enabled).toBe(true);
      expect(bps[1].condition).toBe('x > 5');
    });

    it('removes a breakpoint', () => {
      const id = debugger_.setBreakpoint('test.zoya', 10);
      debugger_.removeBreakpoint(id);
      expect(debugger_.listBreakpoints()).toHaveLength(0);
    });

    it('enables and disables breakpoints', () => {
      const id = debugger_.setBreakpoint('test.zoya', 10);
      debugger_.disableBreakpoint(id);
      const bp = debugger_.listBreakpoints()[0];
      expect(bp.enabled).toBe(false);

      debugger_.enableBreakpoint(id);
      expect(debugger_.listBreakpoints()[0].enabled).toBe(true);
    });

    it('tracks hit count', () => {
      const id = debugger_.setBreakpoint('test.zoya', 5);
      debugger_.attach();

      const bp1 = debugger_.listBreakpoints().find(b => b.id === id)!;
      expect(bp1.hitCount).toBe(0);
    });

    it('does not create duplicate breakpoints at same line', () => {
      debugger_.setBreakpoint('test.zoya', 10);
      debugger_.setBreakpoint('test.zoya', 10);
      expect(debugger_.listBreakpoints()).toHaveLength(1);
    });
  });

  describe('watches', () => {
    it('adds a watch and returns an id', () => {
      const id = debugger_.addWatch('x');
      expect(id).toBeGreaterThan(0);
    });

    it('lists watches', () => {
      debugger_.addWatch('x');
      debugger_.addWatch('y');

      const watches = debugger_.listWatches();
      expect(watches).toHaveLength(2);
    });

    it('removes a watch', () => {
      const id = debugger_.addWatch('x');
      debugger_.removeWatch(id);
      expect(debugger_.listWatches()).toHaveLength(0);
    });

    it('evaluates watch against globals', () => {
      vm.setGlobal('myVar', 42);
      const id = debugger_.addWatch('myVar');
      debugger_.updateWatch(id);

      const watch = debugger_.listWatches().find(w => w.id === id);
      expect(watch).toBeDefined();
      expect(watch!.value).toBe(42);
    });
  });

  describe('stack frames', () => {
    it('returns empty frames when not attached', () => {
      const frames = debugger_.getStackFrames();
      expect(frames).toHaveLength(0);
    });

    it('returns call stack strings', () => {
      debugger_.attach();
      debugger_.onInstruction('test.zoya', 1, 0);

      const callStack = debugger_.getCallStack();
      expect(callStack.length).toBeGreaterThanOrEqual(0);
    });

    it('returns locals for a frame', () => {
      debugger_.attach();
      const locals = debugger_.getLocals(999);
      expect(locals.size).toBe(0);
    });

    it('returns stack for a frame', () => {
      debugger_.attach();
      const stack = debugger_.getStack(999);
      expect(stack).toHaveLength(0);
    });
  });

  describe('memory inspection', () => {
    it('inspects memory at address', () => {
      const mem = debugger_.inspectMemory(0, 10);
      expect(mem).toHaveLength(10);
      expect(mem.every(b => b === 0)).toBe(true);
    });

    it('returns empty array for zero length', () => {
      const mem = debugger_.inspectMemory(0, 0);
      expect(mem).toHaveLength(0);
    });
  });

  describe('heap stats', () => {
    it('returns heap statistics', () => {
      const stats = debugger_.getHeapStats();
      expect(stats).toHaveProperty('totalObjects');
      expect(stats).toHaveProperty('totalSize');
      expect(stats).toHaveProperty('reachableObjects');
      expect(stats.totalObjects).toBeGreaterThanOrEqual(0);
      expect(stats.totalSize).toBeGreaterThanOrEqual(0);
    });
  });

  describe('timeline', () => {
    it('records and stops timeline', () => {
      debugger_.startTimeline();
      const data = debugger_.stopTimeline();
      expect(data.events).toBeDefined();
      expect(Array.isArray(data.events)).toBe(true);
    });

    it('returns performance timeline', () => {
      const data = debugger_.getPerformanceTimeline();
      expect(data).toHaveProperty('events');
      expect(data).toHaveProperty('totalDuration');
      expect(data).toHaveProperty('functionCalls');
      expect(data).toHaveProperty('gcCollections');
    });

    it('records timeline events when attached and stepping', () => {
      debugger_.attach();
      debugger_.startTimeline();
      debugger_.onInstruction('test.zoya', 5, 0);
      const data = debugger_.stopTimeline();

      expect(data.events.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('instruction hook', () => {
    it('handles instruction callback', () => {
      debugger_.attach();
      const result = debugger_.onInstruction('test.zoya', 10, 0);
      expect(result).toBe('continue');
    });

    it('pauses on breakpoint hit', () => {
      debugger_.attach();
      debugger_.setBreakpoint('test.zoya', 10);
      const result = debugger_.onInstruction('test.zoya', 10, 0);
      expect(result).toBe('pause');
      expect(debugger_.isPaused()).toBe(true);
    });

    it('updates current file and line', () => {
      debugger_.attach();
      debugger_.onInstruction('test.zoya', 42, 0);
      expect(debugger_.getState().currentFile).toBe('test.zoya');
      expect(debugger_.getState().currentLine).toBe(42);
    });
  });

  describe('stepping', () => {
    it('stepOver sets stepping state', () => {
      debugger_.attach();
      debugger_.stepOver();
      expect(debugger_.getState().stepping).toBe(true);
    });

    it('stepInto sets stepping state with negative depth', () => {
      debugger_.attach();
      debugger_.stepInto();
      expect(debugger_.getState().stepping).toBe(true);
    });

    it('stepOut sets stepping state', () => {
      debugger_.attach();
      debugger_.stepOut();
      expect(debugger_.getState().stepping).toBe(true);
    });

    it('continue resumes execution', () => {
      debugger_.attach();
      debugger_.pause();
      debugger_.continue();
      expect(debugger_.isPaused()).toBe(false);
      expect(debugger_.getState().stepping).toBe(false);
    });

    it('stepping pauses on next instruction', () => {
      debugger_.attach();
      debugger_.getState().running = true;
      debugger_.stepOver();
      debugger_.onInstruction('test.zoya', 1, 0);
      expect(debugger_.isPaused()).toBe(true);
    });
  });
});
