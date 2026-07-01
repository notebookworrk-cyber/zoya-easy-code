import { randomBytes, createHash } from 'crypto';
import { readFile } from 'fs/promises';
import { resolve } from 'path';

export enum Permission {
  FileRead = 'file:read',
  FileWrite = 'file:write',
  NetworkHttp = 'network:http',
  NetworkWs = 'network:ws',
  ProcessExec = 'process:exec',
  EnvRead = 'env:read',
  EnvWrite = 'env:write',
  SystemInfo = 'system:info',
  Clipboard = 'clipboard',
  AudioCapture = 'audio:capture',
  VideoCapture = 'video:capture',
  Fullscreen = 'fullscreen',
  Storage = 'storage',
  Notification = 'notification',
  Gpu = 'gpu',
  InputMonitor = 'input:monitor',
}

export interface SecurityPolicy {
  allowedPermissions: Permission[];
  deniedPermissions: Permission[];
  allowedOrigins: string[];
  maxFileSize: number;
  maxNetworkRequests: number;
  maxMemory: number;
  sandboxEnabled: boolean;
  trustedSources: string[];
}

export interface SandboxConfig {
  enabled: boolean;
  memoryLimit: number;
  timeLimit: number;
  allowedModules: string[];
  blockedModules: string[];
  allowFileSystemAccess: boolean;
  allowNetworkAccess: boolean;
  allowProcessSpawn: boolean;
  allowDynamicCode: boolean;
  tempDir: string;
}

export interface SecureImportResult {
  module: unknown;
  verified: boolean;
  warnings: string[];
}

const DEFAULT_SANDBOX_CONFIG: SandboxConfig = {
  enabled: true,
  memoryLimit: 256 * 1024 * 1024,
  timeLimit: 30000,
  allowedModules: [],
  blockedModules: ['child_process', 'cluster', 'vm'],
  allowFileSystemAccess: false,
  allowNetworkAccess: false,
  allowProcessSpawn: false,
  allowDynamicCode: false,
  tempDir: '/tmp/zoya-sandbox',
};

const DEFAULT_SECURITY_POLICY: SecurityPolicy = {
  allowedPermissions: [],
  deniedPermissions: [],
  allowedOrigins: [],
  maxFileSize: 10 * 1024 * 1024,
  maxNetworkRequests: 100,
  maxMemory: 256 * 1024 * 1024,
  sandboxEnabled: true,
  trustedSources: [],
};

class SecurityError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly permission?: string
  ) {
    super(message);
    this.name = 'SecurityError';
  }
}

export class Sandbox {
  private config: SandboxConfig;
  private fileOperations = 0;
  private networkRequests = 0;
  private memoryAllocated = 0;
  private startTime: number;
  private destroyed = false;

  constructor(config?: Partial<SandboxConfig>) {
    this.config = { ...DEFAULT_SANDBOX_CONFIG, ...config };
    this.startTime = Date.now();
  }

  initialize(): void {
    this.fileOperations = 0;
    this.networkRequests = 0;
    this.memoryAllocated = 0;
    this.startTime = Date.now();
    this.destroyed = false;
  }

  validateOperation(operation: string, details?: Record<string, unknown>): boolean {
    if (this.destroyed) {
      throw new SecurityError('Sandbox has been destroyed', 'SANDBOX_DESTROYED');
    }

    if (!this.config.enabled) return true;

    if (Date.now() - this.startTime > this.config.timeLimit) {
      throw new SecurityError('Sandbox time limit exceeded', 'TIME_LIMIT_EXCEEDED');
    }

    if (this.memoryAllocated > this.config.memoryLimit) {
      throw new SecurityError('Sandbox memory limit exceeded', 'MEMORY_LIMIT_EXCEEDED');
    }

    switch (operation) {
      case 'file_read':
      case 'file_write':
        if (!this.config.allowFileSystemAccess) {
          throw new SecurityError(
            'File system access is not allowed',
            'ACCESS_DENIED',
            operation
          );
        }
        this.fileOperations++;
        break;

      case 'network_request':
        if (!this.config.allowNetworkAccess) {
          throw new SecurityError(
            'Network access is not allowed',
            'ACCESS_DENIED',
            operation
          );
        }
        this.networkRequests++;
        break;

      case 'process_spawn':
        if (!this.config.allowProcessSpawn) {
          throw new SecurityError(
            'Process spawning is not allowed',
            'ACCESS_DENIED',
            operation
          );
        }
        break;

      case 'dynamic_code':
        if (!this.config.allowDynamicCode) {
          throw new SecurityError(
            'Dynamic code execution is not allowed',
            'ACCESS_DENIED',
            operation
          );
        }
        break;

      case 'module_import':
        if (details?.moduleName && typeof details.moduleName === 'string') {
          const moduleName = details.moduleName;
          if (this.config.blockedModules.includes(moduleName)) {
            throw new SecurityError(
              `Module is blocked: ${moduleName}`,
              'BLOCKED_MODULE',
              operation
            );
          }
          if (
            this.config.allowedModules.length > 0 &&
            !this.config.allowedModules.includes(moduleName)
          ) {
            throw new SecurityError(
              `Module is not in allowed list: ${moduleName}`,
              'MODULE_NOT_ALLOWED',
              operation
            );
          }
        }
        break;

      default:
        break;
    }

    return true;
  }

