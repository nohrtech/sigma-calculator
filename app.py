#!/usr/bin/env python3
"""
NohrTech Sigma Calculator - Web Interface
A professional GNSS position accuracy analysis tool by NohrTech.

This module provides a web interface for the NohrTech Sigma Calculator,
allowing users to upload and analyze GNSS data files through a browser.

Author: NohrTech
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_session import Session
import os
from werkzeug.utils import secure_filename
from nohrtech_sigma import NohrTechSigmaCalculator
from pdf_generator import generate_pdf
import tempfile
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'nohrtech-sigma-calculator-secret-key'  # Static secret key for session management
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in filesystem
app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'flask_session')
app.config['MAX_RESULTS_PER_SESSION'] = 10  # Maximum number of results to store per session

# Ensure the session directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize Flask-Session
Session(app)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'.rnx', '.obs', '.sbf', '.xyz', '.llh'}
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/view_results/<result_id>')
def view_results(result_id):
    logger.debug(f"Accessing results with ID: {result_id}")
    logger.debug(f"Session contents: {session.get('results', {}).keys()}")
    
    if 'results' not in session:
        logger.error("No results found in session")
        return "Results not found", 404
    
    if result_id not in session['results']:
        logger.error(f"Result ID {result_id} not found in session results")
        return "Results not found", 404
    
    results = session['results'][result_id]
    logger.debug(f"Found results for ID {result_id}: {results.get('filename')}")
    return render_template('results.html', 
                         results=results, 
                         filename=results['filename'])

@app.route('/calculate', methods=['POST'])
def calculate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Supported types: .rnx, .obs, .sbf, .xyz, .llh'}), 400

    try:
        # Save uploaded file to temporary location
        temp_dir = app.config['UPLOAD_FOLDER']
        temp_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_path)
        
        # Process the file
        calculator = NohrTechSigmaCalculator(temp_path)
        calculator.read_file()
        results = calculator.calculate_sigma()
        
        if results is None:
            return jsonify({'error': 'No position data found in file'}), 400

        # Convert epoch timestamps to strings if they aren't already
        for epoch in results['epochs']:
            if isinstance(epoch['time'], datetime):
                epoch['time'] = epoch['time'].strftime('%Y/%m/%d %H:%M:%S.%f')
            # Round numerical values to 3 decimal places
            for key in ['horizontal', 'vertical', 'E', 'N', 'U']:
                epoch[key] = round(epoch[key], 3)
        
        # Round summary statistics to 3 decimal places
        for comp in results['summary']:
            for stat in ['mean', 'min', 'max', 'std']:
                results['summary'][comp][stat] = round(results['summary'][comp][stat], 3)
        
        # Store results in session
        if 'results' not in session:
            session['results'] = {}
            
        # Clean up old results if we've reached the maximum
        if len(session['results']) >= app.config['MAX_RESULTS_PER_SESSION']:
            oldest_key = next(iter(session['results']))
            del session['results'][oldest_key]
        
        # Generate unique ID for these results
        result_id = str(uuid.uuid4())
        
        # Store results with filename
        results['filename'] = file.filename
        session['results'][result_id] = results
        session.modified = True

        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify({
            'result_id': result_id,
            'filename': file.filename,
            'summary': results['summary'],
            'epoch_data': results['epochs']
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/compare', methods=['POST'])
def compare_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Two files are required for comparison'}), 400
        
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        return jsonify({'error': 'Both files must be selected'}), 400
        
    # Save files to temporary location
    temp_dir = os.path.join(app.root_path, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    file1_path = os.path.join(temp_dir, secure_filename(file1.filename))
    file2_path = os.path.join(temp_dir, secure_filename(file2.filename))
    
    file1.save(file1_path)
    file2.save(file2_path)
    
    try:
        # Create calculators for both files
        calc1 = NohrTechSigmaCalculator(file1_path)
        calc2 = NohrTechSigmaCalculator(file2_path)
        
        # Read and process files
        calc1.read_file()
        calc2.read_file()
        
        # Compare results
        comparison = calc1.compare_with(calc2)
        
        if comparison is None:
            return jsonify({'error': 'Error processing files'}), 500
            
        # Clean up temporary files
        os.remove(file1_path)
        os.remove(file2_path)
        
        return jsonify({
            'comparison': comparison,
            'file1': file1.filename,
            'file2': file2.filename
        })
        
    except Exception as e:
        # Clean up temporary files
        if os.path.exists(file1_path):
            os.remove(file1_path)
        if os.path.exists(file2_path):
            os.remove(file2_path)
        return jsonify({'error': str(e)}), 500

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_route():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Generate unique filename for PDF
        pdf_filename = f"sigma_results_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

        # Generate PDF
        generate_pdf(pdf_path, data, data.get('filename', 'Unknown File'))

        # Send file to client
        response = send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

        # Clean up PDF file after sending
        @response.call_on_close
        def cleanup():
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
