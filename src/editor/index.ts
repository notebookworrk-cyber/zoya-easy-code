export interface EditorConfig {
  title: string;
  width: number;
  height: number;
  theme: 'dark' | 'light' | 'high-contrast';
  language: string;
  autoSaveInterval: number;
  projectDir: string;
  layout: LayoutConfig;
  showGrid: boolean;
  snapToGrid: boolean;
  gridSize: number;
}

export interface LayoutConfig {
  panels: PanelConfig[];
  activePanel: string;
  sidebarWidth: number;
  bottomPanelHeight: number;
}

export interface PanelConfig {
  id: string;
  type: PanelType;
  title: string;
  visible: boolean;
  position: 'left' | 'right' | 'bottom' | 'center' | 'floating';
  width?: number;
  height?: number;
}

export type PanelType =
  | 'hierarchy'
  | 'inspector'
  | 'scene'
  | 'game'
  | 'assets'
  | 'animation'
  | 'material'
  | 'physics'
  | 'console'
  | 'profiler'
  | 'code'
  | 'terminal'
  | 'preview';

export interface EditorProject {
  name: string;
  path: string;
  type: 'game2d' | 'game3d' | 'ai-app' | 'web-api' | 'desktop' | 'library';
  openedFiles: string[];
  activeFile: string;
  scenes: string[];
  assets: string[];
  lastOpened: Date;
}

export interface EditorPanel {
  id: string;
  type: PanelType;
  title: string;
  icon?: string;

  init(): void;
  render(): void;
  update(dt: number): void;
  destroy(): void;
  onResize(width: number, height: number): void;
  onFocus(): void;
  onBlur(): void;
}

export interface EditorAction {
  type: string;
  description: string;
  timestamp: Date;
  undo(): void;
  redo(): void;
}

export interface ConsoleEntry {
  id: number;
  timestamp: Date;
  level: 'info' | 'warning' | 'error';
  message: string;
  source?: string;
  stack?: string;
}

export interface ProfilerSample {
  frameTime: number;
  updateTime: number;
  renderTime: number;
  physicsTime: number;
  gcTime: number;
  drawCalls: number;
  triangleCount: number;
  memoryUsage: number;
  objectCount: number;
}

const DEFAULT_CONFIG: EditorConfig = {
  title: 'Zoya Editor',
  width: 1920,
  height: 1080,
  theme: 'dark',
  language: 'zoya',
  autoSaveInterval: 30000,
  projectDir: '',
  layout: {
    panels: [
      { id: 'hierarchy', type: 'hierarchy', title: 'Hierarchy', visible: true, position: 'left', width: 250 },
      { id: 'inspector', type: 'inspector', title: 'Inspector', visible: true, position: 'right', width: 300 },
      { id: 'scene-view', type: 'scene', title: 'Scene View', visible: true, position: 'center' },
      { id: 'game-view', type: 'game', title: 'Game View', visible: false, position: 'center' },
      { id: 'asset-browser', type: 'assets', title: 'Asset Browser', visible: true, position: 'left', width: 250 },
      { id: 'console', type: 'console', title: 'Console', visible: true, position: 'bottom', height: 200 },
      { id: 'profiler', type: 'profiler', title: 'Profiler', visible: false, position: 'bottom', height: 200 },
    ],
    activePanel: 'scene-view',
    sidebarWidth: 250,
    bottomPanelHeight: 200,
  },
  showGrid: true,
  snapToGrid: true,
  gridSize: 16,
};

export class Editor {
  private config: EditorConfig;
  private project: EditorProject | null;
  private panels: Map<string, EditorPanel>;
  private sceneView: SceneView;
  private gameView: GameView;
  private assetBrowser: AssetBrowser;
  private editorConsole: EditorConsole;
  private profiler: EditorProfiler;
  private undoStack: EditorAction[];
  private redoStack: EditorAction[];
  private modified: boolean;
  private running: boolean;

  constructor(config?: Partial<EditorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config, layout: { ...DEFAULT_CONFIG.layout, ...config?.layout } };
    this.project = null;
    this.panels = new Map();
    this.sceneView = new SceneView();
    this.gameView = new GameView();
    this.assetBrowser = new AssetBrowser();
    this.editorConsole = new EditorConsole();
    this.profiler = new EditorProfiler();
    this.undoStack = [];
    this.redoStack = [];
    this.modified = false;
    this.running = false;

