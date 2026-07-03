import { EditorPanel, PanelType } from './index';

export interface InspectorProperty {
  name: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'color' | 'vector2' | 'vector3' | 'enum' | 'texture' | 'asset' | 'object' | 'array';
  value: unknown;
  defaultValue: unknown;
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  description?: string;
  readonly: boolean;
}

export interface InspectorCategory {
  name: string;
  collapsed: boolean;
  properties: InspectorProperty[];
}

export class InspectorPanel implements EditorPanel {
  id = 'inspector';
  type: PanelType = 'inspector';
  title = 'Inspector';
  private categories: InspectorCategory[];
  private targetId: string | null;
  private targetType: string;
  private searchQuery: string;
  private modifiedProperties: Set<string>;

  constructor() {
    this.categories = [];
    this.targetId = null;
    this.targetType = '';
    this.searchQuery = '';
    this.modifiedProperties = new Set();
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  inspect(targetId: string, targetType: string): void {
    this.targetId = targetId;
    this.targetType = targetType;
    this.modifiedProperties = new Set();
  }

  clear(): void {
    this.targetId = null;
    this.targetType = '';
    this.categories = [];
    this.modifiedProperties = new Set();
  }

  getTarget(): { id: string; type: string } | null {
    if (!this.targetId) return null;
    return { id: this.targetId, type: this.targetType };
  }

  setCategories(categories: InspectorCategory[]): void {
    this.categories = categories.map((cat) => ({
      ...cat,
      properties: cat.properties.map((p) => ({ ...p })),
    }));
  }

  updateProperty(categoryIndex: number, propertyIndex: number, value: unknown): void {
    if (categoryIndex < 0 || categoryIndex >= this.categories.length) return;
    const category = this.categories[categoryIndex];
    if (propertyIndex < 0 || propertyIndex >= category.properties.length) return;
    const prop = category.properties[propertyIndex];

    const updatedProps = [...category.properties];
    updatedProps[propertyIndex] = { ...prop, value };

    const updatedCategories = [...this.categories];
    updatedCategories[categoryIndex] = { ...category, properties: updatedProps };
    this.categories = updatedCategories;

    this.modifiedProperties = new Set(this.modifiedProperties);
    this.modifiedProperties.add(prop.name);
  }

  resetProperty(categoryIndex: number, propertyIndex: number): void {
    if (categoryIndex < 0 || categoryIndex >= this.categories.length) return;
    const category = this.categories[categoryIndex];
    if (propertyIndex < 0 || propertyIndex >= category.properties.length) return;
    const prop = category.properties[propertyIndex];

    const updatedProps = [...category.properties];
    updatedProps[propertyIndex] = { ...prop, value: prop.defaultValue };

    const updatedCategories = [...this.categories];
    updatedCategories[categoryIndex] = { ...category, properties: updatedProps };
    this.categories = updatedCategories;

    this.modifiedProperties = new Set(this.modifiedProperties);
    this.modifiedProperties.delete(prop.name);
  }

  resetAll(): void {
    this.categories = this.categories.map((cat) => ({
      ...cat,
      properties: cat.properties.map((p) => ({ ...p, value: p.defaultValue })),
    }));
    this.modifiedProperties = new Set();
  }

  collapseCategory(index: number): void {
    if (index < 0 || index >= this.categories.length) return;
    const updated = [...this.categories];
    updated[index] = { ...updated[index], collapsed: true };
    this.categories = updated;
  }

  expandCategory(index: number): void {
    if (index < 0 || index >= this.categories.length) return;
    const updated = [...this.categories];
    updated[index] = { ...updated[index], collapsed: false };
    this.categories = updated;
  }

  search(query: string): void {
    this.searchQuery = query;
  }

  getModifiedProperties(): InspectorProperty[] {
    const result: InspectorProperty[] = [];
    for (const cat of this.categories) {
      for (const prop of cat.properties) {
        if (this.modifiedProperties.has(prop.name)) {
          result.push(prop);
        }
      }
    }
    return result;
  }

  hasModifications(): boolean {
    return this.modifiedProperties.size > 0;
  }

  getCategories(): InspectorCategory[] {
    if (!this.searchQuery) {
      return this.categories.map((cat) => ({
        ...cat,
        properties: cat.properties.map((p) => ({ ...p })),
      }));
    }
    const lower = this.searchQuery.toLowerCase();
    return this.categories
      .map((cat) => ({
        ...cat,
        properties: cat.properties.filter(
          (p) => p.name.toLowerCase().includes(lower) || p.label.toLowerCase().includes(lower),
        ),
      }))
      .filter((cat) => cat.properties.length > 0);
  }

  getSearchQuery(): string {
    return this.searchQuery;
  }
}
