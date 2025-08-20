"""
Flask API server for genetic analysis
Integrates the OfflineGenomeAnalyzer with a REST API for the React frontend
"""

import os
import json
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import our analyzer
import sys
sys.path.append('./OfflineGenomeAnalyzer')
from offline_analyzer import OfflineGenomeAnalyzer, AnalysisResult

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'gz'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store analysis sessions
analysis_sessions: Dict[str, Dict] = {}


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_yolo_metrics(results: List[AnalysisResult]) -> Dict:
    """
    Transform real genomic analysis into humorous YOLO-style metrics
    while preserving the scientific accuracy of the underlying data
    """
    if not results:
        return {
            'riskApeIndex': 50,
            'disciplineFactor': 50,
            'diamondHandsDNA': 50,
            'panicSellPropensity': 50,
            'valueVersusMomentum': 'Balanced Ape',
            'totalSnpsAnalyzed': 0,
            'significantFindings': 0
        }
    
    # Analyze significant SNPs (magnitude >= 2.0)
    significant_snps = [r for r in results if r.magnitude and r.magnitude >= 2.0]
    high_mag_snps = [r for r in results if r.magnitude and r.magnitude >= 3.0]
    
    # Calculate Risk Ape Index based on significant SNPs with bad repute
    bad_significant = [r for r in significant_snps if r.repute and 'bad' in r.repute.lower()]
    good_significant = [r for r in significant_snps if r.repute and 'good' in r.repute.lower()]
    
    # Risk Ape Index: Higher = more genetic risk tolerance
    # Based on ratio of significant SNPs and their magnitudes
    total_magnitude = sum(r.magnitude for r in significant_snps if r.magnitude)
    avg_magnitude = total_magnitude / len(significant_snps) if significant_snps else 2.0
    
    risk_ape_base = min(95, max(5, int((avg_magnitude / 4.0) * 100)))
    risk_ape_index = max(5, min(95, risk_ape_base + len(high_mag_snps) * 2))
    
    # Discipline Factor: Lower = more impulsive (based on neurotransmitter/behavior SNPs)
    behavior_keywords = ['dopamine', 'serotonin', 'anxiety', 'impulsive', 'addiction', 'reward']
    behavior_snps = [
        r for r in results 
        if r.summary and any(keyword in r.summary.lower() for keyword in behavior_keywords)
    ]
    discipline_factor = max(10, min(90, 75 - len(behavior_snps) * 2))
    
    # Diamond Hands DNA: Based on stress response and persistence genes
    stress_keywords = ['stress', 'cortisol', 'resilience', 'persistence', 'endurance']
    stress_snps = [
        r for r in results
        if r.summary and any(keyword in r.summary.lower() for keyword in stress_keywords)
    ]
    diamond_hands = max(15, min(95, 60 + len([s for s in stress_snps if s.repute and 'good' in s.repute.lower()]) * 5))
    
    # Panic Sell Propensity: Inverse of diamond hands + anxiety factors
    anxiety_snps = [
        r for r in results
        if r.summary and 'anxiety' in r.summary.lower() and r.repute and 'bad' in r.repute.lower()
    ]
    panic_sell = max(5, min(85, 100 - diamond_hands + len(anxiety_snps) * 3))
    
    # Value vs Momentum classification
    if risk_ape_index > 80:
        strategy = "Momentum YOLO Ape"
    elif risk_ape_index < 30:
        strategy = "Value Ape (Buffet DNA)"
    elif discipline_factor > 70:
        strategy = "Calculated Risk Chad"
    else:
        strategy = "Balanced Degen"
    
    return {
        'riskApeIndex': risk_ape_index,
        'disciplineFactor': discipline_factor,
        'diamondHandsDNA': diamond_hands,
        'panicSellPropensity': panic_sell,
        'valueVersusMomentum': strategy,
        'totalSnpsAnalyzed': len(results),
        'significantFindings': len(significant_snps),
        'highMagnitudeFindings': len(high_mag_snps),
        'averageMagnitude': round(avg_magnitude, 2) if significant_snps else 0,
        'goodRepute': len(good_significant),
        'badRepute': len(bad_significant)
    }