    this.registerPanel(this.sceneView);
    this.registerPanel(this.gameView);
    this.registerPanel(this.assetBrowser);
    this.registerPanel(this.editorConsole);
    this.registerPanel(this.profiler);
  }

  openProject(path: string): void {
    this.project = {
      name: path.split(/[/\\]/).pop() || 'untitled',
      path,
      type: 'game2d',
      openedFiles: [],
      activeFile: '',
      scenes: [],
      assets: [],
      lastOpened: new Date(),
    };
  }

  createProject(name: string, type: EditorProject['type'], path: string): void {
    this.project = {
      name,
      path,
      type,
      openedFiles: [],
      activeFile: '',
      scenes: [],
      assets: [],
      lastOpened: new Date(),
    };
  }

  saveProject(): void {
    if (!this.project) return;
    this.project = { ...this.project, lastOpened: new Date() };
    this.modified = false;
  }

  closeProject(): void {
    this.project = null;
    this.undoStack = [];
    this.redoStack = [];
    this.modified = false;
  }

  getProject(): EditorProject | null {
    return this.project;
  }

  registerPanel(panel: EditorPanel): void {
    this.panels.set(panel.id, panel);
  }

  getPanel(id: string): EditorPanel | undefined {
    return this.panels.get(id);
  }

  showPanel(id: string): void {
    const cfg = this.config.layout.panels.find((p) => p.id === id);
    if (cfg) {
      const updated = [...this.config.layout.panels];
      const idx = updated.indexOf(cfg);
      updated[idx] = { ...cfg, visible: true };
      this.config = {
        ...this.config,
        layout: { ...this.config.layout, panels: updated },
      };
    }
  }

  hidePanel(id: string): void {
    const cfg = this.config.layout.panels.find((p) => p.id === id);
    if (cfg) {
      const updated = [...this.config.layout.panels];
      const idx = updated.indexOf(cfg);
      updated[idx] = { ...cfg, visible: false };
      this.config = {
        ...this.config,
        layout: { ...this.config.layout, panels: updated },
      };
    }
  }

  togglePanel(id: string): void {
    const cfg = this.config.layout.panels.find((p) => p.id === id);
    if (cfg) {
      if (cfg.visible) {
        this.hidePanel(id);
      } else {
        this.showPanel(id);
      }
    }
  }

  focusPanel(id: string): void {
    this.config = {
      ...this.config,
      layout: { ...this.config.layout, activePanel: id },
    };
  }

  undo(): void {
    const action = this.undoStack.pop();
    if (action) {
      action.undo();
      this.redoStack.push(action);
      this.modified = true;
    }
  }

  redo(): void {
    const action = this.redoStack.pop();
    if (action) {
      action.redo();
      this.undoStack.push(action);
      this.modified = true;
    }
  }

  pushAction(action: EditorAction): void {
    this.undoStack.push(action);
    this.redoStack = [];
    this.modified = true;
  }

  isModified(): boolean {
    return this.modified;
  }

  select(_objectId: string): void {

  }

  deselect(): void {

  }

  getSelection(): string | null {
    return null;
  }

  update(dt: number): void {
    if (!this.running) return;
    for (const panel of this.panels.values()) {
      panel.update(dt);
    }
  }

  render(): void {
    if (!this.running) return;
    for (const panel of this.panels.values()) {
      panel.render();
    }
  }

  updateConfig(config: Partial<EditorConfig>): void {
    this.config = { ...this.config, ...config };
    if (config.layout) {
      this.config = {
        ...this.config,
        layout: { ...this.config.layout, ...config.layout },
      };
    }
  }

  getConfig(): EditorConfig {
    return { ...this.config, layout: { ...this.config.layout, panels: [...this.config.layout.panels.map((p) => ({ ...p }))] } };
  }

  init(): void {
    this.running = true;
    for (const panel of this.panels.values()) {
      panel.init();
    }
  }

  shutdown(): void {
    this.running = false;
    for (const panel of this.panels.values()) {
      panel.destroy();
    }
    this.panels.clear();
  }

  isRunning(): boolean {
    return this.running;
  }
}

export class SceneView implements EditorPanel {
  id = 'scene-view';
  type: PanelType = 'scene';
  title = 'Scene View';
  private camera: { x: number; y: number; zoom: number };
  private selectedObjects: string[];
  private gridVisible: boolean;
  private snapEnabled: boolean;
  private gizmoMode: 'translate' | 'rotate' | 'scale';

