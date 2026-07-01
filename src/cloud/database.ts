import { randomBytes } from 'crypto';

export interface QueryFilter {
  field: string;
  operator: '==' | '!=' | '>' | '<' | '>=' | '<=' | 'in' | 'contains' | 'startsWith' | 'endsWith';
  value: unknown;
}

export interface QueryOrder {
  field: string;
  direction: 'asc' | 'desc';
}

export interface QueryOptions {
  filters?: QueryFilter[];
  orders?: QueryOrder[];
  limit?: number;
  offset?: number;
  select?: string[];
  includeDeleted?: boolean;
}

export interface CollectionSchema {
  name: string;
  fields: Record<string, 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array' | 'reference'>;
  indexes: string[][];
  timestamps: boolean;
  softDelete: boolean;
}

export interface QueryResult<T = Record<string, unknown>> {
  data: T[];
  total: number;
  offset: number;
  limit: number;
  hasMore: boolean;
}

export interface DocumentReference {
  id: string;
  collection: string;
  path: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface AnyRecord extends Record<string, any> {}

interface StoredDocument {
  id: string;
  data: AnyRecord;
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;
}

class DatabaseError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'DatabaseError';
  }
}

function matchesFilter(item: StoredDocument, filter: QueryFilter): boolean {
  const value = item.data[filter.field];
  const filterValue = filter.value;

  switch (filter.operator) {
    case '==':
      return value === filterValue;
    case '!=':
      return value !== filterValue;
    case '>':
      return typeof value === 'number' && typeof filterValue === 'number' && value > filterValue;
    case '<':
      return typeof value === 'number' && typeof filterValue === 'number' && value < filterValue;
    case '>=':
      return typeof value === 'number' && typeof filterValue === 'number' && value >= filterValue;
    case '<=':
      return typeof value === 'number' && typeof filterValue === 'number' && value <= filterValue;
    case 'in':
      return Array.isArray(filterValue) && filterValue.includes(value);
    case 'contains':
      return typeof value === 'string' && value.includes(String(filterValue));
    case 'startsWith':
      return typeof value === 'string' && value.startsWith(String(filterValue));
    case 'endsWith':
      return typeof value === 'string' && value.endsWith(String(filterValue));
    default:
      return false;
  }
}

function compareValues(a: unknown, b: unknown, direction: 'asc' | 'desc'): number {
  if (a == null && b == null) return 0;
  if (a == null) return direction === 'asc' ? -1 : 1;
  if (b == null) return direction === 'asc' ? 1 : -1;

  let cmp = 0;
  if (typeof a === 'string' && typeof b === 'string') {
    cmp = a.localeCompare(b);
  } else {
    cmp = a < b ? -1 : a > b ? 1 : 0;
  }
  return direction === 'desc' ? -cmp : cmp;
}

export class DatabaseService {
  private collections: Map<string, Map<string, StoredDocument>> = new Map();
  private schemas: Map<string, CollectionSchema> = new Map();
  private activeTransactions: Map<string, Map<string, Map<string, StoredDocument>>> = new Map();

  constructor(private readonly baseUrl: string, private readonly apiKey: string) {}

