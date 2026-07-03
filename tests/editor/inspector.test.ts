import { describe, it, expect } from 'vitest';
import { InspectorPanel, InspectorCategory, InspectorProperty } from '../../src/editor/inspector';

function createCategory(name: string, props: Partial<InspectorProperty>[] = []): InspectorCategory {
  return {
    name,
    collapsed: false,
    properties: props.map((p) => ({
      name: p.name || 'prop',
      label: p.label || 'Property',
      type: p.type || 'string',
      value: p.value ?? '',
      defaultValue: p.defaultValue ?? '',
      options: p.options,
      min: p.min,
      max: p.max,
      step: p.step,
      description: p.description,
      readonly: p.readonly || false,
    })),
  };
}

describe('InspectorPanel', () => {
  it('initializes with empty state', () => {
    const ip = new InspectorPanel();
    expect(ip.getTarget()).toBeNull();
    expect(ip.getCategories()).toEqual([]);
    expect(ip.hasModifications()).toBe(false);
  });

  it('inspects a target', () => {
    const ip = new InspectorPanel();
    ip.inspect('obj-1', 'Sprite');
    const target = ip.getTarget();
    expect(target).not.toBeNull();
    expect(target!.id).toBe('obj-1');
    expect(target!.type).toBe('Sprite');
  });

  it('clears inspection', () => {
    const ip = new InspectorPanel();
    ip.inspect('obj-1', 'Sprite');
    ip.clear();
    expect(ip.getTarget()).toBeNull();
  });

  it('sets categories', () => {
    const ip = new InspectorPanel();
    const cats = [
      createCategory('Transform', [
        { name: 'x', label: 'X', type: 'number', value: 10, defaultValue: 0 },
      ]),
    ];
    ip.setCategories(cats);
    expect(ip.getCategories().length).toBe(1);
    expect(ip.getCategories()[0].name).toBe('Transform');
  });

  it('updates a property', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Transform', [
        { name: 'x', label: 'X', type: 'number', value: 0, defaultValue: 0 },
      ]),
    ]);
    ip.updateProperty(0, 0, 42);
    expect(ip.getCategories()[0].properties[0].value).toBe(42);
    expect(ip.hasModifications()).toBe(true);
  });

  it('resets a property to default', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Transform', [
        { name: 'x', label: 'X', type: 'number', value: 42, defaultValue: 0 },
      ]),
    ]);
    ip.updateProperty(0, 0, 42);
    ip.resetProperty(0, 0);
    expect(ip.getCategories()[0].properties[0].value).toBe(0);
  });

  it('resets all properties', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Transform', [
        { name: 'x', label: 'X', type: 'number', value: 42, defaultValue: 0 },
        { name: 'y', label: 'Y', type: 'number', value: 99, defaultValue: 0 },
      ]),
    ]);
    ip.updateProperty(0, 0, 42);
    ip.updateProperty(0, 1, 99);
    ip.resetAll();
    expect(ip.hasModifications()).toBe(false);
    expect(ip.getCategories()[0].properties[0].value).toBe(0);
    expect(ip.getCategories()[0].properties[1].value).toBe(0);
  });

  it('handles invalid category index', () => {
    const ip = new InspectorPanel();
    ip.setCategories([createCategory('Test', [{ name: 'p', label: 'P', type: 'string', value: 'a', defaultValue: '' }])]);
    ip.updateProperty(-1, 0, 'x');
    ip.updateProperty(99, 0, 'x');
    ip.resetProperty(-1, 0);
    expect(ip.getCategories()[0].properties[0].value).toBe('a');
  });

  it('handles invalid property index', () => {
    const ip = new InspectorPanel();
    ip.setCategories([createCategory('Test', [{ name: 'p', label: 'P', type: 'string', value: 'a', defaultValue: '' }])]);
    ip.updateProperty(0, -1, 'x');
    ip.updateProperty(0, 99, 'x');
    ip.resetProperty(0, -1);
    expect(ip.getCategories()[0].properties[0].value).toBe('a');
  });

  it('collapses and expands categories', () => {
    const ip = new InspectorPanel();
    ip.setCategories([createCategory('Test')]);
    ip.collapseCategory(0);
    expect(ip.getCategories()[0].collapsed).toBe(true);
    ip.expandCategory(0);
    expect(ip.getCategories()[0].collapsed).toBe(false);
  });

  it('handles collapse on invalid index', () => {
    const ip = new InspectorPanel();
    ip.collapseCategory(-1);
    ip.collapseCategory(99);
    expect(ip.getCategories()).toEqual([]);
  });

  it('filters properties by search', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Transform', [
        { name: 'positionX', label: 'Position X', type: 'number', value: 0, defaultValue: 0 },
        { name: 'scale', label: 'Scale', type: 'number', value: 1, defaultValue: 1 },
        { name: 'color', label: 'Color', type: 'color', value: '#fff', defaultValue: '#fff' },
      ]),
    ]);
    ip.search('position');
    const cats = ip.getCategories();
    expect(cats.length).toBe(1);
    expect(cats[0].properties.length).toBe(1);
    expect(cats[0].properties[0].name).toBe('positionX');
  });

  it('removes category when all properties filtered out', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Transform', [
        { name: 'posX', label: 'Pos X', type: 'number', value: 0, defaultValue: 0 },
      ]),
      createCategory('Material', [
        { name: 'albedo', label: 'Albedo', type: 'color', value: '#fff', defaultValue: '#fff' },
      ]),
    ]);
    ip.search('albedo');
    const cats = ip.getCategories();
    expect(cats.length).toBe(1);
    expect(cats[0].name).toBe('Material');
  });

  it('returns modified properties', () => {
    const ip = new InspectorPanel();
    ip.setCategories([
      createCategory('Test', [
        { name: 'a', label: 'A', type: 'string', value: '', defaultValue: '' },
        { name: 'b', label: 'B', type: 'number', value: 0, defaultValue: 0 },
      ]),
    ]);
    ip.updateProperty(0, 1, 42);
    const modified = ip.getModifiedProperties();
    expect(modified.length).toBe(1);
    expect(modified[0].name).toBe('b');
  });

  it('preserves immutability when setting categories', () => {
    const ip = new InspectorPanel();
    const original = [createCategory('Test', [{ name: 'p', label: 'P', type: 'string', value: 'val', defaultValue: '' }])];
    ip.setCategories(original);
    original[0].properties[0].value = 'changed';
    expect(ip.getCategories()[0].properties[0].value).toBe('val');
  });

  it('tracks modifications after property updates', () => {
    const ip = new InspectorPanel();
    ip.setCategories([createCategory('Test', [{ name: 'p', label: 'P', type: 'string', value: 'a', defaultValue: 'a' }])]);
    expect(ip.hasModifications()).toBe(false);
    ip.updateProperty(0, 0, 'b');
    expect(ip.hasModifications()).toBe(true);
    ip.resetProperty(0, 0);
    expect(ip.hasModifications()).toBe(false);
  });

  it('maintains search query state', () => {
    const ip = new InspectorPanel();
    expect(ip.getSearchQuery()).toBe('');
    ip.search('test');
    expect(ip.getSearchQuery()).toBe('test');
  });

  it('handles readonly properties', () => {
    const ip = new InspectorPanel();
    ip.setCategories([createCategory('Test', [{ name: 'p', label: 'P', type: 'string', value: 'readonly', defaultValue: 'readonly', readonly: true }])]);
    expect(ip.getCategories()[0].properties[0].readonly).toBe(true);
  });
});
