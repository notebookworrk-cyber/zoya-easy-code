import type { Renderer } from '../render/index.js';
import type { Vector2, Color } from '../core.js';

export abstract class UIElement {
  name: string;
  position: Vector2;
  size: Vector2;
  visible: boolean;
  enabled: boolean;
  parent: UIElement | null;
  children: UIElement[];
  zIndex: number;

  constructor() {
    this.name = '';
    this.position = { x: 0, y: 0 };
    this.size = { x: 100, y: 50 };
    this.visible = true;
    this.enabled = true;
    this.parent = null;
    this.children = [];
    this.zIndex = 0;
  }

  abstract render(renderer: Renderer): void;

  addChild(child: UIElement): void {
    child.parent = this;
    this.children.push(child);
    this.children.sort((a, b) => a.zIndex - b.zIndex);
  }

  removeChild(child: UIElement): void {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      child.parent = null;
      this.children.splice(idx, 1);
    }
  }

  setPosition(x: number, y: number): void {
    this.position = { x, y };
  }

  setSize(w: number, h: number): void {
    this.size = { x: w, y: h };
  }

  show(): void {
    this.visible = true;
  }

  hide(): void {
    this.visible = false;
  }

  getWorldPosition(): Vector2 {
    if (this.parent) {
      const parentPos = this.parent.getWorldPosition();
      return { x: parentPos.x + this.position.x, y: parentPos.y + this.position.y };
    }
    return { ...this.position };
  }

  containsPoint(x: number, y: number): boolean {
    return x >= this.position.x && x <= this.position.x + this.size.x &&
      y >= this.position.y && y <= this.position.y + this.size.y;
  }
}

export class UILabel extends UIElement {
  text: string;
  fontSize: number;
  color: Color;
  align: 'left' | 'center' | 'right';

