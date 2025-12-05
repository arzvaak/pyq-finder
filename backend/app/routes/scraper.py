import threading
from flask import Blueprint, request, jsonify
from app.services.firebase_service import firebase_service
from app.services.portal1_scraper import Portal1Scraper
from app.services.portal2_scraper import Portal2Scraper

scraper_bp = Blueprint('scraper', __name__)

# Track scraping status with stop event
scrape_status = {
    'is_running': False,
    'stop_requested': False,
    'portal': None,
    'progress': 0,
    'skipped': 0,
    'total': 0,
    'errors': [],
    'message': ''
}


def run_scrape(portal: str, years: list = None, upload_to_storage: bool = False, workers: int = 5):
    """
    Background task to run scraping.
    
    By default, only stores PDF links (not the actual files).
    This is faster and doesn't use storage space.
    
    Args:
        portal: 'portal1' or 'portal2'
        years: Optional list of years to filter (for portal2)
        upload_to_storage: Whether to upload PDFs to Firebase Storage
        workers: Number of concurrent workers (default 5, for portal1)
    
    Duplicate detection:
    1. Checks if exact PDF URL already exists
    2. Checks if similar paper exists (same subject_code + year + semester)
    """
    global scrape_status
    
    scrape_status['is_running'] = True
    scrape_status['stop_requested'] = False
    scrape_status['portal'] = portal
    scrape_status['progress'] = 0
    scrape_status['skipped'] = 0
    scrape_status['errors'] = []
    scrape_status['message'] = f'Starting scrape for {portal} with {workers} workers...'
    
    scraper = None
    
    try:
        if portal == 'portal1':
            scraper = Portal1Scraper(max_workers=workers)
            papers_generator = scraper.scrape_all(concurrent=True)
        elif portal == 'portal2':
            scraper = Portal2Scraper(headless=True)
            papers_generator = scraper.scrape_all(years=years)
        else:
            scrape_status['message'] = f'Unknown portal: {portal}'
            scrape_status['is_running'] = False
            return
        
        count = 0
        skipped = 0
        
        for paper in papers_generator:
            # Check if stop was requested
            if scrape_status['stop_requested']:
                scrape_status['message'] = f'Stopped! Scraped {count} papers, skipped {skipped} duplicates.'
                break
            
            try:
                # Check for duplicates using multiple methods
                # 1. Check if exact PDF URL exists
                if firebase_service.paper_exists(paper.pdf_url):
                    scrape_status['message'] = f'Skipping (URL exists): {paper.title}'
                    skipped += 1
                    scrape_status['skipped'] = skipped
                    continue
                
                # 2. Check if similar paper exists (same subject_code + year + semester)
                if paper.subject_code and firebase_service.paper_exists_by_metadata(
                    subject_code=paper.subject_code,
                    year=paper.year,
                    semester=paper.semester,
                    exam_type=paper.exam_type
                ):
                    scrape_status['message'] = f'Skipping (metadata exists): {paper.title}'
                    skipped += 1
                    scrape_status['skipped'] = skipped
                    continue
                
                # Optionally upload PDF to storage (disabled by default)
                if upload_to_storage:
                    try:
                        storage_path = f"papers/{portal}/{paper.year}/{paper.branch}/{paper.title}.pdf"
                        storage_url = firebase_service.upload_pdf(paper.pdf_url, storage_path)
                        paper.storage_url = storage_url
                        scrape_status['message'] = f'Uploaded: {paper.title}'
                    except Exception as e:
                        scrape_status['errors'].append(f'Upload failed for {paper.title}: {str(e)}')
                
                # Save paper metadata to Firestore (includes the original PDF link)
                firebase_service.add_paper(paper)
                count += 1
                scrape_status['progress'] = count
                scrape_status['message'] = f'Saved: {paper.title}'
                
            except Exception as e:
                scrape_status['errors'].append(f'Error processing {paper.title}: {str(e)}')
        
        if not scrape_status['stop_requested']:
            scrape_status['message'] = f'Completed! Scraped {count} new papers, skipped {skipped} duplicates.'
        scrape_status['total'] = count
        
    except Exception as e:
        scrape_status['message'] = f'Scrape failed: {str(e)}'
        scrape_status['errors'].append(str(e))
    
    finally:
        scrape_status['is_running'] = False
        scrape_status['stop_requested'] = False


@scraper_bp.route('/scrape', methods=['POST'])
def start_scrape():
    """
    Start a scraping job.
    
    Body:
        - portal: 'portal1' or 'portal2' or 'both'
        - years: Optional list of years (for portal2)
        - upload_to_storage: Whether to upload PDFs to Firebase Storage (default false)
        - workers: Number of concurrent workers (1-10, default 5)
    """
    global scrape_status
    
    if scrape_status['is_running']:
        return jsonify({
            'success': False,
            'error': 'A scrape is already running',
            'status': scrape_status
        }), 409
    
    data = request.get_json() or {}
    portal = data.get('portal', 'portal1')
    years = data.get('years')
    upload_to_storage = data.get('upload_to_storage', False)
    workers = min(max(int(data.get('workers', 5)), 1), 10)  # Clamp between 1-10
    
    if portal not in ['portal1', 'portal2', 'both']:
        return jsonify({
            'success': False,
            'error': 'Invalid portal. Use portal1, portal2, or both'
        }), 400
    
    # Start scraping in background thread
    if portal == 'both':
        # Run both sequentially
        def run_both():
            run_scrape('portal1', years, upload_to_storage, workers)
            if not scrape_status['stop_requested']:
                run_scrape('portal2', years, upload_to_storage, workers)
        
        thread = threading.Thread(target=run_both)
    else:
        thread = threading.Thread(target=run_scrape, args=(portal, years, upload_to_storage, workers))
    
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Scrape started for {portal}',
        'status': scrape_status
    })


@scraper_bp.route('/scrape/status', methods=['GET'])
def get_scrape_status():
    """Get the current scraping status."""
    return jsonify({
        'success': True,
        'data': scrape_status
    })


@scraper_bp.route('/scrape/stop', methods=['POST'])
def stop_scrape():
    """Stop the current scrape."""
    global scrape_status
    
    if not scrape_status['is_running']:
        return jsonify({
            'success': False,
            'error': 'No scrape is currently running'
        }), 400
    
    # Set stop flag - the scraper loop will check this
    scrape_status['stop_requested'] = True
    scrape_status['message'] = 'Stopping...'
    
    return jsonify({
        'success': True,
        'message': 'Stop requested - scraper will stop after current paper'
    })
