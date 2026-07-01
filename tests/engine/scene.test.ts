import { describe, it, expect, beforeEach } from 'vitest';
import { Scene, SceneManager } from '../../src/engine/scene/index.js';
import { Entity } from '../../src/engine/ecs/index.js';
import { TransformComponent } from '../../src/engine/ecs/components.js';
import type { Color } from '../../src/engine/core.js';

describe('Scene', () => {
  let scene: Scene;

  beforeEach(() => {
    scene = new Scene('test_scene');
  });

  it('creates scene with name', () => {
    expect(scene.name).toBe('test_scene');
    expect(scene.world).toBeDefined();
  });

  it('creates entities within scene', () => {
    const entity = scene.createEntity();
    expect(entity).toBeDefined();
    expect(entity.id).toBeGreaterThan(0);
  });

  it('creates entity with optional name', () => {
    const entity = scene.createEntity('player');
    expect(entity).toBeDefined();
    expect(entity.id).toBeGreaterThan(0);
  });

  it('destroys entity', () => {
    const entity = scene.createEntity();
    const id = entity.id;
    scene.destroyEntity(entity);
    expect(scene.world.getEntity(id)).toBeUndefined();
  });

  it('sets and gets main camera', () => {
    const camera = scene.createEntity();
    camera.add(new TransformComponent());
    scene.setMainCamera(camera);
    const main = scene.getMainCamera();
    expect(main).not.toBeNull();
    expect(main!.id).toBe(camera.id);
    expect(main!.has('camera')).toBe(true);
  });

  it('returns null for main camera when none set', () => {
    expect(scene.getMainCamera()).toBeNull();
  });

  it('sets and gets background color', () => {
    const color: Color = [0, 0, 0, 1];
    scene.setBackgroundColor(color);
    const bg = scene.getBackgroundColor();
    expect(bg[0]).toBe(0);
    expect(bg[1]).toBe(0);
    expect(bg[2]).toBe(0);
    expect(bg[3]).toBe(1);
  });

  it('has default background color', () => {
    const bg = scene.getBackgroundColor();
    expect(bg).toBeDefined();
    expect(bg.length).toBe(4);
  });

  it('gets entities with specific component', () => {
    const e1 = scene.createEntity();
    e1.add(new TransformComponent());
    scene.createEntity();
    const results = scene.getEntitiesWith('transform');
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe(e1.id);
  });

  it('propagates update to world', () => {
    let systemRan = false;
    scene.world.addSystem({
      name: 'test',
      priority: 0,
      update: () => { systemRan = true; },
    });
    scene.update(1);
    expect(systemRan).toBe(true);
  });

  it('calls onEnter and onExit hooks', () => {
    let enterCalled = false;
    let exitCalled = false;
    const testScene = new (class extends Scene {
      onEnter() { enterCalled = true; }
      onExit() { exitCalled = true; }
    })('hook_test');
    const mgr = new SceneManager();
    mgr.addScene(testScene);
    mgr.addScene(new Scene('other'));
    mgr.switchTo('hook_test');
    expect(enterCalled).toBe(true);
    mgr.switchTo('other');
    expect(exitCalled).toBe(true);
  });
});

describe('SceneManager', () => {
  let manager: SceneManager;

  beforeEach(() => {
    manager = new SceneManager();
  });

  it('adds and retrieves scenes', () => {
    const scene = new Scene('menu');
    manager.addScene(scene);
    expect(manager.hasScene('menu')).toBe(true);
    expect(manager.getScene('menu')).toBe(scene);
  });

  it('switches between scenes', () => {
    const s1 = new Scene('scene1');
    const s2 = new Scene('scene2');
    manager.addScene(s1);
    manager.addScene(s2);
    expect(manager.switchTo('scene1')).toBe(true);
    expect(manager.getCurrentScene()?.name).toBe('scene1');
    expect(manager.switchTo('scene2')).toBe(true);
    expect(manager.getCurrentScene()?.name).toBe('scene2');
  });

  it('returns false for switching to non-existent scene', () => {
    expect(manager.switchTo('nonexistent')).toBe(false);
  });

  it('removes scene', () => {
    const scene = new Scene('temp');
    manager.addScene(scene);
    manager.removeScene('temp');
    expect(manager.hasScene('temp')).toBe(false);
  });

  it('updates current scene', () => {
    const scene = new Scene('main');
    let updated = false;
    scene.world.addSystem({
      name: 'test',
      priority: 0,
      update: () => { updated = true; },
    });
    manager.addScene(scene);
    manager.switchTo('main');
    manager.update(1);
    expect(updated).toBe(true);
  });

  it('updates with no current scene does not throw', () => {
    expect(() => manager.update(1)).not.toThrow();
  });

  it('returns scene count', () => {
    manager.addScene(new Scene('a'));
    manager.addScene(new Scene('b'));
    manager.addScene(new Scene('c'));
    expect(manager.sceneCount()).toBe(3);
  });

  it('removing current scene clears it', () => {
    const scene = new Scene('current');
    manager.addScene(scene);
    manager.switchTo('current');
    manager.removeScene('current');
    expect(manager.getCurrentScene()).toBeNull();
  });

  it('getScene returns undefined for missing', () => {
    expect(manager.getScene('missing')).toBeUndefined();
  });
});
