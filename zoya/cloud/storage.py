from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import secrets
import time
import os
import mimetypes


@dataclass
class UploadOptions:
    content_type: str = "application/octet-stream"
    public: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)
    cache_control: Optional[str] = None
    encryption_key: Optional[str] = None


@dataclass
class UploadResult:
    url: str
    path: str
    size: int
    content_type: str
    etag: str
    uploaded_at: float


@dataclass
class StorageObject:
    path: str
    size: int
    content_type: str
    etag: str
    uploaded_at: float
    last_modified: float
    metadata: Dict[str, str] = field(default_factory=dict)


class StorageError(Exception):
    def __init__(self, message: str, code: str = "STORAGE_ERROR"):
        self.code = code
        super().__init__(message)


def _generate_etag() -> str:
    return secrets.token_hex(16)


def _normalize_path(path: str) -> str:
    parts = [p for p in path.replace("\\", "/").split("/") if p and p != "."]
    stack: List[str] = []
    for part in parts:
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return "/".join(stack)


class StorageService:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._buckets: Dict[str, Dict[str, StorageObject]] = {}
        self._bucket_data: Dict[str, Dict[str, bytes]] = {}
        self._bucket_metadata: Dict[str, Dict[str, Any]] = {}
        self._create_bucket_internal("default")

    def _get_upload_url(self, bucket: str, path: str) -> str:
        return f"{self._base_url}/storage/v1/{bucket}/{path}"

    def _get_public_url(self, bucket: str, path: str) -> str:
        return f"{self._base_url}/storage/v1/public/{bucket}/{path}"

    def _create_bucket_internal(self, name: str, region: str = "us-east"):
        if name not in self._buckets:
            self._buckets[name] = {}
            self._bucket_data[name] = {}
            self._bucket_metadata[name] = {"region": region, "created_at": time.time()}

    def _get_bucket_or_raise(self, name: str = "default") -> str:
        if name not in self._buckets:
            raise StorageError(f"Bucket '{name}' does not exist", "BUCKET_NOT_FOUND")
        return name

    def upload(
        self,
        data: bytes,
        path: str,
        options: Optional[UploadOptions] = None,
        bucket: str = "default",
    ) -> UploadResult:
        self._get_bucket_or_raise(bucket)
        options = options or UploadOptions()
        normalized = _normalize_path(path)
        content_type = options.content_type
        if content_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(normalized)
            if guessed:
                content_type = guessed

        etag = _generate_etag()
        now = time.time()

        obj = StorageObject(
            path=normalized,
            size=len(data),
            content_type=content_type,
            etag=etag,
            uploaded_at=now,
            last_modified=now,
            metadata=dict(options.metadata),
        )
        self._buckets[bucket][normalized] = obj
        self._bucket_data[bucket][normalized] = data

        url = self._get_public_url(bucket, normalized) if options.public else self._get_upload_url(bucket, normalized)
        return UploadResult(
            url=url,
            path=normalized,
            size=len(data),
            content_type=content_type,
            etag=etag,
            uploaded_at=now,
        )

    def upload_from_file(
        self,
        file_path: str,
        dest_path: str,
        options: Optional[UploadOptions] = None,
        bucket: str = "default",
    ) -> UploadResult:
        if not os.path.isfile(file_path):
            raise StorageError(f"File not found: {file_path}", "FILE_NOT_FOUND")
        with open(file_path, "rb") as f:
            data = f.read()
        inferred_type, _ = mimetypes.guess_type(file_path)
        opts = UploadOptions(**(options.__dict__ if options else {}))
        if inferred_type and opts.content_type == "application/octet-stream":
            opts.content_type = inferred_type
        return self.upload(data, dest_path, opts, bucket)

    def download(self, path: str, bucket: str = "default") -> bytes:
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        if normalized not in self._bucket_data[bucket]:
            raise StorageError(f"Object not found: {normalized}", "OBJECT_NOT_FOUND")
        return self._bucket_data[bucket][normalized]

    def download_to_file(self, path: str, dest_path: str, bucket: str = "default"):
        data = self.download(path, bucket)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)

    def delete(self, path: str, bucket: str = "default"):
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        self._buckets[bucket].pop(normalized, None)
        self._bucket_data[bucket].pop(normalized, None)

    def delete_batch(self, paths: List[str], bucket: str = "default") -> int:
        self._get_bucket_or_raise(bucket)
        count = 0
        for p in paths:
            normalized = _normalize_path(p)
            if normalized in self._buckets[bucket]:
                self._buckets[bucket].pop(normalized)
                self._bucket_data[bucket].pop(normalized)
                count += 1
        return count

    def exists(self, path: str, bucket: str = "default") -> bool:
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        return normalized in self._buckets[bucket]

    def get_metadata(self, path: str, bucket: str = "default") -> StorageObject:
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        obj = self._buckets[bucket].get(normalized)
        if obj is None:
            raise StorageError(f"Object not found: {normalized}", "OBJECT_NOT_FOUND")
        return obj

    def list(
        self,
        prefix: Optional[str] = None,
        recursive: bool = False,
        bucket: str = "default",
    ) -> List[StorageObject]:
        self._get_bucket_or_raise(bucket)
        results: List[StorageObject] = []
        for obj_path, obj in self._buckets[bucket].items():
            if prefix and not obj_path.startswith(_normalize_path(prefix)):
                continue
            if not recursive and prefix:
                remainder = obj_path[len(_normalize_path(prefix)):].lstrip("/")
                if "/" in remainder:
                    continue
            results.append(obj)
        return sorted(results, key=lambda o: o.path)

    def copy(self, source: str, dest: str, bucket: str = "default") -> str:
        self._get_bucket_or_raise(bucket)
        src_normalized = _normalize_path(source)
        dest_normalized = _normalize_path(dest)
        obj = self._buckets[bucket].get(src_normalized)
        if obj is None:
            raise StorageError(f"Source not found: {src_normalized}", "OBJECT_NOT_FOUND")
        data = self._bucket_data[bucket][src_normalized]
        now = time.time()
        new_obj = StorageObject(
            path=dest_normalized,
            size=obj.size,
            content_type=obj.content_type,
            etag=_generate_etag(),
            uploaded_at=now,
            last_modified=now,
            metadata=dict(obj.metadata),
        )
        self._buckets[bucket][dest_normalized] = new_obj
        self._bucket_data[bucket][dest_normalized] = data
        return self._get_upload_url(bucket, dest_normalized)

    def move(self, source: str, dest: str, bucket: str = "default") -> str:
        url = self.copy(source, dest, bucket)
        self.delete(source, bucket)
        return url

    def get_signed_url(
        self,
        path: str,
        expires_in: int = 3600,
        bucket: str = "default",
    ) -> str:
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        if normalized not in self._buckets[bucket]:
            raise StorageError(f"Object not found: {normalized}", "OBJECT_NOT_FOUND")
        expiry = int(time.time()) + expires_in
        token = secrets.token_urlsafe(16)
        return f"{self._base_url}/storage/v1/signed/{bucket}/{normalized}?expires={expiry}&token={token}"

    def get_public_url(self, path: str, bucket: str = "default") -> str:
        self._get_bucket_or_raise(bucket)
        normalized = _normalize_path(path)
        if normalized not in self._buckets[bucket]:
            raise StorageError(f"Object not found: {normalized}", "OBJECT_NOT_FOUND")
        return self._get_public_url(bucket, normalized)

    def create_bucket(self, name: str, region: str = "us-east"):
        if name in self._buckets:
            raise StorageError(f"Bucket already exists: {name}", "BUCKET_EXISTS")
        self._create_bucket_internal(name, region)

    def delete_bucket(self, name: str):
        if name == "default":
            raise StorageError("Cannot delete default bucket", "BUCKET_PROTECTED")
        if name not in self._buckets:
            raise StorageError(f"Bucket not found: {name}", "BUCKET_NOT_FOUND")
        del self._buckets[name]
        del self._bucket_data[name]
        del self._bucket_metadata[name]

    def list_buckets(self) -> List[str]:
        return list(self._buckets.keys())
