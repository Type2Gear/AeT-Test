import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import sys
import json
from flask_cors import CORS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.heart_rate_analyzer import HeartRateAnalyzer
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-interactive plotting

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes with all origins
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'fit', 'gpx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def time_to_seconds(time_str):
    """Convert time string in format HH:MM:SS to seconds"""
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/what-is-this')
def what_is_this():
    return render_template('what_is_this.html')

@app.route('/how-to-use')
def how_to_use():
    return render_template('how_to_use.html')

@app.route('/preview', methods=['POST'])
def preview():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .fit or .gpx files only.'}), 400
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Create analyzer instance
        analyzer = HeartRateAnalyzer(filepath)
        analyzer.load_data()
        
        # Get the full dataset for the preview
        preview_data = analyzer.get_preview_data()
        
        # Clean up the uploaded file but save the filename in session
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'preview_data': preview_data
        })
        
    except Exception as e:
        # Clean up files in case of error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
            
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get the section data from form data
        section1_start = request.form.get('section1_start')
        section1_end = request.form.get('section1_end')
        section2_start = request.form.get('section2_start')
        section2_end = request.form.get('section2_end')
        
        if not all([section1_start, section1_end, section2_start, section2_end]):
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Missing time ranges'}), 400
        
        # Convert time strings to seconds
        section1_start_sec = time_to_seconds(section1_start)
        section1_end_sec = time_to_seconds(section1_end)
        section2_start_sec = time_to_seconds(section2_start)
        section2_end_sec = time_to_seconds(section2_end)
        
        # Create analyzer instance
        analyzer = HeartRateAnalyzer(filepath)
        analyzer.load_data()
        
        # Generate plot with highlighted sections
        plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'analysis_plot.png')
        analyzer.plot_data(
            (section1_start_sec, section1_end_sec),
            (section2_start_sec, section2_end_sec),
            plot_filename
        )
        
        # Get analysis results
        result = analyzer.compare_sections(
            (section1_start_sec, section1_end_sec),
            (section2_start_sec, section2_end_sec)
        )
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'plot_url': '/plot',
            'results': result
        })
        
    except Exception as e:
        # Clean up files in case of error
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        if 'plot_filename' in locals() and os.path.exists(plot_filename):
            os.remove(plot_filename)
        return jsonify({'error': str(e)}), 500

@app.route('/plot')
def get_plot():
    plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'analysis_plot.png')
    if os.path.exists(plot_path):
        return send_file(plot_path, mimetype='image/png')
    return jsonify({'error': 'Plot not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 