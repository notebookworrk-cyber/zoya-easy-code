export type Color = [number, number, number, number];
export type Vector2 = { x: number; y: number };
export type Vector3 = { x: number; y: number; z: number };
export type Rect = { x: number; y: number; width: number; height: number };
export type Transform = { position: Vector3; rotation: Vector3; scale: Vector3 };

export const Colors = {
  WHITE: [1, 1, 1, 1] as Color,
  BLACK: [0, 0, 0, 1] as Color,
  RED: [1, 0, 0, 1] as Color,
  GREEN: [0, 1, 0, 1] as Color,
  BLUE: [0, 0, 1, 1] as Color,
  YELLOW: [1, 1, 0, 1] as Color,
  CYAN: [0, 1, 1, 1] as Color,
  MAGENTA: [1, 0, 1, 1] as Color,
  TRANSPARENT: [0, 0, 0, 0] as Color,
};

export enum BlendMode { Normal = 0, Additive, Multiply, Subtract }
export enum ProjectionType { Perspective = 0, Orthographic }
