import re
import time
import threading
from typing import List, Generator
from urllib.parse import urljoin, unquote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from app.models.paper import Paper


class Portal2Scraper:
    """
    Scraper for https://libportal.manipal.edu/mit/Question%20Paper.aspx
    
    This portal uses ASPX with JavaScript postbacks for folder navigation.
    Requires Selenium for browser automation.
    
    Improved with:
    - Better timeout handling
    - Stop event support
    - Retry logic for stale elements
    - Progress tracking
    """
    
    BASE_URL = "https://libportal.manipal.edu/mit/Question%20Paper.aspx"
    
    # Timeouts in seconds
    PAGE_LOAD_TIMEOUT = 15
    ELEMENT_TIMEOUT = 5
    NAVIGATION_DELAY = 1.0
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._stop_event = threading.Event()
        self._current_path = []  # Track navigation path for debugging
    
    def stop(self):
        """Signal the scraper to stop."""
        self._stop_event.set()
    
    def _should_stop(self) -> bool:
        """Check if stop was requested."""
        return self._stop_event.is_set()
    
    def _init_driver(self):
        """Initialize Chrome driver with optimized settings."""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')  # New headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-images')  # Faster loading
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Disable unnecessary features for speed
        options.add_experimental_option('prefs', {
            'profile.managed_default_content_settings.images': 2,  # Disable images
        })
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
        self.driver.implicitly_wait(self.ELEMENT_TIMEOUT)
    
    def _close_driver(self):
        """Close Chrome driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def scrape_all(self, years: List[str] = None) -> Generator[Paper, None, None]:
        """
        Scrape all papers from Portal 2.
        
        Args:
            years: Optional list of years to scrape (e.g., ['2023', '2024']).
                   If None, scrapes all available years.
        """
        self._stop_event.clear()
        
        try:
            self._init_driver()
            print(f"[Portal2] Starting scrape from {self.BASE_URL}")
            
            self.driver.get(self.BASE_URL)
            self._wait_for_page_load()
            
            # Get available years
            available_years = self._get_folder_links()
            print(f"[Portal2] Found {len(available_years)} years")
            
            for year_info in available_years:
                if self._should_stop():
                    print("[Portal2] Stop requested, exiting...")
                    break
                
                year = year_info['text']
                
                # Skip if specific years requested and this isn't one of them
                if years and year not in years:
                    continue
                
                print(f"[Portal2] Processing year: {year}")
                self._current_path = [year]
                
                # Click on year folder with retry
                if not self._safe_click_folder(year_info['index']):
                    continue
                
                # Get exam session folders (e.g., "Dec 2022 - Jan 2023")
                session_folders = self._get_folder_links()
                
                for session_info in session_folders:
                    if self._should_stop():
                        break
                    
                    session = session_info['text']
                    print(f"[Portal2]   Session: {session}")
                    self._current_path = [year, session]
                    
                    # Click on session folder
                    if not self._safe_click_folder(session_info['index']):
                        continue
                    
                    # Now we should see branches/semesters
                    try:
                        yield from self._scrape_branch_level(year, session)
                    except Exception as e:
                        print(f"[Portal2] Error in branch level: {e}")
                    
                    # Go back to year level
                    self._safe_go_back()
                
                # Go back to root
                self._safe_go_back()
                
        except Exception as e:
            print(f"[Portal2] Fatal error: {e}")
        finally:
            self._close_driver()
    
    def _scrape_branch_level(self, year: str, session: str) -> Generator[Paper, None, None]:
        """Scrape papers from branch/semester level."""
        if self._should_stop():
            return
        
        folders = self._get_folder_links()
        pdf_links = self._get_pdf_links()
        
        # First yield any PDFs at this level
        for pdf_info in pdf_links:
            if self._should_stop():
                return
            paper = self._create_paper(pdf_info, year, session, "", "")
            if paper:
                yield paper
        
        # Then recurse into folders (limit depth to avoid infinite loops)
        for folder_info in folders:
            if self._should_stop():
                return
            
            folder_name = folder_info['text']
            
            # Skip common non-paper folders
            if self._should_skip_folder(folder_name):
                print(f"[Portal2]     Skipping: {folder_name}")
                continue
            
            print(f"[Portal2]     Folder: {folder_name}")
            
            if not self._safe_click_folder(folder_info['index']):
                continue
            
            # Check for PDFs or more folders
            sub_folders = self._get_folder_links()
            pdf_links = self._get_pdf_links()
            
            if pdf_links:
                # We're at the leaf level with PDFs
                for pdf_info in pdf_links:
                    if self._should_stop():
                        break
                    paper = self._create_paper(pdf_info, year, session, folder_name, "")
                    if paper:
                        yield paper
            
            if sub_folders and len(sub_folders) < 50:  # Limit subfolder recursion
                # More nesting - likely subject folders
                for sub_folder in sub_folders[:30]:  # Limit to first 30 subfolders
                    if self._should_stop():
                        break
                    
                    if not self._safe_click_folder(sub_folder['index']):
                        continue
                    
                    inner_pdfs = self._get_pdf_links()
                    for pdf_info in inner_pdfs:
                        if self._should_stop():
                            break
                        paper = self._create_paper(pdf_info, year, session, folder_name, sub_folder['text'])
                        if paper:
                            yield paper
                    
                    self._safe_go_back()
            
            self._safe_go_back()
    
    def _should_skip_folder(self, name: str) -> bool:
        """Check if folder should be skipped."""
        skip_patterns = [
            'SOP', 'Standard Operating', 'Guidelines', 'Manual',
            'Template', 'Format', 'Instructions', 'Help',
            'Elsevier', 'Open Access', 'Copyright'
        ]
        name_lower = name.lower()
        return any(pattern.lower() in name_lower for pattern in skip_patterns)
    
    def _wait_for_page_load(self, timeout: float = None):
        """Wait for page to finish loading."""
        timeout = timeout or self.ELEMENT_TIMEOUT
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            pass
        time.sleep(self.NAVIGATION_DELAY)
    
    def _get_folder_links(self) -> List[dict]:
        """Get all folder links on current page."""
        folders = []
        try:
            # Wait a bit for elements to load
            time.sleep(0.5)
            
            # Find folder icons and their associated links
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='__doPostBack']")
            
            for i, elem in enumerate(elements):
                try:
                    text = elem.text.strip()
                    if text and not text.endswith('.pdf') and text != '..':
                        folders.append({
                            'text': text,
                            'index': i
                        })
                except StaleElementReferenceException:
                    continue
                    
        except Exception as e:
            print(f"[Portal2] Error getting folders: {e}")
        
        return folders
    
    def _get_pdf_links(self) -> List[dict]:
        """Get all PDF links on current page."""
        pdfs = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
            
            for elem in elements:
                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()
                    if href:
                        pdfs.append({
                            'text': text or href.split('/')[-1],
                            'url': href
                        })
                except StaleElementReferenceException:
                    continue
                    
        except Exception as e:
            print(f"[Portal2] Error getting PDFs: {e}")
        
        return pdfs
    
    def _safe_click_folder(self, index: int, retries: int = 2) -> bool:
        """Click on a folder by index with retry logic."""
        for attempt in range(retries):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='__doPostBack']")
                if index < len(elements):
                    elements[index].click()
                    self._wait_for_page_load()
                    return True
            except StaleElementReferenceException:
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"[Portal2] Error clicking folder (attempt {attempt + 1}): {e}")
                time.sleep(0.5)
        return False
    
    def _safe_go_back(self, retries: int = 2) -> bool:
        """Go back to parent folder with retry logic."""
        for attempt in range(retries):
            try:
                # Look for ".." link (most common back navigation)
                back_links = self.driver.find_elements(By.LINK_TEXT, "..")
                if back_links:
                    back_links[0].click()
                    self._wait_for_page_load()
                    return True
                
                # Or try the go back button if present
                back_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[title='Go Back']")
                if back_buttons:
                    back_buttons[0].click()
                    self._wait_for_page_load()
                    return True
                    
                # If no back button, we might be at root
                return False
                
            except StaleElementReferenceException:
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"[Portal2] Error going back (attempt {attempt + 1}): {e}")
                time.sleep(0.5)
        return False
    
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
