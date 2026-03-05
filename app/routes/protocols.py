from fastapi import APIRouter
from app.services.protocol_simulator import (
    get_protocol_overview,
    get_active_vpn_peers,
    get_ipsec_tunnels,
)

router = APIRouter()


@router.get("/overview")
def protocol_overview():
    """Unified view of all 4 protocols — TLS, SSH, IPsec, VPN."""
    return get_protocol_overview()


@router.get("/vpn/peers")
def vpn_peers():
    """Active VPN peer connections."""
    return get_active_vpn_peers()


@router.get("/ipsec/tunnels")
def ipsec_tunnels():
    """Active IPsec tunnels."""
    return get_ipsec_tunnels()
