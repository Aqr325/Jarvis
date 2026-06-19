"""
J.A.R.V.I.S. WebSocket Manager
---------------------------------
Handles real-time bidirectional communication between client and agent.
Supports streaming responses, notifications, and command execution.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.websocket")


@dataclass
class WSConnection:
    """Represents a single WebSocket connection."""
    ws: Any
    client_id: str
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True

    async def send(self, message: dict):
        """Send a message to the client."""
        try:
            if isinstance(self.ws, dict):
                logger.debug(f"[TEST] Would send to {self.client_id}: {message}")
                return
            await self.ws.send_json(message)
            self.last_activity = time.time()
        except Exception as e:
            logger.error(f"Failed to send to {self.client_id}: {e}")
            self.is_active = False

    def heartbeat(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()


class WebSocketManager:
    """Manages all WebSocket connections, broadcasts, and streaming."""

    TYPE_CHAT_RESPONSE = "chat_response"
    TYPE_TOOL_RESULT = "tool_result"
    TYPE_NOTIFICATION = "notification"
    TYPE_HEARTBEAT = "heartbeat"
    TYPE_ERROR = "error"

    def __init__(self):
        self.connections: Dict[str, WSConnection] = {}
        self._subscription_map: Dict[str, Set[str]] = {}
        logger.info("WebSocket manager initialized")

    async def connect(self, ws, client_id: str) -> str:
        """Register a new WebSocket connection."""
        conn = WSConnection(ws=ws, client_id=client_id)
        self.connections[client_id] = conn
        self._subscription_map[client_id] = {"general", "notifications"}
        
        logger.info(f"Client {client_id} connected (total: {len(self.connections)})")
        
        await conn.send({
            "type": self.TYPE_NOTIFICATION,
            "payload": {
                "message": "Connected to J.A.R.V.I.S. WebSocket",
                "client_id": client_id,
            },
            "timestamp": time.time(),
        })
        
        return client_id

    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.connections:
            self.connections[client_id].is_active = False
            del self.connections[client_id]
            if client_id in self._subscription_map:
                del self._subscription_map[client_id]
            logger.info(f"Client {client_id} disconnected (remaining: {len(self.connections)})")

    async def send_to_client(
        self, client_id: str, message_type: str, payload: dict
    ) -> bool:
        """Send a specific message to a single client."""
        conn = self.connections.get(client_id)
        if not conn or not conn.is_active:
            return False
        
        message = {
            "type": message_type,
            "payload": payload,
            "timestamp": time.time(),
        }
        
        await conn.send(message)
        return True

    async def broadcast(
        self, message_type: str, payload: dict, exclude_client: Optional[str] = None
    ):
        """Broadcast a message to all connected clients."""
        message = {
            "type": message_type,
            "payload": payload,
            "timestamp": time.time(),
        }
        
        for client_id, conn in self.connections.items():
            if client_id == exclude_client:
                continue
            if conn.is_active:
                await conn.send(message)

    async def stream_response(
        self, 
        client_id: str, 
        chunks: List[str], 
        delay: float = 0.1
    ):
        """Stream a response in chunks (typewriter effect)."""
        full_message = ""
        for idx, chunk in enumerate(chunks):
            full_message += chunk
            await self.send_to_client(
                client_id, 
                self.TYPE_CHAT_RESPONSE,
                {
                    "partial": True,
                    "message": full_message,
                    "chunk_index": idx,
                }
            )
            await asyncio.sleep(delay)
        
        await self.send_to_client(
            client_id,
            self.TYPE_CHAT_RESPONSE,
            {
                "partial": False,
                "message": full_message,
                "complete": True,
            }
        )

    async def send_tool_progress(
        self, client_id: str, tool_name: str, status: str, details: dict = None
    ):
        """Notify client about tool execution progress."""
        await self.send_to_client(
            client_id,
            self.TYPE_TOOL_RESULT,
            {
                "tool": tool_name,
                "status": status,
                "details": details or {},
            }
        )

    async def heartbeat_check(self):
        """Ping all connections and detect/cleanup stale ones (> 2 min inactive)."""
        now = time.time()
        stale_clients = []
        
        for client_id, conn in list(self.connections.items()):
            idle_seconds = now - conn.last_activity
            if idle_seconds > 120:  # 2 minutes threshold
                stale_clients.append(client_id)
                logger.warning(
                    f"Closing stale WebSocket connection: {client_id} (idle {idle_seconds:.0f}s)"
                )
                await self.disconnect(client_id)
            elif idle_seconds > 60 and conn.is_active:
                # Send ping to check if still alive
                try:
                    await conn.send({
                        "type": self.TYPE_HEARTBEAT,
                        "payload": {"ping": True, "idle_seconds": round(idle_seconds)},
                        "timestamp": now,
                    })
                except Exception as e:
                    logger.error(f"Heartbeat failed for {client_id}: {e}")
                    await self.disconnect(client_id)
        
        if stale_clients:
            logger.info(f"Heartbeat check: cleaned up {len(stale_clients)} stale connections")

    def get_connection_count(self) -> int:
        """Return number of active connections."""
        return sum(1 for c in self.connections.values() if c.is_active)