  constructor(text: string = '') {
    super();
    this.text = text;
    this.fontSize = 16;
    this.color = [1, 1, 1, 1];
    this.align = 'left';
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawText(this.text, pos.x, pos.y, this.fontSize, this.color);
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UIButton extends UIElement {
  text: string;
  onClick: () => void;
  isPressed: boolean;

  constructor(text: string = 'Button') {
    super();
    this.text = text;
    this.onClick = () => {};
    this.isPressed = false;
    this.size = { x: 120, y: 32 };
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, this.isPressed ? [0.6, 0.6, 0.6, 1] as Color : [0.3, 0.3, 0.3, 1] as Color, true);
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, [0.8, 0.8, 0.8, 1] as Color, false);
    const textX = pos.x + this.size.x / 2 - (this.text.length * 4);
    const textY = pos.y + this.size.y / 2 - 6;
    renderer.drawText(this.text, textX, textY, 14, [1, 1, 1, 1]);
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UIImage extends UIElement {
  texture: string;
  color: Color;
  flipX: boolean;
  flipY: boolean;

  constructor(texture: string = '') {
    super();
    this.texture = texture;
    this.color = [1, 1, 1, 1];
    this.flipX = false;
    this.flipY = false;
    this.size = { x: 64, y: 64 };
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, this.color, true);
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UIPanel extends UIElement {
  backgroundColor: Color;
  borderColor: Color;
  borderWidth: number;
  borderRadius: number;

  constructor() {
    super();
    this.backgroundColor = [0.2, 0.2, 0.25, 0.9];
    this.borderColor = [0.4, 0.4, 0.5, 1];
    this.borderWidth = 1;
    this.borderRadius = 4;
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, this.backgroundColor, true);
    if (this.borderWidth > 0) {
      renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, this.borderColor, false);
    }
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UITextField extends UIElement {
  text: string;
  placeholder: string;
  isFocused: boolean;
  maxLength: number;

  constructor(placeholder: string = '') {
    super();
    this.text = '';
    this.placeholder = placeholder;
    this.isFocused = false;
    this.maxLength = 256;
    this.size = { x: 200, y: 28 };
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, [0.15, 0.15, 0.2, 1] as Color, true);
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, this.isFocused ? [0.4, 0.6, 1, 1] as Color : [0.3, 0.3, 0.35, 1] as Color, false);
    const displayText = this.text || this.placeholder;
    const textColor = this.text ? [1, 1, 1, 1] as Color : [0.5, 0.5, 0.5, 1] as Color;
    renderer.drawText(displayText, pos.x + 4, pos.y + 6, 14, textColor);
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UIList extends UIElement {
  items: string[];
  selectedIndex: number;
  itemHeight: number;

  constructor(items: string[] = []) {
    super();
    this.items = items;
    this.selectedIndex = -1;
    this.itemHeight = 24;
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    for (let i = 0; i < this.items.length; i++) {
      const y = pos.y + i * this.itemHeight;
      if (i === this.selectedIndex) {
        renderer.drawRect(pos.x, y, this.size.x, this.itemHeight, [0.3, 0.5, 0.9, 0.6] as Color, true);
      }
      renderer.drawText(this.items[i], pos.x + 4, y + 4, 14, [1, 1, 1, 1]);
    }
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UISlider extends UIElement {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;

  constructor() {
    super();
    this.value = 50;
    this.min = 0;
    this.max = 100;
    this.step = 1;
    this.onChange = () => {};
    this.size = { x: 200, y: 20 };
  }

  render(renderer: Renderer): void {
    if (!this.visible) return;
    const pos = this.getWorldPosition();
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, [0.2, 0.2, 0.25, 1] as Color, true);
    const fillRatio = (this.value - this.min) / (this.max - this.min);
    renderer.drawRect(pos.x, pos.y, this.size.x * fillRatio, this.size.y, [0.3, 0.6, 1, 0.8] as Color, true);
    renderer.drawRect(pos.x, pos.y, this.size.x, this.size.y, [0.4, 0.4, 0.5, 1] as Color, false);
    for (const child of this.children) {
      child.render(renderer);
    }
  }
}

export class UIManager {
  private rootElements: UIElement[];
  private focused: UIElement | null;

  constructor() {
    this.rootElements = [];
    this.focused = null;
  }

  add(element: UIElement): void {
    this.rootElements.push(element);
  }

  remove(element: UIElement): void {
    const idx = this.rootElements.indexOf(element);
    if (idx !== -1) {
      this.rootElements.splice(idx, 1);
    }
    if (this.focused === element) {
      this.focused = null;
    }
  }

  getByName(name: string): UIElement | undefined {
    const search = (elements: UIElement[]): UIElement | undefined => {
      for (const el of elements) {
        if (el.name === name) return el;
        const found = search(el.children);
        if (found) return found;
      }
      return undefined;
    };
    return search(this.rootElements);
  }

  getFocused(): UIElement | null {
    return this.focused;
  }

  focus(element: UIElement): void {
    this.focused = element;
  }

  blur(): void {
    this.focused = null;
  }

  update(_dt: number): void {
    // UI update logic (animations, etc.)
  }

  render(renderer: Renderer): void {
    const sorted = [...this.rootElements].sort((a, b) => a.zIndex - b.zIndex);
    for (const element of sorted) {
      element.render(renderer);
    }
  }

  clear(): void {
    this.rootElements = [];
    this.focused = null;
  }

  handleInput(x: number, y: number, pressed: boolean): UIElement | null {
    const findHit = (elements: UIElement[]): UIElement | null => {
      for (const el of elements) {
        if (!el.visible || !el.enabled) continue;
        if (el.containsPoint(x, y)) {
          for (const child of el.children) {
            const hit = findHit([child]);
            if (hit) return hit;
          }
          return el;
        }
      }
      return null;
    };

    const hit = findHit(this.rootElements);
    if (hit && hit instanceof UIButton && pressed) {
      hit.isPressed = true;
      hit.onClick();
    }
    if (hit && hit instanceof UIButton && !pressed) {
      hit.isPressed = false;
    }
    if (hit && hit instanceof UITextField && pressed) {
      this.focus(hit);
    }
    return hit;
  }

  getRootElements(): UIElement[] {
    return [...this.rootElements];
  }
}
