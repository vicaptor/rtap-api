import asyncio
import json
import cv2
import numpy as np
from datetime import datetime
from aiohttp import web
import av
import yaml
import os
import logging
from typing import Dict, Set, Optional, List, Any
from urllib.parse import parse_qs

from models import RTSPStream, Annotation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTAPServer:
    def __init__(self):
        self.clients: Set[web.WebSocketResponse] = set()
        self.streams: Dict[str, RTSPStream] = {}
        self.running = False
        self.port = int(os.getenv('RTAP_PORT', 9000))
        self.host = os.getenv('RTAP_HOST', '0.0.0.0')
        self.processing_tasks = {}

    def parse_query_filters(self, query: Dict[str, str]) -> Dict[str, Any]:
        """Parse and validate query parameters into filters."""
        filters = {}
        
        # Handle special time range parameters
        if 'start' in query:
            start_time = Annotation.parse_timestamp(query['start'])
            if start_time:
                filters['start'] = start_time
        
        if 'end' in query:
            end_time = Annotation.parse_timestamp(query['end'])
            if end_time:
                filters['end'] = end_time

        # Handle all other parameters as data filters
        for key, value in query.items():
            if key not in ['start', 'end']:
                filters[key] = value

        logger.info(f"Parsed filters: {filters}")
        return filters

    async def handle_add_annotation(self, request: web.Request) -> web.Response:
        try:
            stream_name = request.match_info['name']
            annotation_type = request.match_info.get('type') or request.query.get('type')
            
            if not annotation_type:
                return web.Response(
                    status=400,
                    text=json.dumps({"error": "Annotation type is required"}),
                    content_type='application/json'
                )
            
            if stream_name not in self.streams:
                return web.Response(
                    status=404,
                    text=json.dumps({"error": f"Stream '{stream_name}' not found"}),
                    content_type='application/json'
                )

            data = await request.json()
            timestamp = data.get('timestamp')
            if not timestamp:
                timestamp = datetime.now().isoformat()

            stream = self.streams[stream_name]
            annotation = stream.add_annotation(annotation_type, data, timestamp)
            
            logger.info(f"Added annotation: {annotation.to_dict()}")
            await self.broadcast_annotation(stream_name, annotation.to_dict())

            return web.Response(
                text=json.dumps(annotation.to_dict()),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error adding annotation: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

    async def handle_get_annotations(self, request: web.Request) -> web.Response:
        try:
            stream_name = request.match_info['name']
            
            if stream_name not in self.streams:
                return web.Response(
                    status=404,
                    text=json.dumps({"error": f"Stream '{stream_name}' not found"}),
                    content_type='application/json'
                )

            stream = self.streams[stream_name]
            filters = self.parse_query_filters(dict(request.query))
            
            annotations = stream.get_annotations(filters)
            annotations_dict = [ann.to_dict() for ann in annotations]
            
            # Sort by timestamp
            annotations_dict.sort(key=lambda x: x['timestamp'])
            
            logger.info(f"Retrieved {len(annotations_dict)} annotations with filters: {filters}")
            return web.Response(
                text=json.dumps(annotations_dict),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error getting annotations: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

        except Exception as e:
            logger.error(f"Error getting annotations: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type='application/json'
            )

    # Stream Handlers
    async def handle_add_stream(self, request: web.Request) -> web.Response:
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

    async def handle_list_streams(self, request: web.Request) -> web.Response:
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

    async def handle_get_stream(self, request: web.Request) -> web.Response:
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

    # WebSocket Handlers
    async def register_client(self, websocket: web.WebSocketResponse) -> None:
        self.clients.add(websocket)
        try:
            while not websocket.closed:
                await asyncio.sleep(1)
        finally:
            self.clients.remove(websocket)
            logger.info("Client disconnected")

    async def broadcast_annotation(self, stream_name: str, annotation: dict) -> None:
        if self.clients:
            disconnected_clients = set()
            message = {
                "stream_name": stream_name,
                "annotation": annotation
            }

            for client in self.clients:
                try:
                    await client.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.add(client)

            self.clients -= disconnected_clients

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.info("New client connected")

        try:
            await self.register_client(ws)
        except Exception as e:
            logger.error(f"Error in websocket handler: {e}")
        finally:
            return ws

    # Stream Processing
    async def process_stream(self, stream: RTSPStream) -> None:
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Connecting to RTSP stream: {stream.name} ({stream.url})")
                container = av.open(stream.url)
                video_stream = container.streams.video[0]

                stream.status = "active"
                stream.last_error = None
                stream.updated_at = datetime.now().isoformat()

                frame_number = 0

                while self.running:
                    try:
                        for frame in container.decode(video=0):
                            if not self.running:
                                break

                            frame_number += 1
                            timestamp = datetime.now().isoformat()

                            frame_array = frame.to_ndarray(format='bgr24')
                            motion = self.detect_motion(frame_array)

                            if motion:
                                annotation = stream.add_annotation(
                                    "motion",
                                    {
                                        "frame": frame_number,
                                        "location": motion
                                    },
                                    timestamp
                                )
                                await self.broadcast_annotation(stream.name, annotation.to_dict())

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

    def detect_motion(self, frame: np.ndarray) -> Optional[dict]:
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

    async def start_server(self) -> None:
        app = web.Application()

        # Stream management routes
        app.router.add_post('/api/streams', self.handle_add_stream)
        app.router.add_get('/api/streams', self.handle_list_streams)
        app.router.add_get('/api/streams/{name}', self.handle_get_stream)

        # Annotation routes - support both path and query parameters
        app.router.add_post('/api/streams/{name}/annotations', self.handle_add_annotation)
        app.router.add_post('/api/streams/{name}/annotations/{type}', self.handle_add_annotation)
        app.router.add_get('/api/streams/{name}/annotations', self.handle_get_annotations)
        app.router.add_get('/api/streams/{name}/annotations/{type}', self.handle_get_annotations)

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
            for task in self.processing_tasks.values():
                task.cancel()
            await runner.cleanup()
