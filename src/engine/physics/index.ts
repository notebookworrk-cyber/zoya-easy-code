import type { Vector2, Rect } from '../core.js';

export interface PhysicsBody {
  entityId: number;
  position: Vector2;
  velocity: Vector2;
  acceleration: Vector2;
  mass: number;
  invMass: number;
  restitution: number;
  friction: number;
  isStatic: boolean;
  shape: 'circle' | 'rect' | 'polygon';
  radius?: number;
  width?: number;
  height?: number;
  vertices?: Vector2[];
}

export interface Collision {
  a: PhysicsBody;
  b: PhysicsBody;
  normal: Vector2;
  depth: number;
  contactPoint: Vector2;
}

export class PhysicsWorld {
  private bodies: PhysicsBody[];
  private gravity: Vector2;
  private collisionCallbacks: Map<string, (a: PhysicsBody, b: PhysicsBody) => void>;

  constructor(gravity?: Vector2) {
    this.gravity = gravity ?? { x: 0, y: 9.81 };
    this.bodies = [];
    this.collisionCallbacks = new Map();
  }

  addBody(body: PhysicsBody): void {
    if (body.mass > 0) {
      body.invMass = 1 / body.mass;
    } else {
      body.invMass = 0;
    }
    this.bodies.push(body);
  }

  removeBody(entityId: number): void {
    const idx = this.bodies.findIndex(b => b.entityId === entityId);
    if (idx !== -1) {
      this.bodies.splice(idx, 1);
    }
  }

  getBody(entityId: number): PhysicsBody | undefined {
    return this.bodies.find(b => b.entityId === entityId);
  }

  step(dt: number): void {
    for (const body of this.bodies) {
      if (body.isStatic) continue;

      body.acceleration.x += this.gravity.x * body.mass;
      body.acceleration.y += this.gravity.y * body.mass;

      body.velocity.x += body.acceleration.x * dt;
      body.velocity.y += body.acceleration.y * dt;

      body.position.x += body.velocity.x * dt;
      body.position.y += body.velocity.y * dt;

      body.acceleration.x = 0;
      body.acceleration.y = 0;
    }

    this.detectCollisions();
  }

  setGravity(gravity: Vector2): void {
    this.gravity = gravity;
  }

  raycast(origin: Vector2, direction: Vector2, maxDistance: number): Collision | null {
    let closest: Collision | null = null;
    let closestDist = maxDistance;

    for (const body of this.bodies) {
      const hit = this.raycastBody(origin, direction, body);
      if (hit && hit.depth < closestDist) {
        closestDist = hit.depth;
        closest = hit;
      }
    }

    return closest;
  }

  private raycastBody(origin: Vector2, direction: Vector2, body: PhysicsBody): Collision | null {
    const dx = body.position.x - origin.x;
    const dy = body.position.y - origin.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    const halfExtent = body.shape === 'circle'
      ? (body.radius ?? 0.5)
      : Math.max(body.width ?? 1, body.height ?? 1) / 2;

    if (dist > halfExtent + 100) return null;

    const nx = direction.x / dist || 0;
    const ny = direction.y / dist || 0;

    return {
      a: { entityId: -1, position: origin, velocity: { x: 0, y: 0 }, acceleration: { x: 0, y: 0 }, mass: 0, invMass: 0, restitution: 0, friction: 0, isStatic: true, shape: 'circle' },
      b: body,
      normal: { x: nx, y: ny },
      depth: dist,
      contactPoint: { x: body.position.x, y: body.position.y },
    };
  }

  onCollisionEnter(callback: (a: PhysicsBody, b: PhysicsBody) => void): void {
    this.collisionCallbacks.set('enter', callback);
  }

  onCollisionExit(callback: (a: PhysicsBody, b: PhysicsBody) => void): void {
    this.collisionCallbacks.set('exit', callback);
  }

