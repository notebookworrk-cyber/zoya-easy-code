import { describe, it, expect } from 'vitest';
import {
  Editor,
  EditorPanel,
  EditorAction,
  SceneView,
  GameView,
  AssetBrowser,
  EditorConsole,
  EditorProfiler,
  ProfilerSample,
} from '../../src/editor/index';

describe('Editor', () => {
  it('creates with default config', () => {
    const editor = new Editor();
    const config = editor.getConfig();
    expect(config.title).toBe('Zoya Editor');
    expect(config.theme).toBe('dark');
    expect(config.layout.panels.length).toBeGreaterThan(0);
  });

  it('creates with custom config', () => {
    const editor = new Editor({ title: 'Test Editor', theme: 'light' });
    expect(editor.getConfig().title).toBe('Test Editor');
    expect(editor.getConfig().theme).toBe('light');
  });

  it('is not running initially', () => {
    const editor = new Editor();
    expect(editor.isRunning()).toBe(false);
  });

  it('init starts the editor', () => {
    const editor = new Editor();
    editor.init();
    expect(editor.isRunning()).toBe(true);
  });

  it('shutdown stops the editor', () => {
    const editor = new Editor();
    editor.init();
    editor.shutdown();
    expect(editor.isRunning()).toBe(false);
  });

  it('manages project lifecycle', () => {
    const editor = new Editor();
    expect(editor.getProject()).toBeNull();

    editor.createProject('MyGame', 'game2d', '/projects/mygame');
    const proj = editor.getProject();
    expect(proj).not.toBeNull();
    expect(proj!.name).toBe('MyGame');
    expect(proj!.type).toBe('game2d');

    editor.saveProject();
    expect(editor.isModified()).toBe(false);

    editor.closeProject();
    expect(editor.getProject()).toBeNull();
  });

  it('opens existing project', () => {
    const editor = new Editor();
    editor.openProject('/projects/existing');
    const proj = editor.getProject();
    expect(proj).not.toBeNull();
    expect(proj!.name).toBe('existing');
    expect(proj!.path).toBe('/projects/existing');
  });

  it('registers and retrieves panels', () => {
    const editor = new Editor();
    const panel: EditorPanel = {
      id: 'test-panel',
      type: 'console',
      title: 'Test',
      init: () => {},
      render: () => {},
      update: () => {},
      destroy: () => {},
      onResize: () => {},
      onFocus: () => {},
      onBlur: () => {},
    };
    editor.registerPanel(panel);
    expect(editor.getPanel('test-panel')).toBe(panel);
  });

  it('shows and hides panels', () => {
    const editor = new Editor();
    const panelId = 'hierarchy';
    editor.hidePanel(panelId);
    const panelCfg = editor.getConfig().layout.panels.find(p => p.id === panelId);
    expect(panelCfg!.visible).toBe(false);

    editor.showPanel(panelId);
    const panelCfg2 = editor.getConfig().layout.panels.find(p => p.id === panelId);
    expect(panelCfg2!.visible).toBe(true);
  });

  it('toggles panel visibility', () => {
    const editor = new Editor();
    const panelId = 'inspector';
    const initial = editor.getConfig().layout.panels.find(p => p.id === panelId)!.visible;
    editor.togglePanel(panelId);
    const after = editor.getConfig().layout.panels.find(p => p.id === panelId)!.visible;
    expect(after).toBe(!initial);
  });

  it('focuses a panel', () => {
    const editor = new Editor();
    editor.focusPanel('scene-view');
    expect(editor.getConfig().layout.activePanel).toBe('scene-view');
  });

  it('manages undo/redo stack', () => {
    const editor = new Editor();
    const action1: EditorAction = {
      type: 'move',
      description: 'Move object',
      timestamp: new Date(),
      undo: () => {},
      redo: () => {},
    };
    const action2: EditorAction = {
      type: 'rotate',
      description: 'Rotate object',
      timestamp: new Date(),
      undo: () => {},
      redo: () => {},
    };
    editor.pushAction(action1);
    editor.pushAction(action2);
    expect(editor.isModified()).toBe(true);

    editor.undo();
    expect(editor.isModified()).toBe(true);

    editor.redo();
    expect(editor.isModified()).toBe(true);
  });

  it('updates config', () => {
    const editor = new Editor();
    editor.updateConfig({ title: 'Updated', gridSize: 32 });
    expect(editor.getConfig().title).toBe('Updated');
    expect(editor.getConfig().gridSize).toBe(32);
  });

  it('updates and renders', () => {
    const editor = new Editor();
    editor.init();
    editor.update(0.016);
    editor.render();
    expect(editor.isRunning()).toBe(true);
  });
});

