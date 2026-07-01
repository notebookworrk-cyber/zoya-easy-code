import { randomBytes } from 'crypto';
import type { QueryFilter } from './database.js';

export interface AnalyticsEvent {
  name: string;
  properties: Record<string, unknown>;
  userId?: string;
  sessionId?: string;
  timestamp: Date;
  value?: number;
}

export interface AnalyticsQuery {
  event: string;
  startDate: Date;
  endDate: Date;
  groupBy?: string;
  metrics: ('count' | 'sum' | 'avg' | 'min' | 'max')[];
  filters?: QueryFilter[];
}

export interface AnalyticsResult {
  event: string;
  metrics: Record<string, number>;
  breakdown?: Record<string, Record<string, number>>;
  total: number;
  period: { start: Date; end: Date };
}

export interface UserSession {
  sessionId: string;
  userId: string;
  startTime: Date;
  endTime?: Date;
  duration: number;
  pageViews: number;
  events: number;
  device?: string;
  os?: string;
  browser?: string;
  ip?: string;
  country?: string;
}

interface StoredEvent extends AnalyticsEvent {
  id: string;
}

class AnalyticsError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'AnalyticsError';
  }
}

export class AnalyticsService {
  private sessionId: string;
  private queuedEvents: StoredEvent[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private storedEvents: StoredEvent[] = [];
  private sessions: Map<string, UserSession> = new Map();
  private optedOut = false;

  constructor(
    private readonly baseUrl: string,
    private readonly apiKey: string
  ) {
    this.sessionId = randomBytes(16).toString('hex');
    this.startFlushTimer();
  }

  track(event: string, properties?: Record<string, unknown>, value?: number): void {
    if (this.optedOut) return;

    const stored: StoredEvent = {
      id: randomBytes(8).toString('hex'),
      name: event,
      properties: properties ?? {},
      userId: undefined,
      sessionId: this.sessionId,
      timestamp: new Date(),
      value,
    };
    this.queuedEvents.push(stored);
    this.storedEvents.push(stored);
  }

  trackPageView(page: string, duration?: number): void {
    this.track('page_view', { page, duration }, duration);
  }

  trackError(error: string, fatal = false): void {
    this.track('error', { error, fatal });
  }

  trackUserAction(action: string, target?: string): void {
    this.track('user_action', { action, target });
  }

  startSession(): void {
    this.sessionId = randomBytes(16).toString('hex');
    const session: UserSession = {
      sessionId: this.sessionId,
      userId: '',
      startTime: new Date(),
      duration: 0,
      pageViews: 0,
      events: 0,
    };
    this.sessions.set(this.sessionId, session);
  }

  endSession(): void {
    const session = this.sessions.get(this.sessionId);
    if (session) {
      session.endTime = new Date();
      session.duration = session.endTime.getTime() - session.startTime.getTime();
    }
  }

  getSessionId(): string {
    return this.sessionId;
  }

  async flush(): Promise<void> {
    if (this.queuedEvents.length === 0) return;
    this.queuedEvents = [];
  }

  setFlushInterval(interval: number): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flushTimer = setInterval(() => {
      this.flush().catch(() => {});
    }, interval);
  }

  async query(query: AnalyticsQuery): Promise<AnalyticsResult> {
    const matching = this.storedEvents.filter((e) => {
      if (e.name !== query.event) return false;
      if (e.timestamp < query.startDate || e.timestamp > query.endDate) return false;
      return true;
    });

    const metrics: Record<string, number> = {};
    const values = matching.map((e) => e.value ?? 0).filter((v) => v !== 0);

    for (const metric of query.metrics) {
      switch (metric) {
        case 'count':
          metrics[metric] = matching.length;
          break;
        case 'sum':
          metrics[metric] = values.reduce((a, b) => a + b, 0);
          break;
        case 'avg':
          metrics[metric] = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
          break;
        case 'min':
          metrics[metric] = values.length > 0 ? Math.min(...values) : 0;
          break;
        case 'max':
          metrics[metric] = values.length > 0 ? Math.max(...values) : 0;
          break;
      }
    }

    let breakdown: Record<string, Record<string, number>> | undefined;
    if (query.groupBy) {
      breakdown = {};
      for (const event of matching) {
        const groupValue = String(event.properties[query.groupBy] ?? 'unknown');
        if (!breakdown[groupValue]) {
          breakdown[groupValue] = {};
          for (const metric of query.metrics) {
            breakdown[groupValue][metric] = 0;
          }
        }
        for (const metric of query.metrics) {
          if (metric === 'count') {
            breakdown[groupValue][metric]++;
          } else {
            const val = event.value ?? 0;
            breakdown[groupValue][metric] = (breakdown[groupValue][metric] ?? 0) + val;
          }
        }
      }
    }

    return {
      event: query.event,
      metrics,
      breakdown,
      total: matching.length,
      period: { start: query.startDate, end: query.endDate },
    };
  }

