from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Paper:
    """Model representing a question paper."""
    id: Optional[str] = None
    title: str = ""
    subject_code: str = ""
    subject_name: str = ""
    year: str = ""
    semester: str = ""
    branch: str = ""
    exam_type: str = ""  # Regular, Makeup, etc.
    pdf_url: str = ""  # Original URL from portal
    storage_url: str = ""  # Firebase Storage URL
    portal: str = ""  # portal1 or portal2
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Firestore."""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Paper':
        """Create Paper from Firestore document."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
