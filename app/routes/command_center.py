from fastapi import APIRouter
from app.services.command_center_service import get_command_center_overview

router = APIRouter()


@router.get("/overview")
def command_center():
    return get_command_center_overview()