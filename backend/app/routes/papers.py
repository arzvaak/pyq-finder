from flask import Blueprint, request, jsonify
from app.services.firebase_service import firebase_service

papers_bp = Blueprint('papers', __name__)


@papers_bp.route('/papers', methods=['GET'])
def get_papers():
    """
    Get papers with optional filters.
    
    Query params:
        - year: Filter by year
        - semester: Filter by semester
        - branch: Filter by branch
        - subject: Filter by subject name
        - search: Search term
        - limit: Max results (default 50)
        - offset: Pagination offset (default 0)
    """
    try:
        year = request.args.get('year')
        semester = request.args.get('semester')
        branch = request.args.get('branch')
        subject = request.args.get('subject')
        search = request.args.get('search')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        if search:
            papers = firebase_service.search_papers(search, limit=limit)
        else:
            papers = firebase_service.get_papers(
                year=year,
                semester=semester,
                branch=branch,
                subject=subject,
                limit=limit,
                offset=offset
            )
        
        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in papers],
            'count': len(papers)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@papers_bp.route('/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id: str):
    """Get a single paper by ID."""
    try:
        paper = firebase_service.get_paper(paper_id)
        
        if not paper:
            return jsonify({
                'success': False,
                'error': 'Paper not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': paper.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@papers_bp.route('/papers/<paper_id>/download', methods=['GET'])
def download_paper(paper_id: str):
    """Get download URL for a paper."""
    try:
        paper = firebase_service.get_paper(paper_id)
        
        if not paper:
            return jsonify({
                'success': False,
                'error': 'Paper not found'
            }), 404
        
        # Return storage URL if available, otherwise original URL
        download_url = paper.storage_url or paper.pdf_url
        
        return jsonify({
            'success': True,
            'data': {
                'download_url': download_url,
                'title': paper.title
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@papers_bp.route('/filters', methods=['GET'])
def get_filters():
    """Get available filter options."""
    try:
        years = firebase_service.get_unique_values('year')
        semesters = firebase_service.get_unique_values('semester')
        branches = firebase_service.get_unique_values('branch')
        
        return jsonify({
            'success': True,
            'data': {
                'years': years,
                'semesters': semesters,
                'branches': branches
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
