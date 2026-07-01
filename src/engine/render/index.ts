import type { Color, Vector2, Vector3, Transform } from '../core.js';
import type { Entity } from '../ecs/index.js';

export interface RendererConfig {
  width: number;
  height: number;
  title: string;
  fullscreen: boolean;
  vsync: boolean;
  antialias: boolean;
  backgroundColor: Color;
}

export abstract class Renderer {
  protected config: RendererConfig;
  protected cameras: Entity[];

  constructor(config: RendererConfig) {
    this.config = config;
    this.cameras = [];
  }

  abstract beginFrame(): void;
  abstract endFrame(): void;
  abstract clear(color?: Color): void;

  abstract drawSprite(
    texture: string,
    transform: Transform,
    color?: Color,
    flipX?: boolean,
    flipY?: boolean,
  ): void;

  abstract drawRect(
    x: number,
    y: number,
    w: number,
    h: number,
    color: Color,
    filled?: boolean,
  ): void;

  abstract drawCircle(
    x: number,
    y: number,
    radius: number,
    color: Color,
    filled?: boolean,
  ): void;

  abstract drawLine(
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color: Color,
    thickness?: number,
  ): void;

  abstract drawText(
    text: string,
    x: number,
    y: number,
    size?: number,
    color?: Color,
  ): void;

  abstract drawTriangle(
    x1: number, y1: number,
    x2: number, y2: number,
    x3: number, y3: number,
    color: Color,
    filled?: boolean,
  ): void;

  abstract drawPolygon(
    points: Vector2[],
    color: Color,
    filled?: boolean,
  ): void;

  abstract getWidth(): number;
  abstract getHeight(): number;

  setCamera(camera: Entity): void {
    if (!camera.has('camera')) {
      camera.add({ type: 'camera' } as any);
    }
    const idx = this.cameras.indexOf(camera);
    if (idx === -1) {
      this.cameras.push(camera);
    }
  }

  updateConfig(config: Partial<RendererConfig>): void {
    Object.assign(this.config, config);
  }

  shutdown(): void {
    this.cameras = [];
  }
}
