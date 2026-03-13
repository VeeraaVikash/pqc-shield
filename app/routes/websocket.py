"""
WebSocket endpoint for real-time dashboard streaming.
Pushes live telemetry, alerts, protocol metrics every 2-3 seconds.

FIX: All sync DB service calls now run via asyncio.to_thread() so they
     don't block the async event loop — this was causing disconnects and
     the 'Reconnecting...' banner on the frontend.
"""
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.command_center_service import get_command_center_overview
from app.services.protocol_simulator import get_protocol_overview
from app.services.telemetry_service import get_performance_metrics
from app.services.alert_service import get_alert_summary
from app.services.qos_service import get_latest_qos

router = APIRouter()

# Track active connections
active_connections: list[WebSocket] = []


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """Send JSON safely — returns False if connection is dead."""
    try:
        await websocket.send_json(data)
        return True
    except Exception:
        return False


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    """
    Main real-time feed. Streams:
    - protocol_update:  protocol metrics every 4s
    - telemetry_update: performance metrics every 2s
    - alert_update:     alert summary every 6s
    - heartbeat:        connection keepalive every 10s

    FIX: sync DB calls wrapped in asyncio.to_thread() so they never
         block the event loop and cause WebSocket timeouts.
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # ── Initial snapshot ──────────────────────────────────────────
        # FIX: run all blocking DB calls in thread pool concurrently
        overview, perf, alerts, qos = await asyncio.gather(
            asyncio.to_thread(get_protocol_overview),
            asyncio.to_thread(get_performance_metrics),
            asyncio.to_thread(get_alert_summary),
            asyncio.to_thread(get_latest_qos),
        )

        ok = await _safe_send(websocket, {
            "type": "initial_snapshot",
            "data": {
                "protocols": overview,
                "performance": perf,
                "alerts": alerts,
                "qos": qos,
                "connected_clients": len(active_connections),
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

        if not ok:
            return

        # ── Streaming loop ────────────────────────────────────────────
        tick = 0
        while True:
            tick += 1
            await asyncio.sleep(2)

            messages = []

            # Every 2s: telemetry/performance
            # FIX: to_thread so DB query doesn't stall the event loop
            perf = await asyncio.to_thread(get_performance_metrics)
            messages.append({
                "type": "telemetry_update",
                "data": perf,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Every 2s: latest handshake for animation
            try:
                from app.routes.telemetry import recent_handshakes
                recents = await asyncio.to_thread(recent_handshakes)
                if recents:
                    messages.append({
                        "type": "handshake_stream",
                        "handshakes": [recents[0]],
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception:
                pass  # non-critical — don't let this kill the connection

            # Every 4s (tick % 2): protocol metrics
            if tick % 2 == 0:
                proto = await asyncio.to_thread(get_protocol_overview)
                messages.append({
                    "type": "protocol_update",
                    "data": {
                        "protocols": proto.get("protocols", {}),
                        "summary": proto.get("summary", {}),
                        "algorithm_distribution": proto.get("algorithm_distribution", {}),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Every 6s (tick % 3): alerts
            if tick % 3 == 0:
                alerts = await asyncio.to_thread(get_alert_summary)
                messages.append({
                    "type": "alert_update",
                    "data": alerts,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Every 10s (tick % 5): QoS + heartbeat
            if tick % 5 == 0:
                qos = await asyncio.to_thread(get_latest_qos)
                messages.append({
                    "type": "qos_update",
                    "data": qos,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                messages.append({
                    "type": "heartbeat",
                    "data": {"connected_clients": len(active_connections)},
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Send all messages for this tick
            for msg in messages:
                ok = await _safe_send(websocket, msg)
                if not ok:
                    return  # FIX: stop loop cleanly if client disconnected

    except WebSocketDisconnect:
        pass  # normal — client navigated away
    except Exception as e:
        print(f"[WebSocket] Unexpected error: {e}")
    finally:
        # FIX: always clean up — was missing finally block
        if websocket in active_connections:
            active_connections.remove(websocket)
        try:
            await websocket.close()
        except Exception:
            pass