"""Threat Intelligence Center routes — platform-wide data, available to any
authenticated user (read-only; no per-user scoping, unlike Dashboard/Scan
Center/Profile)."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.schemas.threat_intel import ThreatDomainQuerySchema
from app.services import threat_intel_service
from app.utils.errors import APIError

threats_bp = Blueprint("threats", __name__)


@threats_bp.get("")
@jwt_required()
def get_threat_intelligence():
    return jsonify(threat_intel_service.get_threat_intelligence_summary())


@threats_bp.get("/domains")
@jwt_required()
def list_threat_domains():
    try:
        params = ThreatDomainQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    items, total = threat_intel_service.get_threat_domains(
        params["page"],
        params["per_page"],
        search=params["search"],
        risk_level=params["risk_level"],
        sort_by=params["sort_by"],
        sort_dir=params["sort_dir"],
    )
    return jsonify(
        {
            "items": items,
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@threats_bp.get("/export")
@jwt_required()
def export_threat_intelligence():
    raise APIError("Threat intelligence export is not yet implemented in this version of CyberShield.", 501)
