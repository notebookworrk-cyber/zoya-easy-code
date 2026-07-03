import { World, Entity } from '../ecs/index.js';
import type { CameraComponent } from '../ecs/components.js';
import type { Color } from '../core.js';

export class Scene {
  readonly name: string;
  readonly world: World;
  private cameras: Entity[];
  private backgroundColor: Color;

  constructor(name: string) {
    this.name = name;
    this.world = new World();
    this.cameras = [];
    this.backgroundColor = [0.1, 0.1, 0.15, 1];
  }

  createEntity(_name?: string): Entity {
    return this.world.createEntity();
  }

  destroyEntity(entity: Entity): void {
    entity.destroy();
    const idx = this.cameras.indexOf(entity);
    if (idx !== -1) {
      this.cameras.splice(idx, 1);
    }
  }

  getMainCamera(): Entity | null {
    for (const camera of this.cameras) {
      if (camera.has('camera')) {
        return camera;
      }
    }
    const camEntities = this.world.query({ all: ['camera'] });
    return camEntities.length > 0 ? camEntities[0] : null;
  }

  setMainCamera(camera: Entity): void {
    if (!camera.has('camera')) {
      camera.add({ type: 'camera' } as CameraComponent);
    }
    if (this.cameras.indexOf(camera) === -1) {
      this.cameras.push(camera);
    }
  }

  getEntitiesWith(component: string): Entity[] {
    return this.world.query({ all: [component] });
  }

  setBackgroundColor(color: Color): void {
    this.backgroundColor = color;
  }

  getBackgroundColor(): Color {
    return this.backgroundColor;
  }

  onEnter(): void {
    // Hook for scene initialization
  }

  onExit(): void {
    // Hook for scene cleanup
  }

  update(dt: number): void {
    this.world.update(dt);
  }
}

export class SceneManager {
  private scenes: Map<string, Scene>;
  private currentScene: Scene | null;

  constructor() {
    this.scenes = new Map();
    this.currentScene = null;
  }

  addScene(scene: Scene): void {
    this.scenes.set(scene.name, scene);
  }

  removeScene(name: string): void {
    if (this.currentScene && this.currentScene.name === name) {
      this.currentScene.onExit();
      this.currentScene = null;
    }
    this.scenes.delete(name);
  }

  switchTo(name: string): boolean {
    const scene = this.scenes.get(name);
    if (!scene) return false;
    if (this.currentScene) {
      this.currentScene.onExit();
    }
    this.currentScene = scene;
    this.currentScene.onEnter();
    return true;
  }

  getCurrentScene(): Scene | null {
    return this.currentScene;
  }

  getScene(name: string): Scene | undefined {
    return this.scenes.get(name);
  }

  update(dt: number): void {
    if (this.currentScene) {
      this.currentScene.update(dt);
    }
  }

  hasScene(name: string): boolean {
    return this.scenes.has(name);
  }

  sceneCount(): number {
    return this.scenes.size;
  }
}
