import { randomBytes } from 'crypto';
import { RealtimeService } from './realtime.js';
import type { RealtimeEvent } from './realtime.js';

export interface MatchConfig {
  maxPlayers: number;
  minPlayers: number;
  timeout: number;
  ranked: boolean;
  region: string;
  customData?: Record<string, unknown>;
}

export interface Match {
  id: string;
  players: string[];
  status: 'waiting' | 'ready' | 'in_progress' | 'completed' | 'cancelled';
  config: MatchConfig;
  createdAt: Date;
  startedAt?: Date;
  endedAt?: Date;
  winnerId?: string;
  serverEndpoint?: string;
}

export interface LobbyPlayer {
  userId: string;
  username: string;
  ready: boolean;
  partyId?: string;
}

export interface Lobby {
  id: string;
  name: string;
  players: LobbyPlayer[];
  config: MatchConfig;
  status: 'open' | 'in_match' | 'closed';
  hostUserId: string;
}

interface Party {
  id: string;
  members: Set<string>;
  leaderId: string;
}

class MultiplayerError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'MultiplayerError';
  }
}

export class MultiplayerService {
  private matches: Map<string, Match> = new Map();
  private lobbies: Map<string, Lobby> = new Map();
  private parties: Map<string, Party> = new Map();
  private userParty: Map<string, string> = new Map();
  private stateSync: Map<string, Set<(state: unknown) => void>> = new Map();
  private eventHandlers: Map<string, Map<string, Set<(data: unknown, sender: string) => void>>> = new Map();
  private matchmakingQueue: Map<string, { userId: string; config: MatchConfig }[]> = new Map();

  constructor(
    private readonly baseUrl: string,
    private readonly apiKey: string,
    private readonly realtime: RealtimeService
  ) {}

  async findMatch(config: MatchConfig): Promise<Match> {
    this.validateMatchConfig(config);

    const regionQueues = this.matchmakingQueue.get(config.region) ?? [];
    const entry = {
      userId: `player_${randomBytes(4).toString('hex')}`,
      config,
    };

    const compatibleIndex = regionQueues.findIndex((q) => this.areConfigsCompatible(q.config, config));
    if (compatibleIndex >= 0) {
      const matched = regionQueues.splice(compatibleIndex, 1)[0];
      const matchId = randomBytes(8).toString('hex');
      const now = new Date();
      const match: Match = {
        id: matchId,
        players: [matched.userId, entry.userId],
        status: 'ready',
        config,
        createdAt: now,
        startedAt: now,
        serverEndpoint: `${this.baseUrl}/match/${matchId}`,
      };
      this.matches.set(matchId, match);
      return { ...match };
    }

    regionQueues.push(entry);
    this.matchmakingQueue.set(config.region, regionQueues);

    const matchId = randomBytes(8).toString('hex');
    const match: Match = {
      id: matchId,
      players: [],
      status: 'waiting',
      config,
      createdAt: new Date(),
      serverEndpoint: `${this.baseUrl}/match/${matchId}`,
    };
    this.matches.set(matchId, match);
    return { ...match };
  }

  async cancelMatchmaking(): Promise<void> {
    for (const [, queue] of this.matchmakingQueue) {
      queue.length = 0;
    }
  }

  async getMatch(matchId: string): Promise<Match> {
    const match = this.matches.get(matchId);
    if (!match) {
      throw new MultiplayerError(`Match not found: ${matchId}`, 'NOT_FOUND');
    }
    return { ...match, players: [...match.players] };
  }

  async leaveMatch(matchId: string): Promise<void> {
    const match = this.matches.get(matchId);
    if (!match) {
      throw new MultiplayerError(`Match not found: ${matchId}`, 'NOT_FOUND');
    }
    match.status = 'cancelled';
    match.endedAt = new Date();
  }

