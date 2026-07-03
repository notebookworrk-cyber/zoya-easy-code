import type { Color, Vector3, Rect } from '../core.js';
import { ProjectionType } from '../core.js';

export interface Mesh {
  vertices: Float32Array;
  indices: Uint16Array;
  normals: Float32Array;
  uvs: Float32Array;
  tangents?: Float32Array;
}

export interface Material {
  name: string;
  albedo: Color;
  metallic: number;
  roughness: number;
  ao: number;
  emissive: Color;
  normalMap?: string;
  albedoMap?: string;
  metallicMap?: string;
  roughnessMap?: string;
  aoMap?: string;
  emissiveMap?: string;
  opacity: number;
  alphaTest: number;
}

export interface Light {
  type: 'directional' | 'point' | 'spot' | 'ambient';
  color: Color;
  intensity: number;
  range: number;
  spotAngle: number;
  shadows: boolean;
  shadowBias: number;
  shadowResolution: number;
}

export interface Camera {
  fov: number;
  near: number;
  far: number;
  projection: ProjectionType;
  viewport: Rect;
  hdr: boolean;
  postProcessing: PostProcessingSettings;
}

export interface PostProcessingSettings {
  bloom: boolean;
  bloomThreshold: number;
  bloomIntensity: number;
  toneMapping: 'aces' | 'reinhard' | 'hable' | 'linear';
  antiAliasing: 'none' | 'fxaa' | 'msaa' | 'taa';
  ssao: boolean;
  ssaoRadius: number;
  ssaoIntensity: number;
  motionBlur: boolean;
  motionBlurSamples: number;
  depthOfField: boolean;
  dofFocusDistance: number;
  dofAperture: number;
  vignette: boolean;
  vignetteIntensity: number;
  colorGrading: ColorGradingSettings;
}

export interface ColorGradingSettings {
  exposure: number;
  contrast: number;
  saturation: number;
  hueShift: number;
  temperature: number;
  tint: number;
}

export interface TerrainData {
  heightMap: Float32Array;
  width: number;
  height: number;
  resolution: number;
  maxHeight: number;
  layers: TerrainLayer[];
  holes?: boolean[][];
}

export interface TerrainLayer {
  name: string;
  albedoMap: string;
  normalMap: string;
  metallic: number;
  roughness: number;
  tileSize: number;
  blendHeight: number;
  blendSharpness: number;
}

export interface Skeleton {
  bones: Bone[];
  animations: Map<string, SkeletalAnimation>;
  rootBone: number;
}

export interface Bone {
  name: string;
  parent: number;
  position: Vector3;
  rotation: Vector3;
  scale: Vector3;
  inverseBindPose: Float32Array;
}

export interface SkeletalAnimation {
  name: string;
  duration: number;
  fps: number;
  loop: boolean;
  channels: AnimationChannel[];
}

export interface AnimationChannel {
  boneIndex: number;
  positionFrames: Keyframe<Vector3>[];
  rotationFrames: Keyframe<Vector3>[];
  scaleFrames: Keyframe<Vector3>[];
}

export interface Keyframe<T> {
  time: number;
  value: T;
  inTangent?: number;
  outTangent?: number;
}

export function createDefaultMaterial(name: string = 'default'): Material {
  return {
    name,
    albedo: [1, 1, 1, 1],
    metallic: 0,
    roughness: 0.5,
    ao: 1,
    emissive: [0, 0, 0, 1],
    opacity: 1,
    alphaTest: 0,
  };
}

export function createDefaultPostProcessing(): PostProcessingSettings {
  return {
    bloom: false,
    bloomThreshold: 1,
    bloomIntensity: 1,
    toneMapping: 'aces',
    antiAliasing: 'none',
    ssao: false,
    ssaoRadius: 0.5,
    ssaoIntensity: 1,
    motionBlur: false,
    motionBlurSamples: 8,
    depthOfField: false,
    dofFocusDistance: 10,
    dofAperture: 0.1,
    vignette: false,
    vignetteIntensity: 0.3,
    colorGrading: {
      exposure: 1,
      contrast: 0,
      saturation: 1,
      hueShift: 0,
      temperature: 0,
      tint: 0,
    },
  };
}