def get_top_findings(results: List[AnalysisResult], limit: int = 10) -> List[Dict]:
    """Get top significant findings for display"""
    significant = [r for r in results if r.magnitude and r.magnitude >= 2.0]
    significant.sort(key=lambda x: x.magnitude, reverse=True)
    
    findings = []
    for result in significant[:limit]:
        findings.append({
            'rsid': result.rsid,
            'genotype': result.user_genotype,
            'magnitude': result.magnitude,
            'repute': result.repute,
            'summary': result.summary,
            'interpretation': result.interpretation,
            'chromosome': result.chromosome,
            'position': result.position
        })
    
    return findings


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/upload', methods=['POST'])
def upload_genome():
    """Upload and analyze a genome file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a .txt or .txt.gz file'}), 400
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)
        
        # Initialize analyzer
        analyzer = OfflineGenomeAnalyzer(db_path="SNPedia2025/SNPedia2025.db")
        
        # Load genome
        genome_stats = analyzer.load_genome(filepath)
        
        # Store session info
        analysis_sessions[session_id] = {
            'status': 'uploaded',
            'filename': filename,
            'filepath': filepath,
            'genome_stats': genome_stats,
            'analyzer': analyzer,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'session_id': session_id,
            'status': 'uploaded',
            'genome_stats': genome_stats,
            'message': f'Successfully loaded {genome_stats["total_snps"]} SNPs from {filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/analyze/<session_id>', methods=['POST'])
def analyze_genome(session_id):
    """Analyze uploaded genome"""
    try:
        if session_id not in analysis_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = analysis_sessions[session_id]
        analyzer = session['analyzer']
        
        # Get analysis parameters
        data = request.get_json() or {}
        magnitude_threshold = data.get('magnitude_threshold', 0.0)
        limit = data.get('limit', None)  # For testing, can limit number of SNPs
        
        # Update session status
        session['status'] = 'analyzing'
        
        # Perform analysis
        results = analyzer.analyze_all(magnitude_threshold=magnitude_threshold, limit=limit)
        
        # Calculate YOLO metrics
        yolo_metrics = calculate_yolo_metrics(results)
        
        # Get top findings
        top_findings = get_top_findings(results, limit=20)
        
        # Get summary stats
        summary_stats = analyzer.get_summary_stats()
        
        # Update session with results
        session.update({
            'status': 'completed',
            'results_count': len(results),
            'yolo_metrics': yolo_metrics,
            'top_findings': top_findings,
            'summary_stats': summary_stats,
            'analyzed_at': datetime.now().isoformat()
        })
        
        return jsonify({
            'session_id': session_id,
            'status': 'completed',
            'yolo_metrics': yolo_metrics,
            'top_findings': top_findings,
            'summary_stats': summary_stats,
            'analysis_summary': {
                'total_analyzed': len(results),
                'significant_snps': len([r for r in results if r.magnitude and r.magnitude >= 2.0]),
                'avg_magnitude': yolo_metrics['averageMagnitude']
            }
        })
        
    except Exception as e:
        if session_id in analysis_sessions:
            analysis_sessions[session_id]['status'] = 'error'
            analysis_sessions[session_id]['error'] = str(e)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/status/<session_id>', methods=['GET'])
def get_analysis_status(session_id):
    """Get status of analysis session"""
    if session_id not in analysis_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = analysis_sessions[session_id]
    
    # Return session info without the analyzer object
    response_data = {
        'session_id': session_id,
        'status': session['status'],
        'created_at': session['created_at']
    }
    
    if 'filename' in session:
        response_data['filename'] = session['filename']
    if 'genome_stats' in session:
        response_data['genome_stats'] = session['genome_stats']
    if 'yolo_metrics' in session:
        response_data['yolo_metrics'] = session['yolo_metrics']
    if 'top_findings' in session:
        response_data['top_findings'] = session['top_findings']
    if 'error' in session:
        response_data['error'] = session['error']
        
    return jsonify(response_data)


@app.route('/api/export/<session_id>', methods=['GET'])
def export_results(session_id):
    """Export analysis results as JSON"""
    if session_id not in analysis_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = analysis_sessions[session_id]
    if session['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    try:
        analyzer = session['analyzer']
        
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            analyzer.export_results(tmp_file.name, format='json')
            temp_filepath = tmp_file.name
        
        # Send file and clean up
        response = send_file(
            temp_filepath,
            as_attachment=True,
            download_name=f'genetic_analysis_{session_id}.json',
            mimetype='application/json'
        )
        
        # Clean up temp file after sending
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(temp_filepath)
            except:
                pass
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all analysis sessions (for debugging)"""
    sessions_info = []
    for session_id, session in analysis_sessions.items():
        session_info = {
            'session_id': session_id,
            'status': session['status'],
            'created_at': session['created_at']
        }
        if 'filename' in session:
            session_info['filename'] = session['filename']
        if 'results_count' in session:
            session_info['results_count'] = session['results_count']
        sessions_info.append(session_info)
    
    return jsonify({'sessions': sessions_info})


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


if __name__ == '__main__':
    print("Starting Genetic YOLO API Server...")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print("Server will run on http://localhost:5001")
    print("\nAPI Endpoints:")
    print("  GET  /api/health                  - Health check")
    print("  POST /api/upload                  - Upload genome file") 
    print("  POST /api/analyze/<session_id>    - Analyze genome")
    print("  GET  /api/status/<session_id>     - Get analysis status")
    print("  GET  /api/export/<session_id>     - Export results as JSON")
    print("  GET  /api/sessions                - List all sessions")
    
    app.run(debug=True, host='0.0.0.0', port=5001)