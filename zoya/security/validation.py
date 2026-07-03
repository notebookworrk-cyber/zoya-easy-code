import re
import json as _json
import ipaddress
import unicodedata
from urllib.parse import urlparse
from typing import List, Dict, Optional


class Validator:
    _email_re = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    _sql_injection_patterns = re.compile(
        r"(union\s+select|select\s+.*\s+from|insert\s+into|"
        r"drop\s+table|delete\s+from|update\s+.*\s+set|"
        r"alter\s+table|create\s+table|truncate\s+table|"
        r"exec\s*\(|execute\s*\(|"
        r"or\s+\d+=\d+|and\s+\d+=\d+|"
        r"'\s*or\s*'[^']*'\s*=\s*'|"
        r"'\s*or\s*1\s*=\s*1|"
        r"--(?:\s|$)|#(?:\s|$)|;\s*--)",
        re.IGNORECASE,
    )

    _xss_patterns = re.compile(
        r"(<script[^>]*>.*?</script>|"
        r"javascript\s*:|"
        r"on\w+\s*=\s*['\"][^'\"]*['\"]|"
        r"on\w+\s*=\s*[^\s>]+|"
        r"<iframe[^>]*>|"
        r"<embed[^>]*>|"
        r"<object[^>]*>|"
        r"expression\s*\(|"
        r"vbscript\s*:|"
        r"data\s*:\s*text/html)",
        re.IGNORECASE,
    )

    _path_traversal_pattern = re.compile(
        r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c|%252e%252e%255c|%252e%252e%252f)"
    )

    _phone_patterns = {
        "US": re.compile(r"^\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$"),
        "UK": re.compile(r"^\+?44\s?\d{4}\s?\d{6}$"),
        "DE": re.compile(r"^\+?49\s?\d{3,4}\s?\d{7,8}$"),
        "FR": re.compile(r"^\+?33\s?\d{1}\s?\d{8}$"),
        "JP": re.compile(r"^\+?81\s?\d{1,4}\s?\d{4}\s?\d{4}$"),
        "CN": re.compile(r"^\+?86\s?\d{3}\s?\d{4}\s?\d{4}$"),
        "IN": re.compile(r"^\+?91\s?\d{5}\s?\d{5}$"),
        "BR": re.compile(r"^\+?55\s?\d{2}\s?\d{4,5}\s?\d{4}$"),
    }

    _hex_color_re = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
    _hex_string_re = re.compile(r"^[0-9a-fA-F]+$")
    _base64_re = re.compile(
        r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
    )

    @staticmethod
    def email(email: str) -> bool:
        if not isinstance(email, str) or len(email) > 254:
            return False
        return bool(Validator._email_re.match(email))

    @staticmethod
    def url(url: str, allow_local: bool = False) -> bool:
        if not isinstance(url, str) or not url.strip():
            return False
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https", "ftp"):
                return False
            if not parsed.netloc:
                return False
            if not allow_local:
                hostname = parsed.hostname or ""
                if hostname in (
                    "localhost",
                    "127.0.0.1",
                    "::1",
                    "0.0.0.0",
                ):
                    return False
                if hostname.endswith(".local") or hostname.endswith(".internal"):
                    return False
                try:
                    addr = ipaddress.ip_address(hostname)
                    if addr.is_private or addr.is_loopback:
                        return False
                except ValueError:
                    pass
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def ip_address(ip: str) -> bool:
        if not isinstance(ip, str):
            return False
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def credit_card(number: str) -> bool:
        if not isinstance(number, str):
            return False
        digits = re.sub(r"\D", "", number)
        if len(digits) < 13 or len(digits) > 19:
            return False
        total = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def phone(phone: str, region: str = "US") -> bool:
        if not isinstance(phone, str):
            return False
        pattern = Validator._phone_patterns.get(region.upper())
        if pattern is None:
            return False
        return bool(pattern.match(phone.strip()))

    @staticmethod
    def password_strength(password: str) -> Dict:
        if not isinstance(password, str):
            return {"score": 0, "feedback": "invalid input"}
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>_~`\-+=\[\]\\;'/]", password))
        min_length = len(password) >= 8
        score = sum([has_upper, has_lower, has_digit, has_special, min_length])
        feedback = []
        if not has_upper:
            feedback.append("add uppercase letters")
        if not has_lower:
            feedback.append("add lowercase letters")
        if not has_digit:
            feedback.append("add digits")
        if not has_special:
            feedback.append("add special characters")
        if not min_length:
            feedback.append("use at least 8 characters")
        if score >= 4:
            feedback = ["strong password"]
        elif score >= 3:
            feedback = ["moderate password"] + feedback
        else:
            feedback = ["weak password"] + feedback
        return {
            "score": score,
            "has_upper": has_upper,
            "has_lower": has_lower,
            "has_digit": has_digit,
            "has_special": has_special,
            "min_length": min_length,
            "feedback": feedback,
        }

    @staticmethod
    def sql_injection(input: str) -> bool:
        if not isinstance(input, str):
            return False
        return bool(Validator._sql_injection_patterns.search(input))

    @staticmethod
    def xss(input: str) -> bool:
        if not isinstance(input, str):
            return False
        return bool(Validator._xss_patterns.search(input))

    @staticmethod
    def path_traversal(input: str) -> bool:
        if not isinstance(input, str):
            return False
        return bool(Validator._path_traversal_pattern.search(input))

    @staticmethod
    def hex_color(input: str) -> bool:
        if not isinstance(input, str):
            return False
        return bool(Validator._hex_color_re.match(input))

    @staticmethod
    def hex_string(input: str) -> bool:
        if not isinstance(input, str):
            return False
        return bool(Validator._hex_string_re.match(input))

    @staticmethod
    def base64(input: str) -> bool:
        if not isinstance(input, str) or len(input) % 4 != 0:
            return False
        return bool(Validator._base64_re.match(input))

    @staticmethod
    def json(input: str) -> bool:
        if not isinstance(input, str):
            return False
        try:
            _json.loads(input)
            return True
        except (_json.JSONDecodeError, ValueError):
            return False


class Sanitizer:
    _html_tag_re = re.compile(r"<[^>]*>")
    _control_chars_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    _dangerous_filename_re = re.compile(
        r'[<>:"/\\|?*\x00-\x1f]'
    )
    _shell_dangerous_re = re.compile(r"[^\w@%+=:,./-]")

    @staticmethod
    def strip_html(html: str, allowed_tags: List[str] = None) -> str:
        if not isinstance(html, str):
            return ""
        if allowed_tags is None:
            return Sanitizer._html_tag_re.sub("", html)
        allowed_set = frozenset(t.lower() for t in allowed_tags)

        def _replace_tag(match):
            tag = match.group(0)
            tag_name_match = re.match(r"</?(\w+)", tag)
            if tag_name_match:
                tag_name = tag_name_match.group(1).lower()
                if tag_name in allowed_set:
                    return tag
            return ""

        return Sanitizer._html_tag_re.sub(_replace_tag, html)

    @staticmethod
    def escape_html(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return (
            input.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    @staticmethod
    def escape_shell(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return Sanitizer._shell_dangerous_re.sub("", input)

    @staticmethod
    def escape_sql(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return input.replace("'", "''").replace("\\", "\\\\")

    @staticmethod
    def strip_whitespace(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return " ".join(input.split())

    @staticmethod
    def strip_control_chars(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return Sanitizer._control_chars_re.sub("", input)

    @staticmethod
    def normalize_unicode(input: str) -> str:
        if not isinstance(input, str):
            return ""
        return unicodedata.normalize("NFC", input)

    @staticmethod
    def sanitize_filename(input: str) -> str:
        if not isinstance(input, str):
            return ""
        cleaned = Sanitizer._dangerous_filename_re.sub("_", input)
        cleaned = cleaned.strip(". ")
        if not cleaned:
            return "unnamed_file"
        return cleaned

    @staticmethod
    def sanitize_url(input: str) -> str:
        if not isinstance(input, str):
            return ""
        input = input.strip()
        dangerous_schemes = (
            "javascript:",
            "vbscript:",
            "data:",
            "file:",
        )
        for scheme in dangerous_schemes:
            if input.lower().startswith(scheme):
                return ""
        return input