  async getEventCount(event: string, startDate: Date, endDate: Date): Promise<number> {
    const result = await this.query({
      event,
      startDate,
      endDate,
      metrics: ['count'],
    });
    return result.metrics.count;
  }

  async getUserCount(startDate: Date, endDate: Date): Promise<number> {
    const matching = this.storedEvents.filter(
      (e) => e.timestamp >= startDate && e.timestamp <= endDate
    );
    const uniqueUsers = new Set(matching.map((e) => e.userId).filter(Boolean));
    return uniqueUsers.size;
  }

  async getActiveUsers(days = 7): Promise<number> {
    const since = new Date(Date.now() - days * 86400000);
    return this.getUserCount(since, new Date());
  }

  async getRetentionRate(cohort: Date, daysSinceOnboarding: number): Promise<number> {
    const cohortEnd = new Date(cohort.getTime() + 86400000);
    const cohortUsers = new Set(
      this.storedEvents
        .filter((e) => e.timestamp >= cohort && e.timestamp <= cohortEnd)
        .map((e) => e.userId)
        .filter(Boolean)
    );

    if (cohortUsers.size === 0) return 0;

    const retentionDate = new Date(cohort.getTime() + daysSinceOnboarding * 86400000);
    const retentionEnd = new Date(retentionDate.getTime() + 86400000);
    const returned = this.storedEvents.filter(
      (e) =>
        e.timestamp >= retentionDate &&
        e.timestamp <= retentionEnd &&
        e.userId &&
        cohortUsers.has(e.userId)
    );

    const returnedUsers = new Set(returned.map((e) => e.userId).filter(Boolean));
    return returnedUsers.size / cohortUsers.size;
  }

  async getSessions(userId: string, limit = 10): Promise<UserSession[]> {
    const userEvents = this.storedEvents.filter((e) => e.userId === userId);
    const userSessionIds = new Set(userEvents.map((e) => e.sessionId).filter((s): s is string => typeof s === 'string'));
    const sessions: UserSession[] = [];

    for (const sid of userSessionIds) {
      const sessionEvents = this.storedEvents.filter((e) => e.sessionId === sid);
      const timestamps = sessionEvents.map((e) => e.timestamp.getTime());
      const startTime = new Date(Math.min(...timestamps));
      const endTime = new Date(Math.max(...timestamps));

      sessions.push({
        sessionId: sid,
        userId,
        startTime,
        endTime,
        duration: endTime.getTime() - startTime.getTime(),
        pageViews: sessionEvents.filter((e) => e.name === 'page_view').length,
        events: sessionEvents.length,
      });
    }

    sessions.sort((a, b) => b.startTime.getTime() - a.startTime.getTime());
    return sessions.slice(0, limit);
  }

  async getDashboard(metrics: string[]): Promise<Record<string, number>> {
    const result: Record<string, number> = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    for (const metric of metrics) {
      switch (metric) {
        case 'active_users_today':
          result[metric] = await this.getActiveUsers(1);
          break;
        case 'active_users_7d':
          result[metric] = await this.getActiveUsers(7);
          break;
        case 'active_users_30d':
          result[metric] = await this.getActiveUsers(30);
          break;
        case 'events_today':
          result[metric] = this.storedEvents.filter((e) => e.timestamp >= today).length;
          break;
        case 'total_events':
          result[metric] = this.storedEvents.length;
          break;
        case 'unique_sessions':
          result[metric] = this.sessions.size;
          break;
        default:
          result[metric] = 0;
      }
    }

    return result;
  }

  optOut(): void {
    this.optedOut = true;
    this.queuedEvents = [];
  }

  optIn(): void {
    this.optedOut = false;
  }

  async deleteUserData(userId: string): Promise<void> {
    this.storedEvents = this.storedEvents.filter((e) => e.userId !== userId);
    for (const [sid, session] of this.sessions) {
      if (session.userId === userId) {
        this.sessions.delete(sid);
      }
    }
  }

  private enqueue(event: StoredEvent): void {
    this.queuedEvents.push(event);
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flush().catch(() => {});
    }, 30000);
  }
}

export { AnalyticsError };
