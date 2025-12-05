import re
import time
from typing import List, Generator
from urllib.parse import urljoin, unquote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app.models.paper import Paper


class Portal2Scraper:
    """
    Scraper for https://libportal.manipal.edu/mit/Question%20Paper.aspx
    
    This portal uses ASPX with JavaScript postbacks for folder navigation.
    Requires Selenium for browser automation.
    """
    
    BASE_URL = "https://libportal.manipal.edu/mit/Question%20Paper.aspx"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver."""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
    
    def _close_driver(self):
        """Close Chrome driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape_all(self, years: List[str] = None) -> Generator[Paper, None, None]:
        """
        Scrape all papers from Portal 2.
        
        Args:
            years: Optional list of years to scrape (e.g., ['2023', '2024']).
                   If None, scrapes all available years.
        """
        try:
            self._init_driver()
            print(f"[Portal2] Starting scrape from {self.BASE_URL}")
            
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            
            # Get available years
            available_years = self._get_folder_links()
            print(f"[Portal2] Found years: {[y['text'] for y in available_years]}")
            
            for year_info in available_years:
                year = year_info['text']
                
                # Skip if specific years requested and this isn't one of them
                if years and year not in years:
                    continue
                
                print(f"[Portal2] Processing year: {year}")
                
                # Click on year folder
                self._click_folder(year_info['index'])
                time.sleep(1)
                
                # Get exam session folders (e.g., "Dec 2022 - Jan 2023")
                session_folders = self._get_folder_links()
                
                for session_info in session_folders:
                    session = session_info['text']
                    print(f"[Portal2] Processing session: {session}")
                    
                    # Click on session folder
                    self._click_folder(session_info['index'])
                    time.sleep(1)
                    
                    # Now we should see branches/semesters
                    yield from self._scrape_branch_level(year, session)
                    
                    # Go back to year level
                    self._go_back()
                    time.sleep(0.5)
                
                # Go back to root
                self._go_back()
                time.sleep(0.5)
                
        finally:
            self._close_driver()
    
    def _scrape_branch_level(self, year: str, session: str) -> Generator[Paper, None, None]:
        """Scrape papers from branch/semester level."""
        folders = self._get_folder_links()
        pdf_links = self._get_pdf_links()
        
        # First yield any PDFs at this level
        for pdf_info in pdf_links:
            paper = self._create_paper(pdf_info, year, session, "", "")
            if paper:
                yield paper
        
        # Then recurse into folders
        for folder_info in folders:
            folder_name = folder_info['text']
            print(f"[Portal2] Processing folder: {folder_name}")
            
            self._click_folder(folder_info['index'])
            time.sleep(0.5)
            
            # Check for PDFs or more folders
            sub_folders = self._get_folder_links()
            pdf_links = self._get_pdf_links()
            
            if pdf_links:
                # We're at the leaf level with PDFs
                for pdf_info in pdf_links:
                    paper = self._create_paper(pdf_info, year, session, folder_name, "")
                    if paper:
                        yield paper
            
            if sub_folders:
                # More nesting - likely subject folders
                for sub_folder in sub_folders:
                    self._click_folder(sub_folder['index'])
                    time.sleep(0.5)
                    
                    inner_pdfs = self._get_pdf_links()
                    for pdf_info in inner_pdfs:
                        paper = self._create_paper(pdf_info, year, session, folder_name, sub_folder['text'])
                        if paper:
                            yield paper
                    
                    self._go_back()
                    time.sleep(0.3)
            
            self._go_back()
            time.sleep(0.3)
    
    def _get_folder_links(self) -> List[dict]:
        """Get all folder links on current page."""
        folders = []
        try:
            # Find folder icons and their associated links
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='__doPostBack']")
            
            for i, elem in enumerate(elements):
                text = elem.text.strip()
                if text and not text.endswith('.pdf'):
                    folders.append({
                        'text': text,
                        'index': i,
                        'element': elem
                    })
        except Exception as e:
            print(f"[Portal2] Error getting folders: {e}")
        
        return folders
    
    def _get_pdf_links(self) -> List[dict]:
        """Get all PDF links on current page."""
        pdfs = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
            
            for elem in elements:
                href = elem.get_attribute('href')
                text = elem.text.strip()
                if href:
                    pdfs.append({
                        'text': text or href.split('/')[-1],
                        'url': href
                    })
        except Exception as e:
            print(f"[Portal2] Error getting PDFs: {e}")
        
        return pdfs
    
    def _click_folder(self, index: int):
        """Click on a folder by index."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='__doPostBack']")
            if index < len(elements):
                elements[index].click()
        except Exception as e:
            print(f"[Portal2] Error clicking folder: {e}")
    
    def _go_back(self):
        """Go back to parent folder."""
        try:
            # Look for "Back" or ".." link
            back_links = self.driver.find_elements(By.LINK_TEXT, "..")
            if back_links:
                back_links[0].click()
                return
            
            # Or try the go back button if present
            back_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[title='Go Back']")
            if back_buttons:
                back_buttons[0].click()
        except Exception as e:
            print(f"[Portal2] Error going back: {e}")
    
    def _create_paper(self, pdf_info: dict, year: str, session: str, 
                      folder1: str, folder2: str) -> Paper:
        """Create a Paper object from extracted info."""
        try:
            filename = pdf_info['text']
            pdf_url = pdf_info['url']
            
            # Parse filename for subject info
            subject_name, subject_code, exam_type = self._parse_filename(filename)
            
            # Determine semester from folder structure
            semester = self._extract_semester(folder1 + " " + folder2)
            
            # Determine branch
            branch = self._extract_branch(folder1 + " " + folder2 + " " + filename)
            
            return Paper(
                title=filename.replace('.pdf', ''),
                subject_code=subject_code,
                subject_name=subject_name,
                year=year,
                semester=semester,
                branch=branch,
                exam_type=exam_type,
                pdf_url=pdf_url,
                portal="portal2"
            )
        except Exception as e:
            print(f"[Portal2] Error creating paper: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> tuple:
        """Parse filename to extract subject info."""
        name = filename.replace('.pdf', '')
        
        exam_type = "Regular"
        if "makeup" in name.lower():
            exam_type = "Makeup"
            name = re.sub(r'\s*\(?[Mm]akeup\)?', '', name)
        
        code_match = re.search(r'\(([A-Z]{2,4}[\s-]*\d{4})\)', name)
        subject_code = ""
        if code_match:
            subject_code = code_match.group(1).replace(' ', '-')
        
        subject_name = re.sub(r'\([^)]*\)', '', name).strip()
        subject_name = re.sub(r'\s+', ' ', subject_name)
        
        return subject_name, subject_code, exam_type
    
    def _extract_semester(self, text: str) -> str:
        """Extract semester from text."""
        sem_match = re.search(r'([IVX]+)\s*[Ss]em', text, re.IGNORECASE)
        if sem_match:
            roman = sem_match.group(1).upper()
            return f"Semester {self._roman_to_int(roman)}"
        return ""
    
    def _extract_branch(self, text: str) -> str:
        """Extract branch from text."""
        branches = [
            "Chemical", "Civil", "Computer", "Electrical", "Electronics",
            "Information Technology", "Mechanical", "Mechatronics",
            "Automobile", "Aeronautical", "Biomedical", "Biotechnology",
            "Industrial", "Instrumentation", "Computer and Communication"
        ]
        
        text_lower = text.lower()
        for branch in branches:
            if branch.lower() in text_lower:
                return branch
        return ""
    
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
