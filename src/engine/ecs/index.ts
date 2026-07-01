export interface Component {
  readonly type: string;
}

export class Entity {
  readonly id: number;
  readonly world: World;
  private components: Map<string, Component>;

  constructor(world: World, id: number) {
    this.world = world;
    this.id = id;
    this.components = new Map();
  }

  add(component: Component): Entity {
    if (this.components.has(component.type)) {
      return this;
    }
    this.components.set(component.type, component);
    return this;
  }

  get<T extends Component>(type: string): T {
    return this.components.get(type) as T;
  }

  has(type: string): boolean {
    return this.components.has(type);
  }

  remove(type: string): Entity {
    this.components.delete(type);
    return this;
  }

  destroy(): void {
    this.world.destroyEntity(this.id);
  }

  matches(filter: QueryFilter): boolean {
    if (filter.all) {
      for (const type of filter.all) {
        if (!this.components.has(type)) return false;
      }
    }
    if (filter.any) {
      if (filter.any.length === 0) return false;
      let found = false;
      for (const type of filter.any) {
        if (this.components.has(type)) {
          found = true;
          break;
        }
      }
      if (!found) return false;
    }
    if (filter.none) {
      for (const type of filter.none) {
        if (this.components.has(type)) return false;
      }
    }
    return true;
  }
}

export class World {
  private entities: Map<number, Entity>;
  private nextId: number;
  private systems: System[];

  constructor() {
    this.entities = new Map();
    this.nextId = 1;
    this.systems = [];
  }

  createEntity(): Entity {
    const id = this.nextId++;
    const entity = new Entity(this, id);
    this.entities.set(id, entity);
    return entity;
  }

  destroyEntity(id: number): void {
    this.entities.delete(id);
  }

  getEntity(id: number): Entity | undefined {
    return this.entities.get(id);
  }

  query(filter: QueryFilter): Entity[] {
    const results: Entity[] = [];
    for (const entity of this.entities.values()) {
      if (entity.matches(filter)) {
        results.push(entity);
      }
    }
    return results;
  }

  addSystem(system: System): void {
    this.systems.push(system);
    this.systems.sort((a, b) => a.priority - b.priority);
  }

  removeSystem(system: System): void {
    const index = this.systems.indexOf(system);
    if (index !== -1) {
      this.systems.splice(index, 1);
    }
  }

  update(dt: number): void {
    for (const system of this.systems) {
      system.update(this, dt);
    }
  }

  clear(): void {
    this.entities.clear();
    this.systems = [];
    this.nextId = 1;
  }

  getComponentCount(): number {
    let count = 0;
    for (const entity of this.entities.values()) {
      count += entity['components'].size;
    }
    return count;
  }
}

export interface System {
  readonly name: string;
  readonly priority: number;
  update(world: World, dt: number): void;
}

export interface QueryFilter {
  all?: string[];
  any?: string[];
  none?: string[];
}

export function defineQuery(world: World, filter: QueryFilter): Entity[] {
  return world.query(filter);
}
