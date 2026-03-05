"""
WebSocket endpoint for real-time dashboard streaming.
Pushes live telemetry, alerts, protocol metrics every 2-3 seconds.
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


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    """
    Main real-time feed. Streams:
    - protocol_update: protocol metrics every 3s
    - telemetry_update: performance metrics every 2s
    - alert_update: alert summary every 5s
    - heartbeat: connection keepalive every 10s
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial snapshot immediately
        overview = get_protocol_overview()
        perf = get_performance_metrics()
        alerts = get_alert_summary()
        qos = get_latest_qos()

        await websocket.send_json({
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

        # Start streaming loops
        tick = 0
        while True:
            tick += 1
            await asyncio.sleep(2)

            messages = []

            # Every 2s: telemetry/performance
            perf = get_performance_metrics()
            messages.append({
                "type": "telemetry_update",
                "data": perf,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Every 3s (tick % 2): protocol metrics
            if tick % 2 == 0:
                proto = get_protocol_overview()
                messages.append({
                    "type": "protocol_update",
                    "data": {
                        "protocols": proto.get("protocols", {}),
                        "summary": proto.get("summary", {}),
                        "algorithm_distribution": proto.get("algorithm_distribution", {}),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Every 5s (tick % 3): alerts
            if tick % 3 == 0:
                alerts = get_alert_summary()
                messages.append({
                    "type": "alert_update",
                    "data": alerts,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Every 10s (tick % 5): QoS + heartbeat
            if tick % 5 == 0:
                qos = get_latest_qos()
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
                await websocket.send_json(msg)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)
