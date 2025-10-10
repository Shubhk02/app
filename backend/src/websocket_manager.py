import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user role
        self.active_connections: Dict[str, List[WebSocket]] = {
            'patient': [],
            'staff': [],
            'admin': []
        }
        # Store connections by user ID for targeted updates
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_role: str):
        await websocket.accept()
        self.user_connections[user_id] = websocket
        self.active_connections[user_role].append(websocket)
        logger.info(f"User {user_id} ({user_role}) connected. Total connections: {len(self.user_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: str, user_role: str):
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        if websocket in self.active_connections[user_role]:
            self.active_connections[user_role].remove(websocket)
        logger.info(f"User {user_id} ({user_role}) disconnected. Total connections: {len(self.user_connections)}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_role(self, message: str, role: str):
        if role in self.active_connections:
            disconnected = []
            for connection in self.active_connections[role]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {role}: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                if connection in self.active_connections[role]:
                    self.active_connections[role].remove(connection)

    async def broadcast_to_all(self, message: str):
        """Broadcast to all connected users"""
        for role in self.active_connections:
            await self.broadcast_to_role(message, role)

    async def send_queue_update(self, queue_data: List[Dict[str, Any]]):
        """Send queue update to all staff and admin users"""
        message = json.dumps({
            "type": "queue_update",
            "data": queue_data
        })
        await self.broadcast_to_role(message, "staff")
        await self.broadcast_to_role(message, "admin")

    async def send_token_update(self, token_data: Dict[str, Any], user_id: str = None):
        """Send token update to specific user or all relevant users"""
        message = json.dumps({
            "type": "token_update",
            "data": token_data
        })
        
        if user_id:
            # Send to specific user (patient who created the token)
            await self.send_personal_message(message, user_id)
        
        # Also send to all staff/admin for queue updates
        await self.broadcast_to_role(message, "staff")
        await self.broadcast_to_role(message, "admin")

    async def send_analytics_update(self, analytics_data: Dict[str, Any]):
        """Send analytics update to staff and admin"""
        message = json.dumps({
            "type": "analytics_update",
            "data": analytics_data
        })
        await self.broadcast_to_role(message, "staff")
        await self.broadcast_to_role(message, "admin")

# Global connection manager instance
manager = ConnectionManager()
