from datetime import datetime
from typing import Dict, Optional, List
from .annotation import Annotation

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
        self.annotations: Dict[str, List[Annotation]] = {}

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "annotations": {
                k: [ann.to_dict() for ann in v]
                for k, v in self.annotations.items()
            }
        }

    def add_annotation(self, annotation_type: str, data: dict, timestamp: str) -> Annotation:
        """Add an annotation to the stream."""
        if annotation_type not in self.annotations:
            self.annotations[annotation_type] = []
        
        # Ensure the data includes all fields from the original request
        processed_data = data.copy()
        
        # Add any type-specific processing here
        if annotation_type == 'event':
            if 'location' in processed_data and 'area' in processed_data['location']:
                processed_data['area'] = processed_data['location']['area']
        
        annotation = Annotation(annotation_type, processed_data, timestamp)
        self.annotations[annotation_type].append(annotation)
        return annotation

    def get_annotations(self, filters: Optional[Dict] = None) -> List[Annotation]:
        """Get all annotations that match the given filters."""
        all_annotations = []
        for annotations in self.annotations.values():
            all_annotations.extend(annotations)
        
        if not filters:
            return all_annotations
        
        return [ann for ann in all_annotations if ann.matches_filters(filters)]
