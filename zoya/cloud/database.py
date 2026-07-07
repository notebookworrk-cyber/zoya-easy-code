"""Cloud database service for managing distributed data storage and queries."""

import copy
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Literal

FieldType = Literal["string", "number", "boolean", "date", "object", "array", "reference"]
QueryOperator = Literal[
    "==", "!=", ">", "<", ">=", "<=", "in", "contains", "startsWith", "endsWith"
]
SortDirection = Literal["asc", "desc"]


@dataclass
class QueryFilter:
    field: str
    operator: QueryOperator
    value: Any


@dataclass
class QueryOrder:
    field: str
    direction: SortDirection = "asc"


@dataclass
class QueryOptions:
    filters: list[QueryFilter] | None = None
    orders: list[QueryOrder] | None = None
    limit: int = 50
    offset: int = 0
    select: list[str] | None = None
    include_deleted: bool = False


@dataclass
class CollectionSchema:
    name: str
    fields: dict[str, FieldType]
    indexes: list[list[str]] = field(default_factory=list)
    timestamps: bool = True
    soft_delete: bool = True


@dataclass
class QueryResult:
    data: list[dict[str, Any]]
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class DocumentReference:
    id: str
    collection: str
    path: str


class DatabaseError(Exception):
    def __init__(self, message: str, code: str = "DB_ERROR"):
        self.code = code
        super().__init__(message)


class StoredDocument:
    def __init__(
        self,
        id: str,
        data: dict[str, Any],
        created_at: float,
        updated_at: float,
        deleted_at: float | None = None,
    ):
        self.id = id
        self.data = data
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at


def _matches_filter(doc: StoredDocument, filter: QueryFilter) -> bool:
    value = doc.data.get(filter.field)
    fv = filter.value

    if filter.operator == "==":
        return value == fv
    elif filter.operator == "!=":
        return value != fv
    elif filter.operator == ">":
        return isinstance(value, (int, float)) and isinstance(fv, (int, float)) and value > fv
    elif filter.operator == "<":
        return isinstance(value, (int, float)) and isinstance(fv, (int, float)) and value < fv
    elif filter.operator == ">=":
        return isinstance(value, (int, float)) and isinstance(fv, (int, float)) and value >= fv
    elif filter.operator == "<=":
        return isinstance(value, (int, float)) and isinstance(fv, (int, float)) and value <= fv
    elif filter.operator == "in":
        return isinstance(fv, list) and value in fv
    elif filter.operator == "contains":
        return isinstance(value, str) and str(fv) in value
    elif filter.operator == "startsWith":
        return isinstance(value, str) and value.startswith(str(fv))
    elif filter.operator == "endsWith":
        return isinstance(value, str) and value.endswith(str(fv))
    return False


def _compare_values(a: Any, b: Any, direction: SortDirection) -> int:
    if a is None and b is None:
        return 0
    if a is None:
        return -1 if direction == "asc" else 1
    if b is None:
        return 1 if direction == "asc" else -1

    if isinstance(a, str) and isinstance(b, str):
        cmp = -1 if a < b else 1 if a > b else 0
    else:
        cmp = -1 if a < b else 1 if a > b else 0
    return -cmp if direction == "desc" else cmp


