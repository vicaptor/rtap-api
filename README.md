
# RTAP-API (Real-Time Annotation Processing API)

A Python-based API service for real-time video stream processing and annotation.

## Features

- Real-time video stream processing
- WebSocket support for live data streaming
- Docker containerization support
- Configurable annotation processing
- RTSP stream handling

## Prerequisites

- Python 3.7+
- pip package manager
- Docker (optional, for containerized deployment)

## Installation

### Local Development Setup

1. Create a new virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Verify installation:
```bash
python -c "import aiohttp, cv2, av, numpy; print('All packages installed successfully')"
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -t rtap-api .
```

2. Run using docker-compose:
```bash
docker-compose up
```

## Configuration

1. Copy the demo environment file:
```bash
cp .env.demo .env
```

2. Update the configuration in `config.yml` according to your needs.

## Usage

### Starting the Server

```bash
python rtap.py
```

### Running Tests

```bash
cd tests
./annotation.sh
```

## Project Structure

```
rtap-api/
├── rtap.py           # Main application entry point
├── config.yml        # Configuration file
├── requirements.txt  # Python dependencies
├── Dockerfile       # Docker configuration
├── docker-compose.yaml
└── tests/           # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add License Information]

## Documentation

For more detailed information, please refer to:
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [TODO.md](TODO.md) - Planned features and improvements
