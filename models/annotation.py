from datetime import datetime
from typing import Dict, Any, Optional

class Annotation:
    def __init__(self, annotation_type: str, data: dict, timestamp: str):
        self.type = annotation_type
        self.data = data
        self.timestamp = timestamp
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "created_at": self.created_at
        }

    def matches_filters(self, filters: Dict[str, Any]) -> bool:
        """Check if annotation matches all provided filters."""
        for key, value in filters.items():
            if key == 'start':
                if self.timestamp < value:
                    return False
            elif key == 'end':
                if self.timestamp > value:
                    return False
            elif key == 'type':
                if self.type != value:
                    return False
            else:
                # Check in data dictionary for other filters
                if key not in self.data or self.data[key] != value:
                    return False
        return True

    @staticmethod
    def parse_timestamp(timestamp: str) -> Optional[str]:
        """Parse and validate timestamp string."""
        try:
            # Attempt to parse the timestamp to validate format
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return timestamp
        except (ValueError, TypeError):
            return None
