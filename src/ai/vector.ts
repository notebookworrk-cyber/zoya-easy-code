import * as fs from 'fs';

export interface VectorRecord {
  id: string;
  vector: Float32Array;
  metadata: Record<string, unknown>;
  text: string;
  timestamp: Date;
  score?: number;
}

interface SerializedVectorRecord {
  id: string;
  vector: number[];
  metadata: Record<string, unknown>;
  text: string;
  timestamp: string;
}

export class VectorMemory {
  private records: VectorRecord[];
  private dimension: number;
  private index: Map<string, VectorRecord>;

  constructor(dimension?: number) {
    this.dimension = dimension || 1536;
    this.records = [];
    this.index = new Map();
  }

  insert(
    id: string,
    text: string,
    vector: Float32Array,
    metadata?: Record<string, unknown>
  ): void {
    if (vector.length !== this.dimension) {
      throw new Error(
        `Vector dimension mismatch: expected ${this.dimension}, got ${vector.length}`
      );
    }

    const record: VectorRecord = {
      id,
      text,
      vector,
      metadata: metadata || {},
      timestamp: new Date(),
    };

    this.records.push(record);
    this.index.set(id, record);
  }

  insertMany(
    items: {
      id: string;
      text: string;
      vector: Float32Array;
      metadata?: Record<string, unknown>;
    }[]
  ): void {
    for (const item of items) {
      this.insert(item.id, item.text, item.vector, item.metadata);
    }
  }

  search(query: Float32Array, topK: number = 10): VectorRecord[] {
    if (query.length !== this.dimension) {
      throw new Error(
        `Query dimension mismatch: expected ${this.dimension}, got ${query.length}`
      );
    }

    const scored = this.records.map((record) => ({
      record,
      similarity: this.cosineSimilarity(query, record.vector),
    }));

    scored.sort((a, b) => b.similarity - a.similarity);

    return scored.slice(0, topK).map((s) => ({
      ...s.record,
      score: s.similarity,
    }));
  }

  async searchByText(text: string, topK: number = 10): Promise<VectorRecord[]> {
    const query = await this.embed(text);
    return this.search(query, topK);
  }

  get(id: string): VectorRecord | undefined {
    const record = this.index.get(id);
    return record ? { ...record } : undefined;
  }

  remove(id: string): void {
    const record = this.index.get(id);
    if (record) {
      this.records = this.records.filter((r) => r.id !== id);
      this.index.delete(id);
    }
  }

  update(id: string, metadata: Record<string, unknown>): void {
    const record = this.index.get(id);
    if (!record) {
      throw new Error(`Record not found: ${id}`);
    }
    record.metadata = { ...record.metadata, ...metadata };
  }

  clear(): void {
    this.records = [];
    this.index.clear();
  }

  get size(): number {
    return this.records.length;
  }

  getDimension(): number {
    return this.dimension;
  }

  consolidate(): void {
    this.records = this.records.filter((r) => this.index.has(r.id));
  }

  getStats(): { totalRecords: number; dimension: number; memoryUsage: number } {
    let memoryUsage = 0;
    for (const record of this.records) {
      memoryUsage += record.vector.byteLength;
      memoryUsage += record.text.length * 2;
      memoryUsage += JSON.stringify(record.metadata).length * 2;
    }
    return {
      totalRecords: this.records.length,
      dimension: this.dimension,
      memoryUsage,
    };
  }

  save(path: string): void {
    const serialized: SerializedVectorRecord[] = this.records.map((r) => ({
      id: r.id,
      vector: Array.from(r.vector),
      metadata: r.metadata,
      text: r.text,
      timestamp: r.timestamp.toISOString(),
    }));

    const data = JSON.stringify(
      { dimension: this.dimension, records: serialized },
      null,
      2
    );
    fs.writeFileSync(path, data, 'utf-8');
  }

  load(path: string): void {
    if (!fs.existsSync(path)) {
      throw new Error(`Vector store file not found: ${path}`);
    }

    const raw = fs.readFileSync(path, 'utf-8');
    const data = JSON.parse(raw) as {
      dimension: number;
      records: SerializedVectorRecord[];
    };

    this.dimension = data.dimension;
    this.records = [];
    this.index = new Map();

    for (const sr of data.records) {
      const record: VectorRecord = {
        id: sr.id,
        vector: new Float32Array(sr.vector),
        metadata: sr.metadata,
        text: sr.text,
        timestamp: new Date(sr.timestamp),
      };
      this.records.push(record);
      this.index.set(sr.id, record);
    }
  }

  private cosineSimilarity(a: Float32Array, b: Float32Array): number {
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    const magnitude = Math.sqrt(normA) * Math.sqrt(normB);
    return magnitude === 0 ? 0 : dotProduct / magnitude;
  }

  private async embed(_text: string): Promise<Float32Array> {
    const vector = new Float32Array(this.dimension);
    for (let i = 0; i < this.dimension; i++) {
      vector[i] = Math.random() * 2 - 1;
    }
    return vector;
  }
}
