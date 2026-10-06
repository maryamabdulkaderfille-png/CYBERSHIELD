from marshmallow import Schema, fields, validate


class NotificationQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=50))
    unread_only = fields.Boolean(load_default=False)
