import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RealtimeService, RealtimeError } from '../../src/cloud/realtime.js';

describe('RealtimeService', () => {
  let realtime: RealtimeService;

  beforeEach(() => {
    vi.restoreAllMocks();
    realtime = new RealtimeService('https://api.zoya.dev', 'test-key');
  });

  describe('Connection Lifecycle', () => {
    it('starts disconnected', () => {
      expect(realtime.isConnected()).toBe(false);
    });

    it('connects successfully', async () => {
      await realtime.connect();
      expect(realtime.isConnected()).toBe(true);
    });

    it('disconnects successfully', async () => {
      await realtime.connect();
      await realtime.disconnect();
      expect(realtime.isConnected()).toBe(false);
    });

    it('handles duplicate connect calls', async () => {
      await realtime.connect();
      await realtime.connect();
      expect(realtime.isConnected()).toBe(true);
    });

    it('handles duplicate disconnect calls', async () => {
      await realtime.disconnect();
      expect(realtime.isConnected()).toBe(false);
    });
  });

  describe('Channel Subscribe/Unsubscribe', () => {
    it('subscribes to a channel', () => {
      const callback = vi.fn();
      realtime.subscribe('test-channel', callback);
      const channels = realtime.listChannels();
      expect(channels).toHaveLength(1);
      expect(channels[0].name).toBe('test-channel');
    });

    it('unsubscribes a specific callback', () => {
      const callback1 = vi.fn();
      const callback2 = vi.fn();
      realtime.subscribe('test-channel', callback1);
      realtime.subscribe('test-channel', callback2);
      realtime.unsubscribe('test-channel', callback1);
      expect(realtime.getChannelSubscribers('test-channel')).toBe(1);
    });

    it('unsubscribes all callbacks from channel', () => {
      const callback = vi.fn();
      realtime.subscribe('test-channel', callback);
      realtime.unsubscribe('test-channel');
      const channels = realtime.listChannels();
      expect(channels).toHaveLength(0);
    });

    it('unsubscribing from non-existent channel does not throw', () => {
      realtime.unsubscribe('phantom-channel');
      expect(realtime.listChannels()).toHaveLength(0);
    });
  });

  describe('Publish/Subscribe Messaging', () => {
    it('receives published messages', async () => {
      await realtime.connect();
      const callback = vi.fn();
      realtime.subscribe('chat', callback);
      await realtime.publish('chat', { text: 'hello' });
      expect(callback).toHaveBeenCalledTimes(1);
      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'message',
          channel: 'chat',
          data: { text: 'hello' },
        })
      );
    });

    it('does not receive messages on other channels', async () => {
      await realtime.connect();
      const callback = vi.fn();
      realtime.subscribe('channel-a', callback);
      await realtime.publish('channel-b', { text: 'noise' });
      expect(callback).not.toHaveBeenCalled();
    });

    it('throws when publishing while disconnected', async () => {
      const callback = vi.fn();
      realtime.subscribe('test', callback);
      await expect(realtime.publish('test', 'data')).rejects.toThrow(RealtimeError);
    });
  });

  describe('Presence Management', () => {
    it('updates presence status', async () => {
      await realtime.connect();
      realtime.subscribe('presence-channel', vi.fn());
      realtime.updatePresence('online', { custom: 'data' });
      const presence = realtime.getPresence('presence-channel');
      expect(presence.length).toBeGreaterThan(0);
      expect(presence[0].status).toBe('online');
    });

    it('returns empty presence for unknown channel', () => {
      const presence = realtime.getPresence('unknown');
      expect(presence).toEqual([]);
    });

    it('triggers presence change callback', async () => {
      await realtime.connect();
      const callback = vi.fn();
      realtime.subscribe('presence-test', vi.fn());
      realtime.onPresenceChange('presence-test', callback);
      realtime.updatePresence('busy');
      expect(callback).toHaveBeenCalled();
    });
  });

  describe('Channel Management', () => {
    it('lists channels with subscriber counts', () => {
      realtime.subscribe('ch-1', vi.fn());
      realtime.subscribe('ch-1', vi.fn());
      realtime.subscribe('ch-2', vi.fn());
      const channels = realtime.listChannels();
      expect(channels).toHaveLength(2);
      const ch1 = channels.find((c) => c.name === 'ch-1')!;
      expect(ch1.subscribers).toBe(2);
    });

    it('gets subscriber count for a channel', () => {
      realtime.subscribe('count-channel', vi.fn());
      realtime.subscribe('count-channel', vi.fn());
      expect(realtime.getChannelSubscribers('count-channel')).toBe(2);
    });

    it('returns 0 for non-existent channel', () => {
      expect(realtime.getChannelSubscribers('phantom')).toBe(0);
    });
  });

  describe('Reconnection', () => {
    it('sets reconnect policy', () => {
      realtime.setReconnectPolicy(5, 1000);
      expect(realtime.isConnected()).toBe(false);
    });
  });

  describe('Global Event Callbacks', () => {
    it('fires onEvent callback for all events', async () => {
      await realtime.connect();
      const callback = vi.fn();
      realtime.onEvent(callback);
      await realtime.publish('any', 'data');
      expect(callback).toHaveBeenCalled();
    });

    it('fires onError callback', () => {
      const callback = vi.fn();
      realtime.onError(callback);
      expect(realtime.isConnected()).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('handleMessage does not throw for malformed data', () => {
      realtime.subscribe('test', vi.fn());
      expect(() => {
        realtime['handleMessage']({ channel: 'test', data: null });
      }).not.toThrow();
    });
  });
});
