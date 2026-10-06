import re

from marshmallow import ValidationError

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")

PASSWORD_RULES = (
    (re.compile(r".{8,}"), "Password must be at least 8 characters long."),
    (re.compile(r"[A-Z]"), "Password must contain an uppercase letter."),
    (re.compile(r"[a-z]"), "Password must contain a lowercase letter."),
    (re.compile(r"\d"), "Password must contain a number."),
    (re.compile(r"[^A-Za-z0-9]"), "Password must contain a special character."),
)


def validate_username(value: str) -> None:
    if not USERNAME_RE.match(value):
        raise ValidationError(
            "Username must be 3-32 characters and contain only letters, numbers, and underscores."
        )


def validate_password_strength(value: str) -> None:
    errors = [message for pattern, message in PASSWORD_RULES if not pattern.search(value)]
    if errors:
        raise ValidationError(errors)
