from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema

from app.utils.validators import validate_password_strength, validate_username


class UpdateProfileSchema(Schema):
    full_name = fields.String(required=False, validate=validate.Length(min=2, max=120))
    username = fields.String(required=False)

    @validates("username")
    def _validate_username(self, value, **kwargs):
        validate_username(value)


class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True, load_only=True)
    new_password = fields.String(required=True, load_only=True)
    confirm_new_password = fields.String(required=True, load_only=True)

    @validates("new_password")
    def _validate_password(self, value, **kwargs):
        validate_password_strength(value)

    @validates_schema
    def _validate_passwords_match(self, data, **kwargs):
        if data.get("new_password") != data.get("confirm_new_password"):
            raise ValidationError("Passwords do not match.", field_name="confirm_new_password")
