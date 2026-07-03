import { describe, it, expect, beforeEach, vi } from 'vitest';
import { Sandbox, SecurityError } from '../../src/security/index.js';
import type { SandboxConfig } from '../../src/security/index.js';

describe('Sandbox', () => {
  let sandbox: Sandbox;

  beforeEach(() => {
    vi.restoreAllMocks();
    sandbox = new Sandbox();
  });

  describe('Initialization', () => {
    it('creates with default config', () => {
      expect(sandbox).toBeDefined();
    });

    it('accepts partial config', () => {
      const custom = new Sandbox({ memoryLimit: 1024, timeLimit: 5000 });
      expect(custom.isWithinLimits()).toBe(true);
    });

    it('initialize resets state', () => {
      sandbox.trackAllocation(100);
      sandbox.initialize();
      const usage = sandbox.getResourceUsage();
      expect(usage.memory).toBe(0);
      expect(usage.files).toBe(0);
      expect(usage.network).toBe(0);
    });
  });

  describe('Operation Validation', () => {
    it('allows operations when sandbox is disabled', () => {
      const disabled = new Sandbox({ enabled: false });
      expect(disabled.validateOperation('process_spawn')).toBe(true);
    });

    it('blocks file system access when not allowed', () => {
      const restricted = new Sandbox({ allowFileSystemAccess: false });
      expect(() => restricted.validateOperation('file_read')).toThrow(SecurityError);
    });

    it('blocks network access when not allowed', () => {
      const restricted = new Sandbox({ allowNetworkAccess: false });
      expect(() => restricted.validateOperation('network_request')).toThrow(SecurityError);
    });

    it('blocks process spawn when not allowed', () => {
      const restricted = new Sandbox({ allowProcessSpawn: false });
      expect(() => restricted.validateOperation('process_spawn')).toThrow(SecurityError);
    });

    it('blocks dynamic code when not allowed', () => {
      const restricted = new Sandbox({ allowDynamicCode: false });
      expect(() => restricted.validateOperation('dynamic_code')).toThrow(SecurityError);
    });

    it('allows file operations when allowed', () => {
      const permissive = new Sandbox({ allowFileSystemAccess: true });
      expect(permissive.validateOperation('file_read')).toBe(true);
    });

    it('allows network when allowed', () => {
      const permissive = new Sandbox({ allowNetworkAccess: true });
      expect(permissive.validateOperation('network_request')).toBe(true);
    });

    it('validates module import against blocked list', () => {
      const s = new Sandbox({ blockedModules: ['child_process'] });
      expect(() =>
        s.validateOperation('module_import', { moduleName: 'child_process' })
      ).toThrow(SecurityError);
    });

    it('validates module import against allowed list', () => {
      const s = new Sandbox({ allowedModules: ['fs'], blockedModules: [] });
      expect(() =>
        s.validateOperation('module_import', { moduleName: 'child_process' })
      ).toThrow(SecurityError);
    });

    it('allows module in allowed list', () => {
      const s = new Sandbox({
        allowedModules: ['fs'],
        blockedModules: [],
      });
      expect(s.validateOperation('module_import', { moduleName: 'fs' })).toBe(true);
    });

    it('throws when sandbox is destroyed', () => {
      sandbox.destroy();
      expect(() => sandbox.validateOperation('file_read')).toThrow(SecurityError);
    });
  });

  describe('Resource Limits', () => {
    it('tracks memory allocation', () => {
      sandbox.trackAllocation(1024);
      const usage = sandbox.getResourceUsage();
      expect(usage.memory).toBe(1024);
    });

    it('throws when memory limit exceeded', () => {
      const limited = new Sandbox({ memoryLimit: 100 });
      expect(() => limited.trackAllocation(200)).toThrow(SecurityError);
    });

    it('tracks file operations', () => {
      sandbox.trackFileOperation();
      sandbox.trackFileOperation();
      sandbox.trackFileOperation();
      const usage = sandbox.getResourceUsage();
      expect(usage.files).toBe(3);
    });

    it('tracks network requests', () => {
      sandbox.trackNetworkRequest();
      sandbox.trackNetworkRequest();
      const usage = sandbox.getResourceUsage();
      expect(usage.network).toBe(2);
    });

    it('trackFileOperation returns false when destroyed', () => {
      sandbox.destroy();
      expect(sandbox.trackFileOperation()).toBe(false);
    });

    it('trackNetworkRequest returns false when destroyed', () => {
      sandbox.destroy();
      expect(sandbox.trackNetworkRequest()).toBe(false);
    });

    it('reports accurate resource usage', () => {
      sandbox.trackAllocation(512);
      sandbox.trackFileOperation();
      sandbox.trackNetworkRequest();
      const usage = sandbox.getResourceUsage();
      expect(usage.memory).toBe(512);
      expect(usage.files).toBe(1);
      expect(usage.network).toBe(1);
      expect(usage.time).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Time Limits', () => {
    it('throws when time limit exceeded', async () => {
      const limited = new Sandbox({ timeLimit: 0 });
      expect(() => limited.validateOperation('file_read')).toThrow(SecurityError);
    });

    it('isWithinLimits returns false after time limit', async () => {
      const limited = new Sandbox({ timeLimit: -1 });
      expect(limited.isWithinLimits()).toBe(false);
    });
  });

  describe('Reset Functionality', () => {
    it('resets all counters', () => {
      sandbox.trackAllocation(999);
      sandbox.trackFileOperation();
      sandbox.trackNetworkRequest();
      sandbox.reset();
      const usage = sandbox.getResourceUsage();
      expect(usage.memory).toBe(0);
      expect(usage.files).toBe(0);
      expect(usage.network).toBe(0);
    });

    it('restores ability to operate after reset', () => {
      sandbox.destroy();
      sandbox.reset();
      expect(sandbox.isWithinLimits()).toBe(true);
    });
  });

  describe('Destroy', () => {
    it('destroy stops all operations', () => {
      sandbox.destroy();
      expect(sandbox.isWithinLimits()).toBe(false);
    });

    it('destroy sets resource usage to zero', () => {
      sandbox.trackAllocation(500);
      sandbox.destroy();
      const usage = sandbox.getResourceUsage();
      expect(usage.memory).toBe(0);
      expect(usage.files).toBe(0);
      expect(usage.network).toBe(0);
    });
  });

  describe('Config Validation', () => {
    it('uses defaults for missing config values', () => {
      const s = new Sandbox({});
      expect(s.isWithinLimits()).toBe(true);
    });

    it('accepts full custom config', () => {
      const config: SandboxConfig = {
        enabled: true,
        memoryLimit: 512,
        timeLimit: 1000,
        allowedModules: ['fs'],
        blockedModules: [],
        allowFileSystemAccess: true,
        allowNetworkAccess: false,
        allowProcessSpawn: false,
        allowDynamicCode: false,
        tempDir: '/custom/tmp',
      };
      const s = new Sandbox(config);
      expect(s.validateOperation('file_read')).toBe(true);
    });
  });
});
