import { randomBytes } from 'crypto';
import { EventEmitter } from 'events';

export type RealtimeEventType = 'connect' | 'disconnect' | 'message' | 'presence' | 'data_change' | 'error';

export interface RealtimeEvent {
  type: RealtimeEventType;
  channel: string;
  data: unknown;
  timestamp: Date;
  sender?: string;
}

export interface RealtimeChannelInfo {
  name: string;
  subscribers: number;
  ephemeral: boolean;
}

export interface PresenceInfo {
  userId: string;
  username: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  lastSeen: Date;
  metadata?: Record<string, unknown>;
}

interface ChannelState {
  name: string;
  ephemeral: boolean;
  subscribers: Set<(event: RealtimeEvent) => void>;
}

class RealtimeError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'RealtimeError';
  }
}

export class RealtimeService {
  private connected = false;
  private channels: Map<string, ChannelState> = new Map();
  private presenceStore: Map<string, Map<string, PresenceInfo>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 2000;
  private eventEmitter = new EventEmitter();
  private eventCallbacks: Set<(event: RealtimeEvent) => void> = new Set();
  private errorCallbacks: Set<(error: Error) => void> = new Set();

  constructor(private readonly baseUrl: string, private readonly apiKey: string) {}

  async connect(): Promise<void> {
    if (this.connected) return;
    this.connected = true;
    this.reconnectAttempts = 0;

    const event: RealtimeEvent = {
      type: 'connect',
      channel: '',
      data: null,
      timestamp: new Date(),
    };
    this.dispatchEvent(event);
  }

  async disconnect(): Promise<void> {
    if (!this.connected) return;
    this.connected = false;
    this.reconnectAttempts = 0;

    const event: RealtimeEvent = {
      type: 'disconnect',
      channel: '',
      data: null,
      timestamp: new Date(),
    };
    this.dispatchEvent(event);
  }

  isConnected(): boolean {
    return this.connected;
  }

  subscribe(channel: string, callback: (event: RealtimeEvent) => void): void {
    let state = this.channels.get(channel);
    if (!state) {
      state = { name: channel, ephemeral: false, subscribers: new Set() };
      this.channels.set(channel, state);
    }
    state.subscribers.add(callback);
  }

  unsubscribe(channel: string, callback?: (event: RealtimeEvent) => void): void {
    const state = this.channels.get(channel);
    if (!state) return;

    if (callback) {
      state.subscribers.delete(callback);
      if (state.subscribers.size === 0) {
        this.channels.delete(channel);
      }
    } else {
      this.channels.delete(channel);
    }
  }

  async publish(channel: string, data: unknown): Promise<void> {
    if (!this.connected) {
      throw new RealtimeError('Not connected to realtime service', 'NOT_CONNECTED');
    }

    const event: RealtimeEvent = {
      type: 'message',
      channel,
      data,
      timestamp: new Date(),
    };

    this.dispatchToChannel(channel, event);
    this.dispatchEvent(event);
  }

  updatePresence(status: PresenceInfo['status'], metadata?: Record<string, unknown>): void {
    if (!this.connected) return;

    const presence: PresenceInfo = {
      userId: `user_${randomBytes(4).toString('hex')}`,
      username: 'current_user',
      status,
      lastSeen: new Date(),
      metadata,
    };

    for (const [channelName] of this.channels) {
      if (!this.presenceStore.has(channelName)) {
        this.presenceStore.set(channelName, new Map());
      }
      const channelPresence = this.presenceStore.get(channelName)!;
      channelPresence.set(presence.userId, presence);

      const event: RealtimeEvent = {
        type: 'presence',
        channel: channelName,
        data: [...channelPresence.values()],
        timestamp: new Date(),
      };
      this.dispatchToChannel(channelName, event);
      this.dispatchEvent(event);
    }
  }

  getPresence(channel: string): PresenceInfo[] {
    const channelPresence = this.presenceStore.get(channel);
    if (!channelPresence) return [];
    return [...channelPresence.values()].map((p) => ({
      ...p,
      metadata: p.metadata ? { ...p.metadata } : undefined,
    }));
  }

  onPresenceChange(channel: string, callback: (presence: PresenceInfo[]) => void): void {
    const wrappedCallback = (event: RealtimeEvent) => {
      if (event.type === 'presence' && event.channel === channel) {
        callback(event.data as PresenceInfo[]);
      }
    };
    this.subscribe(channel, wrappedCallback);
  }

  listChannels(): RealtimeChannelInfo[] {
    return [...this.channels.values()].map((state) => ({
      name: state.name,
      subscribers: state.subscribers.size,
      ephemeral: state.ephemeral,
    }));
  }

  getChannelSubscribers(channel: string): number {
    const state = this.channels.get(channel);
    return state ? state.subscribers.size : 0;
  }

  setReconnectPolicy(maxAttempts: number, interval: number): void {
    this.maxReconnectAttempts = maxAttempts;
    this.reconnectInterval = interval;
  }

  onEvent(callback: (event: RealtimeEvent) => void): void {
    this.eventCallbacks.add(callback);
  }

  onError(callback: (error: Error) => void): void {
    this.errorCallbacks.add(callback);
  }

  private handleMessage(data: unknown): void {
    const parsed = data as { channel?: string; data?: unknown; type?: string };
    const channel = parsed?.channel ?? '';
    const event: RealtimeEvent = {
      type: 'message',
      channel,
      data: parsed?.data,
      timestamp: new Date(),
    };
    this.dispatchToChannel(channel, event);
    this.dispatchEvent(event);
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;

    setTimeout(async () => {
      try {
        await this.connect();
      } catch {
        this.attemptReconnect();
      }
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  private dispatchToChannel(channel: string, event: RealtimeEvent): void {
    const state = this.channels.get(channel);
    if (!state) return;
    for (const callback of state.subscribers) {
      try {
        callback(event);
      } catch {
        continue;
      }
    }
  }

  private dispatchEvent(event: RealtimeEvent): void {
    this.eventEmitter.emit(event.type, event);
    for (const callback of this.eventCallbacks) {
      try {
        callback(event);
      } catch {
        continue;
      }
    }
  }
}

export { RealtimeError };
