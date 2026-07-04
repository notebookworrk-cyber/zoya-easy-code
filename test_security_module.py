import os
import re
import sys
import uuid as _uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import unittest

from zoya.security import (
    AESCipher,
    Hasher,
    KeyGenerator,
    Sanitizer,
    Validator,
    __all__,
    __version__,
)


class TestAESCipher(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Hello, Zoya Security!"
        key = "test-key-12345"
        encrypted = AESCipher.encrypt(plaintext, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        self.assertEqual(plaintext, decrypted)

    def test_encrypt_decrypt_roundtrip_empty_string(self):
        plaintext = ""
        key = "some-key"
        encrypted = AESCipher.encrypt(plaintext, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        self.assertEqual(plaintext, decrypted)

    def test_encrypt_decrypt_roundtrip_special_chars(self):
        plaintext = "!@#$%^&*()_+={}[]|\\:;\"'<>,.?/~`\n\t"
        key = "key-with-special-chars!"
        encrypted = AESCipher.encrypt(plaintext, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        self.assertEqual(plaintext, decrypted)

    def test_encrypt_decrypt_roundtrip_unicode(self):
        plaintext = "日本語 español français русский عربي"
        key = "unicode-key-测试"
        encrypted = AESCipher.encrypt(plaintext, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        self.assertEqual(plaintext, decrypted)

    def test_encrypt_decrypt_roundtrip_long_text(self):
        plaintext = "A" * 10000
        key = "long-text-key"
        encrypted = AESCipher.encrypt(plaintext, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        self.assertEqual(plaintext, decrypted)

    def test_different_keys_different_ciphertext(self):
        plaintext = "Sensitive data"
        ct1 = AESCipher.encrypt(plaintext, "key-one")
        ct2 = AESCipher.encrypt(plaintext, "key-two")
        self.assertNotEqual(ct1, ct2)

    def test_encrypt_produces_base64_string(self):
        plaintext = "test data"
        key = "base64-check"
        encrypted = AESCipher.encrypt(plaintext, key)
        self.assertIsInstance(encrypted, str)
        self.assertTrue(re.match(r"^[A-Za-z0-9+/=]+$", encrypted))

    def test_decrypt_wrong_key_fails(self):
        plaintext = "secret message"
        key1 = "correct-key"
        key2 = "wrong-key"
        encrypted = AESCipher.encrypt(plaintext, key1)
        with self.assertRaises(Exception):  # noqa: B017
            AESCipher.decrypt(encrypted, key2)

    def test_decrypt_invalid_ciphertext_raises(self):
        with self.assertRaises(Exception):  # noqa: B017
            AESCipher.decrypt("!!!invalid!!!", "key")

    def test_same_plaintext_different_ciphertexts(self):
        plaintext = "deterministic check"
        key = "same-key"
        ct1 = AESCipher.encrypt(plaintext, key)
        ct2 = AESCipher.encrypt(plaintext, key)
        self.assertNotEqual(ct1, ct2)


class TestHasher(unittest.TestCase):
    def test_sha256_returns_correct_hex(self):
        result = Hasher.sha256("hello")
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(result, expected)

    def test_sha256_returns_hex_string(self):
        result = Hasher.sha256("test")
        self.assertIsInstance(result, str)
        self.assertTrue(re.match(r"^[0-9a-f]{64}$", result))

    def test_sha512_returns_correct_hex(self):
        result = Hasher.sha512("hello")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 128)

    def test_sha512_different_inputs_different_hashes(self):
        self.assertNotEqual(Hasher.sha512("a"), Hasher.sha512("b"))

    def test_md5_returns_correct_hash(self):
        result = Hasher.md5("hello")
        self.assertEqual(result, "5d41402abc4b2a76b9719d911017c592")

    def test_md5_emits_warning(self):
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Hasher.md5("test")
            self.assertTrue(any("MD5 is not secure" in str(m.message) for m in w))

    def test_hmac_consistent_output(self):
        r1 = Hasher.hmac("key", "data")
        r2 = Hasher.hmac("key", "data")
        self.assertEqual(r1, r2)

    def test_hmac_different_keys_different(self):
        self.assertNotEqual(Hasher.hmac("key1", "data"), Hasher.hmac("key2", "data"))

    def test_pbkdf2_hash_and_verify_roundtrip(self):
        pw = "my_secure_password"
        h, salt = Hasher.pbkdf2(pw)
        self.assertTrue(Hasher.verify_pbkdf2(pw, h, salt))

    def test_pbkdf2_wrong_password_fails(self):
        pw = "correct_password"
        h, salt = Hasher.pbkdf2(pw)
        self.assertFalse(Hasher.verify_pbkdf2("wrong_password", h, salt))

    def test_pbkdf2_different_salts_different_hashes(self):
        pw = "password"
        h1, _ = Hasher.pbkdf2(pw, salt="salt1")
        h2, _ = Hasher.pbkdf2(pw, salt="salt2")
        self.assertNotEqual(h1, h2)

    def test_bcrypt_like_hash_and_verify_roundtrip(self):
        pw = "my_password"
        h, salt = Hasher.bcrypt_like(pw)
        self.assertTrue(Hasher.verify_bcrypt_like(pw, h, salt))

    def test_bcrypt_like_wrong_password_fails(self):
        pw = "correct"
        h, salt = Hasher.bcrypt_like(pw)
        self.assertFalse(Hasher.verify_bcrypt_like("wrong", h, salt))

    def test_bcrypt_like_different_salts_different_hashes(self):
        h1, _ = Hasher.bcrypt_like("pw", salt="salt_a")
        h2, _ = Hasher.bcrypt_like("pw", salt="salt_b")
        self.assertNotEqual(h1, h2)

    def test_different_passwords_different_hashes_pbkdf2(self):
        h1, s1 = Hasher.pbkdf2("password1")
        h2, s2 = Hasher.pbkdf2("password2")
        self.assertNotEqual(h1, h2)


class TestKeyGenerator(unittest.TestCase):
    def test_generate_secret_key_default_length(self):
        key = KeyGenerator.generate_secret_key()
        self.assertEqual(len(key), 64)

    def test_generate_secret_key_custom_length(self):
        key = KeyGenerator.generate_secret_key(16)
        self.assertEqual(len(key), 32)

    def test_generate_api_key_has_correct_prefix(self):
        key = KeyGenerator.generate_api_key()
        self.assertTrue(key.startswith("zk_"))

    def test_generate_api_key_custom_prefix(self):
        key = KeyGenerator.generate_api_key(prefix="prod_")
        self.assertTrue(key.startswith("prod_"))

    def test_generate_otp_returns_numeric_string(self):
        otp = KeyGenerator.generate_otp()
        self.assertTrue(otp.isdigit())

    def test_generate_otp_default_length(self):
        otp = KeyGenerator.generate_otp()
        self.assertEqual(len(otp), 6)

    def test_generate_otp_custom_length(self):
        otp = KeyGenerator.generate_otp(length=8)
        self.assertEqual(len(otp), 8)

    def test_generate_uuid4_returns_uuid_format(self):
        uid = KeyGenerator.generate_uuid4()
        self.assertIsInstance(uid, str)
        parsed = _uuid.UUID(uid)
        self.assertEqual(parsed.version, 4)

    def test_uuid4_string_format(self):
        uid = KeyGenerator.generate_uuid4()
        self.assertTrue(
            re.match(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
                uid,
                re.I,
            )
        )


class TestValidator(unittest.TestCase):
    def test_email_accepts_valid(self):
        self.assertTrue(Validator.email("user@example.com"))
        self.assertTrue(Validator.email("user.name+tag@example.co.uk"))
        self.assertTrue(Validator.email("a@b.cd"))

    def test_email_rejects_invalid(self):
        self.assertFalse(Validator.email("not-an-email"))
        self.assertFalse(Validator.email("@example.com"))
        self.assertFalse(Validator.email("user@"))
        self.assertFalse(Validator.email("user@.com"))

    def test_url_accepts_valid(self):
        self.assertTrue(Validator.url("https://example.com"))
        self.assertTrue(Validator.url("http://example.com/path?q=1"))
        self.assertTrue(Validator.url("ftp://files.example.com"))

    def test_url_rejects_javascript(self):
        self.assertFalse(Validator.url("javascript:alert('xss')"))

    def test_url_rejects_localhost(self):
        self.assertFalse(Validator.url("http://localhost:3000"))
        self.assertFalse(Validator.url("http://127.0.0.1"))

    def test_url_allow_localhost(self):
        self.assertTrue(Validator.url("http://localhost:3000", allow_local=True))

    def test_ip_address_accepts_ipv4(self):
        self.assertTrue(Validator.ip_address("192.168.1.1"))
        self.assertTrue(Validator.ip_address("8.8.8.8"))

    def test_ip_address_accepts_ipv6(self):
        self.assertTrue(Validator.ip_address("::1"))
        self.assertTrue(Validator.ip_address("2001:db8::ff00:42:8329"))

    def test_ip_address_rejects_invalid(self):
        self.assertFalse(Validator.ip_address("not-an-ip"))
        self.assertFalse(Validator.ip_address("999.999.999.999"))

    def test_credit_card_validates_luhn(self):
        self.assertTrue(Validator.credit_card("4111111111111111"))
        self.assertTrue(Validator.credit_card("5500000000000004"))

    def test_credit_card_rejects_invalid(self):
        self.assertFalse(Validator.credit_card("1234567890123456"))
        self.assertFalse(Validator.credit_card("abc"))
        self.assertFalse(Validator.credit_card(""))

    def test_phone_accepts_valid_us(self):
        self.assertTrue(Validator.phone("+1 (555) 123-4567", "US"))
        self.assertTrue(Validator.phone("5551234567", "US"))

    def test_phone_accepts_valid_uk(self):
        self.assertTrue(Validator.phone("+44 7123 456789", "UK"))

    def test_phone_rejects_invalid_region(self):
        self.assertFalse(Validator.phone("not-a-phone", "US"))

    def test_phone_unknown_region(self):
        self.assertFalse(Validator.phone("+1 555-1234", "XX"))

    def test_password_strength_returns_dict(self):
        result = Validator.password_strength("Abcdef1!")
        self.assertIsInstance(result, dict)
        self.assertIn("score", result)
        self.assertIn("feedback", result)

    def test_password_strength_strong(self):
        result = Validator.password_strength("Str0ng!Pass")
        self.assertGreaterEqual(result["score"], 4)

    def test_password_strength_weak(self):
        result = Validator.password_strength("weak")
        self.assertLess(result["score"], 3)

    def test_sql_injection_detects_union_select(self):
        self.assertTrue(Validator.sql_injection("1 UNION SELECT * FROM users"))

    def test_sql_injection_detects_drop_table(self):
        self.assertTrue(Validator.sql_injection("; DROP TABLE users; --"))

    def test_sql_injection_detects_or_1_equals_1(self):
        self.assertTrue(Validator.sql_injection("' OR '1'='1"))

    def test_sql_injection_safe_string(self):
        self.assertFalse(Validator.sql_injection("hello world"))

    def test_xss_detects_script_tag(self):
        self.assertTrue(Validator.xss("<script>alert('xss')</script>"))

    def test_xss_detects_javascript_scheme(self):
        self.assertTrue(Validator.xss("javascript:alert(1)"))

    def test_xss_detects_on_event(self):
        self.assertTrue(Validator.xss("<img onerror='alert(1)' src=x>"))

    def test_xss_detects_iframe(self):
        self.assertTrue(Validator.xss("<iframe src='http://evil.com'></iframe>"))

    def test_xss_safe_string(self):
        self.assertFalse(Validator.xss("Hello, world!"))

    def test_path_traversal_detects_dotdot(self):
        self.assertTrue(Validator.path_traversal("../../../etc/passwd"))

    def test_path_traversal_detects_url_encoded(self):
        self.assertTrue(Validator.path_traversal("%2e%2e%2f%2e%2e%2f"))

    def test_path_traversal_safe_string(self):
        self.assertFalse(Validator.path_traversal("safe/path/to/file.txt"))

    def test_hex_color_valid(self):
        self.assertTrue(Validator.hex_color("#fff"))
        self.assertTrue(Validator.hex_color("#aabbcc"))
        self.assertTrue(Validator.hex_color("#AABBCCDD"))

    def test_hex_color_invalid(self):
        self.assertFalse(Validator.hex_color("not-a-color"))
        self.assertFalse(Validator.hex_color("#gggggg"))
        self.assertFalse(Validator.hex_color("123"))

    def test_json_valid(self):
        self.assertTrue(Validator.json('{"key": "value"}'))
        self.assertTrue(Validator.json("[1, 2, 3]"))
        self.assertTrue(Validator.json('"string"'))

    def test_json_invalid(self):
        self.assertFalse(Validator.json("{invalid json}"))
        self.assertFalse(Validator.json("not json"))

    def test_validator_non_string_inputs(self):
        self.assertFalse(Validator.email(123))
        self.assertFalse(Validator.url(123))
        self.assertFalse(Validator.ip_address(123))
        self.assertFalse(Validator.credit_card(123))
        self.assertFalse(Validator.phone(123))
        self.assertFalse(Validator.sql_injection(123))
        self.assertFalse(Validator.xss(123))
        self.assertFalse(Validator.path_traversal(123))
        self.assertFalse(Validator.hex_color(123))
        self.assertFalse(Validator.json(123))


class TestSanitizer(unittest.TestCase):
    def test_strip_html_removes_tags(self):
        result = Sanitizer.strip_html("<p>Hello</p><script>bad</script>")
        self.assertEqual(result, "Hellobad")

    def test_strip_html_allowed_tags(self):
        result = Sanitizer.strip_html(
            "<p>Hello</p><script>bad</script>", allowed_tags=["p"]
        )
        self.assertEqual(result, "<p>Hello</p>bad")

    def test_strip_html_non_string(self):
        self.assertEqual(Sanitizer.strip_html(123), "")

    def test_escape_html_escapes_angle_brackets(self):
        result = Sanitizer.escape_html("<script>alert('test')</script>")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)

    def test_escape_html_escapes_ampersand_and_quotes(self):
        result = Sanitizer.escape_html('& "quoted"')
        self.assertIn("&amp;", result)
        self.assertIn("&quot;", result)

    def test_escape_html_escapes_apostrophe(self):
        result = Sanitizer.escape_html("it's")
        self.assertIn("&#x27;", result)

    def test_escape_html_non_string(self):
        self.assertEqual(Sanitizer.escape_html(None), "")

    def test_escape_shell_removes_dangerous_chars(self):
        result = Sanitizer.escape_shell("rm -rf /; cat /etc/passwd")
        self.assertNotIn(";", result)
        self.assertNotIn(" ", result)

    def test_escape_shell_preserves_safe_chars(self):
        result = Sanitizer.escape_shell("hello_world-123")
        self.assertEqual(result, "hello_world-123")

    def test_escape_shell_non_string(self):
        self.assertEqual(Sanitizer.escape_shell(42), "")

    def test_sanitize_filename_removes_dangerous_chars(self):
        result = Sanitizer.sanitize_filename('file<>:"/\\|?*.txt')
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn("/", result)

    def test_sanitize_filename_strips_leading_trailing_dots(self):
        result = Sanitizer.sanitize_filename("..file..")
        self.assertFalse(result.startswith("."))
        self.assertFalse(result.endswith("."))

    def test_sanitize_filename_empty_becomes_unnamed(self):
        result = Sanitizer.sanitize_filename("...")
        self.assertEqual(result, "unnamed_file")

    def test_sanitize_filename_non_string(self):
        self.assertEqual(Sanitizer.sanitize_filename(123), "")

    def test_sanitize_url_blocks_javascript(self):
        self.assertEqual(Sanitizer.sanitize_url("javascript:alert(1)"), "")

    def test_sanitize_url_blocks_vbscript(self):
        self.assertEqual(Sanitizer.sanitize_url("vbscript:msgbox"), "")

    def test_sanitize_url_blocks_data(self):
        self.assertEqual(Sanitizer.sanitize_url("data:text/html,<script>"), "")

    def test_sanitize_url_blocks_file(self):
        self.assertEqual(Sanitizer.sanitize_url("file:///etc/passwd"), "")

    def test_sanitize_url_preserves_safe(self):
        self.assertEqual(
            Sanitizer.sanitize_url("https://example.com"),
            "https://example.com",
        )

    def test_sanitize_url_non_string(self):
        self.assertEqual(Sanitizer.sanitize_url(123), "")

    def test_normalize_unicode_nfc(self):
        composed = "\u00e9"
        decomposed = "\u0065\u0301"
        result = Sanitizer.normalize_unicode(decomposed)
        self.assertEqual(result, composed)

    def test_normalize_unicode_non_string(self):
        self.assertEqual(Sanitizer.normalize_unicode(None), "")

    def test_strip_control_chars_removes_control_chars(self):
        result = Sanitizer.strip_control_chars("Hello\x00World\x1fTest")
        self.assertEqual(result, "HelloWorldTest")

    def test_strip_control_chars_preserves_normal(self):
        result = Sanitizer.strip_control_chars("Hello, World!")
        self.assertEqual(result, "Hello, World!")

    def test_strip_control_chars_non_string(self):
        self.assertEqual(Sanitizer.strip_control_chars(42), "")


class TestSecurityInit(unittest.TestCase):
    def test_all_classes_importable(self):
        self.assertIsNotNone(AESCipher)
        self.assertIsNotNone(Hasher)
        self.assertIsNotNone(KeyGenerator)
        self.assertIsNotNone(Validator)
        self.assertIsNotNone(Sanitizer)

    def test_version_exists(self):
        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)

    def test_all_contains_expected(self):
        expected = {
            "AESCipher",
            "Hasher",
            "KeyGenerator",
            "Validator",
            "Sanitizer",
            "__version__",
        }
        self.assertTrue(expected.issubset(set(__all__)))

    def test_all_is_complete_list(self):
        self.assertEqual(len(__all__), 6)


if __name__ == "__main__":
    unittest.main()