  async create<T>(
    collection: string,
    data: T
  ): Promise<T & { id: string; createdAt: Date }> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const id = randomBytes(8).toString('hex');
    const now = new Date();
    const doc: StoredDocument = {
      id,
      data: data as unknown as AnyRecord,
      createdAt: now,
      updatedAt: now,
    };
    col.set(id, doc);
    return { ...data, id, createdAt: now };
  }

  async read<T>(collection: string, id: string): Promise<T | null> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const doc = col.get(id);
    if (!doc) return null;
    if (doc.deletedAt) return null;
    return { id: doc.id, ...doc.data } as unknown as T;
  }

  async update<T>(
    collection: string,
    id: string,
    data: Partial<T>
  ): Promise<T> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const doc = col.get(id);
    if (!doc) {
      throw new DatabaseError(`Document not found: ${id}`, 'NOT_FOUND');
    }
    if (doc.deletedAt) {
      throw new DatabaseError(`Document is deleted: ${id}`, 'DELETED');
    }
    const updated: StoredDocument = {
      ...doc,
      data: { ...doc.data, ...data } as AnyRecord,
      updatedAt: new Date(),
    };
    col.set(id, updated);
    return { id: updated.id, ...updated.data } as unknown as T;
  }

  async delete(collection: string, id: string, soft = true): Promise<void> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const doc = col.get(id);
    if (!doc) {
      throw new DatabaseError(`Document not found: ${id}`, 'NOT_FOUND');
    }
    if (soft) {
      doc.deletedAt = new Date();
    } else {
      col.delete(id);
    }
  }

  async query<T>(
    collection: string,
    options?: QueryOptions
  ): Promise<QueryResult<T>> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    let items = [...col.values()];

    if (!options?.includeDeleted) {
      items = items.filter((item) => !item.deletedAt);
    }

    if (options?.filters) {
      items = items.filter((item) =>
        options.filters!.every((filter) => matchesFilter(item, filter))
      );
    }

    if (options?.orders) {
      for (const order of options.orders) {
        items.sort((a, b) => {
          const aVal = a.data[order.field];
          const bVal = b.data[order.field];
          return compareValues(aVal, bVal, order.direction);
        });
      }
    }

    const total = items.length;
    const offset = options?.offset ?? 0;
    const limit = options?.limit ?? 50;
    const sliced = items.slice(offset, offset + limit);

    const data = sliced.map((doc) => {
      return { id: doc.id, ...doc.data } as unknown as T;
    });

    return {
      data,
      total,
      offset,
      limit,
      hasMore: offset + limit < total,
    };
  }

  async findByIds<T>(collection: string, ids: string[]): Promise<T[]> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const results: T[] = [];
    for (const id of ids) {
      const doc = col.get(id);
      if (doc && !doc.deletedAt) {
        results.push({ id: doc.id, ...doc.data } as unknown as T);
      }
    }
    return results;
  }

  async first<T>(collection: string, filter: QueryFilter): Promise<T | null> {
    const result = await this.query<T>(collection, { filters: [filter], limit: 1 });
    return result.data.length > 0 ? result.data[0] : null;
  }

  async batchCreate<T>(
    collection: string,
    items: T[]
  ): Promise<(T & { id: string; createdAt: Date })[]> {
    const results: (T & { id: string; createdAt: Date })[] = [];
    for (const item of items) {
      const created = await this.create(collection, item);
      results.push(created);
    }
    return results;
  }

  async batchDelete(collection: string, ids: string[]): Promise<number> {
    let count = 0;
    for (const id of ids) {
      try {
        await this.delete(collection, id, false);
        count++;
      } catch {
        continue;
      }
    }
    return count;
  }

  async count(collection: string, filters?: QueryFilter[]): Promise<number> {
    const result = await this.query(collection, { filters });
    return result.total;
  }

  async exists(collection: string, id: string): Promise<boolean> {
    this.ensureCollection(collection);
    const col = this.collections.get(collection)!;
    const doc = col.get(id);
    return doc !== undefined && !doc.deletedAt;
  }

  async createCollection(schema: CollectionSchema): Promise<void> {
    if (this.schemas.has(schema.name)) {
      throw new DatabaseError(`Collection already exists: ${schema.name}`, 'ALREADY_EXISTS');
    }
    this.schemas.set(schema.name, schema);
    if (!this.collections.has(schema.name)) {
      this.collections.set(schema.name, new Map());
    }
  }

  async listCollections(): Promise<string[]> {
    return [...this.schemas.keys()];
  }

  async deleteCollection(name: string): Promise<void> {
    if (!this.schemas.has(name)) {
      throw new DatabaseError(`Collection not found: ${name}`, 'NOT_FOUND');
    }
    this.schemas.delete(name);
    this.collections.delete(name);
  }

  async beginTransaction(): Promise<string> {
    const id = randomBytes(8).toString('hex');
    const snapshot = new Map<string, Map<string, StoredDocument>>();
    for (const [colName, colData] of this.collections) {
      snapshot.set(colName, new Map(colData));
    }
    this.activeTransactions.set(id, snapshot);
    return id;
  }

  async commitTransaction(transactionId: string): Promise<void> {
    if (!this.activeTransactions.has(transactionId)) {
      throw new DatabaseError(`Transaction not found: ${transactionId}`, 'TRANSACTION_NOT_FOUND');
    }
    this.activeTransactions.delete(transactionId);
  }

  async rollbackTransaction(transactionId: string): Promise<void> {
    const snapshot = this.activeTransactions.get(transactionId);
    if (!snapshot) {
      throw new DatabaseError(`Transaction not found: ${transactionId}`, 'TRANSACTION_NOT_FOUND');
    }
    this.collections = snapshot;
    this.activeTransactions.delete(transactionId);
  }

  private ensureCollection(collection: string): void {
    if (!this.collections.has(collection)) {
      this.collections.set(collection, new Map());
    }
  }
}

export { DatabaseError };
