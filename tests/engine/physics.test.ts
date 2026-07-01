import { describe, it, expect, beforeEach } from 'vitest';
import { PhysicsWorld } from '../../src/engine/physics/index.js';
import type { PhysicsBody, Collision } from '../../src/engine/physics/index.js';

function makeCircleBody(entityId: number, x: number, y: number, radius: number, mass: number = 1, isStatic: boolean = false): PhysicsBody {
  return {
    entityId,
    position: { x, y },
    velocity: { x: 0, y: 0 },
    acceleration: { x: 0, y: 0 },
    mass,
    invMass: mass > 0 ? 1 / mass : 0,
    restitution: 0.5,
    friction: 0.3,
    isStatic,
    shape: 'circle',
    radius,
  };
}

function makeRectBody(entityId: number, x: number, y: number, w: number, h: number, mass: number = 1, isStatic: boolean = false): PhysicsBody {
  return {
    entityId,
    position: { x, y },
    velocity: { x: 0, y: 0 },
    acceleration: { x: 0, y: 0 },
    mass,
    invMass: mass > 0 ? 1 / mass : 0,
    restitution: 0.5,
    friction: 0.3,
    isStatic,
    shape: 'rect',
    width: w,
    height: h,
  };
}

describe('PhysicsWorld', () => {
  let world: PhysicsWorld;

  beforeEach(() => {
    world = new PhysicsWorld({ x: 0, y: 9.81 });
  });

  describe('Body management', () => {
    it('adds bodies', () => {
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);
      expect(world.bodyCount()).toBe(1);
    });

    it('calculates invMass on add', () => {
      const light = makeCircleBody(1, 0, 0, 1, 2);
      const heavy = makeCircleBody(2, 0, 0, 1, 10);
      world.addBody(light);
      world.addBody(heavy);
      expect(light.invMass).toBeCloseTo(0.5);
      expect(heavy.invMass).toBeCloseTo(0.1);
    });

    it('zero mass body has zero invMass', () => {
      const body = makeCircleBody(1, 0, 0, 1, 0);
      world.addBody(body);
      expect(body.invMass).toBe(0);
    });

    it('retrieves body by entityId', () => {
      const body = makeCircleBody(42, 10, 20, 1);
      world.addBody(body);
      const retrieved = world.getBody(42);
      expect(retrieved).toBeDefined();
      expect(retrieved!.position.x).toBe(10);
      expect(retrieved!.position.y).toBe(20);
    });

    it('removes body', () => {
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);
      world.removeBody(1);
      expect(world.bodyCount()).toBe(0);
    });

    it('removing non-existent body does nothing', () => {
      world.removeBody(999);
      expect(world.bodyCount()).toBe(0);
    });

    it('getBody returns undefined for unknown', () => {
      expect(world.getBody(999)).toBeUndefined();
    });
  });

  describe('Gravity integration', () => {
    it('applies gravity to dynamic bodies', () => {
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);
      world.step(0.1);
      expect(body.velocity.y).toBeGreaterThan(0);
      expect(body.position.y).toBeGreaterThan(0);
    });

    it('static bodies do not move with gravity', () => {
      const body = makeCircleBody(1, 0, 0, 1, 1, true);
      world.addBody(body);
      world.step(0.1);
      expect(body.velocity.y).toBe(0);
      expect(body.position.y).toBe(0);
    });

    it('sets custom gravity', () => {
      world.setGravity({ x: 5, y: 0 });
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);
      world.step(0.1);
      expect(body.velocity.x).toBeGreaterThan(0);
      expect(body.velocity.y).toBe(0);
    });

    it('integration with multiple steps', () => {
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);
      world.step(0.016);
      world.step(0.016);
      world.step(0.016);
      expect(body.velocity.y).toBeGreaterThan(0.3);
      expect(body.position.y).toBeGreaterThan(0.002);
    });
  });

  describe('Collision detection', () => {
    it('detects circle-circle collision', () => {
      const a = makeCircleBody(1, 0, 0, 1);
      const b = makeCircleBody(2, 1.5, 0, 1);
      world.addBody(a);
      world.addBody(b);
      world.step(0.016);
      expect(a.position.x).not.toBe(0);
    });

    it('no collision when circles are far apart', () => {
      const a = makeCircleBody(1, 0, 0, 1);
      const b = makeCircleBody(2, 10, 10, 1);
      world.addBody(a);
      world.addBody(b);
      const posBefore = a.position.x;
      world.step(0.016);
      expect(a.position.x).toBe(posBefore);
    });

    it('detects rect-rect collision', () => {
      const a = makeRectBody(1, 0, 0, 2, 2);
      const b = makeRectBody(2, 1.5, 0, 2, 2);
      world.addBody(a);
      world.addBody(b);
      world.step(0.016);
      expect(a.position.x).toBeLessThan(0);
    });

    it('no collision between rects far apart', () => {
      const a = makeRectBody(1, 0, 0, 1, 1);
      const b = makeRectBody(2, 10, 10, 1, 1);
      world.addBody(a);
      world.addBody(b);
      const posBefore = { x: a.position.x, y: a.position.y };
      world.step(0.016);
      expect(a.position.x).toBe(posBefore.x);
    });

    it('static bodies do not collide with each other', () => {
      const a = makeCircleBody(1, 0, 0, 1, 1, true);
      const b = makeCircleBody(2, 0.5, 0, 1, 1, true);
      world.addBody(a);
      world.addBody(b);
      expect(() => world.step(0.016)).not.toThrow();
    });
  });

  describe('Raycasting', () => {
    it('hits a body in ray path', () => {
      const body = makeCircleBody(1, 5, 0, 1);
      world.addBody(body);
      const hit = world.raycast({ x: 0, y: 0 }, { x: 1, y: 0 }, 10);
      expect(hit).not.toBeNull();
      expect(hit!.b.entityId).toBe(1);
    });

    it('returns null when no body in ray path', () => {
      const body = makeCircleBody(1, 100, 100, 1);
      world.addBody(body);
      const hit = world.raycast({ x: 0, y: 0 }, { x: 1, y: 0 }, 10);
      expect(hit).toBeNull();
    });
  });

  describe('Collision callbacks', () => {
    it('fires onCollisionEnter callback', () => {
      const a = makeCircleBody(1, 0, 0, 1);
      const b = makeCircleBody(2, 1.5, 0, 1);
      world.addBody(a);
      world.addBody(b);

      let hitA: number | null = null;
      let hitB: number | null = null;
      world.onCollisionEnter((ca, cb) => {
        hitA = ca.entityId;
        hitB = cb.entityId;
      });

      world.step(0.016);
      expect(hitA).toBe(1);
      expect(hitB).toBe(2);
    });

    it('does not fire when no collision', () => {
      const body = makeCircleBody(1, 0, 0, 1);
      world.addBody(body);

      let called = false;
      world.onCollisionEnter(() => { called = true; });
      world.step(0.016);
      expect(called).toBe(false);
    });
  });

  describe('Spatial queries', () => {
    it('queries bodies in rect', () => {
      world.addBody(makeCircleBody(1, 5, 5, 1));
      world.addBody(makeCircleBody(2, 50, 50, 1));
      const results = world.queryRect({ x: 0, y: 0, width: 10, height: 10 });
      expect(results).toHaveLength(1);
      expect(results[0].entityId).toBe(1);
    });

    it('queries bodies in circle', () => {
      world.addBody(makeCircleBody(1, 2, 0, 1));
      world.addBody(makeCircleBody(2, 20, 0, 1));
      const results = world.queryCircle({ x: 0, y: 0 }, 5);
      expect(results).toHaveLength(1);
      expect(results[0].entityId).toBe(1);
    });
  });
});
