import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
import tempfile
import time
import unittest


class TestAuth(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.auth import AuthService

        self.auth = AuthService()
        self.user = self.auth.register("alice@test.com", "secret123", "alice")
        self.auth.login("alice@test.com", "secret123")

    def tearDown(self):
        self.auth._clear_refresh_timer()

    def test_register_creates_user(self):
        u = self.user
        self.assertEqual(u.email, "alice@test.com")
        self.assertEqual(u.username, "alice")
        self.assertEqual(u.display_name, "alice")
        self.assertTrue(u.id)
        self.assertTrue(u.email_verified)
        self.assertTrue(u.created_at > 0)
        self.assertIn("user", u.roles)

    def test_register_with_metadata(self):
        u = self.auth.register(
            "meta@test.com", "pass", "meta_user", metadata={"theme": "dark"}
        )
        self.assertEqual(u.metadata, {"theme": "dark"})

    def test_register_with_require_email_verification(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.require_email_verification = True
        svc = AuthService(cfg)
        svc.register("ev@test.com", "pass", "ev_user")
        self.assertFalse(svc.get_current_user().email_verified)
        self.assertIn("ev@test.com", svc._email_tokens)

    def test_duplicate_email_raises_error(self):
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError) as ctx:
            self.auth.register("alice@test.com", "other", "bob")
        self.assertEqual(ctx.exception.code, "DUPLICATE_EMAIL")

    def test_duplicate_username_raises_error(self):
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError) as ctx:
            self.auth.register("bob@test.com", "secret", "alice")
        self.assertEqual(ctx.exception.code, "DUPLICATE_USERNAME")

    def test_login_with_correct_credentials_returns_session(self):
        self.auth.logout()
        session = self.auth.login("alice@test.com", "secret123")
        self.assertEqual(session.user_id, self.user.id)
        self.assertTrue(session.token)
        self.assertTrue(session.refresh_token)
        self.assertTrue(session.expires_at > time.time())

    def test_login_with_wrong_password_raises_error(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError) as ctx:
            self.auth.login("alice@test.com", "wrongpass")
        self.assertEqual(ctx.exception.code, "INVALID_CREDENTIALS")

    def test_login_with_wrong_email_raises_error(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError) as ctx:
            self.auth.login("nobody@test.com", "secret123")
        self.assertEqual(ctx.exception.code, "INVALID_CREDENTIALS")

    def test_login_with_provider_works_for_configured_providers(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.oauth_providers = ["google", "github"]
        svc = AuthService(cfg)
        session = svc.login_with_provider("google", "gtoken123")
        self.assertTrue(session.token)
        u = svc.get_current_user()
        self.assertTrue(u.email_verified)

    def test_login_with_provider_unsupported_raises_error(self):
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError) as ctx:
            self.auth.login_with_provider("unsupported", "token")
        self.assertEqual(ctx.exception.code, "UNSUPPORTED_PROVIDER")

    def test_login_with_provider_auto_creates_user(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.oauth_providers = ["github"]
        svc = AuthService(cfg)
        svc.login_with_provider("github", "token123")
        u = svc.get_current_user()
        self.assertIn("github", u.id)
        self.assertEqual(u.email_verified, True)

    def test_login_with_provider_existing_user(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.oauth_providers = ["google"]
        svc = AuthService(cfg)
        svc.login_with_provider("google", "sometoken")
        svc.logout()
        session2 = svc.login_with_provider("google", "sometoken")
        self.assertTrue(session2.token)

    def test_login_anonymously_creates_guest_user(self):
        self.auth.logout()
        session = self.auth.login_anonymously()
        self.assertTrue(session.token)
        u = self.auth.get_current_user()
        self.assertEqual(u.display_name, "Guest")
        self.assertEqual(u.roles, ["guest"])

    def test_login_anonymously_disabled_raises_error(self):
        from zoya.cloud.auth import AuthConfig, AuthError, AuthService

        cfg = AuthConfig()
        cfg.allow_anonymous = False
        svc = AuthService(cfg)
        with self.assertRaises(AuthError) as ctx:
            svc.login_anonymously()
        self.assertEqual(ctx.exception.code, "ANONYMOUS_DISABLED")

    def test_logout_clears_session_and_user(self):
        self.auth.logout()
        self.assertIsNone(self.auth.get_current_user())
        self.assertFalse(self.auth.is_authenticated())

    def test_validate_session_active_returns_true(self):
        self.assertTrue(self.auth.validate_session())

    def test_validate_session_after_logout_returns_false(self):
        self.auth.logout()
        self.assertFalse(self.auth.validate_session())

    def test_validate_session_with_expired_token_returns_false(self):
        self.auth._current_session.expires_at = time.time() - 1
        self.assertFalse(self.auth.validate_session())

    def test_get_current_user_returns_copy(self):
        u = self.auth.get_current_user()
        self.assertEqual(u.email, "alice@test.com")

    def test_get_current_user_returns_none_when_not_authenticated(self):
        self.auth.logout()
        self.assertIsNone(self.auth.get_current_user())

    def test_is_authenticated_reflects_state(self):
        self.assertTrue(self.auth.is_authenticated())
        self.auth.logout()
        self.assertFalse(self.auth.is_authenticated())

    def test_update_profile_updates_allowed_fields(self):
        self.auth.update_profile(
            {"display_name": "Alice M", "avatar_url": "http://av.at/1"}
        )
        u = self.auth.get_current_user()
        self.assertEqual(u.display_name, "Alice M")
        self.assertEqual(u.avatar_url, "http://av.at/1")

    def test_update_profile_ignores_disallowed_fields(self):
        self.auth.update_profile({"display_name": "Alice", "score": 100})
        u = self.auth.get_current_user()
        self.assertEqual(u.display_name, "Alice")

    def test_update_profile_raises_when_not_authenticated(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError) as ctx:
            self.auth.update_profile({"display_name": "X"})
        self.assertEqual(ctx.exception.code, "NOT_AUTHENTICATED")

    def test_change_password_works(self):
        self.auth.change_password("secret123", "newpass456")
        self.auth.logout()
        session = self.auth.login("alice@test.com", "newpass456")
        self.assertTrue(session.token)

    def test_change_password_with_wrong_old_password_raises(self):
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError) as ctx:
            self.auth.change_password("wrongold", "newpass")
        self.assertEqual(ctx.exception.code, "INVALID_PASSWORD")

    def test_change_password_for_oauth_user_raises(self):
        from zoya.cloud.auth import AuthConfig, AuthError, AuthService

        cfg = AuthConfig()
        cfg.oauth_providers = ["google"]
        svc = AuthService(cfg)
        svc.login_with_provider("google", "token")
        with self.assertRaises(AuthError) as ctx:
            svc.change_password("old", "new")
        self.assertEqual(ctx.exception.code, "OAUTH_USER")

    def test_verify_email_flow(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.require_email_verification = True
        svc = AuthService(cfg)
        svc.register("verify@test.com", "pass", "verify_user")
        self.assertFalse(svc.get_current_user().email_verified)
        svc.send_verification_email()
        stored_token = svc._email_tokens.get("verify@test.com")
        result = svc.verify_email(stored_token)
        self.assertTrue(result)
        self.assertTrue(svc.get_current_user().email_verified)

    def test_verify_email_with_wrong_token_returns_false(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.require_email_verification = True
        svc = AuthService(cfg)
        svc.register("v2@test.com", "pass", "v2")
        result = svc.verify_email("wrong_token")
        self.assertFalse(result)
        self.assertFalse(svc.get_current_user().email_verified)

    def test_verify_email_not_authenticated_raises(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError):
            self.auth.verify_email("token")

    def test_on_auth_state_change_callback_fires(self):
        results = []

        def cb(user):
            results.append(user)

        self.auth.on_auth_state_change(cb)
        self.auth.logout()
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0])
        self.auth.login("alice@test.com", "secret123")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].email, "alice@test.com")

    def test_reset_password_sends_token(self):
        self.auth.reset_password("alice@test.com")
        self.assertIn("alice@test.com", self.auth._email_tokens)

    def test_reset_password_for_unknown_email_succeeds_silently(self):
        self.auth.reset_password("unknown@test.com")

    def test_delete_account_removes_user(self):
        self.auth.get_current_user().id
        self.auth.delete_account()
        self.assertIsNone(self.auth.get_current_user())
        self.assertFalse(self.auth.is_authenticated())
        self.auth.logout()
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError):
            self.auth.login("alice@test.com", "secret123")

    def test_refresh_token_creates_new_session(self):
        old_session = self.auth._current_session
        new_session = self.auth.refresh_token()
        self.assertNotEqual(old_session.token, new_session.token)
        self.assertTrue(new_session.expires_at > time.time())

    def test_refresh_token_without_session_raises(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError) as ctx:
            self.auth.refresh_token()
        self.assertEqual(ctx.exception.code, "NO_SESSION")

    def test_get_token_returns_token_or_none(self):
        self.assertTrue(self.auth.get_token())
        self.auth.logout()
        self.assertIsNone(self.auth.get_token())

    def test_send_verification_email_already_verified_raises(self):
        from zoya.cloud.auth import AuthError

        with self.assertRaises(AuthError) as ctx:
            self.auth.send_verification_email()
        self.assertEqual(ctx.exception.code, "ALREADY_VERIFIED")

    def test_send_verification_email_not_authenticated_raises(self):
        from zoya.cloud.auth import AuthError

        self.auth.logout()
        with self.assertRaises(AuthError):
            self.auth.send_verification_email()

    def test_max_sessions_evicts_oldest(self):
        from zoya.cloud.auth import AuthConfig, AuthService

        cfg = AuthConfig()
        cfg.max_sessions = 2
        svc = AuthService(cfg)
        svc.register("ms@test.com", "pass", "ms_user")
        svc.login("ms@test.com", "pass")
        first_token = svc._current_session.token
        svc.login("ms@test.com", "pass")
        svc.login("ms@test.com", "pass")
        self.assertNotIn(first_token, svc._sessions)

    def test_logout_during_session_removes_from_store(self):
        token = self.auth._current_session.token
        self.assertIn(token, self.auth._sessions)
        self.auth.logout()
        self.assertNotIn(token, self.auth._sessions)

    def test_delete_account_removes_from_stores(self):
        token = self.auth._current_session.token
        self.auth.delete_account()
        self.assertNotIn(token, self.auth._sessions)

    def test_get_current_user_returns_independent_copy(self):
        u = self.auth.get_current_user()
        u.display_name = "Hacked"
        u2 = self.auth.get_current_user()
        self.assertNotEqual(u2.display_name, "Hacked")


