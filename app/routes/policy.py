from fastapi import APIRouter
from app.services.policy_service import (
    seed_policies,
    calculate_policy_coverage,
    rollout_policy_to_assets
)

router = APIRouter()


@router.get("/coverage/{policy_name}")
def policy_coverage(policy_name: str):
    return calculate_policy_coverage(policy_name)

@router.post("/rollout/{policy_name}")
def rollout(policy_name: str, percentage: int = 90):
    return rollout_policy_to_assets(policy_name, percentage)
