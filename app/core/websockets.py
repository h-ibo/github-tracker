from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        # Bağlı olan tüm istemcileri (tarayıcıları) bu listede tutacağız
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("[WS] Yeni bir istemci bağlandı!")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("[WS] Bir istemci ayrıldı.")

    async def broadcast(self, message: dict):
        # Listede olan herkese gelen mesajı JSON formatında gönder
        for connection in self.active_connections:
            await connection.send_json(message)

# Bu dosyayı import eden herkes aynı manager nesnesini kullansın
manager = ConnectionManager()