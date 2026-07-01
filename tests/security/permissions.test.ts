import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PermissionManager, Permission } from '../../src/security/index.js';
import type { SecurityPolicy } from '../../src/security/index.js';

describe('PermissionManager', () => {
  let pm: PermissionManager;

  beforeEach(() => {
    vi.restoreAllMocks();
    pm = new PermissionManager();
  });

  describe('Policy Definition and Retrieval', () => {
    it('defines a policy', () => {
      pm.definePolicy('default', {
        allowedPermissions: [Permission.FileRead, Permission.Storage],
        maxFileSize: 1024,
      });
      const policy = pm.getPolicy('default');
      expect(policy).toBeDefined();
      expect(policy!.allowedPermissions).toContain(Permission.FileRead);
      expect(policy!.maxFileSize).toBe(1024);
    });

    it('returns undefined for non-existent policy', () => {
      expect(pm.getPolicy('nonexistent')).toBeUndefined();
    });

    it('removes a policy', () => {
      pm.definePolicy('temp', { allowedPermissions: [] });
      pm.removePolicy('temp');
      expect(pm.getPolicy('temp')).toBeUndefined();
    });

    it('returns a copy of the policy (immutability)', () => {
      pm.definePolicy('test', {
        allowedPermissions: [Permission.FileRead],
      });
      const policy = pm.getPolicy('test')!;
      policy.allowedPermissions.push(Permission.FileWrite);
      const policyAgain = pm.getPolicy('test')!;
      expect(policyAgain.allowedPermissions).not.toContain(Permission.FileWrite);
    });
  });

  describe('Grant and Revoke Permissions', () => {
    it('grants a permission', () => {
      pm.grantPermission('user1', Permission.FileRead);
      expect(pm.hasPermission('user1', Permission.FileRead)).toBe(true);
    });

    it('revokes a permission', () => {
      pm.grantPermission('user1', Permission.FileRead);
      pm.revokePermission('user1', Permission.FileRead);
      expect(pm.hasPermission('user1', Permission.FileRead)).toBe(false);
    });

    it('revoke does not throw for non-existent permission', () => {
      expect(() => pm.revokePermission('ghost', Permission.Gpu)).not.toThrow();
    });

    it('tracks permissions per user independently', () => {
      pm.grantPermission('userA', Permission.FileRead);
      pm.grantPermission('userB', Permission.FileWrite);
      expect(pm.hasPermission('userA', Permission.FileRead)).toBe(true);
      expect(pm.hasPermission('userA', Permission.FileWrite)).toBe(false);
      expect(pm.hasPermission('userB', Permission.FileWrite)).toBe(true);
    });
  });

  describe('Permission Checking', () => {
    it('returns false for unpermitted action', () => {
      expect(pm.hasPermission('user1', Permission.ProcessExec)).toBe(false);
    });

    it('returns true for granted permission', () => {
      pm.grantPermission('user1', Permission.Clipboard);
      expect(pm.hasPermission('user1', Permission.Clipboard)).toBe(true);
    });
  });

  describe('Access Control', () => {
    it('checkAccess returns true for granted permission', () => {
      pm.grantPermission('module1', Permission.Storage);
      expect(pm.checkAccess('module1', Permission.Storage)).toBe(true);
    });

    it('checkAccess returns false for ungranted permission', () => {
      expect(pm.checkAccess('module1', Permission.Storage)).toBe(false);
    });

    it('checkAccess respects denied permissions in policies', () => {
      pm.definePolicy('strict', {
        deniedPermissions: [Permission.NetworkHttp],
      });
      pm.grantPermission('module1', Permission.NetworkHttp);
      expect(pm.checkAccess('module1', Permission.NetworkHttp)).toBe(false);
    });

    it('checkAccess validates origin against policy', () => {
      pm.definePolicy('originCheck', {
        allowedOrigins: ['https://trusted.com'],
        allowedPermissions: [Permission.Notification],
        deniedPermissions: [],
      });
      pm.grantPermission('web', Permission.Notification);
      expect(
        pm.checkAccess('web', Permission.Notification, { origin: 'https://trusted.com' })
      ).toBe(true);
      expect(
        pm.checkAccess('web', Permission.Notification, { origin: 'https://evil.com' })
      ).toBe(false);
    });
  });

  describe('Effective Permissions', () => {
    it('returns all effective permissions', () => {
      pm.grantPermission('user1', Permission.FileRead);
      pm.grantPermission('user1', Permission.FileWrite);
      pm.grantPermission('user1', Permission.NetworkHttp);
      const effective = pm.getEffectivePermissions('user1');
      expect(effective).toContain(Permission.FileRead);
      expect(effective).toContain(Permission.NetworkHttp);
      expect(effective.length).toBe(3);
    });

    it('excludes denied permissions from effective list', () => {
      pm.definePolicy('policy1', {
        deniedPermissions: [Permission.FileWrite],
      });
      pm.grantPermission('user1', Permission.FileRead);
      pm.grantPermission('user1', Permission.FileWrite);
      const effective = pm.getEffectivePermissions('user1');
      expect(effective).toContain(Permission.FileRead);
      expect(effective).not.toContain(Permission.FileWrite);
    });

    it('returns empty array for unknown user', () => {
      expect(pm.getEffectivePermissions('nobody')).toEqual([]);
    });
  });

  describe('Request Permission', () => {
    it('returns true if already granted', async () => {
      pm.grantPermission('module1', Permission.Gpu);
      const result = await pm.requestPermission('module1', Permission.Gpu);
      expect(result).toBe(true);
    });

    it('returns false if not granted', async () => {
      const result = await pm.requestPermission('module1', Permission.Gpu);
      expect(result).toBe(false);
    });
  });

  describe('listGrantedPermissions', () => {
    it('lists all granted permissions', () => {
      pm.grantPermission('u1', Permission.FileRead);
      pm.grantPermission('u1', Permission.FileWrite);
      pm.grantPermission('u2', Permission.NetworkHttp);
      const listed = pm.listGrantedPermissions();
      expect(listed.get('u1')).toContain(Permission.FileRead);
      expect(listed.get('u2')).toContain(Permission.NetworkHttp);
      expect(listed.size).toBe(2);
    });

    it('returns empty map when no permissions granted', () => {
      const listed = pm.listGrantedPermissions();
      expect(listed.size).toBe(0);
    });
  });
});
