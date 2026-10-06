from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema

from app.utils.validators import validate_password_strength, validate_username


class RegisterSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    username = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    confirm_password = fields.String(required=True, load_only=True)

    @validates("username")
    def _validate_username(self, value, **kwargs):
        validate_username(value)

    @validates("password")
    def _validate_password(self, value, **kwargs):
        validate_password_strength(value)

    @validates_schema
    def _validate_passwords_match(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("Passwords do not match.", field_name="confirm_password")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    remember_me = fields.Boolean(load_default=False)


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    token = fields.String(required=True)
    password = fields.String(required=True, load_only=True)
    confirm_password = fields.String(required=True, load_only=True)

    @validates("password")
    def _validate_password(self, value, **kwargs):
        validate_password_strength(value)

    @validates_schema
    def _validate_passwords_match(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("Passwords do not match.", field_name="confirm_password")


class VerifyEmailSchema(Schema):
    token = fields.String(required=True)


class ResendVerificationSchema(Schema):
    email = fields.Email(required=True)