class TestDatabase(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.database import DatabaseService

        self.db = DatabaseService("http://localhost", "test_key")

    def test_create_adds_document_with_id_and_created_at(self):
        doc = self.db.create("users", {"name": "Alice", "age": 30})
        self.assertIn("id", doc)
        self.assertIn("created_at", doc)
        self.assertEqual(doc["name"], "Alice")
        self.assertEqual(doc["age"], 30)

    def test_read_returns_document(self):
        created = self.db.create("users", {"name": "Bob"})
        doc = self.db.read("users", created["id"])
        self.assertEqual(doc["name"], "Bob")
        self.assertEqual(doc["id"], created["id"])

    def test_read_returns_none_for_missing_document(self):
        doc = self.db.read("users", "nonexistent")
        self.assertIsNone(doc)

    def test_read_returns_none_for_soft_deleted_document(self):
        created = self.db.create("users", {"name": "Charlie"})
        self.db.delete("users", created["id"], soft=True)
        doc = self.db.read("users", created["id"])
        self.assertIsNone(doc)

    def test_update_modifies_document(self):
        created = self.db.create("users", {"name": "Diana", "age": 25})
        updated = self.db.update("users", created["id"], {"age": 26})
        self.assertEqual(updated["age"], 26)
        self.assertEqual(updated["name"], "Diana")

    def test_update_raises_for_missing_document(self):
        from zoya.cloud.database import DatabaseError

        with self.assertRaises(DatabaseError) as ctx:
            self.db.update("users", "missing", {"x": 1})
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_update_raises_for_deleted_document(self):
        from zoya.cloud.database import DatabaseError

        created = self.db.create("users", {"name": "Test"})
        self.db.delete("users", created["id"], soft=True)
        with self.assertRaises(DatabaseError) as ctx:
            self.db.update("users", created["id"], {"x": 1})
        self.assertEqual(ctx.exception.code, "DELETED")

    def test_soft_delete_marks_deleted(self):
        created = self.db.create("users", {"name": "Eve"})
        self.db.delete("users", created["id"], soft=True)
        self.assertIsNotNone(self.db._collections["users"][created["id"]].deleted_at)
        self.assertIn(created["id"], self.db._collections["users"])

    def test_hard_delete_removes_document(self):
        created = self.db.create("users", {"name": "Frank"})
        self.db.delete("users", created["id"], soft=False)
        self.assertNotIn(created["id"], self.db._collections["users"])

    def test_delete_raises_for_missing_document(self):
        from zoya.cloud.database import DatabaseError

        with self.assertRaises(DatabaseError) as ctx:
            self.db.delete("users", "nonexistent")
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_query_without_filters_returns_all(self):
        self.db.create("items", {"val": 1})
        self.db.create("items", {"val": 2})
        self.db.create("items", {"val": 3})
        result = self.db.query("items")
        self.assertEqual(result.total, 3)
        self.assertEqual(len(result.data), 3)

    def test_query_with_equals_filter(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        self.db.create("items", {"type": "a", "val": 1})
        self.db.create("items", {"type": "b", "val": 2})
        self.db.create("items", {"type": "a", "val": 3})
        result = self.db.query(
            "items",
            QueryOptions(filters=[QueryFilter(field="type", operator="==", value="a")]),
        )
        self.assertEqual(result.total, 2)

    def test_query_with_not_equals_filter(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        self.db.create("items", {"type": "a"})
        self.db.create("items", {"type": "b"})
        result = self.db.query(
            "items",
            QueryOptions(filters=[QueryFilter(field="type", operator="!=", value="a")]),
        )
        self.assertEqual(result.total, 1)

    def test_query_with_comparison_filters(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        for v in range(1, 6):
            self.db.create("nums", {"val": v})
        gt = self.db.query(
            "nums",
            QueryOptions(filters=[QueryFilter(field="val", operator=">", value=3)]),
        )
        self.assertEqual(gt.total, 2)
        lt = self.db.query(
            "nums",
            QueryOptions(filters=[QueryFilter(field="val", operator="<", value=3)]),
        )
        self.assertEqual(lt.total, 2)
        gte = self.db.query(
            "nums",
            QueryOptions(filters=[QueryFilter(field="val", operator=">=", value=3)]),
        )
        self.assertEqual(gte.total, 3)
        lte = self.db.query(
            "nums",
            QueryOptions(filters=[QueryFilter(field="val", operator="<=", value=3)]),
        )
        self.assertEqual(lte.total, 3)

    def test_query_with_in_filter(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        self.db.create("items", {"name": "alpha"})
        self.db.create("items", {"name": "beta"})
        self.db.create("items", {"name": "gamma"})
        result = self.db.query(
            "items",
            QueryOptions(
                filters=[
                    QueryFilter(field="name", operator="in", value=["alpha", "gamma"])
                ]
            ),
        )
        self.assertEqual(result.total, 2)

    def test_query_with_contains_filter(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        self.db.create("items", {"name": "hello world"})
        self.db.create("items", {"name": "hello there"})
        self.db.create("items", {"name": "goodbye"})
        result = self.db.query(
            "items",
            QueryOptions(
                filters=[QueryFilter(field="name", operator="contains", value="hello")]
            ),
        )
        self.assertEqual(result.total, 2)

    def test_query_with_starts_ends_filter(self):
        from zoya.cloud.database import QueryFilter, QueryOptions

        self.db.create("items", {"name": "hello world"})
        self.db.create("items", {"name": "goodbye"})
        s = self.db.query(
            "items",
            QueryOptions(
                filters=[QueryFilter(field="name", operator="startsWith", value="good")]
            ),
        )
        self.assertEqual(s.total, 1)
        e = self.db.query(
            "items",
            QueryOptions(
                filters=[QueryFilter(field="name", operator="endsWith", value="world")]
            ),
        )
        self.assertEqual(e.total, 1)

    def test_query_with_sorting_asc(self):
        from zoya.cloud.database import QueryOptions, QueryOrder

        for v in [3, 1, 2]:
            self.db.create("nums", {"val": v})
        result = self.db.query(
            "nums", QueryOptions(orders=[QueryOrder(field="val", direction="asc")])
        )
        vals = [d["val"] for d in result.data]
        self.assertEqual(vals, [1, 2, 3])

    def test_query_with_sorting_desc(self):
        from zoya.cloud.database import QueryOptions, QueryOrder

        for v in [1, 3, 2]:
            self.db.create("nums", {"val": v})
        result = self.db.query(
            "nums", QueryOptions(orders=[QueryOrder(field="val", direction="desc")])
        )
        vals = [d["val"] for d in result.data]
        self.assertEqual(vals, [3, 2, 1])

    def test_query_with_pagination(self):
        from zoya.cloud.database import QueryOptions

        for i in range(10):
            self.db.create("items", {"idx": i})
        page1 = self.db.query("items", QueryOptions(limit=3, offset=0))
        self.assertEqual(len(page1.data), 3)
        self.assertTrue(page1.has_more)
        self.assertEqual(page1.offset, 0)
        page2 = self.db.query("items", QueryOptions(limit=3, offset=3))
        self.assertEqual(len(page2.data), 3)
        last = self.db.query("items", QueryOptions(limit=3, offset=9))
        self.assertEqual(len(last.data), 1)
        self.assertFalse(last.has_more)
        self.assertEqual(last.total, 10)

    def test_query_with_empty_collection(self):
        from zoya.cloud.database import QueryOptions

        result = self.db.query("empty", QueryOptions(limit=10))
        self.assertEqual(result.total, 0)
        self.assertEqual(len(result.data), 0)
        self.assertFalse(result.has_more)

    def test_query_auto_creates_collection(self):
        result = self.db.query("autocreate")
        self.assertEqual(result.total, 0)

    def test_batch_create(self):
        items = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        docs = self.db.batch_create("items", items)
        self.assertEqual(len(docs), 3)
        for d in docs:
            self.assertIn("id", d)
        result = self.db.query("items")
        self.assertEqual(result.total, 3)

    def test_batch_delete(self):
        d1 = self.db.create("items", {"x": 1})
        d2 = self.db.create("items", {"x": 2})
        d3 = self.db.create("items", {"x": 3})
        count = self.db.batch_delete("items", [d1["id"], d2["id"]])
        self.assertEqual(count, 2)
        self.assertIsNone(self.db.read("items", d1["id"]))
        self.assertIsNotNone(self.db.read("items", d3["id"]))

    def test_batch_delete_skips_missing(self):
        count = self.db.batch_delete("items", ["missing1", "missing2"])
        self.assertEqual(count, 0)

    def test_count(self):
        for i in range(5):
            self.db.create("items", {"v": i})
        self.assertEqual(self.db.count("items"), 5)

    def test_count_with_filters(self):
        from zoya.cloud.database import QueryFilter

        self.db.create("items", {"type": "a"})
        self.db.create("items", {"type": "b"})
        self.db.create("items", {"type": "a"})
        count = self.db.count(
            "items", filters=[QueryFilter(field="type", operator="==", value="a")]
        )
        self.assertEqual(count, 2)

    def test_count_empty_collection(self):
        self.assertEqual(self.db.count("empty"), 0)

    def test_exists(self):
        d = self.db.create("items", {"x": 1})
        self.assertTrue(self.db.exists("items", d["id"]))
        self.assertFalse(self.db.exists("items", "noid"))
        self.db.delete("items", d["id"], soft=True)
        self.assertFalse(self.db.exists("items", d["id"]))

    def test_create_collection_with_schema(self):
        from zoya.cloud.database import CollectionSchema

        schema = CollectionSchema(
            name="books", fields={"title": "string", "pages": "number"}
        )
        self.db.create_collection(schema)
        self.assertIn("books", self.db._schemas)
        self.assertIn("books", self.db._collections)

    def test_create_collection_duplicate_raises(self):
        from zoya.cloud.database import CollectionSchema, DatabaseError

        schema1 = CollectionSchema(name="dup", fields={"v": "string"})
        schema2 = CollectionSchema(name="dup", fields={"v": "string"})
        self.db.create_collection(schema1)
        with self.assertRaises(DatabaseError) as ctx:
            self.db.create_collection(schema2)
        self.assertEqual(ctx.exception.code, "ALREADY_EXISTS")

    def test_list_collections(self):
        from zoya.cloud.database import CollectionSchema

        self.db.create_collection(CollectionSchema(name="a", fields={"v": "string"}))
        self.db.create_collection(CollectionSchema(name="b", fields={"v": "string"}))
        cols = self.db.list_collections()
        self.assertIn("a", cols)
        self.assertIn("b", cols)

    def test_delete_collection(self):
        from zoya.cloud.database import CollectionSchema

        self.db.create_collection(CollectionSchema(name="temp", fields={"v": "string"}))
        self.db.create("temp", {"x": 1})
        self.db.delete_collection("temp")
        self.assertNotIn("temp", self.db._schemas)
        self.assertNotIn("temp", self.db._collections)

    def test_delete_collection_missing_raises(self):
        from zoya.cloud.database import DatabaseError

        with self.assertRaises(DatabaseError) as ctx:
            self.db.delete_collection("nonexistent")
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_transaction_commit(self):
        d = self.db.create("tx", {"val": 1})
        txn_id = self.db.begin_transaction()
        self.db.update("tx", d["id"], {"val": 2})
        self.db.commit_transaction(txn_id)
        doc = self.db.read("tx", d["id"])
        self.assertEqual(doc["val"], 2)

    def test_transaction_rollback(self):
        d = self.db.create("tx", {"val": 1})
        txn_id = self.db.begin_transaction()
        self.db.update("tx", d["id"], {"val": 99})
        self.db.rollback_transaction(txn_id)
        doc = self.db.read("tx", d["id"])
        self.assertEqual(doc["val"], 1)

    def test_transaction_commit_invalid_raises(self):
        from zoya.cloud.database import DatabaseError

        with self.assertRaises(DatabaseError) as ctx:
            self.db.commit_transaction("invalid")
        self.assertEqual(ctx.exception.code, "TRANSACTION_NOT_FOUND")

    def test_transaction_rollback_invalid_raises(self):
        from zoya.cloud.database import DatabaseError

        with self.assertRaises(DatabaseError):
            self.db.rollback_transaction("invalid")

    def test_transaction_rollback_restores_snapshot(self):
        d1 = self.db.create("tx", {"val": 1})
        d2 = self.db.create("tx", {"val": 2})
        txn_id = self.db.begin_transaction()
        self.db.update("tx", d1["id"], {"val": 10})
        self.db.delete("tx", d2["id"], soft=False)
        self.db.rollback_transaction(txn_id)
        self.assertEqual(self.db.read("tx", d1["id"])["val"], 1)
        self.assertIsNotNone(self.db.read("tx", d2["id"]))

    def test_find_by_ids(self):
        d1 = self.db.create("items", {"x": 1})
        self.db.create("items", {"x": 2})
        d3 = self.db.create("items", {"x": 3})
        results = self.db.find_by_ids("items", [d1["id"], d3["id"], "missing"])
        self.assertEqual(len(results), 2)
        ids = [r["id"] for r in results]
        self.assertIn(d1["id"], ids)
        self.assertIn(d3["id"], ids)

    def test_find_by_ids_skips_deleted(self):
        d = self.db.create("items", {"x": 1})
        self.db.delete("items", d["id"], soft=True)
        results = self.db.find_by_ids("items", [d["id"]])
        self.assertEqual(len(results), 0)

    def test_first_returns_matching_document(self):
        from zoya.cloud.database import QueryFilter

        self.db.create("items", {"code": "a"})
        self.db.create("items", {"code": "b"})
        doc = self.db.first(
            "items", QueryFilter(field="code", operator="==", value="a")
        )
        self.assertEqual(doc["code"], "a")

    def test_first_returns_none_when_no_match(self):
        from zoya.cloud.database import QueryFilter

        doc = self.db.first(
            "items", QueryFilter(field="code", operator="==", value="z")
        )
        self.assertIsNone(doc)

    def test_query_with_include_deleted(self):
        from zoya.cloud.database import QueryOptions

        d = self.db.create("items", {"x": 1})
        self.db.delete("items", d["id"], soft=True)
        result = self.db.query("items")
        self.assertEqual(result.total, 0)
        result = self.db.query("items", QueryOptions(include_deleted=True))
        self.assertEqual(result.total, 1)

    def test_create_returns_readable_fields(self):
        doc = self.db.create("users", {"full_name": "Alice", "active": True})
        self.assertIn("id", doc)
        self.assertEqual(doc["full_name"], "Alice")
        self.assertEqual(doc["active"], True)
        self.assertIn("created_at", doc)

    def test_update_returns_merged_data(self):
        created = self.db.create("users", {"a": 1, "b": 2})
        updated = self.db.update("users", created["id"], {"b": 3, "c": 4})
        self.assertEqual(updated["a"], 1)
        self.assertEqual(updated["b"], 3)
        self.assertEqual(updated["c"], 4)


class TestStorage(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.storage import StorageService

        self.store = StorageService("http://localhost", "test_key")

    def test_upload_stores_data_and_returns_result(self):
        data = b"hello world"
        result = self.store.upload(data, "test.txt")
        self.assertEqual(result.size, 11)
        self.assertEqual(result.path, "test.txt")
        self.assertEqual(result.content_type, "text/plain")
        self.assertTrue(result.etag)
        self.assertTrue(result.uploaded_at > 0)

    def test_download_returns_same_bytes(self):
        original = b"binary content\x00\x01\x02"
        self.store.upload(original, "bin/data.bin")
        downloaded = self.store.download("bin/data.bin")
        self.assertEqual(downloaded, original)

    def test_download_missing_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError) as ctx:
            self.store.download("nonexistent.txt")
        self.assertEqual(ctx.exception.code, "OBJECT_NOT_FOUND")

    def test_delete_removes_object(self):
        self.store.upload(b"data", "del.txt")
        self.assertTrue(self.store.exists("del.txt"))
        self.store.delete("del.txt")
        self.assertFalse(self.store.exists("del.txt"))

    def test_delete_nonexistent_succeeds(self):
        self.store.delete("nonexistent.txt")

    def test_exists_returns_bool(self):
        self.store.upload(b"x", "exists.txt")
        self.assertTrue(self.store.exists("exists.txt"))
        self.assertFalse(self.store.exists("no.txt"))

    def test_get_metadata_returns_storage_object(self):
        from zoya.cloud.storage import UploadOptions

        opts = UploadOptions(metadata={"author": "test"}, content_type="text/plain")
        self.store.upload(b"data", "meta/file.txt", opts)
        meta = self.store.get_metadata("meta/file.txt")
        self.assertEqual(meta.path, "meta/file.txt")
        self.assertEqual(meta.size, 4)
        self.assertEqual(meta.content_type, "text/plain")
        self.assertEqual(meta.metadata, {"author": "test"})

    def test_get_metadata_missing_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError):
            self.store.get_metadata("no.txt")

    def test_list_returns_objects(self):
        self.store.upload(b"a", "dir/a.txt")
        self.store.upload(b"b", "dir/b.txt")
        self.store.upload(b"c", "other/c.txt")
        all_objs = self.store.list()
        self.assertEqual(len(all_objs), 3)

    def test_list_with_prefix(self):
        self.store.upload(b"a", "dir/a.txt")
        self.store.upload(b"b", "dir/sub/b.txt")
        self.store.upload(b"c", "other/c.txt")
        dir_objs = self.store.list(prefix="dir", recursive=True)
        self.assertEqual(len(dir_objs), 2)

    def test_list_non_recursive(self):
        self.store.upload(b"a", "root/a.txt")
        self.store.upload(b"b", "root/sub/b.txt")
        objs = self.store.list(prefix="root", recursive=False)
        self.assertEqual(len(objs), 1)

    def test_list_empty_prefix(self):
        objs = self.store.list(prefix="")
        self.assertEqual(len(objs), 0)

    def test_copy_duplicates_object(self):
        self.store.upload(b"data", "src.txt")
        url = self.store.copy("src.txt", "dst.txt")
        self.assertTrue(url)
        self.assertTrue(self.store.exists("dst.txt"))
        self.assertEqual(self.store.download("dst.txt"), b"data")

    def test_copy_missing_source_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError):
            self.store.copy("no.txt", "dst.txt")

    def test_move_relocates_object(self):
        self.store.upload(b"data", "source.txt")
        url = self.store.move("source.txt", "dest.txt")
        self.assertTrue(url)
        self.assertTrue(self.store.exists("dest.txt"))
        self.assertFalse(self.store.exists("source.txt"))

    def test_get_signed_url_returns_url(self):
        self.store.upload(b"data", "secret.txt")
        url = self.store.get_signed_url("secret.txt", expires_in=3600)
        self.assertIn("signed/", url)
        self.assertIn("expires=", url)
        self.assertIn("token=", url)

    def test_get_signed_url_missing_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError):
            self.store.get_signed_url("no.txt")

    def test_get_public_url_returns_url(self):
        self.store.upload(b"data", "pub.txt")
        url = self.store.get_public_url("pub.txt")
        self.assertIn("public/", url)

    def test_get_public_url_missing_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError):
            self.store.get_public_url("no.txt")

    def test_bucket_lifecycle(self):
        self.store.create_bucket("mybucket", region="eu-west")
        self.assertIn("mybucket", self.store.list_buckets())
        self.store.delete_bucket("mybucket")
        self.assertNotIn("mybucket", self.store.list_buckets())

    def test_upload_to_custom_bucket(self):
        self.store.create_bucket("custom")
        result = self.store.upload(b"data", "f.txt", bucket="custom")
        self.assertEqual(result.size, 4)
        self.assertTrue(self.store.exists("f.txt", bucket="custom"))

    def test_create_existing_bucket_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError) as ctx:
            self.store.create_bucket("default")
        self.assertEqual(ctx.exception.code, "BUCKET_EXISTS")

    def test_delete_default_bucket_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError) as ctx:
            self.store.delete_bucket("default")
        self.assertEqual(ctx.exception.code, "BUCKET_PROTECTED")

    def test_missing_bucket_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError) as ctx:
            self.store.upload(b"x", "p", bucket="nobucket")
        self.assertEqual(ctx.exception.code, "BUCKET_NOT_FOUND")

    def test_delete_missing_bucket_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError):
            self.store.delete_bucket("nobucket")

    def test_upload_with_public_option(self):
        from zoya.cloud.storage import UploadOptions

        result = self.store.upload(b"data", "public.txt", UploadOptions(public=True))
        self.assertIn("public/", result.url)

    def test_upload_content_type_guessing(self):
        result = self.store.upload(b"<html>", "page.html")
        self.assertEqual(result.content_type, "text/html")

    def test_upload_from_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"file content")
            f.flush()
            fname = f.name
        try:
            result = self.store.upload_from_file(fname, "uploaded/test.txt")
            self.assertEqual(result.size, 12)
            self.assertEqual(self.store.download("uploaded/test.txt"), b"file content")
        finally:
            os.unlink(fname)

    def test_upload_from_missing_file_raises(self):
        from zoya.cloud.storage import StorageError

        with self.assertRaises(StorageError) as ctx:
            self.store.upload_from_file(r"C:\nonexistent\file.txt", "dest.txt")
        self.assertEqual(ctx.exception.code, "FILE_NOT_FOUND")

    def test_download_to_file(self):
        self.store.upload(b"download content", "dl/test.bin")
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, "out.bin")
            self.store.download_to_file("dl/test.bin", dest)
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"download content")

    def test_delete_batch(self):
        self.store.upload(b"a", "a.txt")
        self.store.upload(b"b", "b.txt")
        self.store.upload(b"c", "c.txt")
        count = self.store.delete_batch(["a.txt", "b.txt"])
        self.assertEqual(count, 2)
        self.assertFalse(self.store.exists("a.txt"))
        self.assertFalse(self.store.exists("b.txt"))
        self.assertTrue(self.store.exists("c.txt"))

    def test_delete_batch_partial(self):
        self.store.upload(b"a", "exists.txt")
        count = self.store.delete_batch(["exists.txt", "missing.txt"])
        self.assertEqual(count, 1)

    def test_path_normalization_removes_dotdot(self):
        self.store.upload(b"data", "foo/bar/../file.txt")
        self.assertTrue(self.store.exists("foo/file.txt"))
        self.assertEqual(self.store.download("foo/bar/../file.txt"), b"data")

    def test_path_normalization_removes_dots(self):
        self.store.upload(b"data", "./dir/./file.txt")
        self.assertTrue(self.store.exists("dir/file.txt"))

    def test_path_normalization_backslashes(self):
        self.store.upload(b"data", "a\\b\\c.txt")
        self.assertTrue(self.store.exists("a/b/c.txt"))

    def test_upload_with_custom_options(self):
        from zoya.cloud.storage import UploadOptions

        opts = UploadOptions(
            content_type="application/json",
            cache_control="public, max-age=3600",
            metadata={"key": "val"},
        )
        result = self.store.upload(b'{"a":1}', "data.json", opts)
        self.assertEqual(result.content_type, "application/json")
        self.assertFalse(result.url.startswith("public"))


