import type { Renderer } from '../render/index.js';
import type { Vector2 } from '../core.js';
import type { Entity } from '../ecs/index.js';

export interface Tile {
  id: number;
  x: number;
  y: number;
  layer: number;
  flippedX: boolean;
  flippedY: boolean;
  rotation: number;
}

export interface TileLayer {
  name: string;
  opacity: number;
  visible: boolean;
  tiles: (Tile | null)[][];
  parallaxFactor: Vector2;
}

export interface TileSet {
  name: string;
  image: string;
  tileWidth: number;
  tileHeight: number;
  columns: number;
  tileCount: number;
  spacing: number;
  margin: number;
}

export class TileMap {
  readonly width: number;
  readonly height: number;
  readonly tileWidth: number;
  readonly tileHeight: number;
  private layers: TileLayer[];
  private tileSets: TileSet[];
  private collisions: Set<string>;

  constructor(width: number, height: number, tileWidth: number, tileHeight: number) {
    this.width = width;
    this.height = height;
    this.tileWidth = tileWidth;
    this.tileHeight = tileHeight;
    this.layers = [];
    this.tileSets = [];
    this.collisions = new Set();
  }

  addLayer(name: string, opacity: number = 1): number {
    const tiles: (Tile | null)[][] = [];
    for (let y = 0; y < this.height; y++) {
      tiles[y] = [];
      for (let x = 0; x < this.width; x++) {
        tiles[y][x] = null;
      }
    }
    this.layers.push({
      name,
      opacity,
      visible: true,
      tiles,
      parallaxFactor: { x: 1, y: 1 },
    });
    return this.layers.length - 1;
  }

  removeLayer(index: number): void {
    if (index >= 0 && index < this.layers.length) {
      this.layers.splice(index, 1);
    }
  }

  setTile(layer: number, x: number, y: number, tile: Tile | null): void {
    if (layer >= 0 && layer < this.layers.length &&
      y >= 0 && y < this.height && x >= 0 && x < this.width) {
      this.layers[layer].tiles[y][x] = tile;
    }
  }

  getTile(layer: number, x: number, y: number): Tile | null {
    if (layer >= 0 && layer < this.layers.length &&
      y >= 0 && y < this.height && x >= 0 && x < this.width) {
      return this.layers[layer].tiles[y][x];
    }
    return null;
  }

  addTileSet(tileSet: TileSet): void {
    this.tileSets.push(tileSet);
  }

  setCollision(x: number, y: number, value: boolean): void {
    const key = `${x},${y}`;
    if (value) {
      this.collisions.add(key);
    } else {
      this.collisions.delete(key);
    }
  }

  hasCollision(x: number, y: number): boolean {
    return this.collisions.has(`${x},${y}`);
  }

  getLayer(index: number): TileLayer | undefined {
    return this.layers[index];
  }

  getLayerCount(): number {
    return this.layers.length;
  }

  render(renderer: Renderer, _camera: Entity): void {
    for (const layer of this.layers) {
      if (!layer.visible) continue;
      for (let y = 0; y < this.height; y++) {
        for (let x = 0; x < this.width; x++) {
          const tile = layer.tiles[y][x];
          if (tile === null) continue;

          const px = x * this.tileWidth;
          const py = y * this.tileHeight;

          renderer.drawRect(
            px, py,
            this.tileWidth, this.tileHeight,
            [0.8, 0.8, 0.8, layer.opacity],
            true,
          );
          renderer.drawRect(
            px, py,
            this.tileWidth, this.tileHeight,
            [0.5, 0.5, 0.5, layer.opacity * 0.5],
            false,
          );
        }
      }
    }
  }

  getTileSets(): TileSet[] {
    return [...this.tileSets];
  }
}