  queryRect(rect: Rect): PhysicsBody[] {
    return this.bodies.filter(body => {
      const bx = body.position.x;
      const by = body.position.y;
      return bx >= rect.x && bx <= rect.x + rect.width &&
        by >= rect.y && by <= rect.y + rect.height;
    });
  }

  queryCircle(center: Vector2, radius: number): PhysicsBody[] {
    return this.bodies.filter(body => {
      const dx = body.position.x - center.x;
      const dy = body.position.y - center.y;
      return dx * dx + dy * dy <= radius * radius;
    });
  }

  bodyCount(): number {
    return this.bodies.length;
  }

  private detectCollisions(): void {
    for (let i = 0; i < this.bodies.length; i++) {
      for (let j = i + 1; j < this.bodies.length; j++) {
        const a = this.bodies[i];
        const b = this.bodies[j];
        if (a.isStatic && b.isStatic) continue;

        const collision = this.testCollision(a, b);
        if (collision) {
          this.resolveCollision(collision);
          const enterCb = this.collisionCallbacks.get('enter');
          if (enterCb) enterCb(a, b);
        }
      }
    }
  }

  private testCollision(a: PhysicsBody, b: PhysicsBody): Collision | null {
    if (a.shape === 'circle' && b.shape === 'circle') {
      return this.circleCircleCollision(a, b);
    }
    if (a.shape === 'rect' && b.shape === 'rect') {
      return this.rectRectCollision(a, b);
    }
    return null;
  }

  private circleCircleCollision(a: PhysicsBody, b: PhysicsBody): Collision | null {
    const dx = b.position.x - a.position.x;
    const dy = b.position.y - a.position.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const radSum = (a.radius ?? 0.5) + (b.radius ?? 0.5);

    if (dist >= radSum || dist === 0) return null;

    return {
      a, b,
      normal: { x: dx / dist, y: dy / dist },
      depth: radSum - dist,
      contactPoint: {
        x: (a.position.x + b.position.x) / 2,
        y: (a.position.y + b.position.y) / 2,
      },
    };
  }

  private rectRectCollision(a: PhysicsBody, b: PhysicsBody): Collision | null {
    const aw = (a.width ?? 1) / 2;
    const ah = (a.height ?? 1) / 2;
    const bw = (b.width ?? 1) / 2;
    const bh = (b.height ?? 1) / 2;

    const dx = b.position.x - a.position.x;
    const dy = b.position.y - a.position.y;

    const overlapX = aw + bw - Math.abs(dx);
    const overlapY = ah + bh - Math.abs(dy);

    if (overlapX <= 0 || overlapY <= 0) return null;

    const depth = Math.min(overlapX, overlapY);
    const normal = overlapX < overlapY
      ? { x: Math.sign(dx), y: 0 }
      : { x: 0, y: Math.sign(dy) };

    return {
      a, b, normal, depth,
      contactPoint: {
        x: (a.position.x + b.position.x) / 2,
        y: (a.position.y + b.position.y) / 2,
      },
    };
  }

  private resolveCollision(col: Collision): void {
    const { a, b, normal, depth } = col;

    if (!a.isStatic) {
      a.position.x -= normal.x * depth * 0.5;
      a.position.y -= normal.y * depth * 0.5;
    }
    if (!b.isStatic) {
      b.position.x += normal.x * depth * 0.5;
      b.position.y += normal.y * depth * 0.5;
    }

    const relVx = a.velocity.x - b.velocity.x;
    const relVy = a.velocity.y - b.velocity.y;
    const relVn = relVx * normal.x + relVy * normal.y;

    if (relVn > 0) return;

    const e = Math.min(a.restitution, b.restitution);
    const j = -(1 + e) * relVn / (a.invMass + b.invMass);

    if (!a.isStatic) {
      a.velocity.x += j * a.invMass * normal.x;
      a.velocity.y += j * a.invMass * normal.y;
    }
    if (!b.isStatic) {
      b.velocity.x -= j * b.invMass * normal.x;
      b.velocity.y -= j * b.invMass * normal.y;
    }
  }
}
