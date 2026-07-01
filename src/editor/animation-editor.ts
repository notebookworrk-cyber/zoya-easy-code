import { EditorPanel, PanelType } from './index';

export interface AnimationEditState {
  clipName: string;
  duration: number;
  fps: number;
  loop: boolean;
  currentTime: number;
  selectedProperty: string | null;
  keyframes: Map<string, KeyframeData[]>;
  recording: boolean;
  snapping: boolean;
  snapInterval: number;
}

export interface KeyframeData {
  time: number;
  value: unknown;
  easing: 'linear' | 'ease_in' | 'ease_out' | 'ease_in_out' | 'bounce' | 'elastic';
  inTangent?: number;
  outTangent?: number;
}

export class AnimationEditorPanel implements EditorPanel {
  id = 'animation-editor';
  type: PanelType = 'animation';
  title = 'Animation Editor';
  private state: AnimationEditState;
  private selectedClip: string | null;
  private availableClips: string[];
  private timelineZoom: number;
  private scrollOffset: number;
  private playbackState: 'stopped' | 'playing' | 'paused';

  constructor() {
    this.state = {
      clipName: '',
      duration: 1,
      fps: 30,
      loop: false,
      currentTime: 0,
      selectedProperty: null,
      keyframes: new Map(),
      recording: false,
      snapping: true,
      snapInterval: 0.1,
    };
    this.selectedClip = null;
    this.availableClips = [];
    this.timelineZoom = 1;
    this.scrollOffset = 0;
    this.playbackState = 'stopped';
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void {
    if (this.playbackState !== 'playing') return;
    const newTime = this.state.currentTime + _dt;
    if (newTime >= this.state.duration) {
      if (this.state.loop) {
        this.state = { ...this.state, currentTime: newTime % this.state.duration };
      } else {
        this.state = { ...this.state, currentTime: this.state.duration };
        this.playbackState = 'stopped';
      }
    } else {
      this.state = { ...this.state, currentTime: newTime };
    }
  }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  loadClip(name: string): void {
    this.selectedClip = name;
    this.state = { ...this.state, clipName: name, currentTime: 0 };
    this.playbackState = 'stopped';
  }

  saveClip(): void {

  }

  play(): void {
    if (this.selectedClip) {
      this.playbackState = 'playing';
    }
  }

  pause(): void {
    if (this.playbackState === 'playing') {
      this.playbackState = 'paused';
    }
  }

  stop(): void {
    this.playbackState = 'stopped';
    this.state = { ...this.state, currentTime: 0 };
  }

  goToFrame(frame: number): void {
    const time = frame / this.state.fps;
    this.state = { ...this.state, currentTime: Math.max(0, Math.min(time, this.state.duration)) };
  }

  goToTime(time: number): void {
    this.state = { ...this.state, currentTime: Math.max(0, Math.min(time, this.state.duration)) };
  }

  addKeyframe(property: string, time: number, value: unknown): void {
    const existing = this.state.keyframes.get(property) || [];
    const filtered = existing.filter((kf) => Math.abs(kf.time - time) > 0.001);
    const sorted = [...filtered, { time, value, easing: 'linear' as const }].sort((a, b) => a.time - b.time);
    const updated = new Map(this.state.keyframes);
    updated.set(property, sorted);
    this.state = { ...this.state, keyframes: updated };
  }

  removeKeyframe(property: string, time: number): void {
    const existing = this.state.keyframes.get(property);
    if (!existing) return;
    const filtered = existing.filter((kf) => Math.abs(kf.time - time) > 0.001);
    const updated = new Map(this.state.keyframes);
    if (filtered.length === 0) {
      updated.delete(property);
    } else {
      updated.set(property, filtered);
    }
    this.state = { ...this.state, keyframes: updated };
  }

  moveKeyframe(property: string, oldTime: number, newTime: number): void {
    const existing = this.state.keyframes.get(property);
    if (!existing) return;
    const kf = existing.find((k) => Math.abs(k.time - oldTime) < 0.001);
    if (!kf) return;
    const filtered = existing.filter((k) => Math.abs(k.time - oldTime) > 0.001);
    const moved = { ...kf, time: newTime };
    const sorted = [...filtered, moved].sort((a, b) => a.time - b.time);
    const updated = new Map(this.state.keyframes);
    updated.set(property, sorted);
    this.state = { ...this.state, keyframes: updated };
  }

  updateKeyframeEasing(property: string, time: number, easing: KeyframeData['easing']): void {
    const existing = this.state.keyframes.get(property);
    if (!existing) return;
    const updatedKfs = existing.map((kf) => {
      if (Math.abs(kf.time - time) < 0.001) {
        return { ...kf, easing };
      }
      return kf;
    });
    const updated = new Map(this.state.keyframes);
    updated.set(property, updatedKfs);
    this.state = { ...this.state, keyframes: updated };
  }

  startRecording(): void {
    this.state = { ...this.state, recording: true };
  }

  stopRecording(): void {
    this.state = { ...this.state, recording: false };
  }

  isRecording(): boolean {
    return this.state.recording;
  }

  setSnapping(enabled: boolean, interval?: number): void {
    this.state = {
      ...this.state,
      snapping: enabled,
      snapInterval: interval ?? this.state.snapInterval,
    };
  }

  setTimelineZoom(zoom: number): void {
    this.timelineZoom = Math.max(0.1, Math.min(zoom, 10));
  }

  getState(): AnimationEditState {
    return {
      ...this.state,
      keyframes: new Map(this.state.keyframes),
    };
  }

  getKeyframes(property: string): KeyframeData[] {
    const kfs = this.state.keyframes.get(property);
    return kfs ? [...kfs] : [];
  }

  getProperties(): string[] {
    return Array.from(this.state.keyframes.keys());
  }

  setLoop(loop: boolean): void {
    this.state = { ...this.state, loop };
  }

  setDuration(duration: number): void {
    this.state = { ...this.state, duration: Math.max(0.016, duration), currentTime: Math.min(this.state.currentTime, duration) };
  }

  setFPS(fps: number): void {
    this.state = { ...this.state, fps: Math.max(1, fps) };
  }

  getAvailableClips(): string[] {
    return [...this.availableClips];
  }

  getSelectedClip(): string | null {
    return this.selectedClip;
  }

  getPlaybackState(): 'stopped' | 'playing' | 'paused' {
    return this.playbackState;
  }

  getTimelineZoom(): number {
    return this.timelineZoom;
  }

  getScrollOffset(): number {
    return this.scrollOffset;
  }
}
