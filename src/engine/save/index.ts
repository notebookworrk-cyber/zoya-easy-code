export interface SaveSlot {
  id: string;
  name: string;
  timestamp: Date;
  playTime: number;
  version: string;
  screenshot?: string;
}

export interface SaveData {
  slot: SaveSlot;
  data: Record<string, unknown>;
}

export class SaveManager {
  private saves: Map<string, SaveData>;
  private readonly saveDir: string;
  private currentSlot: string | null;
  private autoSaveEnabled: boolean;
  private autoSaveInterval: number;
  private autoSaveTimer: number;

  constructor(saveDir?: string) {
    this.saves = new Map();
    this.saveDir = saveDir || './saves';
    this.currentSlot = null;
    this.autoSaveEnabled = false;
    this.autoSaveInterval = 300;
    this.autoSaveTimer = 0;
  }

  save(slotId: string, data: Record<string, unknown>, metadata?: Partial<SaveSlot>): void {
    const slot: SaveSlot = {
      id: slotId,
      name: metadata?.name || slotId,
      timestamp: new Date(),
      playTime: metadata?.playTime || 0,
      version: metadata?.version || '1.0.0',
      screenshot: metadata?.screenshot,
    };

    this.saves.set(slotId, { slot, data });
    this.currentSlot = slotId;
  }

  load(slotId: string): SaveData | undefined {
    const save = this.saves.get(slotId);
    if (save) {
      this.currentSlot = slotId;
    }
    return save;
  }

  delete(slotId: string): void {
    this.saves.delete(slotId);
    if (this.currentSlot === slotId) {
      this.currentSlot = null;
    }
  }

  getSlots(): SaveSlot[] {
    const slots: SaveSlot[] = [];
    for (const save of this.saves.values()) {
      slots.push({ ...save.slot });
    }
    slots.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    return slots;
  }

  getSlot(slotId: string): SaveSlot | undefined {
    const save = this.saves.get(slotId);
    return save ? { ...save.slot } : undefined;
  }

  getCurrentSlot(): string | null {
    return this.currentSlot;
  }

  exists(slotId: string): boolean {
    return this.saves.has(slotId);
  }

  setAutoSave(enabled: boolean, interval?: number): void {
    this.autoSaveEnabled = enabled;
    if (interval !== undefined) {
      this.autoSaveInterval = interval;
    }
    this.autoSaveTimer = 0;
  }

  update(dt: number): void {
    if (!this.autoSaveEnabled || !this.currentSlot) return;
    this.autoSaveTimer += dt;
    if (this.autoSaveTimer >= this.autoSaveInterval) {
      const currentData = this.saves.get(this.currentSlot);
      if (currentData) {
        this.save(this.currentSlot, currentData.data, {
          playTime: currentData.slot.playTime + this.autoSaveTimer,
        });
      }
      this.autoSaveTimer = 0;
    }
  }

  exportSave(slotId: string, _path: string): void {
    const save = this.saves.get(slotId);
    if (!save) return;
    // Stub: would serialize to file at _path
  }

  importSave(_path: string): string | null {
    // Stub: would deserialize from file at _path
    return null;
  }
}
