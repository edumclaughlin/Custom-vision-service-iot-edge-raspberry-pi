# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
import random
import sys
import time
from dotenv import load_dotenv
import logging
from logging_config import setup_logging
from Helpers import Helper

#import iothub_client
# pylint: disable=E0611
# Disabling linting that is not supported by Pylint for C extensions such as iothub_client. See issue https://github.com/PyCQA/pylint/issues/1955
#from iothub_client import (IoTHubModuleClient, IoTHubClientError, IoTHubError,
#                           IoTHubMessage, IoTHubMessageDispositionResult,
#                           IoTHubTransportProvider)

# Ensure logging is configured
# This line initializes logging configuration
setup_logging()
logger = logging.getLogger(__name__)

from azure.iot.device import IoTHubModuleClient, Message

import CameraCapture
from CameraCapture import CameraCapture


# global counters
SEND_CALLBACKS = 0


def send_to_Hub_callback(strMessage):
    message = Message(bytearray(strMessage, 'utf8'))
    hubManager.send_message_to_output(message, "output1")

# Callback received when the message that we're forwarding is processed.

class HubManager(object):

    def __init__(
            self,
            messageTimeout,
            verbose):
        '''
        Communicate with the Edge Hub

        :param int messageTimeout: the maximum time in milliseconds until a message times out. The timeout period starts at IoTHubClient.send_event_async. By default, messages do not expire.
        :param IoTHubTransportProvider protocol: Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
        :param bool verbose: set to true to get detailed logs on messages
        '''
        self.messageTimeout = messageTimeout
        self.client = IoTHubModuleClient.create_from_edge_environment()
        #self.client.set_option("messageTimeout", self.messageTimeout)
        #self.client.set_option("product_info", "edge-camera-capture")
        #if verbose:
        #    self.client.set_option("logtrace", 1)  # enables MQTT logging

    def send_message_to_output(self, event, outputQueueName):
        self.client.send_message_to_output(event, outputQueueName)
        global SEND_CALLBACKS
        SEND_CALLBACKS += 1

def main(
        videoPath,
        localProcess=False,
        imageProcessingEndpoint="",
        imageProcessingParams="",
        cloudProcess=False,
        cloudProcessingEndpoint="",
        cloudProcessingParams="",
        showVideo=True,
        verbose=False,
        loopVideo=True,
        convertToGray=False,
        captureWidth=0,
        captureHeight=0,
        resizeWidth=0,
        resizeHeight=0,
        cloudResizeWidth=0,
        cloudResizeHeight=0,
        waitTime=3,
        annotate=False
):
    '''
    Capture a camera feed, send it to processing and forward outputs to EdgeHub

    :param int videoPath: camera device path such as /dev/video0 or a test video file such as /TestAssets/myvideo.avi. Mandatory.
    :param bool localProcess: Call the local image processing service.
    :param str imageProcessingEndpoint: service endpoint to send the frames to for processing. Example: "http://face-detect-service:8080". Leave empty when no external processing is needed (Default). Optional.
    :param str imageProcessingParams: query parameters to send to the processing service. Example: "'returnLabels': 'true'". Empty by default. Optional.
    :param bool cloudProcess: Call the cloud image processing service.
    :param str cloudProcessingEndpoint: service endpoint to send the frames to for processing in cloud. Example: "http://face-detect-service:8080". Leave empty when no external processing is needed (Default). Optional.
    :param str cloudProcessingParams: query parameters to send to the processing in cloud. Example: "'returnLabels': 'true'". Empty by default. Optional.
    :param bool showVideo: show the video in a windows. False by default. Optional.
    :param bool verbose: show detailed logs and perf timers. False by default. Optional.
    :param bool loopVideo: when reading from a video file, it will loop this video. True by default. Optional.
    :param bool convertToGray: convert to gray before sending to external service for processing. False by default. Optional.
    :param int captureWidth: Resolution used to capture video frame. 1920 by default. Optional.
    :param int captureHeight: Resolution used to capture video frame. 1080 by default. Optional.
    :param int resizeWidth: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.
    :param int resizeHeight: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.
    :param int cloudResizeWidth: resize frame width before sending to cloud service for processing. Does not resize by default (0). Optional.
    :param int cloudResizeHeight: resize frame width before sending to cloud service for processing. Does not resize by default (0). Optional.
    :param int waitTime: wait time in seconds between processing frames - Used to manage cloud API costs. Optional.
    :param bool annotate: when showing the video in a window, it will annotate the frames with rectangles given by the image processing service. False by default. Optional. Rectangles should be passed in a json blob with a key containing the string rectangle, and a top left corner + bottom right corner or top left corner with width and height.
    '''
    try:
        logger.debug("Python %s", sys.version)
        logger.info("Camera Capture Azure IoT Edge Module. Press Ctrl-C to exit.")
        try:
            global hubManager
            hubManager = HubManager(
                10000, verbose)
        except Exception as iothub_error:
            print("Unexpected error %s from IoTHub" % iothub_error)
            return
        with CameraCapture(videoPath, localProcess, imageProcessingEndpoint, imageProcessingParams, 
                           cloudProcess, cloudProcessingEndpoint, cloudProcessingParams,
                           showVideo, verbose, loopVideo, convertToGray, 
                           captureWidth, captureHeight, resizeWidth, resizeHeight, cloudResizeWidth, cloudResizeHeight,
                           waitTime, annotate, send_to_Hub_callback) as cameraCapture:
            cameraCapture.start()
    except KeyboardInterrupt:
        logger.info("Camera capture module stopped")

