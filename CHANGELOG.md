## [0.4.3] - 2024-10-25

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

## [0.4.3] - 2024-10-25

### Added
- Support for query parameter filtering of annotations
- Additional filtering options (start_time, end_time, limit)
- Flexible annotation type specification (path or query parameter)

### Changed
- Enhanced annotation filtering logic
- Improved route handling for annotations
- Better type handling for optional parameters

### Deprecated
- 

### Removed
- 

### Fixed
- Annotation filtering functionality
- Query parameter handling
- Route flexibility for annotation endpoints

### Security
-

## [0.4.2] - 2024-01-09

### Added
- New rtap_server.py module
- Enhanced type hints for all methods
- Return type annotations

### Changed
- Moved RTAPServer class to separate file
- Simplified main rtap.py file
- Improved type safety with annotations
- Enhanced method signatures

### Deprecated
- 

### Removed
- Server logic from main file

### Fixed
- Code organization
- Type safety
- Method signatures

### Security
- 

## [0.4.1] - 2024-01-09

### Added
- New models package for data structures
- Separate model files for Annotation and RTSPStream
- Type hints for model classes

### Changed
- Moved Annotation class to models/annotation.py
- Moved RTSPStream class to models/stream.py
- Improved code organization with modular structure
- Enhanced type annotations

### Deprecated
- 

### Removed
- Inline model definitions from rtap.py

### Fixed
- Code organization and maintainability
- Module imports and dependencies

### Security
- 

## [0.4.0] - 2024-01-09

### Added
- Annotation system with support for different types (transcript, motion, object, custom)
- New API endpoints for managing annotations
- Annotation storage per stream
- Real-time annotation broadcasting
- Annotation timestamp tracking
- Structured annotation data model

### Changed
- Enhanced stream class to include annotation management
- Improved WebSocket broadcasting with structured messages
- Updated motion detection to use annotation system
- Better error handling for annotation operations

### Deprecated
- 

### Removed
- 

### Fixed
- Annotation endpoint routing
- Stream-specific annotation handling
- Real-time annotation updates

### Security
- Added validation for annotation data


## [0.3.0] - 2024-01-09

### Added
- REST API endpoints for stream management
- Stream status monitoring
- Multiple stream support
- Stream configuration parameters
- Individual stream error handling
- Stream metadata tracking

### Changed
- Refactored server architecture for multiple streams
- Enhanced error handling per stream
- Improved stream status reporting
- Updated WebSocket broadcasting with stream identification

### Deprecated
- 

### Removed
- Single stream handling in favor of multiple stream support

### Fixed
- Stream management and monitoring
- Error handling for individual streams
- Stream status tracking

### Security
- Added basic input validation for stream endpoints

## [0.2.2] - 2024-01-09

### Added
- Comprehensive logging system
- Retry mechanism for RTSP connections
- Error handling for WebSocket connections
- Graceful shutdown handling

### Changed
- Improved WebSocket client-server communication
- Enhanced RTSP stream processing reliability
- Better error messages and logging

### Deprecated
- 

### Removed
- 

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

### Deprecated
- 

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

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

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