  trackAllocation(bytes: number): void {
    this.memoryAllocated += bytes;
    if (this.memoryAllocated > this.config.memoryLimit) {
      throw new SecurityError('Sandbox memory limit exceeded', 'MEMORY_LIMIT_EXCEEDED');
    }
  }

  trackFileOperation(): boolean {
    if (this.destroyed) return false;
    this.fileOperations++;
    return true;
  }

  trackNetworkRequest(): boolean {
    if (this.destroyed) return false;
    this.networkRequests++;
    return true;
  }

  getResourceUsage(): { memory: number; files: number; network: number; time: number } {
    return {
      memory: this.memoryAllocated,
      files: this.fileOperations,
      network: this.networkRequests,
      time: Date.now() - this.startTime,
    };
  }

  isWithinLimits(): boolean {
    if (this.destroyed) return false;
    if (Date.now() - this.startTime > this.config.timeLimit) return false;
    if (this.memoryAllocated > this.config.memoryLimit) return false;
    return true;
  }

  reset(): void {
    this.fileOperations = 0;
    this.networkRequests = 0;
    this.memoryAllocated = 0;
    this.startTime = Date.now();
    this.destroyed = false;
  }

  destroy(): void {
    this.destroyed = true;
    this.fileOperations = 0;
    this.networkRequests = 0;
    this.memoryAllocated = 0;
  }
}

export class PermissionManager {
  private policies: Map<string, SecurityPolicy> = new Map();
  private grantedPermissions: Map<string, Set<Permission>> = new Map();
  private pendingRequests: Map<string, Set<Permission>> = new Map();

  constructor() {}

  definePolicy(name: string, policy: Partial<SecurityPolicy>): void {
    const merged: SecurityPolicy = {
      ...DEFAULT_SECURITY_POLICY,
      ...policy,
      allowedPermissions: [...(policy.allowedPermissions ?? [])],
      deniedPermissions: [...(policy.deniedPermissions ?? [])],
      allowedOrigins: [...(policy.allowedOrigins ?? [])],
      trustedSources: [...(policy.trustedSources ?? [])],
    };
    this.policies.set(name, merged);
  }

  getPolicy(name: string): SecurityPolicy | undefined {
    const policy = this.policies.get(name);
    if (!policy) return undefined;
    return {
      ...policy,
      allowedPermissions: [...policy.allowedPermissions],
      deniedPermissions: [...policy.deniedPermissions],
      allowedOrigins: [...policy.allowedOrigins],
      trustedSources: [...policy.trustedSources],
    };
  }

  removePolicy(name: string): void {
    this.policies.delete(name);
  }

  grantPermission(userOrModule: string, permission: Permission): void {
    if (!this.grantedPermissions.has(userOrModule)) {
      this.grantedPermissions.set(userOrModule, new Set());
    }
    this.grantedPermissions.get(userOrModule)!.add(permission);
  }

  revokePermission(userOrModule: string, permission: Permission): void {
    const permissions = this.grantedPermissions.get(userOrModule);
    if (permissions) {
      permissions.delete(permission);
      if (permissions.size === 0) {
        this.grantedPermissions.delete(userOrModule);
      }
    }
  }

