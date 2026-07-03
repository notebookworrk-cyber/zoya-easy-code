import { createHash, randomBytes } from 'crypto';

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  displayName: string;
  avatarUrl?: string;
  emailVerified: boolean;
  createdAt: Date;
  lastLogin: Date;
  roles: string[];
  metadata: Record<string, unknown>;
}

export interface AuthSession {
  userId: string;
  token: string;
  refreshToken: string;
  expiresAt: Date;
  device?: string;
}

export interface AuthConfig {
  jwtSecret?: string;
  sessionDuration: number;
  maxSessions: number;
  requireEmailVerification: boolean;
  allowAnonymous: boolean;
  oauthProviders: string[];
}

export const AUTH_DEFAULTS: AuthConfig = {
  sessionDuration: 3600000,
  maxSessions: 5,
  requireEmailVerification: false,
  allowAnonymous: true,
  oauthProviders: [],
};

class AuthError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'AuthError';
  }
}

function generateToken(): string {
  return randomBytes(32).toString('hex');
}

function hashPassword(password: string): string {
  return createHash('sha256').update(password).digest('hex');
}

export class AuthService {
  private config: AuthConfig;
  private currentUser: AuthUser | null = null;
  private currentSession: AuthSession | null = null;
  private tokenRefreshTimer: NodeJS.Timeout | null = null;
  private stateCallbacks: Set<(user: AuthUser | null) => void> = new Set();
  private users: Map<string, AuthUser & { passwordHash: string }> = new Map();
  private sessions: Map<string, AuthSession> = new Map();
  private refreshTokens: Map<string, string> = new Map();
  private emailTokens: Map<string, string> = new Map();

  constructor(config?: Partial<AuthConfig>) {
    this.config = { ...AUTH_DEFAULTS, ...config };
  }

