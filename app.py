from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify, Response, abort
import pandas as pd
import os
import json
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CLEANED_FOLDER'] = 'cleaned'

# Ensure upload and cleaned folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CLEANED_FOLDER'], exist_ok=True)

# Initialize file history
file_history = []

@app.route('/')
def index():
    return render_template('index.html', file_history=file_history)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        original_filename = secure_filename(file.filename)
        cleaned_filename = f"cleaned_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        cleaned_file_path = os.path.join(app.config['CLEANED_FOLDER'], cleaned_filename)
        
        # Save the original file
        file.save(file_path)
        
        try:
            # Read the file into a pandas DataFrame
            df = pd.read_csv(file_path)  # Adjust based on file type
            
            # Get column data from the form
            columns_data = json.loads(request.form.get('columns', '[]'))
            
            # Process new columns
            for column in columns_data:
                name = column['name']
                value_type = column['type']
                value = column['value']
                
                if value_type == 'empty':
                    df[name] = ''
                elif value_type == 'constant':
                    df[name] = value
                elif value_type == 'index':
                    df[name] = range(len(df))
            
            # Save the cleaned file
            df.to_csv(cleaned_file_path, index=False)
            
            # Add to file history
            file_history.append(original_filename)
            
            return jsonify({
                'success': True,
                'filename': original_filename,
                'message': 'File processed successfully'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500
            
        finally:
            # Clean up the original file
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/download_file')
def download_file():
    filename = request.args.get('filename')
    if not filename:
        abort(400, description="No filename provided")
    
    # Define the path where cleaned files are stored
    # Adjust this path according to your application's structure
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename
            )
        else:
            abort(404, description="File not found")
    except Exception as e:
        abort(500, description=str(e))

@app.route('/delete_history', methods=['POST'])
def delete_history():
    data = request.get_json()
    filename = data.get('filename')
    
    # Remove the file from your history storage
    # This implementation will depend on how you're storing the history
    try:
        # Implement your deletion logic here
        # Example: file_history.remove(filename)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def generate_progress():
    """Generator function to simulate progress updates"""
    steps = ['Reading file', 'Processing data', 'Cleaning', 'Saving results']
    for i, step in enumerate(steps):
        progress = (i + 1) * 25
        yield f"data: {json.dumps({'progress': progress, 'step': step})}\n\n"
        time.sleep(1)  # Simulate processing time

@app.route('/progress')
def progress():
    return Response(generate_progress(), mimetype='text/event-stream')

@app.route('/get_columns', methods=['POST'])
def get_columns():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save the file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + secure_filename(file.filename))
        file.save(temp_path)
        
        try:
            # Read the file into a pandas DataFrame
            df = pd.read_csv(temp_path)  # Adjust based on file type
            
            # Get column names
            columns = df.columns.tolist()
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'columns': columns
            })
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)