  async createLobby(name: string, config: MatchConfig): Promise<Lobby> {
    this.validateMatchConfig(config);
    const lobbyId = randomBytes(8).toString('hex');
    const hostId = `host_${randomBytes(4).toString('hex')}`;
    const lobby: Lobby = {
      id: lobbyId,
      name,
      players: [
        {
          userId: hostId,
          username: `player_${hostId.slice(0, 6)}`,
          ready: false,
        },
      ],
      config,
      status: 'open',
      hostUserId: hostId,
    };
    this.lobbies.set(lobbyId, lobby);
    return this.cloneLobby(lobby);
  }

  async joinLobby(lobbyId: string): Promise<Lobby> {
    const lobby = this.lobbies.get(lobbyId);
    if (!lobby) {
      throw new MultiplayerError(`Lobby not found: ${lobbyId}`, 'NOT_FOUND');
    }
    if (lobby.status !== 'open') {
      throw new MultiplayerError('Lobby is not open', 'LOBBY_CLOSED');
    }
    if (lobby.players.length >= lobby.config.maxPlayers) {
      throw new MultiplayerError('Lobby is full', 'LOBBY_FULL');
    }

    const userId = `player_${randomBytes(4).toString('hex')}`;
    lobby.players.push({
      userId,
      username: `player_${userId.slice(0, 6)}`,
      ready: false,
    });
    return this.cloneLobby(lobby);
  }

  async leaveLobby(lobbyId: string): Promise<void> {
    const lobby = this.lobbies.get(lobbyId);
    if (!lobby) {
      throw new MultiplayerError(`Lobby not found: ${lobbyId}`, 'NOT_FOUND');
    }

    if (lobby.players.length <= 1) {
      this.lobbies.delete(lobbyId);
      return;
    }

    lobby.players.pop();
  }

  async getLobby(lobbyId: string): Promise<Lobby> {
    const lobby = this.lobbies.get(lobbyId);
    if (!lobby) {
      throw new MultiplayerError(`Lobby not found: ${lobbyId}`, 'NOT_FOUND');
    }
    return this.cloneLobby(lobby);
  }

  async listLobbies(): Promise<Lobby[]> {
    return [...this.lobbies.values()]
      .filter((l) => l.status === 'open')
      .map((l) => this.cloneLobby(l));
  }

  async setReady(lobbyId: string, ready: boolean): Promise<void> {
    const lobby = this.lobbies.get(lobbyId);
    if (!lobby) {
      throw new MultiplayerError(`Lobby not found: ${lobbyId}`, 'NOT_FOUND');
    }
    if (lobby.players.length > 0) {
      const lastPlayer = lobby.players[lobby.players.length - 1];
      lastPlayer.ready = ready;
    }
  }

  async startMatch(lobbyId: string): Promise<Match> {
    const lobby = this.lobbies.get(lobbyId);
    if (!lobby) {
      throw new MultiplayerError(`Lobby not found: ${lobbyId}`, 'NOT_FOUND');
    }
    if (lobby.players.length < lobby.config.minPlayers) {
      throw new MultiplayerError(
        `Not enough players. Need ${lobby.config.minPlayers}, have ${lobby.players.length}`,
        'NOT_ENOUGH_PLAYERS'
      );
    }
    if (lobby.players.some((p) => !p.ready)) {
      throw new MultiplayerError('Not all players are ready', 'PLAYERS_NOT_READY');
    }

    const matchId = randomBytes(8).toString('hex');
    const now = new Date();
    const match: Match = {
      id: matchId,
      players: lobby.players.map((p) => p.userId),
      status: 'in_progress',
      config: lobby.config,
      createdAt: now,
      startedAt: now,
      serverEndpoint: `${this.baseUrl}/match/${matchId}`,
    };
    this.matches.set(matchId, match);
    lobby.status = 'in_match';
    return { ...match, players: [...match.players] };
  }

  async createParty(): Promise<string> {
    const partyId = randomBytes(8).toString('hex');
    const userId = `player_${randomBytes(4).toString('hex')}`;
    const party: Party = {
      id: partyId,
      members: new Set([userId]),
      leaderId: userId,
    };
    this.parties.set(partyId, party);
    this.userParty.set(userId, partyId);
    return partyId;
  }

