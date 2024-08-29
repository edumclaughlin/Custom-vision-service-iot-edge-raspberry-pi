
import json
import os
import io
import ObjectDetector
from ObjectDetector import ObjectDetector

# Imports for the REST API
from flask import Flask, request, jsonify

# Imports for image procesing
import numpy as np
import cv2

app = Flask(__name__)

# 4MB Max image size limit
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 

object_detector = ObjectDetector('efficientdet_lite0.tflite', 1, False)

# Default route just shows simple text
@app.route('/')
def index():
    return 'Object Detection - Tensor Flow - Lite'

@app.route('/image', methods=['POST'])
def predict_image_handler(project=None, publishedName=None):
    try:
        # Check if the image data is in files (for multipart/form-data)
        if 'imageData' in request.files:
            image_file = request.files['imageData']
            image_data = image_file.read()  # Read image data as bytes

        # Check if the image data is in form (for form-urlencoded or raw)
        elif 'imageData' in request.form:
            image_data = request.form['imageData']
            image_data = image_data.encode('utf-8')  # Convert string to bytes if necessary

        else:
            # Handle raw binary data sent directly to the endpoint
            image_data = request.get_data()

        # Decode the image from the raw bytes
        npimg = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)  # Color image (BGR format)

        # Perform object detection
        results = object_detector.detect_objects(img)
        
        return jsonify(results)
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500

if __name__ == '__main__':
    # Run the server
    app.run(host='0.0.0.0', port=80)

