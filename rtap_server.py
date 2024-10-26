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
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import shutil
import traceback

from models import RTSPStream, Annotation

# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RTAPServer:
    def __init__(self):
        self.clients: Set[web.WebSocketResponse] = set()
        self.streams: Dict[str, RTSPStream] = {}
        self.running = False
        self.port = int(os.getenv('RTAP_PORT', 9000))
        self.host = os.getenv('RTAP_HOST', '0.0.0.0')
        self.annotation_window = int(os.getenv('ANNOTATION_WINDOW', 5))
        self.processing_tasks = {}
        self.stream_tasks = {}
        self.hls_dir = Path(tempfile.gettempdir()) / 'rtap_hls'
        if self.hls_dir.exists():
            shutil.rmtree(self.hls_dir)
        self.hls_dir.mkdir(exist_ok=True)
        logger.info(f"HLS directory created at: {self.hls_dir}")

    def create_hls_manifest(self, stream_name: str, segment_duration: int = 2) -> None:
        """Create initial HLS manifest file"""
        stream_dir = self.hls_dir / stream_name
        manifest_path = stream_dir / 'stream.m3u8'
        
        manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:{segment_duration}
#EXT-X-MEDIA-SEQUENCE:0
"""
        manifest_path.write_text(manifest_content)
        logger.info(f"Created initial manifest at {manifest_path}")

    async def cleanup_hls(self):
        """Clean up HLS segments periodically"""
        while self.running:
            try:
                for stream_dir in self.hls_dir.iterdir():
                    if stream_dir.is_dir():
                        # Keep only recent segments
                        for file in stream_dir.glob('*.ts'):
                            if (datetime.now().timestamp() - file.stat().st_mtime) > 60:
                                file.unlink()
                                logger.debug(f"Removed old segment: {file}")
                        
                        # Update manifest
                        manifest_path = stream_dir / 'stream.m3u8'
                        if manifest_path.exists():
                            segments = sorted(stream_dir.glob('*.ts'))
                            if segments:
                                self.update_manifest(stream_dir.name, segments)
            except Exception as e:
                logger.error(f"Error cleaning HLS segments: {e}")
            await asyncio.sleep(10)

    def update_manifest(self, stream_name: str, segments: List[Path]) -> None:
        """Update HLS manifest with current segments"""
        stream_dir = self.hls_dir / stream_name
        manifest_path = stream_dir / 'stream.m3u8'
        
        manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:{max(0, len(segments) - 3)}
"""
        
        # Add recent segments
        for segment in segments[-3:]:
            manifest_content += f"""#EXTINF:2.0,
{segment.name}
"""
        
        manifest_path.write_text(manifest_content)
        logger.debug(f"Updated manifest for {stream_name} with {len(segments[-3:])} segments")

    async def start_hls_stream(self, stream: RTSPStream) -> None:
        stream_dir = self.hls_dir / stream.name
        stream_dir.mkdir(exist_ok=True)
        logger.info(f"Created HLS directory for stream {stream.name}: {stream_dir}")
        
        # Create initial manifest
        self.create_hls_manifest(stream.name)
        segment_index = 0

        while self.running:
            try:
                logger.info(f"Starting HLS stream for {stream.name} with URL: {stream.url}")
                input_container = av.open(stream.url, options={
                    'rtsp_transport': 'tcp',
                    'rtsp_flags': 'prefer_tcp',
                    'stimeout': '5000000'
                })
                logger.debug(f"Opened input container for {stream.name}")

                frame_count = 0
                frames_buffer = []
                
                for frame in input_container.decode(video=0):
                    if not self.running:
                        break
                        
                    frames_buffer.append(frame)
                    frame_count += 1
                    
                    # Create new segment every 60 frames (assuming 30fps = 2 seconds)
                    if len(frames_buffer) >= 60:
                        segment_path = stream_dir / f'segment_{segment_index}.ts'
                        logger.debug(f"Creating segment {segment_path}")
                        
                        try:
                            output_container = av.open(
                                str(segment_path),
                                mode='w',
                                format='mpegts'
                            )
                            
                            output_stream = output_container.add_stream('h264', rate=30)
                            output_stream.width = frame.width
                            output_stream.height = frame.height
                            output_stream.pix_fmt = 'yuv420p'
                            
                            for buffer_frame in frames_buffer:
                                packet = output_stream.encode(buffer_frame)
                                if packet:
                                    output_container.mux(packet)
                            
                            # Flush encoder
                            packet = output_stream.encode(None)
                            if packet:
                                output_container.mux(packet)
                                
                            output_container.close()
                            
                            # Update manifest with new segment
                            segments = sorted(stream_dir.glob('*.ts'))
                            self.update_manifest(stream.name, segments)
                            
                            segment_index += 1
                            frames_buffer = []
                            
                        except Exception as e:
                            logger.error(f"Error creating segment: {e}")
                            continue
                    
                    await asyncio.sleep(0.001)
                    
            except Exception as e:
                logger.error(f"Error in HLS stream {stream.name}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                await asyncio.sleep(5)  # Wait before retrying
            finally:
                try:
                    input_container.close()
                except Exception:
                    pass

    async def handle_hls_request(self, request: web.Request) -> web.Response:
        stream_name = request.match_info['name']
        file_name = request.match_info['file']
        
        if stream_name not in self.streams:
            logger.warning(f"Stream not found: {stream_name}")
            raise web.HTTPNotFound()
            
        file_path = self.hls_dir / stream_name / file_name
        logger.debug(f"HLS request for {file_path}")
        
        if not file_path.exists():
            logger.warning(f"HLS file not found: {file_path}")
            raise web.HTTPNotFound()
            
        if file_name.endswith('.m3u8'):
            return web.FileResponse(
                file_path,
                headers={
                    'Content-Type': 'application/vnd.apple.mpegurl',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-cache'
                }
            )
        elif file_name.endswith('.ts'):
            return web.FileResponse(
                file_path,
                headers={
                    'Content-Type': 'video/mp2t',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-cache'
                }
            )
        else:
            raise web.HTTPNotFound()


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

        return filters


    async def stream_video(self, request: web.Request) -> web.StreamResponse:
        stream_name = request.match_info['name']
        if stream_name not in self.streams:
            raise web.HTTPNotFound()

        stream = self.streams[stream_name]
        response = web.StreamResponse()
        response.content_type = 'video/mp4'
        await response.prepare(request)

        try:
            container = av.open(stream.url)
            for frame in container.decode(video=0):
                frame_data = frame.to_ndarray(format='bgr24')
                _, jpeg = cv2.imencode('.jpg', frame_data)
                await response.write(jpeg.tobytes())
                await asyncio.sleep(0.033)  # ~30 FPS
        except Exception as e:
            logger.error(f"Error streaming video: {e}")
        finally:
            await response.write_eof()
        return response


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

            # Start both HLS and processing tasks
            logger.info(f"Starting tasks for stream {name}")
            self.stream_tasks[name] = asyncio.create_task(self.start_hls_stream(stream))
            self.processing_tasks[name] = asyncio.create_task(self.process_stream(stream))

            return web.Response(
                text=json.dumps(stream.to_dict()),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error adding stream: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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


    async def process_stream(self, stream: RTSPStream) -> None:
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Processing RTSP stream: {stream.name} ({stream.url})")
                container = av.open(stream.url, options={
                    'rtsp_transport': 'tcp',
                    'rtsp_flags': 'prefer_tcp',
                    'stimeout': '5000000'
                })
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

        # Static files
        app.router.add_static('/static', Path(__file__).parent / 'static')
        app.router.add_get('/', lambda r: web.FileResponse(Path(__file__).parent / 'static' / 'index.html'))
        app.router.add_get('/favicon.ico', lambda r: web.FileResponse(Path(__file__).parent / 'static' / 'favicon.ico'))

        # Stream management routes
        app.router.add_post('/api/streams', self.handle_add_stream)
        app.router.add_get('/api/streams', self.handle_list_streams)
        app.router.add_get('/api/streams/{name}', self.handle_get_stream)

        # HLS streaming
        app.router.add_get('/hls/{name}/{file}', self.handle_hls_request)

        # Annotation routes
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

            # Start HLS cleanup task
            cleanup_task = asyncio.create_task(self.cleanup_hls())

            while True:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            for task in self.processing_tasks.values():
                task.cancel()
            for task in self.stream_tasks.values():
                task.cancel()
            cleanup_task.cancel()
            await runner.cleanup()

            # Cleanup HLS directory
            try:
                shutil.rmtree(self.hls_dir)
            except Exception as e:
                logger.error(f"Error cleaning up HLS directory: {e}")

