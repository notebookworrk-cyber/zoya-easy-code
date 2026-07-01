import { EditorPanel, PanelType } from './index';

export interface MaterialEditState {
  name: string;
  albedo: [number, number, number, number];
  metallic: number;
  roughness: number;
  ao: number;
  emissive: [number, number, number];
  opacity: number;
  alphaTest: number;
  albedoMap: string | null;
  normalMap: string | null;
  metallicMap: string | null;
  roughnessMap: string | null;
  aoMap: string | null;
  emissiveMap: string | null;
  tiling: [number, number];
  offset: [number, number];
}

const DEFAULT_STATE: MaterialEditState = {
  name: 'new_material',
  albedo: [1, 1, 1, 1],
  metallic: 0,
  roughness: 0.5,
  ao: 1,
  emissive: [0, 0, 0],
  opacity: 1,
  alphaTest: 0,
  albedoMap: null,
  normalMap: null,
  metallicMap: null,
  roughnessMap: null,
  aoMap: null,
  emissiveMap: null,
  tiling: [1, 1],
  offset: [0, 0],
};

export class MaterialEditorPanel implements EditorPanel {
  id = 'material-editor';
  type: PanelType = 'material';
  title = 'Material Editor';
  private state: MaterialEditState;
  private previewMesh: 'sphere' | 'cube' | 'plane';
  private previewRotation: number;
  private dirty: boolean;

  constructor() {
    this.state = { ...DEFAULT_STATE, name: 'new_material', albedo: [...DEFAULT_STATE.albedo] as [number, number, number, number], emissive: [...DEFAULT_STATE.emissive] as [number, number, number], tiling: [...DEFAULT_STATE.tiling] as [number, number], offset: [...DEFAULT_STATE.offset] as [number, number] };
    this.previewMesh = 'sphere';
    this.previewRotation = 0;
    this.dirty = false;
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void {
    this.previewRotation = (this.previewRotation + _dt * 30) % 360;
  }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  loadMaterial(name: string): void {
    this.state = { ...DEFAULT_STATE, name, albedo: [...DEFAULT_STATE.albedo] as [number, number, number, number], emissive: [...DEFAULT_STATE.emissive] as [number, number, number], tiling: [...DEFAULT_STATE.tiling] as [number, number], offset: [...DEFAULT_STATE.offset] as [number, number] };
    this.dirty = false;
  }

  saveMaterial(): void {
    this.dirty = false;
  }

  resetMaterial(): void {
    this.state = { ...DEFAULT_STATE, name: this.state.name, albedo: [...DEFAULT_STATE.albedo] as [number, number, number, number], emissive: [...DEFAULT_STATE.emissive] as [number, number, number], tiling: [...DEFAULT_STATE.tiling] as [number, number], offset: [...DEFAULT_STATE.offset] as [number, number] };
    this.dirty = false;
  }

  setAlbedo(color: [number, number, number, number]): void {
    this.state = { ...this.state, albedo: [...color] as [number, number, number, number] };
    this.dirty = true;
  }

  setMetallic(value: number): void {
    this.state = { ...this.state, metallic: Math.max(0, Math.min(1, value)) };
    this.dirty = true;
  }

  setRoughness(value: number): void {
    this.state = { ...this.state, roughness: Math.max(0, Math.min(1, value)) };
    this.dirty = true;
  }

  setAO(value: number): void {
    this.state = { ...this.state, ao: Math.max(0, Math.min(1, value)) };
    this.dirty = true;
  }

  setEmissive(color: [number, number, number]): void {
    this.state = { ...this.state, emissive: [...color] as [number, number, number] };
    this.dirty = true;
  }

  setOpacity(value: number): void {
    this.state = { ...this.state, opacity: Math.max(0, Math.min(1, value)) };
    this.dirty = true;
  }

  setAlbedoMap(path: string | null): void {
    this.state = { ...this.state, albedoMap: path };
    this.dirty = true;
  }

  setNormalMap(path: string | null): void {
    this.state = { ...this.state, normalMap: path };
    this.dirty = true;
  }

  setMetallicMap(path: string | null): void {
    this.state = { ...this.state, metallicMap: path };
    this.dirty = true;
  }

  setRoughnessMap(path: string | null): void {
    this.state = { ...this.state, roughnessMap: path };
    this.dirty = true;
  }

  setAOMap(path: string | null): void {
    this.state = { ...this.state, aoMap: path };
    this.dirty = true;
  }

  setEmissiveMap(path: string | null): void {
    this.state = { ...this.state, emissiveMap: path };
    this.dirty = true;
  }

  setPreviewMesh(mesh: 'sphere' | 'cube' | 'plane'): void {
    this.previewMesh = mesh;
  }

  setTiling(u: number, v: number): void {
    this.state = { ...this.state, tiling: [u, v] };
    this.dirty = true;
  }

  setOffset(u: number, v: number): void {
    this.state = { ...this.state, offset: [u, v] };
    this.dirty = true;
  }

  getState(): MaterialEditState {
    return {
      ...this.state,
      albedo: [...this.state.albedo] as [number, number, number, number],
      emissive: [...this.state.emissive] as [number, number, number],
      tiling: [...this.state.tiling] as [number, number],
      offset: [...this.state.offset] as [number, number],
    };
  }

  hasChanges(): boolean {
    return this.dirty;
  }

  getPreviewMesh(): 'sphere' | 'cube' | 'plane' {
    return this.previewMesh;
  }

  getPreviewRotation(): number {
    return this.previewRotation;
  }
}