  hasPermission(userOrModule: string, permission: Permission): boolean {
    const permissions = this.grantedPermissions.get(userOrModule);
    return permissions !== undefined && permissions.has(permission);
  }

  async requestPermission(
    userOrModule: string,
    permission: Permission
  ): Promise<boolean> {
    if (this.hasPermission(userOrModule, permission)) {
      return true;
    }

    if (!this.pendingRequests.has(userOrModule)) {
      this.pendingRequests.set(userOrModule, new Set());
    }
    this.pendingRequests.get(userOrModule)!.add(permission);
    return false;
  }

  checkAccess(
    userOrModule: string,
    permission: Permission,
    context?: Record<string, unknown>
  ): boolean {
    const granted = this.hasPermission(userOrModule, permission);
    if (!granted) return false;

    for (const [, policy] of this.policies) {
      if (policy.deniedPermissions.includes(permission)) {
        return false;
      }
    }

    if (context?.origin && typeof context.origin === 'string') {
      for (const [, policy] of this.policies) {
        if (
          policy.allowedOrigins.length > 0 &&
          !policy.allowedOrigins.includes(context.origin)
        ) {
          return false;
        }
      }
    }

    return true;
  }

  getEffectivePermissions(userOrModule: string): Permission[] {
    const granted = this.grantedPermissions.get(userOrModule);
    if (!granted) return [];

    const denied = new Set<Permission>();
    for (const [, policy] of this.policies) {
      for (const perm of policy.deniedPermissions) {
        denied.add(perm);
      }
    }

    return [...granted].filter((perm) => !denied.has(perm));
  }

  listGrantedPermissions(): Map<string, Permission[]> {
    const result = new Map<string, Permission[]>();
    for (const [key, perms] of this.grantedPermissions) {
      result.set(key, [...perms]);
    }
    return result;
  }
}

export class PackageVerifier {
  constructor() {}

  async verifyChecksum(
    packagePath: string,
    expectedChecksum: string
  ): Promise<boolean> {
    try {
      const content = await readFile(resolve(packagePath));
      const hash = createHash('sha256').update(content).digest('hex');
      return hash === expectedChecksum;
    } catch {
      return false;
    }
  }

  async verifySignature(
    packagePath: string,
    signature: string,
    publicKey: string
  ): Promise<boolean> {
    try {
      const content = await readFile(resolve(packagePath));
      const verifier = createHash('sha256');
      verifier.update(content);
      verifier.update(publicKey);
      const expected = verifier.digest('hex');
      return signature === expected;
    } catch {
      return false;
    }
  }

  async scanForMaliciousCode(
    packagePath: string
  ): Promise<{ safe: boolean; issues: string[] }> {
    const issues: string[] = [];
    const suspiciousPatterns = [
      { pattern: /eval\s*\(/g, description: 'Uses eval()' },
      { pattern: /Function\s*\(/g, description: 'Uses Function constructor' },
      { pattern: /require\s*\(['"`]child_process['"`]\)/g, description: 'Requires child_process' },
      { pattern: /require\s*\(['"`]fs['"`]\)/g, description: 'Requires fs module' },
      { pattern: /process\.env/g, description: 'Accesses environment variables' },
      { pattern: /global\./g, description: 'Modifies global scope' },
      { pattern: /__dirname/g, description: 'Uses __dirname' },
      { pattern: /__filename/g, description: 'Uses __filename' },
      { pattern: /\/\/\s*secret|password|token|apikey/i, description: 'Possible hardcoded secret' },
      { pattern: /new\s+Function\s*\(/g, description: 'Dynamic function creation' },
    ];

    try {
      const content = await readFile(resolve(packagePath), 'utf-8');
      for (const { pattern, description } of suspiciousPatterns) {
        if (pattern.test(content)) {
          issues.push(description);
        }
      }
    } catch {
      issues.push('Could not read package file');
    }

    return {
      safe: issues.length === 0,
      issues,
    };
  }

  async verifyIntegrity(manifest: Record<string, string>): Promise<boolean> {
    for (const [filePath, expectedHash] of Object.entries(manifest)) {
      try {
        const content = await readFile(resolve(filePath));
        const hash = createHash('sha256').update(content).digest('hex');
        if (hash !== expectedHash) {
          return false;
        }
      } catch {
        return false;
      }
    }
    return true;
  }
}

export { SecurityError };
