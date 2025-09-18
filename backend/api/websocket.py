"""
WebSocket 管理器
处理 WebSocket 连接和消息广播
"""

from typing import Set, Dict, List, Any
from fastapi import WebSocket
import json
import structlog
import asyncio


logger = structlog.get_logger()


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.topic_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info("WebSocket 客户端连接", total_connections=len(self.active_connections))
    
    async def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        async with self._lock:
            self.active_connections.discard(websocket)
            
            # 从所有主题订阅中移除
            for topic, subscribers in self.topic_subscriptions.items():
                subscribers.discard(websocket)
        
        logger.info("WebSocket 客户端断开", total_connections=len(self.active_connections))
    
    async def subscribe_to_topics(self, websocket: WebSocket, topics: List[str]):
        """订阅主题"""
        async with self._lock:
            for topic in topics:
                if topic not in self.topic_subscriptions:
                    self.topic_subscriptions[topic] = set()
                self.topic_subscriptions[topic].add(websocket)
        
        logger.info("WebSocket 客户端订阅主题", topics=topics)
        
        # 发送订阅确认
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "topics": topics,
        }))
    
    async def unsubscribe_from_topics(self, websocket: WebSocket, topics: List[str]):
        """取消订阅主题"""
        async with self._lock:
            for topic in topics:
                if topic in self.topic_subscriptions:
                    self.topic_subscriptions[topic].discard(websocket)
        
        logger.info("WebSocket 客户端取消订阅主题", topics=topics)
        
        # 发送取消订阅确认
        await websocket.send_text(json.dumps({
            "type": "unsubscription_confirmed",
            "topics": topics,
        }))
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """向特定主题的订阅者广播消息"""
        if topic not in self.topic_subscriptions:
            return
        
        subscribers = list(self.topic_subscriptions[topic])
        if not subscribers:
            return
        
        message_text = json.dumps({
            "topic": topic,
            "data": message,
            "timestamp": message.get("timestamp"),
        })
        
        # 并发发送消息
        tasks = []
        for websocket in subscribers:
            tasks.append(self._send_safe(websocket, message_text))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """向所有连接广播消息"""
        if not self.active_connections:
            return
        
        connections = list(self.active_connections)
        message_text = json.dumps(message)
        
        # 并发发送消息
        tasks = []
        for websocket in connections:
            tasks.append(self._send_safe(websocket, message_text))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_safe(self, websocket: WebSocket, message: str):
        """安全发送消息（处理连接错误）"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning("WebSocket 发送消息失败", error=str(e))
            # 移除失效的连接
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "topic_subscriptions": {
                topic: len(subscribers) 
                for topic, subscribers in self.topic_subscriptions.items()
            },
        }