describe('SceneView', () => {
  it('initializes with default state', () => {
    const sv = new SceneView();
    expect(sv.id).toBe('scene-view');
    expect(sv.title).toBe('Scene View');
  });

  it('zooms in and out', () => {
    const sv = new SceneView();
    sv.zoomIn();
    expect(sv.getCamera().zoom).toBeGreaterThan(1);
    sv.zoomOut();
    sv.zoomOut();
    expect(sv.getCamera().zoom).toBeLessThan(1);
  });

  it('resets camera', () => {
    const sv = new SceneView();
    sv.zoomIn();
    sv.resetCamera();
    expect(sv.getCamera().zoom).toBe(1);
    expect(sv.getCamera().x).toBe(0);
    expect(sv.getCamera().y).toBe(0);
  });

  it('sets gizmo mode', () => {
    const sv = new SceneView();
    sv.setGizmoMode('rotate');
    expect(sv.getGizmoMode()).toBe('rotate');
    sv.setGizmoMode('scale');
    expect(sv.getGizmoMode()).toBe('scale');
  });

  it('focuses on object', () => {
    const sv = new SceneView();
    sv.focusOn('obj-1');
    expect(sv.getSelectedObjects()).toContain('obj-1');
  });

  it('toggles grid and snap', () => {
    const sv = new SceneView();
    sv.setGridVisible(false);
    expect(sv.isGridVisible()).toBe(false);
    sv.setSnapEnabled(false);
    expect(sv.isSnapEnabled()).toBe(false);
    sv.setSnapEnabled(true);
    expect(sv.isSnapEnabled()).toBe(true);
  });
});

describe('GameView', () => {
  it('initializes with stopped state', () => {
    const gv = new GameView();
    expect(gv.isPlaying()).toBe(false);
    expect(gv.isPaused()).toBe(false);
  });

  it('plays and stops', () => {
    const gv = new GameView();
    gv.play();
    expect(gv.isPlaying()).toBe(true);
    gv.stop();
    expect(gv.isPlaying()).toBe(false);
  });

  it('pauses and resumes', () => {
    const gv = new GameView();
    gv.play();
    gv.pause();
    expect(gv.isPaused()).toBe(true);
    gv.play();
    expect(gv.isPaused()).toBe(false);
  });

  it('restarts game', () => {
    const gv = new GameView();
    gv.play();
    gv.restart();
    expect(gv.isPlaying()).toBe(true);
  });

  it('updates FPS counter', () => {
    const gv = new GameView();
    gv.play();
    gv.update(0.016);
    gv.update(0.016);
    expect(gv.getFPS()).toBe(0);
    expect(gv.isPlaying()).toBe(true);
  });

  it('does not update when stopped', () => {
    const gv = new GameView();
    gv.update(0.016);
    expect(gv.getFPS()).toBe(0);
  });
});

describe('AssetBrowser', () => {
  it('initializes with root path', () => {
    const ab = new AssetBrowser();
    expect(ab.getCurrentPath()).toBe('/');
    expect(ab.getSelectedAsset()).toBeNull();
  });

  it('navigates to paths', () => {
    const ab = new AssetBrowser();
    ab.navigateTo('/textures/characters');
    expect(ab.getCurrentPath()).toBe('/textures/characters');
  });

  it('navigates up', () => {
    const ab = new AssetBrowser();
    ab.navigateTo('/textures/characters');
    ab.navigateUp();
    expect(ab.getCurrentPath()).toBe('/textures');
    ab.navigateUp();
    expect(ab.getCurrentPath()).toBe('/');
  });

  it('does not navigate above root', () => {
    const ab = new AssetBrowser();
    ab.navigateUp();
    expect(ab.getCurrentPath()).toBe('/');
  });

  it('toggles view mode', () => {
    const ab = new AssetBrowser();
    expect(ab.getViewMode()).toBe('grid');
    ab.setViewMode('list');
    expect(ab.getViewMode()).toBe('list');
  });

  it('searches assets', () => {
    const ab = new AssetBrowser();
    ab.search('player');
    expect(ab.getFiles()).toEqual([]);
  });

  it('returns null selected asset when none selected', () => {
    const ab = new AssetBrowser();
    expect(ab.getSelectedAsset()).toBeNull();
  });
});