class TestRealtime(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.realtime import RealtimeService

        self.rt = RealtimeService("http://localhost", "test_key")

    def test_connect_sets_connected(self):
        self.assertFalse(self.rt.is_connected())
        self.rt.connect()
        self.assertTrue(self.rt.is_connected())

    def test_disconnect_clears_connected(self):
        self.rt.connect()
        self.rt.disconnect()
        self.assertFalse(self.rt.is_connected())

    def test_is_connected_reflects_state(self):
        self.assertFalse(self.rt.is_connected())
        self.rt.connect()
        self.assertTrue(self.rt.is_connected())
        self.rt.disconnect()
        self.assertFalse(self.rt.is_connected())

    def test_subscribe_adds_callback(self):
        self.rt.connect()
        events = []

        def cb(event):
            events.append(event)

        self.rt.subscribe("channel1", cb)
        self.rt.publish("channel1", "hello")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data, "hello")

    def test_unsubscribe_removes_callback(self):
        self.rt.connect()
        events = []

        def cb(event):
            events.append(event)

        self.rt.subscribe("ch", cb)
        self.rt.unsubscribe("ch", cb)
        self.rt.publish("ch", "data")
        self.assertEqual(len(events), 0)

    def test_unsubscribe_all_removes_channel(self):
        self.rt.connect()
        events = []

        def cb1(e):
            events.append("a")

        def cb2(e):
            events.append("b")

        self.rt.subscribe("ch", cb1)
        self.rt.subscribe("ch", cb2)
        self.rt.unsubscribe("ch")
        self.rt.publish("ch", "data")
        self.assertEqual(len(events), 0)

    def test_unsubscribe_unknown_channel_succeeds(self):
        self.rt.unsubscribe("no_such_channel")

    def test_publish_dispatches_to_subscribers(self):
        self.rt.connect()
        received = []

        def cb(event):
            received.append(event.data)

        self.rt.subscribe("test_channel", cb)
        self.rt.publish("test_channel", {"msg": "hi"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {"msg": "hi"})

    def test_publish_only_dispatches_to_channel_subscribers(self):
        self.rt.connect()
        received = []

        def cb(event):
            received.append(event.data)

        self.rt.subscribe("alpha", cb)
        self.rt.publish("beta", "should_not_arrive")
        self.assertEqual(len(received), 0)

    def test_publish_raises_when_not_connected(self):
        from zoya.cloud.realtime import RealtimeError

        with self.assertRaises(RealtimeError) as ctx:
            self.rt.publish("ch", "data")
        self.assertEqual(ctx.exception.code, "NOT_CONNECTED")

    def test_update_presence(self):
        self.rt.connect()
        self.rt.subscribe("room1", lambda e: None)
        self.rt.update_presence("online", {"avatar": "a.png"}, "user1", "Alice")
        presence = self.rt.get_presence("room1")
        self.assertEqual(len(presence), 1)
        self.assertEqual(presence[0].user_id, "user1")
        self.assertEqual(presence[0].status, "online")

    def test_update_presence_raises_when_not_connected(self):
        from zoya.cloud.realtime import RealtimeError

        with self.assertRaises(RealtimeError):
            self.rt.update_presence("online")

    def test_get_presence_empty_channel(self):
        self.rt.connect()
        self.rt.subscribe("empty_room", lambda e: None)
        presence = self.rt.get_presence("empty_room")
        self.assertEqual(len(presence), 0)

    def test_list_channels(self):
        self.rt.connect()
        self.rt.subscribe("a", lambda e: None)
        self.rt.subscribe("b", lambda e: None)
        channels = self.rt.list_channels()
        names = [c.name for c in channels]
        self.assertIn("a", names)
        self.assertIn("b", names)
        for c in channels:
            self.assertEqual(c.subscribers, 1)

    def test_list_channels_empty(self):
        channels = self.rt.list_channels()
        self.assertEqual(len(channels), 0)

    def test_get_channel_subscribers(self):
        self.rt.connect()
        self.rt.subscribe("ch", lambda e: None)
        self.rt.subscribe("ch", lambda e: None)
        self.assertEqual(self.rt.get_channel_subscribers("ch"), 2)
        self.assertEqual(self.rt.get_channel_subscribers("nonexistent"), 0)

    def test_on_event_global_callback(self):
        self.rt.connect()
        events = []

        def cb(e):
            events.append(e.type.value)

        self.rt.on_event(cb)
        self.rt.publish("ch", "data")
        self.assertIn("message", events)

    def test_on_event_connect_disconnect(self):
        events = []

        def cb(e):
            events.append(e.type.value)

        self.rt.on_event(cb)
        self.rt.connect()
        self.rt.disconnect()
        self.assertIn("connect", events)
        self.assertIn("disconnect", events)

    def test_on_error_global_callback(self):
        self.rt.connect()
        errors = []

        def cb(err):
            errors.append(err)

        self.rt.on_error(cb)

        def bad_cb(e):
            raise ValueError("bad!")

        self.rt.subscribe("ch", bad_cb)
        self.rt.publish("ch", "data")
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValueError)

    def test_set_reconnect_policy(self):
        self.rt.set_reconnect_policy(10, 5.0)
        self.assertEqual(self.rt._reconnect_max_attempts, 10)
        self.assertEqual(self.rt._reconnect_interval, 5.0)

    def test_on_presence_change_callback(self):
        self.rt.connect()
        self.rt.subscribe("room", lambda e: None)
        presences = []

        def cb(p_list):
            presences.extend(p_list)

        self.rt.on_presence_change("room", cb)
        self.rt.update_presence("busy", user_id="u1", username="User1")
        self.assertEqual(len(presences), 1)
        self.assertEqual(presences[0].user_id, "u1")

    def test_presence_callback_not_invoked_for_unsubscribed_channel(self):
        self.rt.connect()
        presences = []

        def cb(p_list):
            presences.extend(p_list)

        self.rt.on_presence_change("room_a", cb)
        self.rt.subscribe("room_b", lambda e: None)
        self.rt.update_presence("online", user_id="u1", username="U1")
        self.assertEqual(len(presences), 0)


