import { describe, it, expect, beforeEach } from 'vitest';
import { World, Entity, defineQuery } from '../../src/engine/ecs/index.js';
import type { Component, System, QueryFilter } from '../../src/engine/ecs/index.js';

class PositionComponent implements Component {
  readonly type = 'position';
  constructor(public x: number = 0, public y: number = 0) {}
}

class VelocityComponent implements Component {
  readonly type = 'velocity';
  constructor(public x: number = 0, public y: number = 0) {}
}

class HealthComponent implements Component {
  readonly type = 'health';
  constructor(public value: number = 100) {}
}

class NameComponent implements Component {
  readonly type = 'name';
  constructor(public name: string = '') {}
}

describe('ECS World', () => {
  let world: World;

  beforeEach(() => {
    world = new World();
  });

  describe('Entity', () => {
    it('creates entity with unique id', () => {
      const e1 = world.createEntity();
      const e2 = world.createEntity();
      expect(e1.id).toBe(1);
      expect(e2.id).toBe(2);
      expect(e1.id).not.toBe(e2.id);
    });

    it('adds and retrieves components', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent(10, 20));
      const pos = entity.get<PositionComponent>('position');
      expect(pos.x).toBe(10);
      expect(pos.y).toBe(20);
    });

    it('checks component existence', () => {
      const entity = world.createEntity();
      expect(entity.has('position')).toBe(false);
      entity.add(new PositionComponent());
      expect(entity.has('position')).toBe(true);
    });

    it('removes components', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent(5, 5));
      expect(entity.has('position')).toBe(true);
      entity.remove('position');
      expect(entity.has('position')).toBe(false);
    });

    it('supports multiple component types', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent(1, 2));
      entity.add(new VelocityComponent(3, 4));
      entity.add(new HealthComponent(50));

      expect(entity.has('position')).toBe(true);
      expect(entity.has('velocity')).toBe(true);
      expect(entity.has('health')).toBe(true);
      expect(entity.get<PositionComponent>('position').x).toBe(1);
      expect(entity.get<VelocityComponent>('velocity').x).toBe(3);
      expect(entity.get<HealthComponent>('health').value).toBe(50);
    });

    it('add returns entity for chaining', () => {
      const entity = world.createEntity();
      const returned = entity.add(new PositionComponent());
      expect(returned).toBe(entity);
    });

    it('remove returns entity for chaining', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent());
      const returned = entity.remove('position');
      expect(returned).toBe(entity);
    });

    it('double add of same type does not overwrite', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent(1, 2));
      entity.add(new PositionComponent(3, 4));
      const pos = entity.get<PositionComponent>('position');
      expect(pos.x).toBe(1);
    });

    it('destroy removes entity from world', () => {
      const entity = world.createEntity();
      const id = entity.id;
      entity.destroy();
      expect(world.getEntity(id)).toBeUndefined();
    });

    it('destroy non-existent entity does nothing', () => {
      const entity = world.createEntity();
      const id = entity.id;
      entity.destroy();
      world.destroyEntity(id);
      expect(world.getEntity(id)).toBeUndefined();
    });

    it('reuses ids after world clear', () => {
      world.createEntity();
      world.createEntity();
      world.clear();
      const e3 = world.createEntity();
      expect(e3.id).toBe(1);
    });
  });

  describe('World querying', () => {
    it('queries entities with all components', () => {
      const e1 = world.createEntity();
      e1.add(new PositionComponent(1, 1));
      e1.add(new VelocityComponent(1, 1));

      const e2 = world.createEntity();
      e2.add(new PositionComponent(2, 2));

      const results = world.query({ all: ['position', 'velocity'] });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe(e1.id);
    });

    it('queries entities with any components', () => {
      const e1 = world.createEntity();
      e1.add(new NameComponent('Alice'));

      const e2 = world.createEntity();
      e2.add(new PositionComponent(5, 5));

      const results = world.query({ any: ['name', 'position'] });
      expect(results).toHaveLength(2);
    });

    it('queries entities excluding components', () => {
      const e1 = world.createEntity();
      e1.add(new PositionComponent(1, 1));

      const e2 = world.createEntity();
      e2.add(new PositionComponent(2, 2));
      e2.add(new HealthComponent());

      const results = world.query({ all: ['position'], none: ['health'] });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe(e1.id);
    });

    it('returns empty array when no match', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent());
      const results = world.query({ all: ['nonexistent'] });
      expect(results).toHaveLength(0);
    });

    it('defineQuery is alias for world.query', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent());
      const results = defineQuery(world, { all: ['position'] });
      expect(results).toHaveLength(1);
    });

    it('handles empty filter (all entities)', () => {
      world.createEntity();
      world.createEntity();
      world.createEntity();
      const results = world.query({});
      expect(results).toHaveLength(3);
    });

    it('handles any with empty array', () => {
      const entity = world.createEntity();
      entity.add(new PositionComponent());
      const results = world.query({ any: [] });
      expect(results).toHaveLength(0);
    });
  });

  describe('Systems', () => {
    it('executes systems in priority order', () => {
      const order: number[] = [];

      const sys1: System = {
        name: 'sys1',
        priority: 10,
        update: () => order.push(1),
      };
      const sys2: System = {
        name: 'sys2',
        priority: 5,
        update: () => order.push(2),
      };
      const sys3: System = {
        name: 'sys3',
        priority: 0,
        update: () => order.push(3),
      };

      world.addSystem(sys1);
      world.addSystem(sys2);
      world.addSystem(sys3);
      world.update(1);

      expect(order).toEqual([3, 2, 1]);
    });

    it('adds system after creation', () => {
      let updated = false;
      const system: System = {
        name: 'test',
        priority: 0,
        update: () => { updated = true; },
      };
      world.addSystem(system);
      world.update(1);
      expect(updated).toBe(true);
    });

    it('removes system', () => {
      let callCount = 0;
      const system: System = {
        name: 'test',
        priority: 0,
        update: () => { callCount++; },
      };
      world.addSystem(system);
      world.update(1);
      world.removeSystem(system);
      world.update(1);
      expect(callCount).toBe(1);
    });

    it('remove non-existent system does nothing', () => {
      const sys: System = { name: 'ghost', priority: 0, update: () => {} };
      world.addSystem(sys);
      world.removeSystem({ name: 'fake', priority: 0, update: () => {} });
      let ran = false;
      const real: System = { name: 'real', priority: 0, update: () => { ran = true; } };
      world.addSystem(real);
      world.removeSystem({ name: 'nobody', priority: 99, update: () => {} });
      world.update(1);
      expect(ran).toBe(true);
    });
  });

  describe('Edge cases', () => {
    it('getComponentCount returns correct count', () => {
      const e1 = world.createEntity();
      e1.add(new PositionComponent());
      e1.add(new VelocityComponent());
      const e2 = world.createEntity();
      e2.add(new HealthComponent());
      expect(world.getComponentCount()).toBe(3);
    });

    it('clear resets everything', () => {
      world.createEntity().add(new PositionComponent());
      const sys: System = { name: 's', priority: 0, update: () => {} };
      world.addSystem(sys);
      world.clear();
      expect(world.getComponentCount()).toBe(0);
      world.update(1);
      expect(world.query({})).toHaveLength(0);
    });

    it('getEntity returns undefined for unknown id', () => {
      expect(world.getEntity(999)).toBeUndefined();
    });

    it('entity matches filter with any matching', () => {
      const entity = world.createEntity();
      entity.add(new NameComponent('test'));
      expect(entity.matches({ any: ['name'] })).toBe(true);
      expect(entity.matches({ any: ['nonexistent'] })).toBe(false);
    });
  });
});
