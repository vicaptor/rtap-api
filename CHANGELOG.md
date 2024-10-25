## [0.2.2] - 2024-10-25

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

## [0.2.2] - Error: date.txt not found. Please run the script that generates it first.

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - Error: date.txt not found. Please run the script that generates it first.

### Added
- Comprehensive logging system
- Retry mechanism for RTSP connections
- Error handling for WebSocket connections
- Graceful shutdown handling

### Changed
- Improved WebSocket client-server communication
- Enhanced RTSP stream processing reliability
- Better error messages and logging


### Fixed
- WebSocket wait_closed() attribute error
- RTSP connection handling
- Client disconnection handling
- Server shutdown process

### Security
- Added basic error handling to prevent information leakage

## [0.2.1] - 2024-01-09

### Added
- Missing numpy import in rtap.py

### Changed
- Standardized port usage between server and client
- Improved code organization and comments


### Removed
- Duplicate start_server method

### Fixed
- Port initialization in RTAPClient
- Server and client port synchronization
- Code formatting and structure

### Security
- 

## [0.2.0] - 2024-01-09

### Added
- Project documentation structure
- Comprehensive README.md with installation and usage guides
- Makefile for common development tasks
- Version management script (scripts/version.sh)
- TODO list for tracking planned features
- Changelog for tracking project history

### Changed
- Enhanced project documentation
- Improved build and deployment instructions
- Restructured development workflow


## [0.1.0] - 2024-01-09

### Added
- Initial project setup
- Basic RTSP stream processing functionality
- WebSocket support for real-time data streaming
- Docker containerization
- Configuration system
- Basic test suite
- Environment configuration (.env.demo)
- Docker compose support
- Basic test framework

