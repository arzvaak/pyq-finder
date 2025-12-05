import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Generator
from urllib.parse import urljoin, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.models.paper import Paper


class Portal1Scraper:
    """
    Scraper for https://mitmpllibportal.manipal.edu/question-papers
    
    This portal has a flat list of PDF links organized by year/semester/branch.
    Supports concurrent scraping for faster performance.
    """
    
    BASE_URL = "https://mitmpllibportal.manipal.edu/question-papers"
    
    def __init__(self, max_workers: int = 5):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.max_workers = max_workers
        self._stop_event = threading.Event()
    
    def stop(self):
        """Signal the scraper to stop."""
        self._stop_event.set()
    
    def scrape_all(self, concurrent: bool = True) -> Generator[Paper, None, None]:
        """
        Scrape all papers from Portal 1.
        
        Args:
            concurrent: If True, use parallel processing for faster scraping
        """
        self._stop_event.clear()
        print(f"[Portal1] Starting scrape from {self.BASE_URL}")
        
        response = self.session.get(self.BASE_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find all PDF links
        pdf_links = soup.find_all('a', href=lambda x: x and x.endswith('.pdf'))
        print(f"[Portal1] Found {len(pdf_links)} PDF links")
        
        if concurrent and len(pdf_links) > 10:
            # Use concurrent processing for large batches
            yield from self._scrape_concurrent(pdf_links)
        else:
            # Sequential processing for small batches
            for link in pdf_links:
                if self._stop_event.is_set():
                    print("[Portal1] Stop requested, stopping...")
                    break
                try:
                    paper = self._parse_pdf_link(link)
                    if paper:
                        yield paper
                except Exception as e:
                    print(f"[Portal1] Error parsing link: {e}")
                    continue
    
    def _scrape_concurrent(self, pdf_links) -> Generator[Paper, None, None]:
        """Process PDF links concurrently using ThreadPoolExecutor."""
        papers_queue = []
        
        def process_link(link):
            if self._stop_event.is_set():
                return None
            try:
                return self._parse_pdf_link(link)
            except Exception as e:
                print(f"[Portal1] Error parsing link: {e}")
                return None
        
        # Process in batches to allow yielding results progressively
        batch_size = self.max_workers * 2
        
        for i in range(0, len(pdf_links), batch_size):
            if self._stop_event.is_set():
                print("[Portal1] Stop requested, stopping...")
                break
            
            batch = pdf_links[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_link, link): link for link in batch}
                
                for future in as_completed(futures):
                    if self._stop_event.is_set():
                        break
                    
                    paper = future.result()
                    if paper:
                        yield paper
            
            # Small delay between batches to be respectful
            time.sleep(0.2)
    
    def _parse_pdf_link(self, link) -> Paper:
        """Parse a PDF link and extract metadata."""
        href = link.get('href', '')
        if not href:
            return None
        
        # Make absolute URL
        pdf_url = urljoin(self.BASE_URL, href)
        
        # Extract info from URL path
        # Example: /sites/default/files/Question-Papers/2019/Question Papers Dec 2018-Jan 2019/III Sem/Chemical/...
        path = unquote(pdf_url)
        
        # Parse the path components
        parts = path.split('/')
        
        # Extract year
        year = self._extract_year(path)
        
        # Extract semester
        semester = self._extract_semester(path)
        
        # Extract branch
        branch = self._extract_branch(path)
        
        # Get filename and extract subject info
        filename = parts[-1] if parts else ""
        subject_name, subject_code, exam_type = self._parse_filename(filename)
        
        return Paper(
            title=filename.replace('.pdf', ''),
            subject_code=subject_code,
            subject_name=subject_name,
            year=year,
            semester=semester,
            branch=branch,
            exam_type=exam_type,
            pdf_url=pdf_url,
            portal="portal1"
        )
    
    def _extract_year(self, path: str) -> str:
        """Extract year from path."""
        # Look for 4-digit year
        years = re.findall(r'20\d{2}', path)
        if years:
            return years[0]
        return ""
    
    def _extract_semester(self, path: str) -> str:
        """Extract semester from path."""
        # Look for semester patterns like "III Sem", "I sem", "V Sem"
        sem_match = re.search(r'([IVX]+)\s*[Ss]em', path, re.IGNORECASE)
        if sem_match:
            roman = sem_match.group(1).upper()
            return f"Semester {self._roman_to_int(roman)}"
        return ""
    
    def _extract_branch(self, path: str) -> str:
        """Extract branch from path."""
        branches = [
            "Chemical", "Civil", "Computer", "Electrical", "Electronics",
            "Information Technology", "Mechanical", "Mechatronics",
            "Automobile", "Aeronautical", "Biomedical", "Biotechnology",
            "Industrial", "Instrumentation", "Computer and Communication",
            "Architecture"
        ]
        
        path_lower = path.lower()
        for branch in branches:
            if branch.lower() in path_lower:
                return branch
        
        return ""
    
    def _parse_filename(self, filename: str) -> tuple:
        """Parse filename to extract subject name, code, and exam type."""
        # Remove .pdf extension
        name = filename.replace('.pdf', '')
        
        # Check for Makeup
        exam_type = "Regular"
        if "makeup" in name.lower():
            exam_type = "Makeup"
            name = re.sub(r'\s*\(?[Mm]akeup\)?', '', name)
        
        # Try to extract subject code (e.g., CHE 2104, ICT 2103)
        code_match = re.search(r'\(([A-Z]{2,4}[\s-]*\d{4})\)', name)
        subject_code = ""
        if code_match:
            subject_code = code_match.group(1).replace(' ', '-')
        
        # Clean up subject name
        subject_name = re.sub(r'\([^)]*\)', '', name).strip()
        subject_name = re.sub(r'\s+', ' ', subject_name)
        
        return subject_name, subject_code, exam_type
    
    def _roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer."""
        values = {'I': 1, 'V': 5, 'X': 10}
        result = 0
        prev = 0
        
        for char in reversed(roman.upper()):
            curr = values.get(char, 0)
            if curr < prev:
                result -= curr
            else:
                result += curr
            prev = curr
        
        return result