describe('EditorConsole', () => {
  it('initializes empty', () => {
    const ec = new EditorConsole();
    expect(ec.getEntryCount()).toBe(0);
    expect(ec.getEntries()).toEqual([]);
  });

  it('logs messages', () => {
    const ec = new EditorConsole();
    ec.log('Test message');
    expect(ec.getEntryCount()).toBe(1);
    const entries = ec.getEntries();
    expect(entries[0].message).toBe('Test message');
    expect(entries[0].level).toBe('info');
  });

  it('logs warnings', () => {
    const ec = new EditorConsole();
    ec.warn('Warning message');
    const entries = ec.getEntries();
    expect(entries[0].level).toBe('warning');
  });

  it('logs errors with stack traces', () => {
    const ec = new EditorConsole();
    ec.error('Error message');
    const entries = ec.getEntries();
    expect(entries[0].level).toBe('error');
    expect(entries[0].stack).toBeDefined();
  });

  it('clears all entries', () => {
    const ec = new EditorConsole();
    ec.log('Entry 1');
    ec.log('Entry 2');
    expect(ec.getEntryCount()).toBe(2);
    ec.clear();
    expect(ec.getEntryCount()).toBe(0);
  });

  it('filters entries by level', () => {
    const ec = new EditorConsole();
    ec.log('Info message');
    ec.warn('Warning message');
    ec.error('Error message');
    ec.setFilter('error');
    const errors = ec.getEntries();
    expect(errors.length).toBe(1);
    expect(errors[0].level).toBe('error');
  });

  it('shows all entries when filter is all', () => {
    const ec = new EditorConsole();
    ec.log('Info');
    ec.warn('Warning');
    ec.setFilter('all');
    expect(ec.getEntries().length).toBe(2);
  });

  it('exports entries as string', () => {
    const ec = new EditorConsole();
    ec.log('Test');
    const exported = ec.export();
    expect(exported).toContain('[INFO]');
    expect(exported).toContain('Test');
  });

  it('limits entries to max', () => {
    const ec = new EditorConsole();
    for (let i = 0; i < 1500; i++) {
      ec.log(`Entry ${i}`);
    }
    expect(ec.getEntryCount()).toBeLessThanOrEqual(1000);
  });

  it('logs with source', () => {
    const ec = new EditorConsole();
    ec.log('Network error', 'error', 'NetworkModule');
    const entries = ec.getEntries();
    expect(entries[0].source).toBe('NetworkModule');
  });

  it('sets auto scroll', () => {
    const ec = new EditorConsole();
    expect(ec.isAutoScroll()).toBe(true);
    ec.setAutoScroll(false);
    expect(ec.isAutoScroll()).toBe(false);
  });

  it('sets filter level', () => {
    const ec = new EditorConsole();
    expect(ec.getFilterLevel()).toBe('all');
    ec.setFilter('warning');
    expect(ec.getFilterLevel()).toBe('warning');
  });
});

describe('EditorProfiler', () => {
  it('initializes with no recordings', () => {
    const ep = new EditorProfiler();
    expect(ep.isRecording()).toBe(false);
    expect(ep.getSamples()).toEqual([]);
  });

  it('starts and stops recording', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    expect(ep.isRecording()).toBe(true);
    ep.stopRecording();
    expect(ep.isRecording()).toBe(false);
  });

  it('records samples', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    const sample: ProfilerSample = {
      frameTime: 16.5,
      updateTime: 5.2,
      renderTime: 8.1,
      physicsTime: 1.5,
      gcTime: 0.3,
      drawCalls: 100,
      triangleCount: 5000,
      memoryUsage: 256,
      objectCount: 150,
    };
    ep.recordSample(sample);
    expect(ep.getSamples().length).toBe(1);
    expect(ep.getSamples()[0].frameTime).toBe(16.5);
  });

  it('does not record when not recording', () => {
    const ep = new EditorProfiler();
    ep.recordSample({
      frameTime: 16, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0,
      drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0,
    });
    expect(ep.getSamples().length).toBe(0);
  });

  it('calculates frame time statistics', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    ep.recordSample({ frameTime: 10, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });
    ep.recordSample({ frameTime: 20, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });
    ep.recordSample({ frameTime: 30, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });

    expect(ep.getAverageFrameTime()).toBe(20);
    expect(ep.getMaxFrameTime()).toBe(30);
    expect(ep.getMinFrameTime()).toBe(10);
  });

  it('returns 0 for stats when no samples', () => {
    const ep = new EditorProfiler();
    expect(ep.getAverageFrameTime()).toBe(0);
    expect(ep.getMaxFrameTime()).toBe(0);
    expect(ep.getMinFrameTime()).toBe(0);
  });

  it('calculates FPS from average', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    ep.recordSample({ frameTime: 16.666, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });
    expect(ep.getFPS()).toBeGreaterThan(0);
  });

  it('returns 0 FPS with no samples', () => {
    const ep = new EditorProfiler();
    expect(ep.getFPS()).toBe(0);
  });

  it('clears all samples', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    ep.recordSample({ frameTime: 16, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });
    ep.clear();
    expect(ep.getSamples().length).toBe(0);
  });

  it('limits samples to max', () => {
    const ep = new EditorProfiler();
    ep.startRecording();
    for (let i = 0; i < 2000; i++) {
      ep.recordSample({ frameTime: i, updateTime: 0, renderTime: 0, physicsTime: 0, gcTime: 0, drawCalls: 0, triangleCount: 0, memoryUsage: 0, objectCount: 0 });
    }
    expect(ep.getSamples().length).toBeLessThanOrEqual(1000);
  });
});
