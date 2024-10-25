import asyncio
import json
import cv2
import numpy as np
import websockets
from datetime import datetime
from aiohttp import web
import av
from fractions import Fraction
import yaml
import os
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTSPStream:
    def __init__(self, name: str, url: str, description: str = "", parameters: Optional[Dict] = None):
        self.name = name
        self.url = url
        self.description = description
        self.parameters = parameters or {}
        self.status = "inactive"
        self.last_error = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class RTAPServer:
    def __init__(self):
        self.clients = set()
        self.streams: Dict[str, RTSPStream] = {}
        self.running = False
        self.port = int(os.getenv('RTAP_PORT', 9000))  # Changed default to 9000
        self.host = os.getenv('RTAP_HOST', '0.0.0.0')
        self.processing_tasks = {}

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    # REST API Handlers
    async def handle_add_stream(self, request):
        try:
            data = await request.json()
            name = data.get('name')
            url = data.get('url')
            description = data.get('description', '')
            parameters = data.get('parameters', {})

            if not all([name, url]):
                return web.Response(
                    status=400,
                    text=json.dumps({"error": "name and url are required"}),
                    content_type='application/json'
                )

            if name in self.streams:
                return web.Response(
                    status=409,
                    text=json.dumps({"error": f"Stream '{name}' already exists"}),
                    content_type='application/json'
                )

            stream = RTSPStream(name, url, description, parameters)
            self.streams[name] = stream
            
            # Start processing the stream
            self.processing_tasks[name] = asyncio.create_task(
                self.process_stream(stream)
            )

            return web.Response(
                text=json.dumps(stream.to_dict()),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error adding stream: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

    async def handle_list_streams(self, request):
        try:
            streams = {name: stream.to_dict() for name, stream in self.streams.items()}
            return web.Response(
                text=json.dumps(streams),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error listing streams: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

    async def handle_get_stream(self, request):
        try:
            name = request.match_info['name']
            stream = self.streams.get(name)
            
            if not stream:
                return web.Response(
                    status=404,
                    text=json.dumps({"error": f"Stream '{name}' not found"}),
                    content_type='application/json'
                )

            return web.Response(
                text=json.dumps(stream.to_dict()),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error getting stream: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

    async def register_client(self, websocket):
        self.clients.add(websocket)
        try:
            while not websocket.closed:
                await asyncio.sleep(1)
        finally:
            self.clients.remove(websocket)
            logger.info("Client disconnected")

    async def broadcast_annotation(self, stream_name: str, annotation):
        if self.clients:
            disconnected_clients = set()
            annotation['stream_name'] = stream_name
            
            for client in self.clients:
                try:
                    await client.send_json(annotation)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.add(client)
            
            self.clients -= disconnected_clients

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.info("New client connected")
        
        try:
            await self.register_client(ws)
        except Exception as e:
            logger.error(f"Error in websocket handler: {e}")
        finally:
            return ws

    async def process_stream(self, stream: RTSPStream):
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Connecting to RTSP stream: {stream.name} ({stream.url})")
                container = av.open(stream.url)
                video_stream = container.streams.video[0]

                # Update stream status
                stream.status = "active"
                stream.last_error = None
                stream.updated_at = datetime.now().isoformat()

                metadata_stream = {
                    "type": "metadata",
                    "timestamp": None,
                    "frame_number": 0,
                    "annotations": []
                }

                while self.running:
                    try:
                        for frame in container.decode(video=0):
                            if not self.running:
                                break

                            metadata_stream["timestamp"] = datetime.now().isoformat()
                            metadata_stream["frame_number"] += 1

                            frame_array = frame.to_ndarray(format='bgr24')
                            motion = self.detect_motion(frame_array)

                            if motion:
                                annotation = {
                                    "type": "motion_detection",
                                    "frame": metadata_stream["frame_number"],
                                    "timestamp": metadata_stream["timestamp"],
                                    "location": motion
                                }
                                metadata_stream["annotations"].append(annotation)
                                await self.broadcast_annotation(stream.name, annotation)

                            await asyncio.sleep(0.001)

                    except av.error.EOFError:
                        logger.warning(f"End of stream reached: {stream.name}")
                        break

            except Exception as e:
                retry_count += 1
                error_msg = f"Error processing stream {stream.name}: {str(e)}"
                logger.error(error_msg)
                stream.status = "error"
                stream.last_error = error_msg
                stream.updated_at = datetime.now().isoformat()
                
                if retry_count < max_retries:
                    await asyncio.sleep(5)
                else:
                    logger.error(f"Max retries reached for stream {stream.name}")
                    break

        stream.status = "inactive"
        stream.updated_at = datetime.now().isoformat()

    def detect_motion(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            movement_detected = np.mean(gray) > 127

            if movement_detected:
                return {
                    "x": 0,
                    "y": 0,
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                }
        except Exception as e:
            logger.error(f"Error in motion detection: {e}")
        return None

    async def start_server(self):
        app = web.Application()
        
        # REST API routes
        app.router.add_post('/api/streams', self.handle_add_stream)
        app.router.add_get('/api/streams', self.handle_list_streams)
        app.router.add_get('/api/streams/{name}', self.handle_get_stream)
        
        # WebSocket route
        app.router.add_get('/ws', self.handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        try:
            await site.start()
            logger.info(f"RTAP Server started on http://{self.host}:{self.port}")
            self.running = True
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            # Cancel all stream processing tasks
            for task in self.processing_tasks.values():
                task.cancel()
            await runner.cleanup()


async def main():
    try:
        server = RTAPServer()
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