if __name__ == '__main__':
    load_dotenv()

    try:
        VIDEO_PATH = os.environ['VIDEO_PATH']
        LOCAL_PROCESS = Helper.convert_string_to_bool(os.getenv('LOCAL_PROCESS', 'False'))
        IMAGE_PROCESSING_ENDPOINT = os.getenv('IMAGE_PROCESSING_ENDPOINT', "")
        IMAGE_PROCESSING_PARAMS = os.getenv('IMAGE_PROCESSING_PARAMS', "")
        CLOUD_PROCESS = Helper.convert_string_to_bool(os.getenv('CLOUD_PROCESS', 'False'))
        CLOUD_PROCESSING_ENDPOINT = os.getenv('CLOUD_PROCESSING_ENDPOINT', "")
        CLOUD_PROCESSING_PARAMS = os.getenv('CLOUD_PROCESSING_PARAMS', "")
        SHOW_VIDEO = Helper.convert_string_to_bool(os.getenv('SHOW_VIDEO', 'False'))
        VERBOSE = Helper.convert_string_to_bool(os.getenv('VERBOSE', 'False'))
        LOOP_VIDEO = Helper.convert_string_to_bool(os.getenv('LOOP_VIDEO', 'True'))
        CONVERT_TO_GRAY = Helper.convert_string_to_bool(os.getenv('CONVERT_TO_GRAY', 'False'))
        CAPTURE_WIDTH = int(os.getenv('CAPTURE_WIDTH', 0))
        CAPTURE_HEIGHT = int(os.getenv('CAPTURE_HEIGHT', 0))
        RESIZE_WIDTH = int(os.getenv('RESIZE_WIDTH', 0))
        RESIZE_HEIGHT = int(os.getenv('RESIZE_HEIGHT', 0))
        CLOUD_RESIZE_WIDTH = int(os.getenv('CLOUD_RESIZE_WIDTH', 0))
        CLOUD_RESIZE_HEIGHT = int(os.getenv('CLOUD_RESIZE_HEIGHT', 0))
        WAIT_TIME = int(os.getenv('WAIT_TIME', 0))
        ANNOTATE = Helper.convert_string_to_bool(os.getenv('ANNOTATE', 'False'))

    except ValueError as error:
        print(error)
        sys.exit(1)

    main(VIDEO_PATH, LOCAL_PROCESS, IMAGE_PROCESSING_ENDPOINT, IMAGE_PROCESSING_PARAMS, CLOUD_PROCESS, CLOUD_PROCESSING_ENDPOINT, CLOUD_PROCESSING_PARAMS, SHOW_VIDEO,
         VERBOSE, LOOP_VIDEO, CONVERT_TO_GRAY, CAPTURE_WIDTH, CAPTURE_HEIGHT, RESIZE_WIDTH, RESIZE_HEIGHT, CLOUD_RESIZE_WIDTH, CLOUD_RESIZE_HEIGHT, WAIT_TIME, ANNOTATE)
