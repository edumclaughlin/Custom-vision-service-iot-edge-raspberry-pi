
import json
import os
import io
import ObjectDetector
from ObjectDetector import ObjectDetector

# Imports for the REST API
from flask import Flask, request, jsonify

# Imports for image procesing
from PIL import Image

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
        imageData = None
        if ('imageData' in request.files):
            imageData = request.files['imageData']
        elif ('imageData' in request.form):
            imageData = request.form['imageData']
        else:
            imageData = io.BytesIO(request.get_data())

        img = Image.open(imageData)
        results = object_detector.detect_objects(img)
        return jsonify(results)
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500

if __name__ == '__main__':
    # Run the server
    app.run(host='0.0.0.0', port=80)

