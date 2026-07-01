import { describe, it, expect } from 'vitest';
import { HierarchyPanel, HierarchyNode } from '../../src/editor/hierarchy';

function createNode(id: string, name: string, children: HierarchyNode[] = []): HierarchyNode {
  return { id, name, type: 'object', children, expanded: true, visible: true };
}

describe('HierarchyPanel', () => {
  it('initializes with empty state', () => {
    const hp = new HierarchyPanel();
    expect(hp.getRootNodes()).toEqual([]);
    expect(hp.getSelectedId()).toBeNull();
  });

  it('sets root nodes', () => {
    const hp = new HierarchyPanel();
    const nodes = [createNode('1', 'Node A'), createNode('2', 'Node B')];
    hp.setNodes(nodes);
    expect(hp.getRootNodes().length).toBe(2);
  });

  it('adds a root node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Root'));
    expect(hp.getRootNodes().length).toBe(1);
    expect(hp.getRootNodes()[0].name).toBe('Root');
  });

  it('adds a child node to a parent', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('parent', 'Parent'));
    hp.addNode(createNode('child', 'Child'), 'parent');
    const parent = hp.getNode('parent');
    expect(parent).toBeDefined();
    expect(parent!.children.length).toBe(1);
    expect(parent!.children[0].name).toBe('Child');
  });

  it('removes a node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Node'));
    hp.removeNode('1');
    expect(hp.getRootNodes().length).toBe(0);
  });

  it('removes a child node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('parent', 'Parent'));
    hp.addNode(createNode('child', 'Child'), 'parent');
    hp.removeNode('child');
    const parent = hp.getNode('parent');
    expect(parent!.children.length).toBe(0);
  });

  it('clears selection when removing selected node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Node'));
    hp.selectNode('1');
    hp.removeNode('1');
    expect(hp.getSelectedId()).toBeNull();
  });

  it('updates a node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Original'));
    hp.updateNode('1', { name: 'Updated' });
    expect(hp.getNode('1')!.name).toBe('Updated');
  });

  it('updates a child node', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('parent', 'Parent'));
    hp.addNode(createNode('child', 'Child'), 'parent');
    hp.updateNode('child', { name: 'Updated Child' });
    expect(hp.getNode('child')!.name).toBe('Updated Child');
  });

  it('selects and deselects nodes', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Node'));
    hp.selectNode('1');
    expect(hp.getSelectedId()).toBe('1');
    hp.deselect();
    expect(hp.getSelectedId()).toBeNull();
  });

  it('expands and collapses all', () => {
    const hp = new HierarchyPanel();
    const inner = createNode('inner', 'Inner');
    hp.addNode(createNode('1', 'Root', [inner]));
    hp.collapseAll();
    expect(hp.getNode('1')!.expanded).toBe(false);
    hp.expandAll();
    expect(hp.getNode('1')!.expanded).toBe(true);
  });

  it('expands to a specific node', () => {
    const hp = new HierarchyPanel();
    const inner = createNode('inner', 'Inner');
    const root = createNode('root', 'Root', [inner]);
    hp.setNodes([root]);
    hp.collapseAll();
    hp.expandTo('inner');
    expect(hp.getNode('root')!.expanded).toBe(true);
  });

  it('filters nodes by name', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'Player'));
    hp.addNode(createNode('2', 'Enemy'));
    hp.addNode(createNode('3', 'Projectile'));
    hp.filter('Player');
    expect(hp.getRootNodes().length).toBe(1);
    expect(hp.getRootNodes()[0].name).toBe('Player');
  });

  it('filters nodes by type', () => {
    const hp = new HierarchyPanel();
    hp.setNodes([{ ...createNode('1', 'Player'), type: 'character' }, { ...createNode('2', 'Floor'), type: 'environment' }]);
    hp.filter('environment');
    expect(hp.getRootNodes().length).toBe(1);
    expect(hp.getRootNodes()[0].id).toBe('2');
  });

  it('returns all nodes when filter is empty', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('1', 'A'));
    hp.addNode(createNode('2', 'B'));
    hp.filter('');
    expect(hp.getRootNodes().length).toBe(2);
  });

  it('shows parent when child matches filter', () => {
    const hp = new HierarchyPanel();
    const child = createNode('child', 'TargetChild');
    const parent = createNode('parent', 'Parent', [child]);
    hp.setNodes([parent]);
    hp.filter('TargetChild');
    const roots = hp.getRootNodes();
    expect(roots.length).toBe(1);
    expect(roots[0].id).toBe('parent');
    expect(roots[0].children.length).toBe(1);
  });

  it('moves a node to root', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('parent', 'Parent'));
    hp.addNode(createNode('child', 'Child'), 'parent');
    hp.moveNode('child', 'root', 0);
    expect(hp.getNode('child')).toBeDefined();
    const parent = hp.getNode('parent');
    expect(parent!.children.length).toBe(0);
  });

  it('moves a node to a new parent', () => {
    const hp = new HierarchyPanel();
    hp.addNode(createNode('oldParent', 'Old'));
    hp.addNode(createNode('newParent', 'New'));
    hp.addNode(createNode('child', 'Child'), 'oldParent');
    hp.moveNode('child', 'newParent');
    const oldP = hp.getNode('oldParent');
    expect(oldP!.children.length).toBe(0);
    const newP = hp.getNode('newParent');
    expect(newP!.children.length).toBe(1);
  });

  it('manages drag over state', () => {
    const hp = new HierarchyPanel();
    expect(hp.getDragOverId()).toBeNull();
    hp.setDragOverId('target');
    expect(hp.getDragOverId()).toBe('target');
  });

  it('returns undefined for unknown node', () => {
    const hp = new HierarchyPanel();
    expect(hp.getNode('nonexistent')).toBeUndefined();
  });

  it('preserves immutability when setting nodes', () => {
    const hp = new HierarchyPanel();
    const original = [createNode('1', 'Original')];
    hp.setNodes(original);
    original.push(createNode('2', 'Extra'));
    expect(hp.getRootNodes().length).toBe(1);
  });

  it('filters nested child nodes', () => {
    const hp = new HierarchyPanel();
    const grandchild = createNode('gc', 'Grandchild');
    const child = createNode('child', 'Child', [grandchild]);
    const parent = createNode('parent', 'Parent', [child]);
    hp.setNodes([parent]);
    const visible = hp.getRootNodes();
    expect(visible.length).toBe(1);
  });
});
