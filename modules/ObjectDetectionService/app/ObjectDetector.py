# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main script to run the object detection routine."""
import argparse
import sys
import time

import cv2
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import utils
import numpy as np

class ObjectDetector:
    """Run object detection on images acquired from a camera.

    Args:
        model: Name of the TFLite object detection model.
        camera_id: The camera id to be passed to OpenCV.
        width: The width of the frame captured from the camera.
        height: The height of the frame captured from the camera.
        num_threads: The number of CPU threads to run the model.
        enable_edgetpu: True/False whether the model is a EdgeTPU model.
    """
    def __init__(self, model: str, num_threads: int, enable_edgetpu: bool):
        # Initialize the object detection model
        self.base_options = core.BaseOptions(
            file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
        self.detection_options = processor.DetectionOptions(
            max_results=3, score_threshold=0.3)
        self.options = vision.ObjectDetectorOptions(
            base_options=self.base_options, detection_options=self.detection_options)
        self.detector = vision.ObjectDetector.create_from_options(self.options)

    def detect_objects(self, image) -> np.ndarray:
        # Visualization parameters
        row_size = 20  # pixels
        left_margin = 24  # pixels
        text_color = (0, 0, 255)  # red
        font_size = 1
        font_thickness = 1
        fps_avg_frame_count = 10

        # Flip image - Why? - Raspberry pi camera perhaps
        #image = cv2.flip(image, 1)

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Create a TensorImage object from the RGB image.
        input_tensor = vision.TensorImage.create_from_array(rgb_image)

        # Run object detection estimation using the model.
        detection_result = self.detector.detect(input_tensor)

        # Draw keypoints and edges on input image
        #image = utils.visualize(image, detection_result)

        return detection_result

