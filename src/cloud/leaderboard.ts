import { randomBytes } from 'crypto';

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  username: string;
  score: number;
  metadata?: Record<string, unknown>;
  updatedAt: Date;
}

export interface LeaderboardDefinition {
  id: string;
  name: string;
  sortOrder: 'asc' | 'desc';
  updateStrategy: 'best' | 'latest' | 'sum' | 'average';
  resetPeriod?: 'daily' | 'weekly' | 'monthly' | 'never';
  maxEntries?: number;
}

interface StoredScore {
  userId: string;
  username: string;
  score: number;
  count: number;
  metadata?: Record<string, unknown>;
  updatedAt: Date;
}

class LeaderboardError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'LeaderboardError';
  }
}

export class LeaderboardService {
  private leaderboards: Map<string, LeaderboardDefinition> = new Map();
  private scores: Map<string, Map<string, StoredScore>> = new Map();

  constructor(private readonly baseUrl: string, private readonly apiKey: string) {}

  async submitScore(
    leaderboardId: string,
    userId: string,
    score: number,
    metadata?: Record<string, unknown>
  ): Promise<LeaderboardEntry> {
    const def = this.leaderboards.get(leaderboardId);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${leaderboardId}`, 'NOT_FOUND');
    }

    if (!this.scores.has(leaderboardId)) {
      this.scores.set(leaderboardId, new Map());
    }
    const boardScores = this.scores.get(leaderboardId)!;
    const existing = boardScores.get(userId);
    const now = new Date();

    let newScore: number;
    let newCount: number;

    if (existing) {
      newCount = existing.count + 1;
      switch (def.updateStrategy) {
        case 'best':
          newScore = Math.max(existing.score, score);
          break;
        case 'latest':
          newScore = score;
          break;
        case 'sum':
          newScore = existing.score + score;
          break;
        case 'average':
          newScore = Math.round((existing.score * existing.count + score) / newCount);
          break;
        default:
          newScore = score;
      }
    } else {
      newCount = 1;
      newScore = score;
    }

    const stored: StoredScore = {
      userId,
      username: `user_${userId.slice(0, 6)}`,
      score: newScore,
      count: newCount,
      metadata: metadata ? { ...metadata } : existing?.metadata ? { ...existing.metadata } : undefined,
      updatedAt: now,
    };

    boardScores.set(userId, stored);
    return this.buildEntry(stored, def);
  }

  async getScores(
    leaderboardId: string,
    limit = 50,
    offset = 0
  ): Promise<LeaderboardEntry[]> {
    const def = this.leaderboards.get(leaderboardId);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${leaderboardId}`, 'NOT_FOUND');
    }

    const boardScores = this.scores.get(leaderboardId);
    if (!boardScores) return [];

    const sorted = this.sortScores(boardScores, def);
    const sliced = sorted.slice(offset, offset + limit);
    return sliced.map((s, i) => this.buildEntry(s, def, offset + i + 1));
  }

  async getRank(leaderboardId: string, userId: string): Promise<LeaderboardEntry | null> {
    const def = this.leaderboards.get(leaderboardId);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${leaderboardId}`, 'NOT_FOUND');
    }

    const boardScores = this.scores.get(leaderboardId);
    if (!boardScores) return null;

    const sorted = this.sortScores(boardScores, def);
    const index = sorted.findIndex((s) => s.userId === userId);
    if (index === -1) return null;

    return this.buildEntry(sorted[index], def, index + 1);
  }

  async getAroundUser(
    leaderboardId: string,
    userId: string,
    range = 3
  ): Promise<LeaderboardEntry[]> {
    const def = this.leaderboards.get(leaderboardId);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${leaderboardId}`, 'NOT_FOUND');
    }

    const boardScores = this.scores.get(leaderboardId);
    if (!boardScores) return [];

    const sorted = this.sortScores(boardScores, def);
    const index = sorted.findIndex((s) => s.userId === userId);
    if (index === -1) return [];

    const start = Math.max(0, index - range);
    const end = Math.min(sorted.length, index + range + 1);
    return sorted.slice(start, end).map((s, i) => this.buildEntry(s, def, start + i + 1));
  }

  async getFriendsLeaderboard(
    leaderboardId: string,
    userId: string
  ): Promise<LeaderboardEntry[]> {
    const def = this.leaderboards.get(leaderboardId);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${leaderboardId}`, 'NOT_FOUND');
    }

    const boardScores = this.scores.get(leaderboardId);
    if (!boardScores) return [];

    const sorted = this.sortScores(boardScores, def);
    const friendIds = this.getMockFriends(userId);
    const filtered = sorted.filter((s) => friendIds.includes(s.userId) || s.userId === userId);

    if (filtered.length === 0) return [];

    const userIndex = filtered.findIndex((s) => s.userId === userId);
    const globalRank = sorted.findIndex((s) => s.userId === userId) + 1;

    return filtered.map((s, i) => {
      const entry = this.buildEntry(s, def, i + 1);
      if (s.userId === userId) {
        entry.rank = globalRank;
      }
      return entry;
    });
  }

  async createLeaderboard(definition: LeaderboardDefinition): Promise<void> {
    if (this.leaderboards.has(definition.id)) {
      throw new LeaderboardError(
        `Leaderboard already exists: ${definition.id}`,
        'ALREADY_EXISTS'
      );
    }
    this.leaderboards.set(definition.id, { ...definition });
    this.scores.set(definition.id, new Map());
  }

  async updateLeaderboard(
    id: string,
    updates: Partial<LeaderboardDefinition>
  ): Promise<void> {
    const def = this.leaderboards.get(id);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${id}`, 'NOT_FOUND');
    }
    Object.assign(def, updates);
  }

  async deleteLeaderboard(id: string): Promise<void> {
    if (!this.leaderboards.has(id)) {
      throw new LeaderboardError(`Leaderboard not found: ${id}`, 'NOT_FOUND');
    }
    this.leaderboards.delete(id);
    this.scores.delete(id);
  }

  async listLeaderboards(): Promise<LeaderboardDefinition[]> {
    return [...this.leaderboards.values()].map((def) => ({ ...def }));
  }

  async resetLeaderboard(id: string): Promise<void> {
    const def = this.leaderboards.get(id);
    if (!def) {
      throw new LeaderboardError(`Leaderboard not found: ${id}`, 'NOT_FOUND');
    }
    this.scores.set(id, new Map());
  }

  async getResetSchedule(id: string): Promise<string | null> {
    const def = this.leaderboards.get(id);
    if (!def) return null;
    return def.resetPeriod ?? null;
  }

  private sortScores(
    boardScores: Map<string, StoredScore>,
    def: LeaderboardDefinition
  ): StoredScore[] {
    const sorted = [...boardScores.values()];
    sorted.sort((a, b) => {
      const cmp = a.score - b.score;
      return def.sortOrder === 'desc' ? -cmp : cmp;
    });
    return sorted;
  }

  private buildEntry(
    stored: StoredScore,
    def: LeaderboardDefinition,
    rank?: number
  ): LeaderboardEntry {
    const entryRank: number = rank ?? 0;
    return {
      rank: entryRank,
      userId: stored.userId,
      username: stored.username,
      score: stored.score,
      metadata: stored.metadata ? { ...stored.metadata } : undefined,
      updatedAt: stored.updatedAt,
    };
  }

  private getMockFriends(userId: string): string[] {
    const friends: string[] = [];
    for (let i = 1; i <= 10; i++) {
      friends.push(`friend_${i}`);
    }
    return friends;
  }
}

export { LeaderboardError };
