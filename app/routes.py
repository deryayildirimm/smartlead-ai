from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)

from constants import ResponseMessages
from app.database import lead_ekle, tum_leadler
from app.validators import require_object, validate_lead


pages_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__)


@pages_bp.get("/")
def ana_sayfa():
    return render_template("index.html")


@pages_bp.get("/dashboard")
def yonetim_paneli():
    return render_template("dashboard.html")


@api_bp.post("/sohbet")
def sohbet():
    data = request.get_json()
    require_object(data)

    ai_service = current_app.extensions["ai_service"]

    cevap = ai_service.yanit_uret(
        data.get("mesaj"),
        data.get("gecmis", []),
    )

    return jsonify({
        "basari": True,
        "cevap": cevap,
    }), 200


@api_bp.post("/leads")
def kayit_olustur():
    data = request.get_json()
    temiz_veri = validate_lead(data)

    kayit_id = lead_ekle(**temiz_veri)

    return jsonify({
        "basari": True,
        "id": kayit_id,
        "mesaj": ResponseMessages.LEAD_CREATED,
    }), 201


@api_bp.get("/leads")
def kayitlari_listele():
    return jsonify({
        "basari": True,
        "leadler": tum_leadler(),
    }), 200