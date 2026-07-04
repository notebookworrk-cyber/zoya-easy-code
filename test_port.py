import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: I001
from zoya.cloud.auth import AuthConfig, AuthError, AuthService
from zoya.cloud.database import (
    CollectionSchema,
    DatabaseService,
    QueryFilter,
    QueryOptions,
    QueryOrder,
)

# Soft delete + exists
db2 = DatabaseService("x", "y")
d = db2.create("col", {"x": 1})
db2.delete("col", d["id"], soft=True)
assert db2.read("col", d["id"]) is None
assert not db2.exists("col", d["id"])
print("soft delete: OK")

# Hard delete
d3 = db2.create("col", {"x": 2})
db2.delete("col", d3["id"], soft=False)
assert d3["id"] not in db2._collections["col"]
print("hard delete: OK")

# Count
db3 = DatabaseService("x", "y")
for i in range(5):
    db3.create("test", {"n": i})
assert db3.count("test") == 5
assert db3.count("test", [QueryFilter(field="n", operator=">=", value=3)]) == 2
print("count: OK")

# Transaction rollback
txn = db3.begin_transaction()
db3.create("test", {"n": 99})
assert db3.count("test") == 6
db3.rollback_transaction(txn)
assert db3.count("test") == 5
print("rollback: OK")

# Transaction commit
txn2 = db3.begin_transaction()
db3.create("test", {"n": 100})
db3.commit_transaction(txn2)
assert db3.count("test") == 6
print("commit: OK")

# Query operators
db5 = DatabaseService("x", "y")
db5.create("users", {"name": "Alice", "age": 30})
db5.create("users", {"name": "Bob", "age": 25})

r = db5.query(
    "users",
    QueryOptions(filters=[QueryFilter(field="age", operator="in", value=[25, 30])]),
)
assert r.total == 2
print("in: OK")

r = db5.query(
    "users",
    QueryOptions(filters=[QueryFilter(field="name", operator="contains", value="Ali")]),
)
assert r.total == 1
print("contains: OK")

r = db5.query(
    "users",
    QueryOptions(filters=[QueryFilter(field="name", operator="startsWith", value="A")]),
)
assert r.total == 1
print("startsWith: OK")

r = db5.query(
    "users",
    QueryOptions(filters=[QueryFilter(field="name", operator="endsWith", value="ce")]),
)
assert r.total == 1
print("endsWith: OK")

r = db5.query(
    "users", QueryOptions(filters=[QueryFilter(field="age", operator=">", value=25)])
)
assert r.total == 1
print(">: OK")

r = db5.query(
    "users", QueryOptions(filters=[QueryFilter(field="age", operator="<", value=30)])
)
assert r.total == 1
print("<: OK")

r = db5.query(
    "users", QueryOptions(filters=[QueryFilter(field="age", operator="!=", value=25)])
)
assert r.total == 1
print("!=: OK")

r = db2.query("col", QueryOptions(include_deleted=True))
assert r.total == 1
print("include_deleted: OK")

assert db5.first("users", QueryFilter(field="name", operator="==", value="Z")) is None
print("first no match: OK")

r = db5.query("users", QueryOptions(orders=[QueryOrder(field="age", direction="asc")]))
assert r.data[0]["name"] == "Bob"
assert r.data[1]["name"] == "Alice"
print("ordering asc: OK")

r = db5.query("users", QueryOptions(limit=1, offset=1))
assert r.total == 2 and len(r.data) == 1
print("pagination: OK")

# Batch
db6 = DatabaseService("x", "y")
items = db6.batch_create("users", [{"name": "C"}, {"name": "D"}])
assert len(items) == 2
assert db6.batch_delete("users", [items[0]["id"], items[1]["id"]]) == 2
print("batch: OK")

# find_by_ids
db4 = DatabaseService("x", "y")
d1 = db4.create("c", {"v": 1})
d2 = db4.create("c", {"v": 2})
assert len(db4.find_by_ids("c", [d1["id"], d2["id"]])) == 2
print("find_by_ids: OK")

# Collection lifecycle
db4.create_collection(CollectionSchema(name="temp", fields={"x": "string"}))
assert "temp" in db4.list_collections()
db4.delete_collection("temp")
assert "temp" not in db4.list_collections()
print("collection lifecycle: OK")

# Auth with email verification
verify_cfg = AuthConfig()
verify_cfg.require_email_verification = True
vauth = AuthService(verify_cfg)
vu = vauth.register("v@test.com", "pw", "vuser")
assert not vu.email_verified
vauth.login("v@test.com", "pw")
vauth.send_verification_email()
assert not vauth.verify_email("badtoken")
print("verify email: OK")

# Standard auth
auth = AuthService()
u = auth.register("test@test.com", "pass123", "testuser")
assert u.email == "test@test.com"
assert not auth.is_authenticated()
session = auth.login("test@test.com", "pass123")
assert session.user_id == u.id
assert auth.is_authenticated()
assert auth.get_token() == session.token
assert auth.validate_session()
print("login/register: OK")

try:
    auth.login("test@test.com", "wrongpass")
except AuthError as e:
    assert e.code == "INVALID_CREDENTIALS"
print("wrong password: OK")

auth.change_password("pass123", "newpass")
auth.login("test@test.com", "newpass")
print("change password: OK")

updated = auth.update_profile({"display_name": "New Name"})
assert updated.display_name == "New Name"
print("update profile: OK")

auth.logout()
assert not auth.is_authenticated()
assert auth.get_token() is None
print("logout: OK")

anon = AuthService(AuthConfig()).login_anonymously()
assert "anon_" in anon.user_id
print("anonymous: OK")

oa = AuthService()
oa._config["oauth_providers"] = ["google"]
oa.login_with_provider("google", "tok")
assert oa.is_authenticated()
oa.delete_account()
assert not oa.is_authenticated()
print("OAuth: OK")

try:
    auth.register("test@test.com", "pw2", "other")
except AuthError as e:
    assert e.code == "DUPLICATE_EMAIL"
print("dup email: OK")

cb = AuthService()
results = []
cb.on_auth_state_change(lambda u: results.append(1))
cb.register("cb@test.com", "pw", "cbuser")
assert len(results) == 1
print("state callback: OK")

try:
    AuthService().login_with_provider("github", "tok")
except AuthError as e:
    assert e.code == "UNSUPPORTED_PROVIDER"
print("unsupported provider: OK")

restrict = AuthService(AuthConfig())
restrict._config["allow_anonymous"] = False
try:
    restrict.login_anonymously()
except AuthError as e:
    assert e.code == "ANONYMOUS_DISABLED"
print("anonymous disabled: OK")

auth.reset_password("nonexistent@test.com")
print("reset password (unknown): OK")

oa2 = AuthService()
oa2._config["oauth_providers"] = ["google"]
oa2.login_with_provider("google", "tok")
try:
    oa2.change_password("old", "new")
except AuthError as e:
    assert e.code == "OAUTH_USER"
print("OAuth no password: OK")

try:
    vauth.register("v@test.com", "pw2", "vuser2")
except AuthError as e:
    assert e.code == "DUPLICATE_EMAIL"
print("dup email (verified): OK")

print()
print("=== ALL SMOKE TESTS PASSED ===")
