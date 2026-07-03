import type { Vector2, Color, Rect } from '../core.js';

export interface Particle {
  position: Vector2;
  velocity: Vector2;
  acceleration: Vector2;
  color: Color;
  initialColor: Color;
  finalColor: Color;
  size: number;
  initialSize: number;
  finalSize: number;
  lifetime: number;
  elapsed: number;
  alpha: number;
  rotation: number;
  angularVelocity: number;
  alive: boolean;
}

export interface ParticleEmitterConfig {
  position: Vector2;
  emissionRate: number;
  maxParticles: number;
  lifetime: [number, number];
  speed: [number, number];
  size: [number, number];
  color: Color;
  endColor: Color;
  direction: number;
  spread: number;
  gravity: Vector2;
  damping: number;
  rotationSpeed: [number, number];
  emissionShape: 'point' | 'circle' | 'rect';
  emissionRect?: Rect;
  emissionRadius?: number;
  oneShot: boolean;
  duration: number;
}

export class ParticleSystem {
  private emitters: Map<number, ParticleEmitterConfig>;
  private particles: Particle[];
  private nextEmitterId: number;

  constructor() {
    this.emitters = new Map();
    this.particles = [];
    this.nextEmitterId = 1;
  }

  createEmitter(config: ParticleEmitterConfig): number {
    const id = this.nextEmitterId++;
    this.emitters.set(id, { ...config });
    return id;
  }

  removeEmitter(id: number): void {
    this.emitters.delete(id);
    this.particles = this.particles.filter(p => p.alive);
  }

  getEmitter(id: number): ParticleEmitterConfig | undefined {
    return this.emitters.get(id);
  }

  burst(emitterId: number, count: number): void {
    const config = this.emitters.get(emitterId);
    if (!config) return;

    for (let i = 0; i < count; i++) {
      if (this.particles.length >= config.maxParticles) break;
      this.particles.push(this.createParticle(config));
    }
  }

  update(dt: number): void {
    for (const [id, config] of this.emitters) {
      if (config.oneShot) continue;
      const emissionCount = Math.floor(config.emissionRate * dt);
      this.burst(id, emissionCount);
    }

    for (const p of this.particles) {
      if (!p.alive) continue;

      p.elapsed += dt;
      const t = Math.min(p.elapsed / p.lifetime, 1);

      p.velocity.x += p.acceleration.x * dt;
      p.velocity.y += p.acceleration.y * dt;

      const config = this.getEmitterConfigForParticle(p);
      if (config) {
        p.velocity.x += config.gravity.x * dt;
        p.velocity.y += config.gravity.y * dt;
      }

      p.velocity.x *= (1 - p.alpha * dt);
      p.velocity.y *= (1 - p.alpha * dt);

      p.position.x += p.velocity.x * dt;
      p.position.y += p.velocity.y * dt;

      p.rotation += p.angularVelocity * dt;

      p.color[0] = lerp(p.initialColor[0], p.finalColor[0], t);
      p.color[1] = lerp(p.initialColor[1], p.finalColor[1], t);
      p.color[2] = lerp(p.initialColor[2], p.finalColor[2], t);
      p.color[3] = lerp(p.initialColor[3], p.finalColor[3], t) * (1 - t);

      p.size = lerp(p.initialSize, p.finalSize, t);

      if (t >= 1) {
        p.alive = false;
      }
    }

    this.particles = this.particles.filter(p => p.alive);
  }

  getActiveParticles(): Particle[] {
    return this.particles.filter(p => p.alive);
  }

  getParticleCount(): number {
    return this.particles.filter(p => p.alive).length;
  }

  clear(): void {
    this.particles = [];
    this.emitters.clear();
  }

  updateEmitter(id: number, config: Partial<ParticleEmitterConfig>): void {
    const existing = this.emitters.get(id);
    if (existing) {
      Object.assign(existing, config);
    }
  }

  private getEmitterConfigForParticle(_particle: Particle): ParticleEmitterConfig | undefined {
    for (const config of this.emitters.values()) {
      return config;
    }
    return undefined;
  }

  private createParticle(config: ParticleEmitterConfig): Particle {
    const lifetime = randomRange(config.lifetime[0], config.lifetime[1]);
    const speed = randomRange(config.speed[0], config.speed[1]);
    const size = randomRange(config.size[0], config.size[1]);
    const rotSpeed = randomRange(config.rotationSpeed[0], config.rotationSpeed[1]);

    let pos: Vector2 = { ...config.position };
    if (config.emissionShape === 'circle' && config.emissionRadius) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.random() * config.emissionRadius;
      pos = { x: pos.x + Math.cos(angle) * r, y: pos.y + Math.sin(angle) * r };
    } else if (config.emissionShape === 'rect' && config.emissionRect) {
      pos = {
        x: pos.x + (Math.random() - 0.5) * config.emissionRect.width,
        y: pos.y + (Math.random() - 0.5) * config.emissionRect.height,
      };
    }

    const spreadAngle = config.direction + (Math.random() - 0.5) * config.spread;
    const vx = Math.cos(spreadAngle) * speed;
    const vy = Math.sin(spreadAngle) * speed;

    return {
      position: pos,
      velocity: { x: vx, y: vy },
      acceleration: { x: 0, y: 0 },
      color: [...config.color] as Color,
      initialColor: [...config.color] as Color,
      finalColor: [...config.endColor] as Color,
      size,
      initialSize: size,
      finalSize: size * 0.1,
      lifetime,
      elapsed: 0,
      alpha: 1,
      rotation: 0,
      angularVelocity: rotSpeed,
      alive: true,
    };
  }
}

function randomRange(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}