  constructor() {
    this.camera = { x: 0, y: 0, zoom: 1 };
    this.selectedObjects = [];
    this.gridVisible = true;
    this.snapEnabled = true;
    this.gizmoMode = 'translate';
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  zoomIn(): void {
    this.camera = { ...this.camera, zoom: Math.min(this.camera.zoom * 1.25, 10) };
  }

  zoomOut(): void {
    this.camera = { ...this.camera, zoom: Math.max(this.camera.zoom / 1.25, 0.1) };
  }

  resetCamera(): void {
    this.camera = { x: 0, y: 0, zoom: 1 };
  }

  setGizmoMode(mode: 'translate' | 'rotate' | 'scale'): void {
    this.gizmoMode = mode;
  }

  focusOn(objectId: string): void {
    this.selectedObjects = [objectId];
  }

  setGridVisible(visible: boolean): void {
    this.gridVisible = visible;
  }

  setSnapEnabled(enabled: boolean): void {
    this.snapEnabled = enabled;
  }

  getCamera(): { x: number; y: number; zoom: number } {
    return { ...this.camera };
  }

  getSelectedObjects(): string[] {
    return [...this.selectedObjects];
  }

  isGridVisible(): boolean {
    return this.gridVisible;
  }

  isSnapEnabled(): boolean {
    return this.snapEnabled;
  }

  getGizmoMode(): 'translate' | 'rotate' | 'scale' {
    return this.gizmoMode;
  }
}

export class GameView implements EditorPanel {
  id = 'game-view';
  type: PanelType = 'game';
  title = 'Game View';
  private playing: boolean;
  private paused: boolean;
  private fps: number;
  private frameCount: number;
  private lastTime: number;

  constructor() {
    this.playing = false;
    this.paused = false;
    this.fps = 0;
    this.frameCount = 0;
    this.lastTime = 0;
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void {
    if (!this.playing || this.paused) return;
    this.frameCount++;
    const now = Date.now();
    if (now - this.lastTime >= 1000) {
      this.fps = this.frameCount;
      this.frameCount = 0;
      this.lastTime = now;
    }
  }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  play(): void {
    this.playing = true;
    this.paused = false;
    this.frameCount = 0;
    this.lastTime = Date.now();
  }

  pause(): void {
    this.paused = true;
  }

  stop(): void {
    this.playing = false;
    this.paused = false;
    this.fps = 0;
    this.frameCount = 0;
  }

  restart(): void {
    this.stop();
    this.play();
  }

  isPlaying(): boolean {
    return this.playing;
  }

  isPaused(): boolean {
    return this.paused;
  }

  getFPS(): number {
    return this.fps;
  }
}

export class AssetBrowser implements EditorPanel {
  id = 'asset-browser';
  type: PanelType = 'assets';
  title = 'Asset Browser';
  private currentPath: string;
  private selectedAsset: string | null;
  private viewMode: 'grid' | 'list';
  private searchQuery: string;
  private files: string[];

  constructor() {
    this.currentPath = '/';
    this.selectedAsset = null;
    this.viewMode = 'grid';
    this.searchQuery = '';
    this.files = [];
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  navigateTo(path: string): void {
    this.currentPath = path;
    this.selectedAsset = null;
  }

  navigateUp(): void {
    const parts = this.currentPath.replace(/\\/g, '/').split('/').filter(Boolean);
    if (parts.length > 0) {
      parts.pop();
      this.currentPath = '/' + parts.join('/');
    } else {
      this.currentPath = '/';
    }
    this.selectedAsset = null;
  }

  refresh(): void {
    this.files = [...this.files];
  }

  import(_path: string): void {

  }

  delete(assetPath: string): void {
    this.files = this.files.filter((f) => f !== assetPath);
    if (this.selectedAsset === assetPath) {
      this.selectedAsset = null;
    }
  }

  rename(oldPath: string, newPath: string): void {
    this.files = this.files.map((f) => (f === oldPath ? newPath : f));
  }

  search(query: string): void {
    this.searchQuery = query;
  }

  setViewMode(mode: 'grid' | 'list'): void {
    this.viewMode = mode;
  }

  getSelectedAsset(): string | null {
    return this.selectedAsset;
  }

  getCurrentPath(): string {
    return this.currentPath;
  }

  getFiles(): string[] {
    if (!this.searchQuery) return [...this.files];
    const lower = this.searchQuery.toLowerCase();
    return this.files.filter((f) => f.toLowerCase().includes(lower));
  }

  getViewMode(): 'grid' | 'list' {
    return this.viewMode;
  }
}

export class EditorConsole implements EditorPanel {
  id = 'console';
  type: PanelType = 'console';
  title = 'Console';
  private entries: ConsoleEntry[];
  private filterLevel: 'all' | 'info' | 'warning' | 'error';
  private maxEntries: number;
  private autoScroll: boolean;
  private nextId: number;