class TestLeaderboard(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.leaderboard import (
            LeaderboardDefinition,
            LeaderboardService,
            ResetPeriod,
            SortOrder,
            UpdateStrategy,
        )

        self.lb = LeaderboardService("http://localhost", "key")
        self.defn = LeaderboardDefinition(
            id="rank1",
            name="High Scores",
            sort_order=SortOrder.DESC,
            update_strategy=UpdateStrategy.BEST,
            reset_period=ResetPeriod.NEVER,
            max_entries=100,
        )
        self.lb.create_leaderboard(self.defn)

    def test_create_leaderboard(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition

        self.lb.create_leaderboard(LeaderboardDefinition(id="newlb", name="New"))
        self.assertIn("newlb", [d.id for d in self.lb.list_leaderboards()])

    def test_create_duplicate_raises(self):
        from zoya.cloud.leaderboard import LeaderboardError

        with self.assertRaises(LeaderboardError) as ctx:
            self.lb.create_leaderboard(self.defn)
        self.assertEqual(ctx.exception.code, "CONFLICT")

    def test_list_leaderboards(self):
        lbs = self.lb.list_leaderboards()
        self.assertEqual(len(lbs), 1)
        self.assertEqual(lbs[0].id, "rank1")

    def test_submit_score_with_best_strategy(self):
        self.lb.submit_score("rank1", "user_alice", 100.0)
        e1 = self.lb.submit_score("rank1", "user_alice", 50.0)
        self.assertEqual(e1.score, 100.0)
        e2 = self.lb.submit_score("rank1", "user_alice", 200.0)
        self.assertEqual(e2.score, 200.0)

    def test_submit_score_with_latest_strategy(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition, UpdateStrategy

        self.lb.create_leaderboard(
            LeaderboardDefinition(
                id="latest", name="Latest", update_strategy=UpdateStrategy.LATEST
            )
        )
        self.lb.submit_score("latest", "user_bob", 10.0)
        e = self.lb.submit_score("latest", "user_bob", 99.0)
        self.assertEqual(e.score, 99.0)

    def test_submit_score_with_sum_strategy(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition, UpdateStrategy

        self.lb.create_leaderboard(
            LeaderboardDefinition(
                id="sumlb", name="Sum", update_strategy=UpdateStrategy.SUM
            )
        )
        self.lb.submit_score("sumlb", "user_bob", 10.0)
        e = self.lb.submit_score("sumlb", "user_bob", 20.0)
        self.assertEqual(e.score, 30.0)

    def test_submit_score_with_average_strategy(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition, UpdateStrategy

        self.lb.create_leaderboard(
            LeaderboardDefinition(
                id="avglb", name="Avg", update_strategy=UpdateStrategy.AVERAGE
            )
        )
        self.lb.submit_score("avglb", "user_bob", 10.0)
        e = self.lb.submit_score("avglb", "user_bob", 20.0)
        self.assertEqual(e.score, 15.0)

    def test_submit_score_missing_leaderboard_raises(self):
        from zoya.cloud.leaderboard import LeaderboardError

        with self.assertRaises(LeaderboardError) as ctx:
            self.lb.submit_score("nonexistent", "user_alice", 10)
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_submit_score_with_metadata(self):
        e = self.lb.submit_score("rank1", "user_alice", 100, metadata={"level": 5})
        self.assertEqual(e.metadata, {"level": 5})

    def test_submit_score_merges_metadata(self):
        self.lb.submit_score("rank1", "user_alice", 100, metadata={"level": 5})
        e = self.lb.submit_score(
            "rank1", "user_alice", 200, metadata={"class": "warrior"}
        )
        self.assertIsNotNone(e.metadata)
        self.assertEqual(e.metadata["level"], 5)
        self.assertEqual(e.metadata["class"], "warrior")

    def test_get_scores_returns_sorted_desc(self):
        self.lb.submit_score("rank1", "user_alice", 50.0)
        self.lb.submit_score("rank1", "user_bob", 100.0)
        self.lb.submit_score("rank1", "user_charlie", 75.0)
        scores = self.lb.get_scores("rank1")
        self.assertEqual(len(scores), 3)
        self.assertEqual(scores[0].user_id, "user_bob")
        self.assertEqual(scores[1].user_id, "user_charlie")
        self.assertEqual(scores[2].user_id, "user_alice")

    def test_get_scores_asc_order(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition, SortOrder

        self.lb.create_leaderboard(
            LeaderboardDefinition(
                id="asc_lb", name="Ascending", sort_order=SortOrder.ASC
            )
        )
        self.lb.submit_score("asc_lb", "user_bob", 100.0)
        self.lb.submit_score("asc_lb", "user_alice", 50.0)
        scores = self.lb.get_scores("asc_lb")
        self.assertEqual(scores[0].user_id, "user_alice")
        self.assertEqual(scores[1].user_id, "user_bob")

    def test_get_scores_with_pagination(self):
        for i, uid in enumerate(
            ["user_alice", "user_bob", "user_charlie", "user_diana", "user_eve"]
        ):
            self.lb.submit_score("rank1", uid, float(i * 10))
        page = self.lb.get_scores("rank1", limit=2, offset=0)
        self.assertEqual(len(page), 2)

    def test_get_scores_empty_leaderboard(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition

        self.lb.create_leaderboard(LeaderboardDefinition(id="empty", name="Empty"))
        scores = self.lb.get_scores("empty")
        self.assertEqual(len(scores), 0)

    def test_get_scores_unknown_leaderboard(self):
        scores = self.lb.get_scores("unknown")
        self.assertEqual(len(scores), 0)

    def test_get_rank_returns_correct_entry(self):
        self.lb.submit_score("rank1", "user_alice", 10.0)
        self.lb.submit_score("rank1", "user_bob", 50.0)
        entry = self.lb.get_rank("rank1", "user_alice")
        self.assertEqual(entry.rank, 2)
        self.assertEqual(entry.score, 10.0)

    def test_get_rank_number_one(self):
        self.lb.submit_score("rank1", "user_alice", 10.0)
        self.lb.submit_score("rank1", "user_bob", 50.0)
        entry = self.lb.get_rank("rank1", "user_bob")
        self.assertEqual(entry.rank, 1)

    def test_get_rank_returns_none_for_unknown_user(self):
        entry = self.lb.get_rank("rank1", "nobody")
        self.assertIsNone(entry)

    def test_get_around_user_returns_neighbors(self):
        uids = ["user_alice", "user_bob", "user_charlie", "user_diana", "user_eve"]
        for i, uid in enumerate(uids):
            self.lb.submit_score("rank1", uid, float(i * 10))
        around = self.lb.get_around_user("rank1", "user_charlie", range=1)
        self.assertEqual(len(around), 3)
        self.assertEqual(around[1].user_id, "user_charlie")
        self.assertIn(around[0].user_id, ["user_diana", "user_eve"])

    def test_get_around_user_returns_empty_for_unknown(self):
        around = self.lb.get_around_user("rank1", "nobody")
        self.assertEqual(around, [])

    def test_get_around_user_clamps_at_boundaries(self):
        for i, uid in enumerate(["user_alice", "user_bob", "user_charlie"]):
            self.lb.submit_score("rank1", uid, float(i * 10))
        around = self.lb.get_around_user("rank1", "user_alice", range=2)
        self.assertEqual(len(around), 3)

    def test_delete_leaderboard(self):
        self.lb.delete_leaderboard("rank1")
        self.assertEqual(len(self.lb.list_leaderboards()), 0)
        from zoya.cloud.leaderboard import LeaderboardError

        with self.assertRaises(LeaderboardError):
            self.lb.submit_score("rank1", "user_alice", 10)

    def test_delete_missing_leaderboard_raises(self):
        from zoya.cloud.leaderboard import LeaderboardError

        with self.assertRaises(LeaderboardError) as ctx:
            self.lb.delete_leaderboard("nonexistent")
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_update_leaderboard(self):
        self.lb.update_leaderboard("rank1", {"name": "Updated Name"})
        lbs = self.lb.list_leaderboards()
        self.assertEqual(lbs[0].name, "Updated Name")

    def test_update_missing_leaderboard_raises(self):
        from zoya.cloud.leaderboard import LeaderboardError

        with self.assertRaises(LeaderboardError):
            self.lb.update_leaderboard("nonexistent", {})

    def test_reset_leaderboard_clears_scores(self):
        self.lb.submit_score("rank1", "user_alice", 100)
        self.lb.reset_leaderboard("rank1")
        scores = self.lb.get_scores("rank1")
        self.assertEqual(len(scores), 0)

    def test_get_reset_schedule(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition, ResetPeriod

        self.lb.create_leaderboard(
            LeaderboardDefinition(
                id="daily", name="Daily", reset_period=ResetPeriod.DAILY
            )
        )
        self.assertEqual(self.lb.get_reset_schedule("daily"), "daily")
        self.assertIsNone(self.lb.get_reset_schedule("rank1"))

    def test_get_friends_leaderboard(self):
        self.lb.submit_score("rank1", "user_alice", 50)
        self.lb.submit_score("rank1", "user_bob", 100)
        self.lb.submit_score("rank1", "user_charlie", 75)
        self.lb.submit_score("rank1", "user_diana", 25)
        friends = self.lb.get_friends_leaderboard("rank1", "user_alice")
        fids = [e.user_id for e in friends]
        self.assertIn("user_alice", fids)
        self.assertIn("user_bob", fids)
        self.assertIn("user_charlie", fids)
        self.assertNotIn("user_diana", fids)

    def test_max_entries_respected(self):
        from zoya.cloud.leaderboard import LeaderboardDefinition

        self.lb.create_leaderboard(
            LeaderboardDefinition(id="limited", name="Limited", max_entries=2)
        )
        uids = ["user_alice", "user_bob", "user_charlie"]
        for i, uid in enumerate(uids):
            self.lb.submit_score("limited", uid, float(i * 10))
        scores = self.lb.get_scores("limited")
        self.assertEqual(len(scores), 2)


class TestMultiplayer(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.multiplayer import MultiplayerService
        from zoya.cloud.realtime import RealtimeService

        self.rt = RealtimeService("http://localhost", "key")
        self.mp = MultiplayerService("http://localhost", "key", self.rt)

    def _make_real_match(self):
        import secrets
        import time

        from zoya.cloud.multiplayer import Match, MatchConfig, MatchStatus

        match = Match(
            id=secrets.token_hex(8),
            players=["user_alice", "user_bob"],
            status=MatchStatus.IN_PROGRESS,
            config=MatchConfig(),
            created_at=time.time(),
            started_at=time.time(),
        )
        self.mp._matches[match.id] = match
        self.mp._player_match["user_alice"] = match.id
        self.mp._player_match["user_bob"] = match.id
        return match

    def test_find_match_creates_match(self):
        from zoya.cloud.multiplayer import MatchConfig

        self.mp._matchmaking_queue[:] = ["user_alice", "user_bob"]
        self.mp._matchmaking_users.update(["user_alice", "user_bob"])
        match = self.mp.find_match(MatchConfig(max_players=2, min_players=2))
        self.assertNotEqual(match.id, "pending")
        self.assertEqual(len(match.players), 2)
        self.assertEqual(match.status.value, "in_progress")

    def test_find_match_returns_pending_when_no_opponent(self):
        from zoya.cloud.multiplayer import MatchConfig

        self.mp._matchmaking_queue.clear()
        self.mp._matchmaking_users.clear()
        match = self.mp.find_match(MatchConfig(max_players=2, min_players=2))
        self.assertEqual(match.id, "pending")

    def test_cancel_matchmaking(self):
        from zoya.cloud.multiplayer import MatchConfig

        self.mp.find_match(MatchConfig())
        self.mp.cancel_matchmaking()
        self.assertNotIn("user_alice", self.mp._matchmaking_queue)

    def test_get_match_returns_match(self):
        match = self._make_real_match()
        retrieved = self.mp.get_match(match.id)
        self.assertEqual(retrieved.id, match.id)
        self.assertEqual(retrieved.players, match.players)

    def test_get_match_returns_copy(self):
        match = self._make_real_match()
        retrieved = self.mp.get_match(match.id)
        retrieved.status = "mutated"
        original = self.mp.get_match(match.id)
        self.assertNotEqual(original.status.value, "mutated")

    def test_get_match_missing_raises(self):
        from zoya.cloud.multiplayer import MultiplayerError

        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.get_match("nonexistent")
        self.assertEqual(ctx.exception.code, "MATCH_NOT_FOUND")

    def test_leave_match_cancels(self):
        match = self._make_real_match()
        self.mp.leave_match(match.id)
        retrieved = self.mp.get_match(match.id)
        self.assertEqual(retrieved.status.value, "cancelled")
        self.assertIsNotNone(retrieved.ended_at)

    def test_leave_match_missing_raises(self):
        from zoya.cloud.multiplayer import MultiplayerError

        with self.assertRaises(MultiplayerError):
            self.mp.leave_match("nonexistent")

    def test_create_lobby(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("Test Lobby", MatchConfig())
        self.assertEqual(lobby.name, "Test Lobby")
        self.assertEqual(lobby.host_user_id, "user_alice")

    def test_create_lobby_appears_in_list(self):
        from zoya.cloud.multiplayer import MatchConfig

        self.mp.create_lobby("Lobby1", MatchConfig())
        self.assertEqual(len(self.mp.list_lobbies()), 1)

    def test_join_lobby(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("Lobby", MatchConfig())
        self.mp.join_lobby(lobby.id)
        retrieved = self.mp.get_lobby(lobby.id)
        self.assertIn("user_alice", [p.user_id for p in retrieved.players])

    def test_join_lobby_missing_raises(self):
        from zoya.cloud.multiplayer import MultiplayerError

        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.join_lobby("nonexistent")
        self.assertEqual(ctx.exception.code, "LOBBY_NOT_FOUND")

    def test_leave_lobby(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("L", MatchConfig())
        self.mp.join_lobby(lobby.id)
        self.mp.leave_lobby(lobby.id)
        players = self.mp.get_lobby(lobby.id).players
        self.assertNotIn("user_alice", [p.user_id for p in players])

    def test_get_lobby(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("GetMe", MatchConfig())
        retrieved = self.mp.get_lobby(lobby.id)
        self.assertEqual(retrieved.id, lobby.id)
        self.assertEqual(retrieved.name, "GetMe")

    def test_get_lobby_returns_copy(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("L", MatchConfig())
        retrieved = self.mp.get_lobby(lobby.id)
        retrieved.name = "mutated"
        original = self.mp.get_lobby(lobby.id)
        self.assertEqual(original.name, "L")

    def test_get_lobby_missing_raises(self):
        from zoya.cloud.multiplayer import MultiplayerError

        with self.assertRaises(MultiplayerError):
            self.mp.get_lobby("no")

    def test_list_lobbies(self):
        from zoya.cloud.multiplayer import MatchConfig

        self.mp.create_lobby("A", MatchConfig())
        self.mp.create_lobby("B", MatchConfig())
        self.assertEqual(len(self.mp.list_lobbies()), 2)

    def test_set_ready(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("L", MatchConfig())
        self.mp.join_lobby(lobby.id)
        self.mp.set_ready(lobby.id, True)
        retrieved = self.mp.get_lobby(lobby.id)
        for p in retrieved.players:
            if p.user_id == "user_alice":
                self.assertTrue(p.ready)

    def test_set_ready_user_not_in_lobby_raises(self):
        from zoya.cloud.multiplayer import MatchConfig, MultiplayerError

        lobby = self.mp.create_lobby("L", MatchConfig())
        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.set_ready(lobby.id, True)
        self.assertEqual(ctx.exception.code, "USER_NOT_IN_LOBBY")

    def test_start_match(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("L", MatchConfig(min_players=1))
        self.mp.join_lobby(lobby.id)
        self.mp.set_ready(lobby.id, True)
        match = self.mp.start_match(lobby.id)
        self.assertEqual(match.status.value, "in_progress")
        self.assertIn("user_alice", match.players)

    def test_start_match_not_enough_ready_raises(self):
        from zoya.cloud.multiplayer import MatchConfig, MultiplayerError

        lobby = self.mp.create_lobby("L", MatchConfig(min_players=2))
        self.mp.join_lobby(lobby.id)
        self.mp.set_ready(lobby.id, True)
        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.start_match(lobby.id)
        self.assertEqual(ctx.exception.code, "NOT_ENOUGH_PLAYERS")

    def test_start_match_as_non_host_raises(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("L", MatchConfig())
        lobby.host_user_id = "someone_else"
        from zoya.cloud.multiplayer import MultiplayerError

        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.start_match(lobby.id)
        self.assertEqual(ctx.exception.code, "NOT_HOST")

    def test_create_party(self):
        party_id = self.mp.create_party()
        self.assertTrue(party_id)
        self.assertIn("user_alice", self.mp._parties[party_id])
        self.assertEqual(self.mp._player_parties.get("user_alice"), party_id)

    def test_join_party(self):
        pid = self.mp.create_party()
        self.mp.leave_party()
        self.mp.join_party(pid)
        self.assertEqual(self.mp._player_parties.get("user_alice"), pid)

    def test_join_party_creates_if_not_exists(self):
        self.mp.join_party("new_party_id")
        self.assertIn("new_party_id", self.mp._parties)
        self.assertIn("user_alice", self.mp._parties["new_party_id"])

    def test_leave_party(self):
        self.mp.create_party()
        self.mp.leave_party()
        self.assertNotIn("user_alice", self.mp._player_parties)

    def test_leave_party_cleans_up_empty_party(self):
        pid = self.mp.create_party()
        self.mp.leave_party()
        self.assertNotIn(pid, self.mp._parties)

    def test_invite_to_party_without_party_raises(self):
        from zoya.cloud.multiplayer import MultiplayerError

        self.mp.leave_party()
        with self.assertRaises(MultiplayerError) as ctx:
            self.mp.invite_to_party("user_bob")
        self.assertEqual(ctx.exception.code, "NO_PARTY")

    def test_invite_to_party(self):
        self.mp.create_party()
        self.mp.invite_to_party("user_bob")

    def test_sync_state_and_get_state(self):
        self.mp.sync_state("match1", {"health": 100})
        state = self.mp.get_state("match1")
        self.assertEqual(state, {"health": 100})

    def test_get_state_returns_copy(self):
        self.mp.sync_state("match1", {"health": 100})
        state = self.mp.get_state("match1")
        state["health"] = 50
        self.assertEqual(self.mp.get_state("match1")["health"], 100)

    def test_get_state_none_for_unknown_match(self):
        self.assertIsNone(self.mp.get_state("unknown"))

    def test_on_state_change_callback(self):
        received = []

        def cb(state):
            received.append(state)

        self.mp.on_state_change("match1", cb)
        self.mp.sync_state("match1", {"pos": [0, 0]})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {"pos": [0, 0]})

    def test_send_event_and_on_event(self):
        received = []

        def cb(data):
            received.append(data)

        self.mp.on_event("match1", "move", cb)
        self.mp.send_event("match1", "move", {"x": 10})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {"x": 10})

    def test_send_event_without_handler_succeeds(self):
        self.mp.send_event("match1", "unhandled", {"x": 1})

    def test_send_event_wildcard_handler(self):
        received = []

        def cb(data):
            received.append(data)

        self.mp.on_event("match1", "*", cb)
        self.mp.send_event("match1", "any_event", {"k": "v"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {"event": "any_event", "data": {"k": "v"}})

    def test_get_lobby_returns_lobby_for_existing(self):
        from zoya.cloud.multiplayer import MatchConfig

        lobby = self.mp.create_lobby("test_lobby", MatchConfig())
        result = self.mp.get_lobby(lobby.id)
        self.assertEqual(result.id, lobby.id)


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        from zoya.cloud.analytics import AnalyticsService

        self.analytics = AnalyticsService("http://localhost", "key")

    def tearDown(self):
        if self.analytics._flush_timer is not None:
            self.analytics._flush_timer.cancel()

    def test_track_stores_event(self):
        self.analytics.track("purchase", {"item": "sword"}, value=9.99)
        self.assertEqual(len(self.analytics._events), 1)
        self.assertEqual(self.analytics._events[0].name, "purchase")
        self.assertEqual(self.analytics._events[0].value, 9.99)

    def test_track_page_view(self):
        self.analytics.track_page_view("/home", duration=1.5)
        events = [e for e in self.analytics._events if e.name == "page_view"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].properties["page"], "/home")

    def test_track_error(self):
        self.analytics.track_error("Something broke", fatal=True)
        events = [e for e in self.analytics._events if e.name == "error"]
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].properties["fatal"])

    def test_track_user_action(self):
        self.analytics.track_user_action("click", "#button")
        events = [e for e in self.analytics._events if e.name == "user_action"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].properties["action"], "click")

    def test_start_end_session(self):
        self.analytics.start_session()
        sid = self.analytics.get_session_id()
        self.assertIn(sid, self.analytics._active_sessions)
        self.analytics.end_session()
        self.assertNotIn(sid, self.analytics._active_sessions)
        self.assertIn(sid, self.analytics._sessions)
        self.assertIsNotNone(self.analytics._sessions[sid].end_time)

    def test_end_session_without_start_succeeds(self):
        self.analytics.end_session()

    def test_get_session_id(self):
        sid = self.analytics.get_session_id()
        self.assertTrue(sid)
        self.assertIsInstance(sid, str)

    def test_query_returns_count_metric(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("click", value=1.0)
        self.analytics.track("click", value=2.0)
        self.analytics.track("other", value=3.0)
        from zoya.cloud.analytics import AnalyticsQuery

        result = self.analytics.query(
            AnalyticsQuery(
                event="click",
                start_date=now - 10,
                end_date=now + 10,
                metrics=["count", "sum", "avg", "min", "max"],
            )
        )
        self.assertEqual(result.metrics["count"], 2)
        self.assertEqual(result.metrics["sum"], 3.0)
        self.assertEqual(result.metrics["avg"], 1.5)
        self.assertEqual(result.metrics["min"], 1.0)
        self.assertEqual(result.metrics["max"], 2.0)

    def test_query_outside_date_range(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("click", value=1.0)
        from zoya.cloud.analytics import AnalyticsQuery

        result = self.analytics.query(
            AnalyticsQuery(
                event="click",
                start_date=now + 1000,
                end_date=now + 2000,
                metrics=["count"],
            )
        )
        self.assertEqual(result.metrics["count"], 0)

    def test_query_with_group_by_returns_breakdown(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("click", {"category": "A"}, value=1)
        self.analytics.track("click", {"category": "A"}, value=2)
        self.analytics.track("click", {"category": "B"}, value=5)
        from zoya.cloud.analytics import AnalyticsQuery

        result = self.analytics.query(
            AnalyticsQuery(
                event="click",
                start_date=now - 10,
                end_date=now + 10,
                group_by="category",
                metrics=["count", "sum"],
            )
        )
        self.assertIsNotNone(result.breakdown)
        self.assertIn("A", result.breakdown)
        self.assertIn("B", result.breakdown)
        self.assertEqual(result.breakdown["A"]["count"], 2)
        self.assertEqual(result.breakdown["A"]["sum"], 3.0)
        self.assertEqual(result.breakdown["B"]["count"], 1)
        self.assertEqual(result.breakdown["B"]["sum"], 5.0)

    def test_query_group_by_unknown_field(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("click", {"category": "A"})
        from zoya.cloud.analytics import AnalyticsQuery

        result = self.analytics.query(
            AnalyticsQuery(
                event="click",
                start_date=now - 10,
                end_date=now + 10,
                group_by="nonexistent",
                metrics=["count"],
            )
        )
        self.assertIn("unknown", result.breakdown)

    def test_get_event_count(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("login")
        self.analytics.track("login")
        self.assertEqual(self.analytics.get_event_count("login", now - 10, now + 10), 2)
        self.assertEqual(
            self.analytics.get_event_count("nonexistent", now - 10, now + 10), 0
        )

    def test_get_user_count(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("e1")
        count = self.analytics.get_user_count(now - 10, now + 10)
        self.assertEqual(count, 1)

    def test_get_active_users(self):
        self.analytics.track("e1")
        active = self.analytics.get_active_users(days=7)
        self.assertEqual(active, 1)

    def test_get_active_users_no_data(self):
        active = self.analytics.get_active_users(days=7)
        self.assertEqual(active, 0)

    def test_get_retention_rate(self):
        import time as ttime

        now = ttime.time()
        self.analytics.track("install")
        rate = self.analytics.get_retention_rate(now - 86400, days_since_onboarding=1)
        self.assertEqual(rate, 1.0)

    def test_get_retention_rate_no_data(self):
        import time as ttime

        now = ttime.time()
        rate = self.analytics.get_retention_rate(
            now + 86400 * 10, days_since_onboarding=1
        )
        self.assertEqual(rate, 0.0)

    def test_get_sessions_returns_user_sessions(self):
        self.analytics.start_session()
        sessions = self.analytics.get_sessions("user_alice")
        self.assertEqual(len(sessions), 1)

    def test_get_sessions_empty(self):
        sessions = self.analytics.get_sessions("nobody")
        self.assertEqual(len(sessions), 0)

    def test_get_dashboard_returns_requested_metrics(self):
        self.analytics.track("e1")
        self.analytics.start_session()
        dashboard = self.analytics.get_dashboard(
            ["total_events", "active_sessions", "total_sessions"]
        )
        self.assertIn("total_events", dashboard)
        self.assertIn("active_sessions", dashboard)
        self.assertIn("total_sessions", dashboard)
        self.assertGreater(dashboard["total_events"], 0)

    def test_get_dashboard_empty_metrics(self):
        dashboard = self.analytics.get_dashboard([])
        self.assertEqual(dashboard, {})

    def test_opt_out_stops_tracking(self):
        self.analytics.opt_out()
        self.analytics.track("should_not_appear")
        self.assertEqual(len(self.analytics._events), 0)

    def test_opt_in_resumes_tracking(self):
        self.analytics.opt_out()
        self.analytics.track("lost")
        self.analytics.opt_in()
        self.analytics.track("found")
        self.assertEqual(len(self.analytics._events), 1)
        self.assertEqual(self.analytics._events[0].name, "found")

    def test_delete_user_data(self):
        self.analytics.track("e1")
        self.analytics.start_session()
        self.analytics.delete_user_data("user_alice")
        self.assertEqual(len(self.analytics._events), 0)
        self.assertEqual(len(self.analytics._sessions), 0)
        self.assertEqual(len(self.analytics._active_sessions), 0)

    def test_delete_user_data_other_users_preserved(self):
        self.analytics.track("e1")
        self.analytics.delete_user_data("other_user")
        self.assertEqual(len(self.analytics._events), 1)

    def test_flush_clears_events(self):
        self.analytics.track("e1")
        self.analytics.flush()
        self.assertEqual(len(self.analytics._events), 0)

    def test_set_flush_interval(self):
        self.analytics.set_flush_interval(60.0)
        self.assertEqual(self.analytics._flush_interval, 60.0)

    def test_track_during_active_session_increments_event_count(self):
        self.analytics.start_session()
        sid = self.analytics.get_session_id()
        self.analytics.track("action1")
        self.analytics.track("action2")
        self.assertEqual(self.analytics._active_sessions[sid].events_count, 3)

    def test_track_page_view_increments_page_views(self):
        self.analytics.start_session()
        sid = self.analytics.get_session_id()
        self.analytics.track_page_view("/page1")
        self.analytics.track_page_view("/page2")
        self.assertEqual(self.analytics._active_sessions[sid].page_views, 2)


class TestCloudClient(unittest.TestCase):

    def test_import_all_modules(self):
        import zoya.cloud.analytics as analytics_mod
        import zoya.cloud.auth as auth_mod
        import zoya.cloud.database as db_mod
        import zoya.cloud.leaderboard as lb_mod
        import zoya.cloud.multiplayer as mp_mod
        import zoya.cloud.realtime as rt_mod
        import zoya.cloud.storage as store_mod

        self.assertTrue(hasattr(auth_mod, "AuthService"))
        self.assertTrue(hasattr(auth_mod, "AuthUser"))
        self.assertTrue(hasattr(auth_mod, "AuthSession"))
        self.assertTrue(hasattr(auth_mod, "AuthError"))
        self.assertTrue(hasattr(db_mod, "DatabaseService"))
        self.assertTrue(hasattr(db_mod, "QueryFilter"))
        self.assertTrue(hasattr(db_mod, "QueryResult"))
        self.assertTrue(hasattr(db_mod, "DatabaseError"))
        self.assertTrue(hasattr(store_mod, "StorageService"))
        self.assertTrue(hasattr(store_mod, "UploadResult"))
        self.assertTrue(hasattr(store_mod, "StorageObject"))
        self.assertTrue(hasattr(rt_mod, "RealtimeService"))
        self.assertTrue(hasattr(rt_mod, "RealtimeEvent"))
        self.assertTrue(hasattr(rt_mod, "RealtimeError"))
        self.assertTrue(hasattr(lb_mod, "LeaderboardService"))
        self.assertTrue(hasattr(lb_mod, "LeaderboardEntry"))
        self.assertTrue(hasattr(lb_mod, "LeaderboardError"))
        self.assertTrue(hasattr(mp_mod, "MultiplayerService"))
        self.assertTrue(hasattr(mp_mod, "Match"))
        self.assertTrue(hasattr(mp_mod, "Lobby"))
        self.assertTrue(hasattr(mp_mod, "MultiplayerError"))
        self.assertTrue(hasattr(analytics_mod, "AnalyticsService"))
        self.assertTrue(hasattr(analytics_mod, "AnalyticsEvent"))
        self.assertTrue(hasattr(analytics_mod, "AnalyticsQuery"))
        self.assertTrue(hasattr(analytics_mod, "AnalyticsResult"))
        self.assertTrue(hasattr(analytics_mod, "AnalyticsError"))

    def test_all_services_can_be_constructed(self):
        from zoya.cloud.analytics import AnalyticsService
        from zoya.cloud.auth import AuthService
        from zoya.cloud.database import DatabaseService
        from zoya.cloud.leaderboard import LeaderboardService
        from zoya.cloud.multiplayer import MultiplayerService
        from zoya.cloud.realtime import RealtimeService
        from zoya.cloud.storage import StorageService

        auth = AuthService()
        db = DatabaseService("http://localhost:54321", "api_key")
        store = StorageService("http://localhost:54321", "api_key")
        rt = RealtimeService("http://localhost:54321", "api_key")
        lb = LeaderboardService("http://localhost:54321", "api_key")
        analytics = AnalyticsService("http://localhost:54321", "api_key")
        mp = MultiplayerService("http://localhost:54321", "api_key", rt)

        self.assertIsNotNone(auth)
        self.assertIsNotNone(db)
        self.assertIsNotNone(store)
        self.assertIsNotNone(rt)
        self.assertIsNotNone(lb)
        self.assertIsNotNone(mp)
        self.assertIsNotNone(analytics)

    def test_end_to_end_multi_service_flow(self):
        from zoya.cloud.analytics import AnalyticsService
        from zoya.cloud.auth import AuthService
        from zoya.cloud.database import DatabaseService
        from zoya.cloud.leaderboard import LeaderboardService
        from zoya.cloud.multiplayer import MultiplayerService
        from zoya.cloud.realtime import RealtimeService
        from zoya.cloud.storage import StorageService

        rt = RealtimeService("http://localhost:54321", "key")
        auth = AuthService()
        db = DatabaseService("http://localhost:54321", "key")
        store = StorageService("http://localhost:54321", "key")
        lb = LeaderboardService("http://localhost:54321", "key")
        analytics = AnalyticsService("http://localhost:54321", "key")
        MultiplayerService("http://localhost:54321", "key", rt)

        rt.connect()
        self.assertTrue(rt.is_connected())

        auth.register("user@test.com", "pass", "user1")
        auth.login("user@test.com", "pass")
        self.assertTrue(auth.is_authenticated())

        d = db.create("items", {"value": 42})
        self.assertEqual(d["value"], 42)

        result = store.upload(b"hello", "greeting.txt")
        self.assertEqual(result.size, 5)

        self.assertEqual(len(lb.list_leaderboards()), 0)

        analytics.track("init")
        self.assertEqual(len(analytics._events), 1)

        rt.disconnect()
        self.assertFalse(rt.is_connected())

    def test_error_hierarchy(self):
        from zoya.cloud.analytics import AnalyticsError
        from zoya.cloud.auth import AuthError
        from zoya.cloud.database import DatabaseError
        from zoya.cloud.leaderboard import LeaderboardError
        from zoya.cloud.multiplayer import MultiplayerError
        from zoya.cloud.realtime import RealtimeError
        from zoya.cloud.storage import StorageError

        for exc_cls in [
            AuthError,
            DatabaseError,
            StorageError,
            RealtimeError,
            LeaderboardError,
            MultiplayerError,
            AnalyticsError,
        ]:
            e = exc_cls("test", "TEST_CODE")
            self.assertIsInstance(e, Exception)
            self.assertEqual(str(e), "test")
            self.assertEqual(e.code, "TEST_CODE")


if __name__ == "__main__":
    unittest.main()
