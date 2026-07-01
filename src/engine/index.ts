import { SceneManager } from './scene/index.js';
import { PhysicsWorld } from './physics/index.js';
import { AudioManager } from './audio/index.js';
import { AnimationManager } from './animation/index.js';
import { ParticleSystem } from './particles/index.js';
import { UIManager } from './ui/index.js';
import { AssetManager } from './assets/index.js';
import { SaveManager } from './save/index.js';
import type { Color } from './core.js';

export interface EngineConfig {
  width: number;
  height: number;
  title: string;
  fullscreen: boolean;
  vsync: boolean;
  targetFPS: number;
  fixedTimeStep: number;
  maxDeltaTime: number;
  backgroundColor: Color;
  physicsEnabled: boolean;
  audioEnabled: boolean;
  assetRoot: string;
  debugMode: boolean;
}

export const DefaultEngineConfig: EngineConfig = {
  width: 1280,
  height: 720,
  title: 'Zoya Game',
  fullscreen: false,
  vsync: true,
  targetFPS: 60,
  fixedTimeStep: 0.016,
  maxDeltaTime: 0.1,
  backgroundColor: [0.1, 0.1, 0.15, 1],
  physicsEnabled: true,
  audioEnabled: true,
  assetRoot: './assets',
  debugMode: false,
};

export class ZoyaEngine {
  readonly scene: SceneManager;
  readonly physics: PhysicsWorld;
  readonly audio: AudioManager;
  readonly animation: AnimationManager;
  readonly particles: ParticleSystem;
  readonly ui: UIManager;
  readonly assets: AssetManager;
  readonly save: SaveManager;
  readonly config: EngineConfig;
  private running: boolean;
  private lastTime: number;
  private fpsCounter: number;
  private fpsTimer: number;
  private currentFps: number;
  private deltaTime: number;

  constructor(config?: Partial<EngineConfig>) {
    this.config = { ...DefaultEngineConfig, ...config };
    this.scene = new SceneManager();
    this.physics = new PhysicsWorld();
    this.audio = new AudioManager();
    this.animation = new AnimationManager();
    this.particles = new ParticleSystem();
    this.ui = new UIManager();
    this.assets = new AssetManager();
    this.save = new SaveManager();
    this.running = false;
    this.lastTime = 0;
    this.fpsCounter = 0;
    this.fpsTimer = 0;
    this.currentFps = 0;
    this.deltaTime = 0;
  }

  init(_config?: Partial<EngineConfig>): void {
    // Initialization stub
  }

  start(): void {
    this.running = true;
    this.lastTime = performance.now();
  }

  stop(): void {
    this.running = false;
  }

  update(): void {
    if (!this.running) return;

    const now = performance.now();
    let dt = (now - this.lastTime) / 1000;
    this.lastTime = now;

    if (dt > this.config.maxDeltaTime) {
      dt = this.config.maxDeltaTime;
    }

    this.deltaTime = dt;

    this.fpsCounter++;
    this.fpsTimer += dt;
    if (this.fpsTimer >= 1) {
      this.currentFps = this.fpsCounter;
      this.fpsCounter = 0;
      this.fpsTimer -= 1;
    }

    this.scene.update(dt);

    if (this.config.physicsEnabled) {
      this.physics.step(dt);
    }

    this.animation.update(dt);
    this.particles.update(dt);
    this.audio.update(dt);
    this.ui.update(dt);
    this.save.update(dt);
  }

  getFPS(): number {
    return this.currentFps;
  }

  getDeltaTime(): number {
    return this.deltaTime;
  }

  isRunning(): boolean {
    return this.running;
  }

  shutdown(): void {
    this.running = false;
    this.audio.stopAll();
    this.animation.stopAll();
    this.particles.clear();
    this.ui.clear();
    this.scene.switchTo('');
    this.save.setAutoSave(false);
  }
}

export {
  SceneManager,
  Scene,
} from './scene/index.js';

export {
  World,
  Entity,
  defineQuery,
} from './ecs/index.js';

export {
  TransformComponent,
  SpriteComponent,
  PhysicsComponent,
  ColliderComponent,
  ScriptComponent,
  TagComponent,
  HealthComponent,
  CameraComponent,
  LightComponent,
  AnimationComponent,
} from './ecs/components.js';

export { PhysicsWorld } from './physics/index.js';
export { AudioManager } from './audio/index.js';
export { AnimationManager } from './animation/index.js';
export { ParticleSystem } from './particles/index.js';
export { UIManager, UILabel, UIButton, UIImage, UIPanel, UITextField, UIList, UISlider } from './ui/index.js';
export { TileMap } from './tilemap/index.js';
export { AssetManager } from './assets/index.js';
export { SaveManager } from './save/index.js';
export { Renderer } from './render/index.js';
export * from './core.js';
export * from './3d/index.js';
