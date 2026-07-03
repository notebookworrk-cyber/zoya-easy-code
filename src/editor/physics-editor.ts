import { EditorPanel, PanelType } from './index';

export interface PhysicsEditState {
  bodyType: 'static' | 'dynamic' | 'kinematic';
  mass: number;
  friction: number;
  restitution: number;
  gravityScale: number;
  linearDamping: number;
  angularDamping: number;
  colliderType: 'rect' | 'circle' | 'polygon';
  colliderSize: [number, number];
  colliderOffset: [number, number];
  colliderRadius: number;
  isSensor: boolean;
  collisionLayer: number;
  collisionMask: number;
  fixedRotation: boolean;
  bullet: boolean;
}

const DEFAULT_STATE: PhysicsEditState = {
  bodyType: 'dynamic',
  mass: 1,
  friction: 0.5,
  restitution: 0,
  gravityScale: 1,
  linearDamping: 0,
  angularDamping: 0,
  colliderType: 'rect',
  colliderSize: [1, 1],
  colliderOffset: [0, 0],
  colliderRadius: 0.5,
  isSensor: false,
  collisionLayer: 1,
  collisionMask: 1,
  fixedRotation: false,
  bullet: false,
};

export class PhysicsEditorPanel implements EditorPanel {
  id = 'physics-editor';
  type: PanelType = 'physics';
  title = 'Physics Editor';
  private state: PhysicsEditState;
  private showColliders: boolean;

  constructor() {
    this.state = {
      ...DEFAULT_STATE,
      colliderSize: [...DEFAULT_STATE.colliderSize] as [number, number],
      colliderOffset: [...DEFAULT_STATE.colliderOffset] as [number, number],
    };
    this.showColliders = true;
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  loadBody(_entityId: string): void {
    this.state = {
      ...DEFAULT_STATE,
      colliderSize: [...DEFAULT_STATE.colliderSize] as [number, number],
      colliderOffset: [...DEFAULT_STATE.colliderOffset] as [number, number],
    };
  }

  saveBody(): void {

  }

  setBodyType(type: PhysicsEditState['bodyType']): void {
    this.state = { ...this.state, bodyType: type };
  }

  setMass(mass: number): void {
    this.state = { ...this.state, mass: Math.max(0.001, mass) };
  }

  setFriction(friction: number): void {
    this.state = { ...this.state, friction: Math.max(0, friction) };
  }

  setRestitution(restitution: number): void {
    this.state = { ...this.state, restitution: Math.max(0, Math.min(1, restitution)) };
  }

  setColliderType(type: PhysicsEditState['colliderType']): void {
    this.state = { ...this.state, colliderType: type };
  }

  toggleColliderVisibility(): void {
    this.showColliders = !this.showColliders;
  }

  areCollidersVisible(): boolean {
    return this.showColliders;
  }

  getState(): PhysicsEditState {
    return {
      ...this.state,
      colliderSize: [...this.state.colliderSize] as [number, number],
      colliderOffset: [...this.state.colliderOffset] as [number, number],
    };
  }

  getColliderShape(): { type: string; vertices: [number, number][] } {
    switch (this.state.colliderType) {
      case 'rect': {
        const hw = this.state.colliderSize[0] / 2;
        const hh = this.state.colliderSize[1] / 2;
        const ox = this.state.colliderOffset[0];
        const oy = this.state.colliderOffset[1];
        return {
          type: 'polygon',
          vertices: [
            [ox - hw, oy - hh],
            [ox + hw, oy - hh],
            [ox + hw, oy + hh],
            [ox - hw, oy + hh],
          ],
        };
      }
      case 'circle':
        return {
          type: 'circle',
          vertices: [[this.state.colliderOffset[0], this.state.colliderOffset[1]]],
        };
      case 'polygon':
        return {
          type: 'polygon',
          vertices: [
            [-0.5, -0.5],
            [0.5, -0.5],
            [0.5, 0.5],
            [-0.5, 0.5],
          ],
        };
    }
  }

  setGravityScale(scale: number): void {
    this.state = { ...this.state, gravityScale: scale };
  }

  setLinearDamping(damping: number): void {
    this.state = { ...this.state, linearDamping: Math.max(0, damping) };
  }

  setAngularDamping(damping: number): void {
    this.state = { ...this.state, angularDamping: Math.max(0, damping) };
  }

  setColliderSize(width: number, height: number): void {
    this.state = { ...this.state, colliderSize: [Math.max(0.001, width), Math.max(0.001, height)] };
  }

  setColliderOffset(x: number, y: number): void {
    this.state = { ...this.state, colliderOffset: [x, y] };
  }

  setColliderRadius(radius: number): void {
    this.state = { ...this.state, colliderRadius: Math.max(0.001, radius) };
  }

  setIsSensor(sensor: boolean): void {
    this.state = { ...this.state, isSensor: sensor };
  }

  setCollisionLayer(layer: number): void {
    this.state = { ...this.state, collisionLayer: Math.max(0, layer) };
  }

  setCollisionMask(mask: number): void {
    this.state = { ...this.state, collisionMask: mask };
  }

  setFixedRotation(fixed: boolean): void {
    this.state = { ...this.state, fixedRotation: fixed };
  }

  setBullet(bullet: boolean): void {
    this.state = { ...this.state, bullet: bullet };
  }
}