  async joinParty(partyId: string): Promise<void> {
    const party = this.parties.get(partyId);
    if (!party) {
      throw new MultiplayerError(`Party not found: ${partyId}`, 'NOT_FOUND');
    }
    const userId = `player_${randomBytes(4).toString('hex')}`;
    party.members.add(userId);
    this.userParty.set(userId, partyId);
  }

  async leaveParty(): Promise<void> {
    for (const [userId, partyId] of this.userParty) {
      const party = this.parties.get(partyId);
      if (party) {
        party.members.delete(userId);
        if (party.members.size === 0) {
          this.parties.delete(partyId);
        } else if (party.leaderId === userId) {
          party.leaderId = [...party.members][0];
        }
      }
      this.userParty.delete(userId);
    }
  }

  async inviteToParty(userId: string): Promise<void> {
    const partyId = this.userParty.get(userId);
    if (!partyId) {
      throw new MultiplayerError('User is not in a party', 'NOT_IN_PARTY');
    }
  }

  async syncState(matchId: string, state: unknown): Promise<void> {
    const match = this.matches.get(matchId);
    if (!match) {
      throw new MultiplayerError(`Match not found: ${matchId}`, 'NOT_FOUND');
    }
    const callbacks = this.stateSync.get(matchId);
    if (callbacks) {
      for (const cb of callbacks) {
        try {
          cb(state);
        } catch {
          continue;
        }
      }
    }
  }

  async getState(matchId: string): Promise<unknown> {
    const match = this.matches.get(matchId);
    if (!match) {
      throw new MultiplayerError(`Match not found: ${matchId}`, 'NOT_FOUND');
    }
    return match.config.customData ?? null;
  }

  onStateChange(matchId: string, callback: (state: unknown) => void): void {
    if (!this.stateSync.has(matchId)) {
      this.stateSync.set(matchId, new Set());
    }
    this.stateSync.get(matchId)!.add(callback);
  }

  async sendEvent(matchId: string, event: string, data?: unknown): Promise<void> {
    const match = this.matches.get(matchId);
    if (!match) {
      throw new MultiplayerError(`Match not found: ${matchId}`, 'NOT_FOUND');
    }
    const matchEvents = this.eventHandlers.get(matchId);
    if (matchEvents) {
      const handlers = matchEvents.get(event);
      if (handlers) {
        for (const cb of handlers) {
          try {
            cb(data, 'server');
          } catch {
            continue;
          }
        }
      }
    }
  }

  onEvent(
    matchId: string,
    eventType: string,
    callback: (data: unknown, sender: string) => void
  ): void {
    if (!this.eventHandlers.has(matchId)) {
      this.eventHandlers.set(matchId, new Map());
    }
    const matchEvents = this.eventHandlers.get(matchId)!;
    if (!matchEvents.has(eventType)) {
      matchEvents.set(eventType, new Set());
    }
    matchEvents.get(eventType)!.add(callback);
  }

  private validateMatchConfig(config: MatchConfig): void {
    if (config.maxPlayers < 2) {
      throw new MultiplayerError('maxPlayers must be at least 2', 'INVALID_CONFIG');
    }
    if (config.minPlayers < 1) {
      throw new MultiplayerError('minPlayers must be at least 1', 'INVALID_CONFIG');
    }
    if (config.minPlayers > config.maxPlayers) {
      throw new MultiplayerError('minPlayers cannot exceed maxPlayers', 'INVALID_CONFIG');
    }
    if (config.timeout <= 0) {
      throw new MultiplayerError('timeout must be positive', 'INVALID_CONFIG');
    }
  }

  private areConfigsCompatible(a: MatchConfig, b: MatchConfig): boolean {
    return (
      a.maxPlayers === b.maxPlayers &&
      a.minPlayers === b.minPlayers &&
      a.ranked === b.ranked
    );
  }

  private cloneLobby(lobby: Lobby): Lobby {
    return {
      ...lobby,
      players: lobby.players.map((p) => ({ ...p })),
      config: { ...lobby.config, customData: lobby.config.customData ? { ...lobby.config.customData } : undefined },
    };
  }
}

export { MultiplayerError };
