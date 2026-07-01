export interface AnimationFrame {
  index: number;
  duration: number;
  uv?: { x: number; y: number; w: number; h: number };
  events?: { time: number; name: string }[];
}

export interface AnimationClip {
  name: string;
  frames: AnimationFrame[];
  loop: boolean;
  speed: number;
  fps?: number;
}

export interface AnimationState {
  clipName: string;
  currentFrame: number;
  frameTimer: number;
  playing: boolean;
  loop: boolean;
  speed: number;
  onComplete?: () => void;
}

export class AnimationManager {
  private clips: Map<string, AnimationClip>;
  private states: Map<number, AnimationState>;

  constructor() {
    this.clips = new Map();
    this.states = new Map();
  }

  addClip(clip: AnimationClip): void {
    this.clips.set(clip.name, clip);
  }

  removeClip(name: string): void {
    this.clips.delete(name);
  }

  getClip(name: string): AnimationClip | undefined {
    return this.clips.get(name);
  }

  play(entityId: number, clipName: string, loop: boolean = true, onComplete?: () => void): void {
    const clip = this.clips.get(clipName);
    if (!clip || clip.frames.length === 0) return;

    this.states.set(entityId, {
      clipName,
      currentFrame: 0,
      frameTimer: 0,
      playing: true,
      loop,
      speed: 1,
      onComplete,
    });
  }

  stop(entityId: number): void {
    this.states.delete(entityId);
  }

  pause(entityId: number): void {
    const state = this.states.get(entityId);
    if (state) {
      state.playing = false;
    }
  }

  resume(entityId: number): void {
    const state = this.states.get(entityId);
    if (state) {
      state.playing = true;
    }
  }

  getState(entityId: number): AnimationState | undefined {
    return this.states.get(entityId);
  }

  isPlaying(entityId: number): boolean {
    const state = this.states.get(entityId);
    return state ? state.playing : false;
  }

  update(dt: number): void {
    const finished: number[] = [];

    for (const [entityId, state] of this.states) {
      if (!state.playing) continue;

      const clip = this.clips.get(state.clipName);
      if (!clip || clip.frames.length === 0) {
        finished.push(entityId);
        continue;
      }

      state.frameTimer += dt * state.speed * clip.speed;

      const currentFrame = clip.frames[state.currentFrame];
      if (currentFrame && state.frameTimer >= currentFrame.duration) {
        state.frameTimer -= currentFrame.duration;
        state.currentFrame++;

        if (state.currentFrame >= clip.frames.length) {
          if (state.loop) {
            state.currentFrame = 0;
          } else {
            if (state.onComplete) {
              state.onComplete();
            }
            finished.push(entityId);
          }
        }
      }
    }

    for (const id of finished) {
      this.states.delete(id);
    }
  }

  stopAll(): void {
    this.states.clear();
  }

  getCurrentFrame(entityId: number): AnimationFrame | null {
    const state = this.states.get(entityId);
    if (!state) return null;

    const clip = this.clips.get(state.clipName);
    if (!clip || clip.frames.length === 0) return null;

    return clip.frames[state.currentFrame] ?? null;
  }

  clipCount(): number {
    return this.clips.size;
  }
}