export function createPlaneMesh(width: number = 1, height: number = 1): Mesh {
  const w2 = width / 2;
  const h2 = height / 2;
  const vertices = new Float32Array([
    -w2, -h2, 0,  w2, -h2, 0,  w2, h2, 0,  -w2, h2, 0,
  ]);
  const indices = new Uint16Array([0, 1, 2, 0, 2, 3]);
  const normals = new Float32Array([
    0, 0, 1,  0, 0, 1,  0, 0, 1,  0, 0, 1,
  ]);
  const uvs = new Float32Array([
    0, 0,  1, 0,  1, 1,  0, 1,
  ]);
  return { vertices, indices, normals, uvs };
}

export function createCubeMesh(size: number = 1): Mesh {
  const s = size / 2;
  const vertData = [
    [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
    [s, -s, -s], [-s, -s, -s], [-s, s, -s], [s, s, -s],
  ];
  const idxData = [
    0,1,2,0,2,3, 4,5,6,4,6,7,
    1,4,7,1,7,2, 5,0,3,5,3,6,
    3,2,7,3,7,6, 1,0,5,1,5,4,
  ];
  const normData = [
    [0,0,1],[0,0,1],[0,0,1],[0,0,1],
    [0,0,-1],[0,0,-1],[0,0,-1],[0,0,-1],
  ];
  const uvData = [
    [0,0],[1,0],[1,1],[0,1],
    [0,0],[1,0],[1,1],[0,1],
  ];

  const vertices = new Float32Array(vertData.flat());
  const indices = new Uint16Array(idxData);
  const normals = new Float32Array(normData.flat());
  const uvs = new Float32Array(uvData.flat());

  return { vertices, indices, normals, uvs };
}

export function createSphereMesh(radius: number = 0.5, segments: number = 16): Mesh {
  const verts: number[] = [];
  const idx: number[] = [];
  const norms: number[] = [];
  const uvs: number[] = [];

  for (let lat = 0; lat <= segments; lat++) {
    const theta = (lat * Math.PI) / segments;
    const sinTheta = Math.sin(theta);
    const cosTheta = Math.cos(theta);

    for (let lon = 0; lon <= segments; lon++) {
      const phi = (lon * 2 * Math.PI) / segments;
      const sinPhi = Math.sin(phi);
      const cosPhi = Math.cos(phi);

      const x = cosPhi * sinTheta;
      const y = cosTheta;
      const z = sinPhi * sinTheta;

      verts.push(x * radius, y * radius, z * radius);
      norms.push(x, y, z);
      uvs.push(lon / segments, lat / segments);
    }
  }

  for (let lat = 0; lat < segments; lat++) {
    for (let lon = 0; lon < segments; lon++) {
      const first = lat * (segments + 1) + lon;
      const second = first + segments + 1;
      idx.push(first, second, first + 1);
      idx.push(second, second + 1, first + 1);
    }
  }

  return {
    vertices: new Float32Array(verts),
    indices: new Uint16Array(idx),
    normals: new Float32Array(norms),
    uvs: new Float32Array(uvs),
  };
}

export function interpolateKeyframes<T>(frames: Keyframe<T>[], time: number): T {
  if (frames.length === 0) return { x: 0, y: 0, z: 0 } as unknown as T;
  if (frames.length === 1) return frames[0].value;

  for (let i = 0; i < frames.length - 1; i++) {
    if (time >= frames[i].time && time <= frames[i + 1].time) {
      const t = (time - frames[i].time) / (frames[i + 1].time - frames[i].time);
      const a = frames[i].value as unknown as Vector3;
      const b = frames[i + 1].value as unknown as Vector3;
      return {
        x: a.x + (b.x - a.x) * t,
        y: a.y + (b.y - a.y) * t,
        z: a.z + (b.z - a.z) * t,
      } as unknown as T;
    }
  }

  return frames[frames.length - 1].value;
}
