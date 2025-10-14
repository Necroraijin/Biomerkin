"""
Serialization and deserialization utilities for data models.
"""

import json
import pickle
from typing import Any, Dict, Type, TypeVar, Union
from datetime import datetime
from pathlib import Path

T = TypeVar('T')


class BiomerkinEncoder(json.JSONEncoder):
    """Custom JSON encoder for Biomerkin data types."""
    
    def default(self, obj: Any) -> Any:
        """Handle custom object serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


class SerializationUtils:
    """Utilities for serializing and deserializing data models."""
    
    @staticmethod
    def to_json(obj: Any, indent: int = 2) -> str:
        """Serialize object to JSON string."""
        return json.dumps(obj, cls=BiomerkinEncoder, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str, target_class: Type[T] = None) -> Union[Dict[str, Any], T]:
        """Deserialize JSON string to object."""
        data = json.loads(json_str)
        if target_class and hasattr(target_class, 'from_dict'):
            return target_class.from_dict(data)
        return data
    
    @staticmethod
    def to_json_file(obj: Any, file_path: Union[str, Path], indent: int = 2) -> None:
        """Serialize object to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, cls=BiomerkinEncoder, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def from_json_file(file_path: Union[str, Path], target_class: Type[T] = None) -> Union[Dict[str, Any], T]:
        """Deserialize JSON file to object."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if target_class and hasattr(target_class, 'from_dict'):
            return target_class.from_dict(data)
        return data
    
    @staticmethod
    def to_pickle(obj: Any, file_path: Union[str, Path]) -> None:
        """Serialize object to pickle file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(obj, f)
    
    @staticmethod
    def from_pickle(file_path: Union[str, Path]) -> Any:
        """Deserialize pickle file to object."""
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], required_fields: list) -> bool:
        """Validate that JSON data contains required fields."""
        return all(field in data for field in required_fields)
    
    @staticmethod
    def sanitize_for_json(obj: Any) -> Any:
        """Sanitize object for JSON serialization by removing non-serializable fields."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: SerializationUtils.sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [SerializationUtils.sanitize_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            # For other types, try to convert to string
            return str(obj)


def serialize_workflow_state(workflow_state: Any) -> str:
    """Convenience function to serialize workflow state."""
    return SerializationUtils.to_json(workflow_state)


def deserialize_workflow_state(json_str: str, target_class: Type[T]) -> T:
    """Convenience function to deserialize workflow state."""
    return SerializationUtils.from_json(json_str, target_class)


def save_analysis_results(results: Any, output_dir: Union[str, Path], workflow_id: str) -> None:
    """Save analysis results to files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_file = output_dir / f"{workflow_id}_results.json"
    SerializationUtils.to_json_file(results, json_file)
    
    # Save as pickle for Python interoperability
    pickle_file = output_dir / f"{workflow_id}_results.pkl"
    SerializationUtils.to_pickle(results, pickle_file)


def load_analysis_results(file_path: Union[str, Path], target_class: Type[T] = None) -> Union[Dict[str, Any], T]:
    """Load analysis results from file."""
    file_path = Path(file_path)
    
    if file_path.suffix == '.json':
        return SerializationUtils.from_json_file(file_path, target_class)
    elif file_path.suffix == '.pkl':
        return SerializationUtils.from_pickle(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")