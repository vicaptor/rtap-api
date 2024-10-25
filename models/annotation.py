from datetime import datetime
from typing import Dict

class Annotation:
    def __init__(self, annotation_type: str, data: dict, timestamp: str):
        self.type = annotation_type
        self.data = data
        self.timestamp = timestamp
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "created_at": self.created_at
        }
