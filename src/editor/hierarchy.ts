import { EditorPanel, PanelType } from './index';

export interface HierarchyNode {
  id: string;
  name: string;
  type: string;
  children: HierarchyNode[];
  expanded: boolean;
  visible: boolean;
  icon?: string;
  color?: string;
}

export class HierarchyPanel implements EditorPanel {
  id = 'hierarchy';
  type: PanelType = 'hierarchy';
  title = 'Hierarchy';
  private rootNodes: HierarchyNode[];
  private selectedId: string | null;
  private filterText: string;
  private dragOverId: string | null;

  constructor() {
    this.rootNodes = [];
    this.selectedId = null;
    this.filterText = '';
    this.dragOverId = null;
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  setNodes(nodes: HierarchyNode[]): void {
    this.rootNodes = nodes.map((n) => this.deepCloneNode(n));
  }

  addNode(node: HierarchyNode, parentId?: string): void {
    const newNode = this.deepCloneNode(node);
    if (!parentId) {
      this.rootNodes = [...this.rootNodes, newNode];
      return;
    }
    this.rootNodes = this.rootNodes.map((n) => this.addChildToNode(n, parentId, newNode));
  }

  removeNode(id: string): void {
    this.rootNodes = this.rootNodes
      .map((n) => this.removeChildFromNode(n, id))
      .filter((n) => n.id !== id);
    if (this.selectedId === id) {
      this.selectedId = null;
    }
  }

  updateNode(id: string, updates: Partial<HierarchyNode>): void {
    this.rootNodes = this.rootNodes.map((n) => this.updateNodeInTree(n, id, updates));
  }

  selectNode(id: string): void {
    this.selectedId = id;
  }

  deselect(): void {
    this.selectedId = null;
  }

  getSelectedId(): string | null {
    return this.selectedId;
  }

  expandAll(): void {
    this.rootNodes = this.rootNodes.map((n) => this.setNodeExpanded(n, true));
  }

  collapseAll(): void {
    this.rootNodes = this.rootNodes.map((n) => this.setNodeExpanded(n, false));
  }

  expandTo(id: string): void {
    this.rootNodes = this.rootNodes.map((n) => this.expandPathToNode(n, id));
  }

  filter(query: string): void {
    this.filterText = query;
  }

  moveNode(id: string, newParentId: string, index?: number): void {
    const sourceNode = this.findNodeById(id);
    if (!sourceNode) return;

    const cleaned = this.rootNodes
      .map((n) => this.removeChildFromNode(n, id))
      .filter((n) => n.id !== id);

    const moved = { ...sourceNode };
    if (newParentId === 'root') {
      if (typeof index === 'number') {
        cleaned.splice(index, 0, moved);
      } else {
        cleaned.push(moved);
      }
      this.rootNodes = cleaned;
    } else {
      this.rootNodes = cleaned.map((n) => {
        const updated = this.addChildToNodeAt(n, newParentId, moved, index);
        if (updated) return updated;
        return n;
      });
    }
  }

  getNode(id: string): HierarchyNode | undefined {
    return this.findNodeById(id);
  }

  getRootNodes(): HierarchyNode[] {
    if (!this.filterText) return this.rootNodes.map((n) => this.deepCloneNode(n));
    const lower = this.filterText.toLowerCase();
    return this.rootNodes
      .map((n) => this.filterNodeTree(n, lower))
      .filter((n): n is HierarchyNode => n !== null);
  }

  getDragOverId(): string | null {
    return this.dragOverId;
  }

  setDragOverId(id: string | null): void {
    this.dragOverId = id;
  }

  private deepCloneNode(node: HierarchyNode): HierarchyNode {
    return {
      ...node,
      children: node.children.map((c) => this.deepCloneNode(c)),
    };
  }

  private findNodeById(id: string, nodes?: HierarchyNode[]): HierarchyNode | undefined {
    const list = nodes || this.rootNodes;
    for (const n of list) {
      if (n.id === id) return n;
      const found = this.findNodeById(id, n.children);
      if (found) return found;
    }
    return undefined;
  }

  private addChildToNode(node: HierarchyNode, parentId: string, child: HierarchyNode): HierarchyNode {
    if (node.id === parentId) {
      return { ...node, children: [...node.children, child] };
    }
    return { ...node, children: node.children.map((c) => this.addChildToNode(c, parentId, child)) };
  }

  private addChildToNodeAt(node: HierarchyNode, parentId: string, child: HierarchyNode, index?: number): HierarchyNode | null {
    if (node.id === parentId) {
      const children = [...node.children];
      if (typeof index === 'number' && index >= 0 && index <= children.length) {
        children.splice(index, 0, child);
      } else {
        children.push(child);
      }
      return { ...node, children };
    }
    const updatedChildren = node.children
      .map((c) => this.addChildToNodeAt(c, parentId, child, index))
      .filter((c): c is HierarchyNode => c !== null);
    if (updatedChildren.length > 0 || node.children.length === 0) {
      return { ...node, children: updatedChildren.length > 0 ? updatedChildren : node.children };
    }
    return null;
  }

  private removeChildFromNode(node: HierarchyNode, id: string): HierarchyNode {
    return {
      ...node,
      children: node.children
        .filter((c) => c.id !== id)
        .map((c) => this.removeChildFromNode(c, id)),
    };
  }

  private updateNodeInTree(node: HierarchyNode, id: string, updates: Partial<HierarchyNode>): HierarchyNode {
    if (node.id === id) {
      return { ...node, ...updates, children: node.children };
    }
    return { ...node, children: node.children.map((c) => this.updateNodeInTree(c, id, updates)) };
  }

  private setNodeExpanded(node: HierarchyNode, expanded: boolean): HierarchyNode {
    return {
      ...node,
      expanded,
      children: node.children.map((c) => this.setNodeExpanded(c, expanded)),
    };
  }

  private expandPathToNode(node: HierarchyNode, targetId: string): HierarchyNode {
    if (node.id === targetId) return node;
    const hasTarget = this.findNodeById(targetId, node.children);
    return {
      ...node,
      expanded: hasTarget ? true : node.expanded,
      children: node.children.map((c) => this.expandPathToNode(c, targetId)),
    };
  }

  private filterNodeTree(node: HierarchyNode, query: string): HierarchyNode | null {
    const filteredChildren = node.children
      .map((c) => this.filterNodeTree(c, query))
      .filter((c): c is HierarchyNode => c !== null);

    const nameMatch = node.name.toLowerCase().includes(query);
    const typeMatch = node.type.toLowerCase().includes(query);

    if (nameMatch || typeMatch || filteredChildren.length > 0) {
      return {
        ...node,
        expanded: filteredChildren.length > 0 ? true : node.expanded,
        children: filteredChildren,
      };
    }
    return null;
  }
}
