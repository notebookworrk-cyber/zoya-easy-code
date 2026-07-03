/**
 * Zoya 3.0 - Core runtime values and types
 */

export type ZoyaNumber = number;
export type ZoyaInteger = number;
export type ZoyaString = string;
export type ZoyaBoolean = boolean;
export type ZoyaNull = null;

export interface ZoyaObject {
  readonly __zoya_type: string;
  readonly __id: number;
}

export interface ZoyaArray extends ZoyaObject {
  readonly __zoya_type: 'array';
  readonly __id: number;
  elements: ZoyaValue[];
  length: number;
}

export interface ZoyaFunction {
  readonly __zoya_type: 'function';
  readonly __id: number;
  readonly name: string;
  readonly arity: number;
  readonly chunk: { code: Uint8Array; constants: ZoyaValue[] };
  readonly upvalues?: ZoyaValue[];
}

export interface ZoyaClosure {
  readonly __zoya_type: 'closure';
  readonly __id: number;
  readonly function: ZoyaFunction;
  readonly upvalues: ZoyaValue[];
}

export interface ZoyaNative {
  readonly __zoya_type: 'native';
  readonly __id: number;
  arity: number;
  fn: (...args: ZoyaValue[]) => ZoyaValue;
}

export interface ZoyaUpvalue {
  readonly __zoya_type: 'upvalue';
  readonly __id: number;
  closed: boolean;
  value: ZoyaValue;
  next?: ZoyaUpvalue;
}

export type ZoyaValue =
  | ZoyaNull
  | ZoyaBoolean
  | ZoyaNumber
  | ZoyaString
  | ZoyaObject
  | ZoyaArray
  | ZoyaFunction
  | ZoyaClosure
  | ZoyaNative
  | ZoyaUpvalue;

export type ZoyaTypeName =
  | 'null'
  | 'boolean'
  | 'number'
  | 'string'
  | 'object'
  | 'array'
  | 'function'
  | 'closure'
  | 'native'
  | 'upvalue';

export const ZOYA_NIL: ZoyaNull = null;
export const ZOYA_TRUE: ZoyaBoolean = true;
export const ZOYA_FALSE: ZoyaBoolean = false;

export function typeOf(value: ZoyaValue): ZoyaTypeName {
  if (value === null) return 'null';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'string') return 'string';
  return (value as ZoyaObject).__zoya_type as ZoyaTypeName;
}

export function isTruthy(value: ZoyaValue): boolean {
  if (value === null) return false;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') return value.length > 0;
  return true;
}

export function isEqual(a: ZoyaValue, b: ZoyaValue): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (typeof a === 'number' && typeof b === 'number') {
    return a === b;
  }
  return false;
}

let nextObjectId = 1;

/**
 * Allocates a unique identity for Zoya heap objects. Used by the GC
 * to object-identity-track across weak collections and finalizers.
 */
export function allocateObjectId(): number {
  return nextObjectId++;
}
