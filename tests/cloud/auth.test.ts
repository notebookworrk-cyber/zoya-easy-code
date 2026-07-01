import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthService, AuthError } from '../../src/cloud/auth.js';

describe('AuthService', () => {
  let auth: AuthService;

  beforeEach(() => {
    vi.restoreAllMocks();
    auth = new AuthService();
  });

  describe('Registration', () => {
    it('registers a new user', async () => {
      const user = await auth.register('test@example.com', 'password123', 'testuser');
      expect(user.email).toBe('test@example.com');
      expect(user.username).toBe('testuser');
      expect(user.displayName).toBe('testuser');
      expect(user.id).toBeDefined();
      expect(user.emailVerified).toBe(true);
      expect(user.roles).toEqual(['user']);
      expect(user.createdAt).toBeInstanceOf(Date);
      expect(user.lastLogin).toBeInstanceOf(Date);
    });

    it('throws on duplicate email', async () => {
      await auth.register('dup@example.com', 'pass1', 'user1');
      await expect(auth.register('dup@example.com', 'pass2', 'user2')).rejects.toThrow(
        AuthError
      );
    });

    it('throws on duplicate username', async () => {
      await auth.register('a@example.com', 'pass1', 'sameuser');
      await expect(auth.register('b@example.com', 'pass2', 'sameuser')).rejects.toThrow(
        AuthError
      );
    });

    it('stores metadata on registration', async () => {
      const metadata = { favoriteColor: 'blue', age: 25 };
      const user = await auth.register('meta@example.com', 'pass', 'metauser', metadata);
      expect(user.metadata).toEqual(metadata);
    });
  });

  describe('Login', () => {
    it('logs in with valid credentials', async () => {
      await auth.register('login@example.com', 'password123', 'loginuser');
      const session = await auth.login('login@example.com', 'password123');
      expect(session.token).toBeDefined();
      expect(session.refreshToken).toBeDefined();
      expect(session.userId).toBeDefined();
      expect(session.expiresAt).toBeInstanceOf(Date);
      expect(session.expiresAt.getTime()).toBeGreaterThan(Date.now());
    });

    it('throws on invalid password', async () => {
      await auth.register('fail@example.com', 'correct', 'failuser');
      await expect(auth.login('fail@example.com', 'wrong')).rejects.toThrow(AuthError);
    });

    it('throws on non-existent email', async () => {
      await expect(auth.login('nobody@example.com', 'pass')).rejects.toThrow(AuthError);
    });

    it('updates lastLogin on successful login', async () => {
      await auth.register('logintime@example.com', 'pass', 'logintimeuser');
      const before = Date.now();
      await auth.login('logintime@example.com', 'pass');
      const user = auth.getCurrentUser();
      expect(user!.lastLogin.getTime()).toBeGreaterThanOrEqual(before);
    });
  });

  describe('OAuth Login', () => {
    it('logs in with supported provider', async () => {
      const oauthAuth = new AuthService({ oauthProviders: ['google'] });
      const session = await oauthAuth.loginWithProvider('google', 'google_token_123');
      expect(session.token).toBeDefined();
      expect(oauthAuth.isAuthenticated()).toBe(true);
    });

    it('throws on unsupported provider', async () => {
      await expect(auth.loginWithProvider('unsupported', 'token')).rejects.toThrow(AuthError);
    });
  });

  describe('Anonymous Login', () => {
    it('logs in anonymously', async () => {
      const session = await auth.loginAnonymously();
      expect(session.token).toBeDefined();
      expect(auth.getCurrentUser()!.username).toMatch(/^guest_/);
    });

    it('throws when anonymous login is disabled', async () => {
      const noAnon = new AuthService({ allowAnonymous: false });
      await expect(noAnon.loginAnonymously()).rejects.toThrow(AuthError);
    });
  });

  describe('Session Management', () => {
    it('validates active session', async () => {
      await auth.register('session@example.com', 'pass', 'sessionuser');
      await auth.login('session@example.com', 'pass');
      expect(await auth.validateSession()).toBe(true);
    });

    it('returns false when not authenticated', async () => {
      expect(await auth.validateSession()).toBe(false);
    });

    it('refreshes token', async () => {
      await auth.register('refresh@example.com', 'pass', 'refreshuser');
      const session = await auth.login('refresh@example.com', 'pass');
      const refreshed = await auth.refreshToken();
      expect(refreshed.token).toBeDefined();
      expect(refreshed.token).not.toBe(session.token);
    });

    it('throws on refresh with no session', async () => {
      await expect(auth.refreshToken()).rejects.toThrow(AuthError);
    });
  });

  describe('Authentication State', () => {
    it('returns false before login', () => {
      expect(auth.isAuthenticated()).toBe(false);
    });

    it('returns true after login', async () => {
      await auth.register('state@example.com', 'pass', 'stateuser');
      await auth.login('state@example.com', 'pass');
      expect(auth.isAuthenticated()).toBe(true);
    });

    it('returns false after logout', async () => {
      await auth.register('logout@example.com', 'pass', 'logoutuser');
      await auth.login('logout@example.com', 'pass');
      await auth.logout();
      expect(auth.isAuthenticated()).toBe(false);
    });

    it('returns null user before login', () => {
      expect(auth.getCurrentUser()).toBeNull();
    });

    it('returns user after login', async () => {
      await auth.register('me@example.com', 'pass', 'meuser');
      await auth.login('me@example.com', 'pass');
      const user = auth.getCurrentUser();
      expect(user).not.toBeNull();
      expect(user!.email).toBe('me@example.com');
    });
  });

  describe('Profile Updates', () => {
    it('updates display name', async () => {
      await auth.register('profile@example.com', 'pass', 'profileuser');
      await auth.login('profile@example.com', 'pass');
      const updated = await auth.updateProfile({ displayName: 'New Name' });
      expect(updated.displayName).toBe('New Name');
    });

    it('updates avatar url', async () => {
      await auth.register('avatar@example.com', 'pass', 'avataruser');
      await auth.login('avatar@example.com', 'pass');
      const updated = await auth.updateProfile({ avatarUrl: 'https://example.com/avatar.png' });
      expect(updated.avatarUrl).toBe('https://example.com/avatar.png');
    });

    it('throws when not authenticated', async () => {
      await expect(auth.updateProfile({ displayName: 'Nope' })).rejects.toThrow(AuthError);
    });
  });

  describe('Password Management', () => {
    it('changes password with correct old password', async () => {
      await auth.register('pwd@example.com', 'oldpass', 'pwduser');
      await auth.login('pwd@example.com', 'oldpass');
      await expect(auth.changePassword('oldpass', 'newpass')).resolves.toBeUndefined();
    });

    it('throws with incorrect old password', async () => {
      await auth.register('badpwd@example.com', 'oldpass', 'badpwduser');
      await auth.login('badpwd@example.com', 'oldpass');
      await expect(auth.changePassword('wrong', 'newpass')).rejects.toThrow(AuthError);
    });

    it('throws when not authenticated', async () => {
      await expect(auth.changePassword('old', 'new')).rejects.toThrow(AuthError);
    });
  });

  describe('Email Verification', () => {
    it('sends verification email', async () => {
      const verifyAuth = new AuthService({ requireEmailVerification: true });
      await verifyAuth.register('verify@example.com', 'pass', 'verifyuser');
      await verifyAuth.login('verify@example.com', 'pass');
      await expect(verifyAuth.sendVerificationEmail()).resolves.toBeUndefined();
    });

    it('throws when email already verified', async () => {
      await auth.register('already@example.com', 'pass', 'alreadyuser');
      await auth.login('already@example.com', 'pass');
      await expect(auth.sendVerificationEmail()).rejects.toThrow(AuthError);
    });

    it('throws when not authenticated', async () => {
      await expect(auth.sendVerificationEmail()).rejects.toThrow(AuthError);
    });
  });

  describe('Token Management', () => {
    it('returns null token before login', () => {
      expect(auth.getToken()).toBeNull();
    });

    it('returns token after login', async () => {
      await auth.register('token@example.com', 'pass', 'tokenuser');
      await auth.login('token@example.com', 'pass');
      expect(auth.getToken()).toBeTruthy();
    });

    it('returns null token after logout', async () => {
      await auth.register('tokenclear@example.com', 'pass', 'tokenclearuser');
      await auth.login('tokenclear@example.com', 'pass');
      await auth.logout();
      expect(auth.getToken()).toBeNull();
    });
  });

  describe('Auth State Change', () => {
    it('notifies on login', async () => {
      const callback = vi.fn();
      auth.onAuthStateChange(callback);
      await auth.register('notify@example.com', 'pass', 'notifyuser');
      await auth.login('notify@example.com', 'pass');
      expect(callback).toHaveBeenCalledWith(expect.objectContaining({ email: 'notify@example.com' }));
    });

    it('notifies null on logout', async () => {
      const callback = vi.fn();
      auth.onAuthStateChange(callback);
      await auth.register('logoutnotify@example.com', 'pass', 'logoutnotifyuser');
      await auth.login('logoutnotify@example.com', 'pass');
      await auth.logout();
      expect(callback).toHaveBeenLastCalledWith(null);
    });
  });

  describe('Account Deletion', () => {
    it('deletes authenticated user account', async () => {
      await auth.register('delete@example.com', 'pass', 'deleteuser');
      await auth.login('delete@example.com', 'pass');
      await auth.deleteAccount();
      expect(auth.isAuthenticated()).toBe(false);
    });

    it('throws when not authenticated', async () => {
      await expect(auth.deleteAccount()).rejects.toThrow(AuthError);
    });
  });
});
