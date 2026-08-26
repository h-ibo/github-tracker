from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websockets import manager

# WebSocket için ayrı bir router oluşturuyoruz
router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/repo-alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # İstemciden mesaj gelirse diye bekliyoruz (bağlantıyı açık tutmak için şart)
            # Bu projede istemciden bize veri gelmeyecek, sadece biz ona push yapacağız.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/ws/test-broadcast")
async def test_broadcast():
    test_message = {
        "repo_name": "tiangolo/fastapi",
        "title": "Bu, sunucudan tarayıcıya gelen CANLI bir test bildirimidir!"
    }
    # manager üzerinden bağlı olan tüm HTML sayfalarına bu mesajı fırlatıyoruz
    await manager.broadcast(test_message)
    return {"message": "Bildirim başarıyla fırlatıldı!"}

from pydantic import BaseModel

# Dışarıdan (Worker'dan) gelecek verinin formatı
class AlertData(BaseModel):
    repo_name: str
    title: str

# Worker'ın gizlice tetikleyeceği yeni endpoint
@router.post("/ws/trigger-alert")
async def trigger_alert(data: AlertData):
    # Veriyi sözlüğe (dict) çevirip tarayıcılara fırlatıyoruz
    await manager.broadcast(data.model_dump())
    return {"message": "Canlı bildirim tüm istemcilere fırlatıldı!"}