  async register(
    email: string,
    password: string,
    username: string,
    metadata?: Record<string, unknown>
  ): Promise<AuthUser> {
    for (const [, user] of this.users) {
      if (user.email === email) {
        throw new AuthError('Email already registered', 'DUPLICATE_EMAIL');
      }
      if (user.username === username) {
        throw new AuthError('Username already taken', 'DUPLICATE_USERNAME');
      }
    }

    const id = randomBytes(8).toString('hex');
    const now = new Date();
    const passwordHash = hashPassword(password);
    const user: AuthUser & { passwordHash: string } = {
      id,
      email,
      username,
      displayName: username,
      emailVerified: !this.config.requireEmailVerification,
      createdAt: now,
      lastLogin: now,
      roles: ['user'],
      metadata: metadata ?? {},
      passwordHash,
    };

    this.users.set(id, user);
    this.currentUser = { ...user, passwordHash: undefined } as unknown as AuthUser;

    if (this.config.requireEmailVerification) {
      const token = generateToken();
      this.emailTokens.set(email, token);
    }

    this.notifyStateChange();
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      displayName: user.displayName,
      avatarUrl: user.avatarUrl,
      emailVerified: user.emailVerified,
      createdAt: user.createdAt,
      lastLogin: user.lastLogin,
      roles: [...user.roles],
      metadata: { ...user.metadata },
    };
  }

  async login(email: string, password: string): Promise<AuthSession> {
    let foundUser: (AuthUser & { passwordHash: string }) | undefined;
    for (const [, user] of this.users) {
      if (user.email === email) {
        foundUser = user;
        break;
      }
    }

    if (!foundUser) {
      throw new AuthError('Invalid email or password', 'INVALID_CREDENTIALS');
    }

    if (foundUser.passwordHash !== hashPassword(password)) {
      throw new AuthError('Invalid email or password', 'INVALID_CREDENTIALS');
    }

    const session = this.createSession(foundUser.id);
    foundUser.lastLogin = new Date();
    this.currentUser = { ...foundUser, passwordHash: undefined } as unknown as AuthUser;
    this.notifyStateChange();
    return session;
  }

  async loginWithProvider(provider: string, token: string): Promise<AuthSession> {
    if (!this.config.oauthProviders.includes(provider)) {
      throw new AuthError(`OAuth provider not supported: ${provider}`, 'UNSUPPORTED_PROVIDER');
    }

    const mockUserId = `oauth_${provider}_${createHash('sha256').update(token).digest('hex').slice(0, 12)}`;

    if (!this.users.has(mockUserId)) {
      const now = new Date();
      const user: AuthUser & { passwordHash: string } = {
        id: mockUserId,
        email: `${mockUserId}@${provider}.auth`,
        username: `${provider}_user_${mockUserId.slice(0, 6)}`,
        displayName: `${provider} User`,
        emailVerified: true,
        createdAt: now,
        lastLogin: now,
        roles: ['user'],
        metadata: { provider },
        passwordHash: '',
      };
      this.users.set(mockUserId, user);
      this.currentUser = { ...user, passwordHash: undefined } as unknown as AuthUser;
    } else {
      const stored = this.users.get(mockUserId)!;
      stored.lastLogin = new Date();
      this.currentUser = { ...stored, passwordHash: undefined } as unknown as AuthUser;
    }

    this.notifyStateChange();
    return this.createSession(mockUserId);
  }

  async loginAnonymously(): Promise<AuthSession> {
    if (!this.config.allowAnonymous) {
      throw new AuthError('Anonymous login is disabled', 'ANONYMOUS_DISABLED');
    }

    const id = `anon_${randomBytes(8).toString('hex')}`;
    const now = new Date();
    const user: AuthUser & { passwordHash: string } = {
      id,
      email: '',
      username: `guest_${id.slice(0, 8)}`,
      displayName: 'Guest',
      emailVerified: false,
      createdAt: now,
      lastLogin: now,
      roles: ['guest'],
      metadata: {},
      passwordHash: '',
    };

    this.users.set(id, user);
    this.currentUser = { ...user, passwordHash: undefined } as unknown as AuthUser;
    this.notifyStateChange();
    return this.createSession(id);
  }

  async logout(): Promise<void> {
    if (this.currentSession) {
      this.sessions.delete(this.currentSession.token);
      this.refreshTokens.delete(this.currentSession.refreshToken);
    }
    this.clearRefreshTimer();
    this.currentSession = null;
    this.currentUser = null;
    this.notifyStateChange();
  }

  async refreshToken(): Promise<AuthSession> {
    if (!this.currentSession) {
      throw new AuthError('No active session', 'NO_SESSION');
    }

    const userId = this.currentSession.userId;
    const user = this.users.get(userId);
    if (!user) {
      throw new AuthError('User not found', 'USER_NOT_FOUND');
    }

    this.sessions.delete(this.currentSession.token);
    this.refreshTokens.delete(this.currentSession.refreshToken);
    const session = this.createSession(userId);
    this.currentSession = session;
    this.currentUser = { ...user, passwordHash: undefined } as unknown as AuthUser;
    this.notifyStateChange();
    return session;
  }

  async validateSession(): Promise<boolean> {
    if (!this.currentSession) {
      return false;
    }

    if (new Date() >= this.currentSession.expiresAt) {
      return false;
    }

    const stored = this.sessions.get(this.currentSession.token);
    if (!stored) {
      return false;
    }

    return this.users.has(stored.userId);
  }

  getCurrentUser(): AuthUser | null {
    if (!this.currentUser) {
      return null;
    }
    return {
      id: this.currentUser.id,
      email: this.currentUser.email,
      username: this.currentUser.username,
      displayName: this.currentUser.displayName,
      avatarUrl: this.currentUser.avatarUrl,
      emailVerified: this.currentUser.emailVerified,
      createdAt: this.currentUser.createdAt,
      lastLogin: this.currentUser.lastLogin,
      roles: [...this.currentUser.roles],
      metadata: { ...this.currentUser.metadata },
    };
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null && this.currentSession !== null;
  }

  async updateProfile(data: Partial<AuthUser>): Promise<AuthUser> {
    if (!this.currentUser) {
      throw new AuthError('Not authenticated', 'NOT_AUTHENTICATED');
    }

    const stored = this.users.get(this.currentUser.id);
    if (!stored) {
      throw new AuthError('User not found', 'USER_NOT_FOUND');
    }

    const allowedFields: (keyof AuthUser)[] = ['displayName', 'avatarUrl', 'username'];
    for (const [key, value] of Object.entries(data)) {
      if (allowedFields.includes(key as keyof AuthUser)) {
        (stored as unknown as Record<string, unknown>)[key] = value;
      }
    }

    this.currentUser = { ...stored, passwordHash: undefined } as unknown as AuthUser;
    this.notifyStateChange();
    return this.getCurrentUser()!;
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    if (!this.currentUser) {
      throw new AuthError('Not authenticated', 'NOT_AUTHENTICATED');
    }

    const stored = this.users.get(this.currentUser.id);
    if (!stored) {
      throw new AuthError('User not found', 'USER_NOT_FOUND');
    }

    if (!stored.passwordHash) {
      throw new AuthError('Cannot change password for OAuth users', 'OAUTH_USER');
    }

    if (stored.passwordHash !== hashPassword(oldPassword)) {
      throw new AuthError('Current password is incorrect', 'INVALID_PASSWORD');
    }

    stored.passwordHash = hashPassword(newPassword);
  }

  async resetPassword(email: string): Promise<void> {
    let foundUser: (AuthUser & { passwordHash: string }) | undefined;
    for (const [, user] of this.users) {
      if (user.email === email) {
        foundUser = user;
        break;
      }
    }

    if (!foundUser) {
      return;
    }

    const token = generateToken();
    this.emailTokens.set(email, token);
  }

  async deleteAccount(): Promise<void> {
    if (!this.currentUser) {
      throw new AuthError('Not authenticated', 'NOT_AUTHENTICATED');
    }

    this.users.delete(this.currentUser.id);
    if (this.currentSession) {
      this.sessions.delete(this.currentSession.token);
      this.refreshTokens.delete(this.currentSession.refreshToken);
    }
    this.clearRefreshTimer();
    this.currentSession = null;
    this.currentUser = null;
    this.notifyStateChange();
  }

  async sendVerificationEmail(): Promise<void> {
    if (!this.currentUser) {
      throw new AuthError('Not authenticated', 'NOT_AUTHENTICATED');
    }

    if (this.currentUser.emailVerified) {
      throw new AuthError('Email already verified', 'ALREADY_VERIFIED');
    }

    const token = generateToken();
    this.emailTokens.set(this.currentUser.email, token);
  }

  async verifyEmail(token: string): Promise<boolean> {
    if (!this.currentUser) {
      throw new AuthError('Not authenticated', 'NOT_AUTHENTICATED');
    }

    const storedToken = this.emailTokens.get(this.currentUser.email);
    if (!storedToken || storedToken !== token) {
      return false;
    }

    this.emailTokens.delete(this.currentUser.email);
    const stored = this.users.get(this.currentUser.id);
    if (stored) {
      stored.emailVerified = true;
    }
    this.currentUser = { ...this.currentUser, emailVerified: true };
    this.notifyStateChange();
    return true;
  }

  getToken(): string | null {
    return this.currentSession?.token ?? null;
  }

  onAuthStateChange(callback: (user: AuthUser | null) => void): void {
    this.stateCallbacks.add(callback);
  }

  private createSession(userId: string): AuthSession {
    const existingSessions: string[] = [];
    for (const [token, session] of this.sessions) {
      if (session.userId === userId) {
        existingSessions.push(token);
      }
    }

    while (existingSessions.length >= this.config.maxSessions) {
      const oldest = existingSessions.shift()!;
      const removed = this.sessions.get(oldest);
      if (removed) {
        this.refreshTokens.delete(removed.refreshToken);
      }
      this.sessions.delete(oldest);
    }

    const token = generateToken();
    const refreshToken = generateToken();
    const expiresAt = new Date(Date.now() + this.config.sessionDuration);
    const session: AuthSession = { userId, token, refreshToken, expiresAt };

    this.sessions.set(token, session);
    this.refreshTokens.set(refreshToken, token);
    this.currentSession = session;
    this.scheduleTokenRefresh(this.config.sessionDuration);
    return { ...session };
  }

  private scheduleTokenRefresh(expiresIn: number): void {
    this.clearRefreshTimer();
    const refreshAt = Math.max(expiresIn - 60000, 0);
    this.tokenRefreshTimer = setTimeout(async () => {
      try {
        await this.refreshToken();
      } catch {
        this.currentSession = null;
        this.currentUser = null;
        this.notifyStateChange();
      }
    }, refreshAt);
  }

  private clearRefreshTimer(): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }

  private notifyStateChange(): void {
    const user = this.getCurrentUser();
    for (const callback of this.stateCallbacks) {
      callback(user);
    }
  }
}

export { AuthError };
