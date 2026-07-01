import type { Vector3 } from '../core.js';

export enum AudioState { Playing = 0, Paused, Stopped }

export interface AudioClip {
  name: string;
  data: Float32Array;
  sampleRate: number;
  channels: number;
  duration: number;
}

export interface AudioSource {
  clip: string;
  volume: number;
  pitch: number;
  loop: boolean;
  spatial: boolean;
  position: Vector3;
  state: AudioState;
}

export class AudioManager {
  private clips: Map<string, AudioClip>;
  private sources: Map<number, AudioSource>;
  private masterVolume: number;
  private nextSourceId: number;

  constructor() {
    this.clips = new Map();
    this.sources = new Map();
    this.masterVolume = 1;
    this.nextSourceId = 1;
  }

  loadClip(name: string, data: Float32Array, sampleRate: number): void {
    const duration = data.length / sampleRate;
    this.clips.set(name, {
      name,
      data,
      sampleRate,
      channels: 1,
      duration,
    });
  }

  unloadClip(name: string): void {
    this.clips.delete(name);
  }

  play(clip: string, volume: number = 1, loop: boolean = false): number {
    if (!this.clips.has(clip)) return -1;
    const id = this.nextSourceId++;
    this.sources.set(id, {
      clip,
      volume,
      pitch: 1,
      loop,
      spatial: false,
      position: { x: 0, y: 0, z: 0 },
      state: AudioState.Playing,
    });
    return id;
  }

  stop(sourceId: number): void {
    const source = this.sources.get(sourceId);
    if (source) {
      source.state = AudioState.Stopped;
      this.sources.delete(sourceId);
    }
  }

  pause(sourceId: number): void {
    const source = this.sources.get(sourceId);
    if (source) {
      source.state = AudioState.Paused;
    }
  }

  resume(sourceId: number): void {
    const source = this.sources.get(sourceId);
    if (source) {
      source.state = AudioState.Playing;
    }
  }

  setVolume(sourceId: number, volume: number): void {
    const source = this.sources.get(sourceId);
    if (source) {
      source.volume = Math.max(0, Math.min(1, volume));
    }
  }

  setPitch(sourceId: number, pitch: number): void {
    const source = this.sources.get(sourceId);
    if (source) {
      source.pitch = Math.max(0.1, pitch);
    }
  }

  setMasterVolume(volume: number): void {
    this.masterVolume = Math.max(0, Math.min(1, volume));
  }

  getSource(sourceId: number): AudioSource | undefined {
    return this.sources.get(sourceId);
  }

  isPlaying(sourceId: number): boolean {
    const source = this.sources.get(sourceId);
    return source ? source.state === AudioState.Playing : false;
  }

  stopAll(): void {
    for (const [id] of this.sources) {
      this.stop(id);
    }
  }

  update(_dt: number): void {
    // Stub: real audio would process buffers here
  }

  getActiveSourceCount(): number {
    return this.sources.size;
  }
}
