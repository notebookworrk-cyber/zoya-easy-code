import { AuthService } from './auth.js';
import { DatabaseService } from './database.js';
import { StorageService } from './storage.js';
import { RealtimeService } from './realtime.js';
import { LeaderboardService } from './leaderboard.js';
import { MultiplayerService } from './multiplayer.js';
import { AnalyticsService } from './analytics.js';

export interface CloudConfig {
  projectId: string;
  apiKey: string;
  region: string;
  baseUrl: string;
  timeout: number;
  retryCount: number;
}

export const CLOUD_DEFAULTS: CloudConfig = {
  projectId: '',
  apiKey: '',
  region: 'us-east',
  baseUrl: 'https://api.zoya.dev',
  timeout: 10000,
  retryCount: 3,
};

export class ZoyaCloud {
  readonly auth: AuthService;
  readonly database: DatabaseService;
  readonly storage: StorageService;
  readonly realtime: RealtimeService;
  readonly leaderboard: LeaderboardService;
  readonly multiplayer: MultiplayerService;
  readonly analytics: AnalyticsService;
  private config: CloudConfig;
  private _connected = false;

  constructor(config: Partial<CloudConfig>) {
    this.config = { ...CLOUD_DEFAULTS, ...config };
    this.auth = new AuthService();
    this.database = new DatabaseService(this.config.baseUrl, this.config.apiKey);
    this.storage = new StorageService(this.config.baseUrl, this.config.apiKey);
    this.realtime = new RealtimeService(this.config.baseUrl, this.config.apiKey);
    this.leaderboard = new LeaderboardService(this.config.baseUrl, this.config.apiKey);
    this.multiplayer = new MultiplayerService(
      this.config.baseUrl,
      this.config.apiKey,
      this.realtime
    );
    this.analytics = new AnalyticsService(this.config.baseUrl, this.config.apiKey);
  }

  async connect(): Promise<void> {
    if (!this.config.apiKey) {
      throw new Error('API key is required to connect');
    }
    this._connected = true;
    await this.realtime.connect();
  }

  async disconnect(): Promise<void> {
    this._connected = false;
    await this.realtime.disconnect();
  }

  isConnected(): boolean {
    return this._connected;
  }

  getConfig(): CloudConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<CloudConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
