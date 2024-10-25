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
                # Handle nested fields in data
                if not self._check_nested_field(self.data, key, value):
                    return False
        return True

    def _check_nested_field(self, data: Dict[str, Any], key: str, value: Any) -> bool:
        """Recursively check nested fields in data dictionary."""
        # Split the key into parts (e.g., 'location.area' -> ['location', 'area'])
        key_parts = key.split('.')
        
        current = data
        for part in key_parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        last_key = key_parts[-1]
        
        # Handle special cases for different annotation types
        if self.type == 'event':
            if last_key == 'severity' and 'severity' in data:
                return str(data['severity']).lower() == str(value).lower()
            elif last_key == 'area' and 'location' in data:
                return data['location'].get('area', '').lower() == str(value).lower()
            elif last_key in data:
                return str(data[last_key]).lower() == str(value).lower()
        
        # For other annotation types, check if the field exists and matches
        if last_key not in current:
            return False
        
        return str(current[last_key]).lower() == str(value).lower()

    @staticmethod
    def parse_timestamp(timestamp: str) -> Optional[str]:
        """Parse and validate timestamp string."""
        try:
            # Attempt to parse the timestamp to validate format
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return timestamp
        except (ValueError, TypeError):
            return None
