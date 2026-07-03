import type { Color, Vector3, Rect } from '../core.js';
import type { Component } from './index.js';

export class TransformComponent implements Component {
  readonly type = 'transform';
  constructor(
    public position: Vector3 = { x: 0, y: 0, z: 0 },
    public rotation: Vector3 = { x: 0, y: 0, z: 0 },
    public scale: Vector3 = { x: 1, y: 1, z: 1 },
  ) {}
}

export class SpriteComponent implements Component {
  readonly type = 'sprite';
  constructor(
    public texture: string = '',
    public color: Color = [1, 1, 1, 1],
    public flipX: boolean = false,
    public flipY: boolean = false,
    public width: number = 0,
    public height: number = 0,
    public pivot: Vector3 = { x: 0.5, y: 0.5, z: 0 },
  ) {}
}

export class PhysicsComponent implements Component {
  readonly type = 'physics';
  constructor(
    public velocity: Vector3 = { x: 0, y: 0, z: 0 },
    public mass: number = 1,
    public friction: number = 0,
    public restitution: number = 0,
    public isStatic: boolean = false,
  ) {}
}

export class ColliderComponent implements Component {
  readonly type = 'collider';
  constructor(
    public shape: 'rect' | 'circle' | 'polygon' = 'rect',
    public width: number = 1,
    public height: number = 1,
    public radius: number = 0.5,
    public offset: Vector3 = { x: 0, y: 0, z: 0 },
  ) {}
}

export interface ScriptCallbacks {
  onCreate?: () => void;
  onUpdate?: (dt: number) => void;
  onDestroy?: () => void;
}

export class ScriptComponent implements Component {
  readonly type = 'script';
  constructor(
    public onCreate?: () => void,
    public onUpdate?: (dt: number) => void,
    public onDestroy?: () => void,
  ) {}
}

export class TagComponent implements Component {
  readonly type = 'tag';
  constructor(public tags: string[] = []) {}
}

export class HealthComponent implements Component {
  readonly type = 'health';
  constructor(
    public current: number = 100,
    public max: number = 100,
    public regen: number = 0,
  ) {}
}

export class CameraComponent implements Component {
  readonly type = 'camera';
  constructor(
    public viewport: Rect = { x: 0, y: 0, width: 1280, height: 720 },
    public zoom: number = 1,
    public followTarget: number | null = null,
  ) {}
}

export class LightComponent implements Component {
  readonly type = 'light';
  constructor(
    public lightType: 'ambient' | 'directional' | 'point' | 'spot' = 'point',
    public color: Color = [1, 1, 1, 1],
    public intensity: number = 1,
    public radius: number = 10,
  ) {}
}

export class AnimationComponent implements Component {
  readonly type = 'animation';
  constructor(
    public currentAnim: string = '',
    public frame: number = 0,
    public speed: number = 1,
    public playing: boolean = false,
    public loop: boolean = true,
  ) {}
}