class DatabaseService:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url
        self._api_key = api_key
        self._collections: dict[str, dict[str, StoredDocument]] = {}
        self._schemas: dict[str, CollectionSchema] = {}
        self._active_transactions: dict[str, dict[str, dict[str, StoredDocument]]] = {}

    def _ensure_collection(self, collection: str) -> None:
        if collection not in self._collections:
            self._collections[collection] = {}

    def create(self, collection: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_collection(collection)
        col = self._collections[collection]
        doc_id = secrets.token_hex(8)
        now = time.time()
        doc = StoredDocument(id=doc_id, data=copy.deepcopy(data), created_at=now, updated_at=now)
        col[doc_id] = doc
        return {"id": doc_id, **data, "created_at": now}

    def read(self, collection: str, id: str) -> dict[str, Any] | None:
        self._ensure_collection(collection)
        col = self._collections[collection]
        doc = col.get(id)
        if not doc:
            return None
        if doc.deleted_at is not None:
            return None
        return {"id": doc.id, **copy.deepcopy(doc.data)}

    def update(self, collection: str, id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_collection(collection)
        col = self._collections[collection]
        doc = col.get(id)
        if not doc:
            raise DatabaseError(f"Document not found: {id}", "NOT_FOUND")
        if doc.deleted_at is not None:
            raise DatabaseError(f"Document is deleted: {id}", "DELETED")
        doc.data.update(data)
        doc.updated_at = time.time()
        return {"id": doc.id, **copy.deepcopy(doc.data)}

    def delete(self, collection: str, id: str, soft: bool = True) -> None:
        self._ensure_collection(collection)
        col = self._collections[collection]
        doc = col.get(id)
        if not doc:
            raise DatabaseError(f"Document not found: {id}", "NOT_FOUND")
        if soft:
            doc.deleted_at = time.time()
        else:
            col.pop(id, None)

    def query(self, collection: str, options: QueryOptions | None = None) -> QueryResult:
        self._ensure_collection(collection)
        col = self._collections[collection]
        items = list(col.values())

        if not options or not options.include_deleted:
            items = [i for i in items if i.deleted_at is None]

        if options and options.filters:
            for f in options.filters:
                items = [i for i in items if _matches_filter(i, f)]

        if options and options.orders:
            for order in options.orders:
                items.sort(
                    key=lambda i, f=order.field, d=order.direction: (
                        i.data.get(f) if i.data.get(f) is not None else ""
                    )
                )
                if order.direction == "desc":
                    items.reverse()

        total = len(items)
        offset = options.offset if options else 0
        limit = options.limit if options else 50
        sliced = items[offset : offset + limit]

        data = [{"id": doc.id, **copy.deepcopy(doc.data)} for doc in sliced]
        return QueryResult(
            data=data, total=total, offset=offset, limit=limit, has_more=(offset + limit < total)
        )

    def find_by_ids(self, collection: str, ids: list[str]) -> list[dict[str, Any]]:
        self._ensure_collection(collection)
        col = self._collections[collection]
        results = []
        for doc_id in ids:
            doc = col.get(doc_id)
            if doc and doc.deleted_at is None:
                results.append({"id": doc.id, **copy.deepcopy(doc.data)})
        return results

    def first(self, collection: str, filter: QueryFilter) -> dict[str, Any] | None:
        result = self.query(collection, QueryOptions(filters=[filter], limit=1))
        return result.data[0] if result.data else None

    def batch_create(self, collection: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.create(collection, item) for item in items]

    def batch_delete(self, collection: str, ids: list[str]) -> int:
        count = 0
        for doc_id in ids:
            try:
                self.delete(collection, doc_id, soft=False)
                count += 1
            except DatabaseError:
                continue
        return count

    def count(self, collection: str, filters: list[QueryFilter] | None = None) -> int:
        result = self.query(collection, QueryOptions(filters=filters))
        return result.total

    def exists(self, collection: str, id: str) -> bool:
        self._ensure_collection(collection)
        col = self._collections[collection]
        doc = col.get(id)
        return doc is not None and doc.deleted_at is None

    def create_collection(self, schema: CollectionSchema) -> None:
        if schema.name in self._schemas:
            raise DatabaseError(f"Collection already exists: {schema.name}", "ALREADY_EXISTS")
        self._schemas[schema.name] = schema
        if schema.name not in self._collections:
            self._collections[schema.name] = {}

    def list_collections(self) -> list[str]:
        return list(self._schemas.keys())

    def delete_collection(self, name: str) -> None:
        if name not in self._schemas:
            raise DatabaseError(f"Collection not found: {name}", "NOT_FOUND")
        self._schemas.pop(name, None)
        self._collections.pop(name, None)

    def begin_transaction(self) -> str:
        txn_id = secrets.token_hex(8)
        snapshot: dict[str, dict[str, StoredDocument]] = {}
        for col_name, col_data in self._collections.items():
            snapshot[col_name] = {k: copy.deepcopy(v) for k, v in col_data.items()}
        self._active_transactions[txn_id] = snapshot
        return txn_id

    def commit_transaction(self, transaction_id: str) -> None:
        if transaction_id not in self._active_transactions:
            raise DatabaseError(f"Transaction not found: {transaction_id}", "TRANSACTION_NOT_FOUND")
        self._active_transactions.pop(transaction_id, None)

    def rollback_transaction(self, transaction_id: str) -> None:
        snapshot = self._active_transactions.get(transaction_id)
        if not snapshot:
            raise DatabaseError(f"Transaction not found: {transaction_id}", "TRANSACTION_NOT_FOUND")
        self._collections = snapshot
        self._active_transactions.pop(transaction_id, None)
