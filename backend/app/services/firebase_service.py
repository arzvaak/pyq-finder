import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Optional, List
from datetime import datetime
import requests

from app.models.paper import Paper


class FirebaseService:
    """Service for Firebase Firestore and Storage operations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FirebaseService._initialized:
            self._initialize_firebase()
            FirebaseService._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        # Look for service account in project root
        service_account_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'pyqfinder-273f6dac5489.json'
        )
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found at {service_account_path}")
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'pyqfinder.firebasestorage.app'
        })
        
        # Use the pyq-finder database (not default)
        self.db = firestore.client(database_id='pyq-finder')
        self.bucket = storage.bucket()
        self.papers_collection = self.db.collection('papers')
    
    # ==================== Paper Operations ====================
    
    def add_paper(self, paper: Paper) -> str:
        """Add a new paper to Firestore."""
        paper.created_at = datetime.utcnow()
        paper.updated_at = datetime.utcnow()
        
        doc_ref = self.papers_collection.add(paper.to_dict())
        return doc_ref[1].id
    
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by ID."""
        doc = self.papers_collection.document(paper_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return Paper.from_dict(data)
        return None
    
    def get_papers(
        self,
        year: Optional[str] = None,
        semester: Optional[str] = None,
        branch: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Paper]:
        """Get papers with optional filters."""
        query = self.papers_collection
        
        if year:
            query = query.where('year', '==', year)
        if semester:
            query = query.where('semester', '==', semester)
        if branch:
            query = query.where('branch', '==', branch)
        if subject:
            query = query.where('subject_name', '==', subject)
        
        # Order by creation date
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        
        # Pagination
        query = query.limit(limit).offset(offset)
        
        papers = []
        for doc in query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            papers.append(Paper.from_dict(data))
        
        return papers
    
    def search_papers(self, search_term: str, limit: int = 50) -> List[Paper]:
        """Search papers by subject name or title."""
        # Firestore doesn't support full-text search, so we'll fetch and filter
        # For production, consider using Algolia or Elasticsearch
        papers = []
        search_lower = search_term.lower()
        
        for doc in self.papers_collection.limit(500).stream():
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Search in title and subject_name
            if (search_lower in data.get('title', '').lower() or 
                search_lower in data.get('subject_name', '').lower() or
                search_lower in data.get('subject_code', '').lower()):
                papers.append(Paper.from_dict(data))
                
            if len(papers) >= limit:
                break
        
        return papers
    
    def fuzzy_search_papers(self, subject_names: List[str], threshold: int = 60, limit: int = 100) -> List[dict]:
        """
        Find papers matching subject names using fuzzy string matching.
        
        Args:
            subject_names: List of subject names to search for
            threshold: Minimum similarity score (0-100) to include a match
            limit: Maximum number of results to return
            
        Returns:
            List of papers with similarity scores, sorted by best match
        """
        from rapidfuzz import fuzz, process
        
        # Fetch all papers (in production, consider caching or indexing)
        all_papers = []
        for doc in self.papers_collection.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            all_papers.append(data)
        
        if not all_papers:
            return []
        
        # Build searchable text for each paper
        paper_texts = []
        for paper in all_papers:
            # Combine subject_name, title, and subject_code for matching
            text = f"{paper.get('subject_name', '')} {paper.get('title', '')} {paper.get('subject_code', '')}"
            paper_texts.append(text.lower())
        
        # Find matches for each subject
        matched_papers = {}
        
        for subject in subject_names:
            subject_lower = subject.lower()
            
            for i, (paper, text) in enumerate(zip(all_papers, paper_texts)):
                paper_id = paper['id']
                
                # Calculate similarity using multiple methods
                # Token set ratio works well for subject names with different word orders
                ratio = fuzz.token_set_ratio(subject_lower, text)
                
                # Also check partial ratio for substring matches
                partial = fuzz.partial_ratio(subject_lower, text)
                
                # Use the higher score
                score = max(ratio, partial)
                
                if score >= threshold:
                    if paper_id not in matched_papers or matched_papers[paper_id]['score'] < score:
                        matched_papers[paper_id] = {
                            **paper,
                            'score': score,
                            'matched_subject': subject
                        }
        
        # Sort by score (highest first) and return top results
        results = sorted(matched_papers.values(), key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_all_papers_for_search(self) -> List[dict]:
        """Get all papers for client-side searching."""
        papers = []
        for doc in self.papers_collection.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            papers.append(data)
        return papers
    
    def paper_exists(self, pdf_url: str) -> bool:
        """Check if a paper with the given PDF URL already exists."""
        query = self.papers_collection.where('pdf_url', '==', pdf_url).limit(1)
        return len(list(query.stream())) > 0
    
    def paper_exists_by_metadata(
        self, 
        subject_code: str, 
        year: str, 
        semester: str,
        exam_type: str = None
    ) -> bool:
        """
        Check if a paper with similar metadata exists.
        This catches duplicates even if the PDF URL is slightly different.
        
        Matches on: subject_code + year + semester + exam_type (if provided)
        """
        if not subject_code or not year:
            return False
        
        query = self.papers_collection.where('subject_code', '==', subject_code)
        query = query.where('year', '==', year)
        
        if semester:
            query = query.where('semester', '==', semester)
        
        if exam_type:
            query = query.where('exam_type', '==', exam_type)
        
        return len(list(query.limit(1).stream())) > 0
    
    def get_unique_values(self, field: str) -> List[str]:
        """Get unique values for a field (year, semester, branch, etc.)."""
        values = set()
        for doc in self.papers_collection.stream():
            data = doc.to_dict()
            if field in data and data[field]:
                values.add(data[field])
        return sorted(list(values))
    
    # ==================== Storage Operations ====================
    
    def upload_pdf(self, pdf_url: str, destination_path: str) -> str:
        """Download PDF from URL and upload to Firebase Storage."""
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Upload to Storage
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(
            response.content,
            content_type='application/pdf'
        )
        
        # Make publicly accessible
        blob.make_public()
        
        return blob.public_url
    
    def get_download_url(self, storage_path: str) -> str:
        """Get download URL for a file in Storage."""
        blob = self.bucket.blob(storage_path)
        return blob.public_url


# Singleton instance
firebase_service = FirebaseService()