  constructor() {
    this.entries = [];
    this.filterLevel = 'all';
    this.maxEntries = 1000;
    this.autoScroll = true;
    this.nextId = 0;
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  log(message: string, level: 'info' | 'warning' | 'error' = 'info', source?: string): void {
    const entry: ConsoleEntry = {
      id: this.nextId++,
      timestamp: new Date(),
      level,
      message,
      source,
    };
    this.entries = [...this.entries, entry];
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(this.entries.length - this.maxEntries);
    }
  }

  warn(message: string, source?: string): void {
    this.log(message, 'warning', source);
  }

  error(message: string, source?: string): void {
    const entry: ConsoleEntry = {
      id: this.nextId++,
      timestamp: new Date(),
      level: 'error',
      message,
      source,
      stack: new Error().stack,
    };
    this.entries = [...this.entries, entry];
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(this.entries.length - this.maxEntries);
    }
  }

  clear(): void {
    this.entries = [];
  }

  setFilter(level: 'all' | 'info' | 'warning' | 'error'): void {
    this.filterLevel = level;
  }

  getEntries(): ConsoleEntry[] {
    if (this.filterLevel === 'all') return [...this.entries];
    return this.entries.filter((e) => e.level === this.filterLevel);
  }

  getEntryCount(): number {
    return this.entries.length;
  }

  export(): string {
    return this.entries
      .map((e) => `[${e.timestamp.toISOString()}] [${e.level.toUpperCase()}] ${e.message}${e.source ? ` (${e.source})` : ''}`)
      .join('\n');
  }

  isAutoScroll(): boolean {
    return this.autoScroll;
  }

  setAutoScroll(scroll: boolean): void {
    this.autoScroll = scroll;
  }

  getFilterLevel(): 'all' | 'info' | 'warning' | 'error' {
    return this.filterLevel;
  }
}

export class EditorProfiler implements EditorPanel {
  id = 'profiler';
  type: PanelType = 'profiler';
  title = 'Profiler';
  private recording: boolean;
  private samples: ProfilerSample[];
  private maxSamples: number;
  private frameTimeHistory: number[];

  constructor() {
    this.recording = false;
    this.samples = [];
    this.maxSamples = 1000;
    this.frameTimeHistory = [];
  }

  init(): void { }
  render(): void { }
  update(_dt: number): void { }
  destroy(): void { }
  onResize(_width: number, _height: number): void { }
  onFocus(): void { }
  onBlur(): void { }

  startRecording(): void {
    this.recording = true;
  }

  stopRecording(): void {
    this.recording = false;
  }

  isRecording(): boolean {
    return this.recording;
  }

  clear(): void {
    this.samples = [];
    this.frameTimeHistory = [];
  }

  recordSample(sample: ProfilerSample): void {
    if (!this.recording) return;
    this.samples = [...this.samples, sample];
    this.frameTimeHistory = [...this.frameTimeHistory, sample.frameTime];
    if (this.samples.length > this.maxSamples) {
      this.samples = this.samples.slice(this.samples.length - this.maxSamples);
      this.frameTimeHistory = this.frameTimeHistory.slice(this.frameTimeHistory.length - this.maxSamples);
    }
  }

  getSamples(): ProfilerSample[] {
    return [...this.samples];
  }

  getAverageFrameTime(): number {
    if (this.frameTimeHistory.length === 0) return 0;
    const sum = this.frameTimeHistory.reduce((a, b) => a + b, 0);
    return sum / this.frameTimeHistory.length;
  }

  getMaxFrameTime(): number {
    if (this.frameTimeHistory.length === 0) return 0;
    return Math.max(...this.frameTimeHistory);
  }

  getMinFrameTime(): number {
    if (this.frameTimeHistory.length === 0) return 0;
    return Math.min(...this.frameTimeHistory);
  }

  getFPS(): number {
    const avg = this.getAverageFrameTime();
    return avg > 0 ? Math.round(1000 / avg) : 0;
  }
}
