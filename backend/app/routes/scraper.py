import threading
from flask import Blueprint, request, jsonify
from app.services.firebase_service import firebase_service
from app.services.portal1_scraper import Portal1Scraper
from app.services.portal2_scraper import Portal2Scraper

scraper_bp = Blueprint('scraper', __name__)

# Track scraping status
scrape_status = {
    'is_running': False,
    'portal': None,
    'progress': 0,
    'total': 0,
    'errors': [],
    'message': ''
}


def run_scrape(portal: str, years: list = None, upload_to_storage: bool = True):
    """Background task to run scraping."""
    global scrape_status
    
    scrape_status['is_running'] = True
    scrape_status['portal'] = portal
    scrape_status['progress'] = 0
    scrape_status['errors'] = []
    scrape_status['message'] = f'Starting scrape for {portal}...'
    
    try:
        if portal == 'portal1':
            scraper = Portal1Scraper()
            papers_generator = scraper.scrape_all()
        elif portal == 'portal2':
            scraper = Portal2Scraper(headless=True)
            papers_generator = scraper.scrape_all(years=years)
        else:
            scrape_status['message'] = f'Unknown portal: {portal}'
            scrape_status['is_running'] = False
            return
        
        count = 0
        for paper in papers_generator:
            try:
                # Check if paper already exists
                if firebase_service.paper_exists(paper.pdf_url):
                    scrape_status['message'] = f'Skipping existing: {paper.title}'
                    continue
                
                # Upload PDF to storage if requested
                if upload_to_storage:
                    try:
                        storage_path = f"papers/{portal}/{paper.year}/{paper.branch}/{paper.title}.pdf"
                        storage_url = firebase_service.upload_pdf(paper.pdf_url, storage_path)
                        paper.storage_url = storage_url
                        scrape_status['message'] = f'Uploaded: {paper.title}'
                    except Exception as e:
                        scrape_status['errors'].append(f'Upload failed for {paper.title}: {str(e)}')
                        # Still save the paper without storage URL
                
                # Save paper to Firestore
                firebase_service.add_paper(paper)
                count += 1
                scrape_status['progress'] = count
                scrape_status['message'] = f'Saved: {paper.title}'
                
            except Exception as e:
                scrape_status['errors'].append(f'Error processing {paper.title}: {str(e)}')
        
        scrape_status['message'] = f'Completed! Scraped {count} papers.'
        scrape_status['total'] = count
        
    except Exception as e:
        scrape_status['message'] = f'Scrape failed: {str(e)}'
        scrape_status['errors'].append(str(e))
    
    finally:
        scrape_status['is_running'] = False


@scraper_bp.route('/scrape', methods=['POST'])
def start_scrape():
    """
    Start a scraping job.
    
    Body:
        - portal: 'portal1' or 'portal2' or 'both'
        - years: Optional list of years (for portal2)
        - upload_to_storage: Whether to upload PDFs to Firebase Storage (default true)
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
    upload_to_storage = data.get('upload_to_storage', True)
    
    if portal not in ['portal1', 'portal2', 'both']:
        return jsonify({
            'success': False,
            'error': 'Invalid portal. Use portal1, portal2, or both'
        }), 400
    
    # Start scraping in background thread
    if portal == 'both':
        # Run both sequentially
        def run_both():
            run_scrape('portal1', years, upload_to_storage)
            run_scrape('portal2', years, upload_to_storage)
        
        thread = threading.Thread(target=run_both)
    else:
        thread = threading.Thread(target=run_scrape, args=(portal, years, upload_to_storage))
    
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
    """Request to stop the current scrape (best effort)."""
    global scrape_status
    
    if not scrape_status['is_running']:
        return jsonify({
            'success': False,
            'error': 'No scrape is currently running'
        }), 400
    
    # Note: This doesn't actually stop the thread, just marks it for stopping
    # A proper implementation would use threading events
    scrape_status['message'] = 'Stop requested...'
    
    return jsonify({
        'success': True,
        'message': 'Stop requested'
    })
