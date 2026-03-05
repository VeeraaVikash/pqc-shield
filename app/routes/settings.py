from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.settings_models import Setting
from app.services.audit_service import log_event
from app.routes.auth import get_current_user

router = APIRouter()

DEFAULTS = {
    "crypto.default_kem": "Kyber768",
    "crypto.default_sig": "Dilithium3",
    "crypto.fallback_mode": "hybrid",
    "keys.auto_rotate": "true",
    "keys.rotation_days": "30",
    "security.mfa_enabled": "true",
    "security.session_timeout": "60",
    "security.audit_retention_days": "90",
    "notifications.email_alerts": "true",
    "notifications.slack_alerts": "false",
    "notifications.threshold": "medium",
    "policy.enforcement_mode": "enforce",
    "policy.canary_percentage": "10",
    "policy.fail_mode": "fail-open",
}


def seed_settings():
    db = SessionLocal()
    for key, value in DEFAULTS.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            category = key.split(".")[0]
            db.add(Setting(key=key, value=value, category=category))
    db.commit()
    db.close()


@router.get("/")
def get_all_settings(user=Depends(get_current_user)):
    seed_settings()
    db = SessionLocal()
    settings = db.query(Setting).all()
    db.close()
    result = {}
    for s in settings:
        if s.category not in result:
            result[s.category] = {}
        result[s.category][s.key] = {
            "value": s.value,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "updated_by": s.updated_by,
        }
    return result


class UpdateSetting(BaseModel):
    key: str
    value: str


class BulkUpdate(BaseModel):
    settings: list[UpdateSetting]


@router.put("/")
def update_settings(body: BulkUpdate, user=Depends(get_current_user)):
    db = SessionLocal()
    updated = []
    for item in body.settings:
        setting = db.query(Setting).filter(Setting.key == item.key).first()
        if setting:
            old_value = setting.value
            setting.value = item.value
            setting.updated_by = user.get("email", "admin")
            updated.append(item.key)
            log_event(
                event_type="SETTING_CHANGED",
                description=f"{item.key}: {old_value} -> {item.value}",
                severity="INFO",
                actor=user.get("email", "admin"),
                source="settings"
            )
        else:
            category = item.key.split(".")[0] if "." in item.key else "general"
            db.add(Setting(key=item.key, value=item.value, category=category, updated_by=user.get("email", "admin")))
            updated.append(item.key)
    db.commit()
    db.close()
    return {"updated": updated, "count": len(updated)}


@router.get("/{key}")
def get_setting(key: str, user=Depends(get_current_user)):
    db = SessionLocal()
    setting = db.query(Setting).filter(Setting.key == key).first()
    db.close()
    if not setting:
        return {"key": key, "value": None}
    return {"key": setting.key, "value": setting.value}