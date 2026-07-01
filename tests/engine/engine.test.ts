import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ZoyaEngine, DefaultEngineConfig } from '../../src/engine/index.js';
import type { EngineConfig } from '../../src/engine/index.js';

describe('ZoyaEngine', () => {
  let engine: ZoyaEngine;

  beforeEach(() => {
    engine = new ZoyaEngine();
  });

  describe('Initialization', () => {
    it('creates engine with default config', () => {
      expect(engine.config).toBeDefined();
      expect(engine.config.width).toBe(1280);
      expect(engine.config.height).toBe(720);
      expect(engine.config.targetFPS).toBe(60);
      expect(engine.config.title).toBe('Zoya Game');
    });

    it('accepts partial config override', () => {
      const custom = new ZoyaEngine({ width: 800, height: 600, title: 'Custom' });
      expect(custom.config.width).toBe(800);
      expect(custom.config.height).toBe(600);
      expect(custom.config.title).toBe('Custom');
      expect(custom.config.targetFPS).toBe(60);
    });

    it('full config override works', () => {
      const fullConfig: EngineConfig = {
        width: 1920,
        height: 1080,
        title: 'Full HD',
        fullscreen: true,
        vsync: false,
        targetFPS: 144,
        fixedTimeStep: 0.008,
        maxDeltaTime: 0.05,
        backgroundColor: [0, 0, 0, 1],
        physicsEnabled: false,
        audioEnabled: false,
        assetRoot: '/custom/assets',
        debugMode: true,
      };
      const custom = new ZoyaEngine(fullConfig);
      expect(custom.config.width).toBe(1920);
      expect(custom.config.height).toBe(1080);
      expect(custom.config.fullscreen).toBe(true);
      expect(custom.config.targetFPS).toBe(144);
      expect(custom.config.physicsEnabled).toBe(false);
    });

    it('initializes all subsystems', () => {
      expect(engine.scene).toBeDefined();
      expect(engine.physics).toBeDefined();
      expect(engine.audio).toBeDefined();
      expect(engine.animation).toBeDefined();
      expect(engine.particles).toBeDefined();
      expect(engine.ui).toBeDefined();
      expect(engine.assets).toBeDefined();
      expect(engine.save).toBeDefined();
    });

    it('DefaultEngineConfig is frozen in spirit (immutable)', () => {
      const original = DefaultEngineConfig.width;
      const config = { ...DefaultEngineConfig, width: 999 };
      expect(config.width).toBe(999);
      expect(DefaultEngineConfig.width).toBe(original);
    });
  });

  describe('Lifecycle', () => {
    it('starts as not running', () => {
      expect(engine.isRunning()).toBe(false);
    });

    it('starts running after start()', () => {
      engine.start();
      expect(engine.isRunning()).toBe(true);
    });

    it('stops running after stop()', () => {
      engine.start();
      engine.stop();
      expect(engine.isRunning()).toBe(false);
    });

    it('init does not throw', () => {
      expect(() => engine.init()).not.toThrow();
      expect(() => engine.init({ debugMode: true })).not.toThrow();
    });
  });

  describe('FPS tracking', () => {
    it('returns 0 FPS before any updates', () => {
      expect(engine.getFPS()).toBe(0);
    });

    it('returns 0 delta time before any updates', () => {
      expect(engine.getDeltaTime()).toBe(0);
    });

    it('tracks FPS after updates', () => {
      engine.start();
      engine.update();
      const fps = engine.getFPS();
      expect(engine.getDeltaTime()).toBeGreaterThan(0);
      expect(fps).toBeGreaterThanOrEqual(0);
    });

    it('does not update when not running', () => {
      engine.update();
      expect(engine.getDeltaTime()).toBe(0);
    });

    it('clamps delta time to maxDeltaTime', () => {
      engine.start();
      engine['lastTime'] = performance.now() - 5000;
      engine.update();
      expect(engine.getDeltaTime()).toBeLessThanOrEqual(engine.config.maxDeltaTime);
    });
  });

  describe('Shutdown', () => {
    it('shutdown stops the engine', () => {
      engine.start();
      engine.shutdown();
      expect(engine.isRunning()).toBe(false);
    });

    it('shutdown clears subsystems', () => {
      engine.start();
      engine.animation.addClip({
        name: 'test',
        frames: [{ index: 0, duration: 0.1 }],
        loop: false,
        speed: 1,
      });
      engine.animation.play(1, 'test');
      engine.shutdown();
      expect(engine.animation.isPlaying(1)).toBe(false);
      expect(engine.particles.getParticleCount()).toBe(0);
    });

    it('multiple shutdowns do not throw', () => {
      expect(() => {
        engine.shutdown();
        engine.shutdown();
      }).not.toThrow();
    });
  });

  describe('Integration', () => {
    it('full update cycle does not throw', () => {
      engine.start();
      expect(() => {
        for (let i = 0; i < 10; i++) {
          engine.update();
        }
      }).not.toThrow();
    });

    it('updates physics when enabled', () => {
      const physEngine = new ZoyaEngine({ physicsEnabled: true });
      physEngine.start();
      physEngine.physics.addBody({
        entityId: 1,
        position: { x: 0, y: 0 },
        velocity: { x: 0, y: 0 },
        acceleration: { x: 0, y: 0 },
        mass: 1,
        invMass: 1,
        restitution: 0,
        friction: 0,
        isStatic: false,
        shape: 'circle',
        radius: 1,
      });
      physEngine.update();
      const body = physEngine.physics.getBody(1);
      expect(body!.velocity.y).toBeGreaterThan(0);
    });

    it('skips physics when disabled', () => {
      const noPhysEngine = new ZoyaEngine({ physicsEnabled: false });
      noPhysEngine.start();
      noPhysEngine.physics.addBody({
        entityId: 1,
        position: { x: 0, y: 0 },
        velocity: { x: 0, y: 0 },
        acceleration: { x: 0, y: 0 },
        mass: 1,
        invMass: 1,
        restitution: 0,
        friction: 0,
        isStatic: false,
        shape: 'circle',
        radius: 1,
      });
      noPhysEngine.update();
      const body = noPhysEngine.physics.getBody(1);
      expect(body!.velocity.y).toBe(0);
    });
  });
});
