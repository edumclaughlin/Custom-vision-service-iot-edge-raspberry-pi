#To make python 2 and python 3 compatible code
from __future__ import division
from __future__ import absolute_import

#Imports
import sys
if sys.version_info[0] < 3:#e.g python version <3
    import cv2
else:
    import cv2
    from cv2 import cv2
# pylint: disable=E1101
# pylint: disable=E0401
# Disabling linting that is not supported by Pylint for C extensions such as OpenCV. See issue https://github.com/PyCQA/pylint/issues/1955 
import numpy as np
import requests
import json
import time
import base64
from queue import Queue
import threading
from threading import Thread, Event
#from multiprocessing import Process
import time
import queue
import VideoStream
from VideoStream import VideoStream
import AnnotationParser
from AnnotationParser import AnnotationParser
import ImageServer
from ImageServer import ImageServer
import ImageProcessor
from ImageProcessor import ImageProcessor
import logging
from Helpers import Helper

# Get a logger for this module
logger = logging.getLogger(__name__)

# class will continually poll the camera and raise events for the ImageServer (after start is called)
class CameraCapture(object):

    def __IsInt(self,string):
        try: 
            int(string)
            return True
        except ValueError:
            return False

    # Initialise all instance variables here, this is important to avoid instance confusion
    def __init__(
            self,
            videoPath,
            localProcess = False, 
            imageProcessingEndpoint = "",
            imageProcessingParams = "", 
            cloudProcess = False, 
            cloudProcessingEndpoint = "",
            cloudProcessingParams = "", 
            showVideo = False, 
            verbose = False,
            loopVideo = True,
            convertToGray = False,
            captureWidth = 1920,
            captureHeight = 1080,
            resizeWidth = 0,
            resizeHeight = 0,
            cloudResizeWidth = 0,
            cloudResizeHeight = 0,
            waitTime = 3,
            annotate = False,
            sendToHubCallback = None):
        self.videoPath = videoPath
        self.isWebcam = True
        self.localProcess = localProcess
        if not self.localProcess:
            imageProcessingEndpoint = ""
        self.imageProcessingEndpoint = imageProcessingEndpoint
        if imageProcessingParams == "":
            self.imageProcessingParams = "" 
        else:
            self.imageProcessingParams = json.loads(imageProcessingParams)
        self.cloudProcess = cloudProcess
        if not self.cloudProcess:
            cloudProcessingEndpoint = ""
        self.cloudProcessingEndpoint = cloudProcessingEndpoint
        if cloudProcessingParams == "":
            self.cloudProcessingParams = "" 
        else:
            self.cloudProcessingParams = json.loads(cloudProcessingParams)
        self.showVideo = showVideo
        self.verbose = verbose
        self.loopVideo = loopVideo
        self.captureWidth = captureWidth
        self.captureHeight = captureHeight
        self.convertToGray = convertToGray
        self.resizeWidth = resizeWidth
        self.resizeHeight = resizeHeight
        self.cloudResizeWidth = cloudResizeWidth
        self.cloudResizeHeight = cloudResizeHeight
        self.annotate = (self.imageProcessingEndpoint != "") and self.showVideo & annotate
        self.nbOfPreprocessingSteps = 0
        self.autoRotate = True
        self.sendToHubCallback = sendToHubCallback
        self.vs = None
        self.waitTime = waitTime # Processing delay between frames in seconds

        if self.convertToGray:
            self.nbOfPreprocessingSteps +=1
        if self.resizeWidth != 0 or self.resizeHeight != 0:
            self.nbOfPreprocessingSteps +=1

        # Instance variable used to hold the current web-cam frame and accessed by the ImageServer     
        self.displayFrame = None
        # Instance variable used to hold the current processed frame and accessed by the ImageServer     
        self.processedFrame = None

        # Create an ImageServer (When configured) web-socket server on port 5012 and send it a start message
        if self.showVideo:
            self.imageServer = ImageServer(5012, self)
            self.imageServer.start()
        
        self.display_originalFrame = None
        self.display_processedFrame = None

        self.processor = ImageProcessor(self)
        self.prompt = ""

        self.localDetections = "No Local Detections"
        self.remoteDetections = "No Remote Detections"
        self.productsDetected = ""
        self.promptResponse = ""
        self.personDetected = False

        self.sendLocalDetectionsToHub = False
        self.sendRemoteDetectionsToHub = False

        if self.verbose:
            logger.info("Initialising the camera capture with the following parameters: ")
            logger.info("   - Video path: %s", self.videoPath)
            logger.info("   - Process Locally: %s", str(self.localProcess))
            logger.info("   - Image processing endpoint: %s", self.imageProcessingEndpoint)
            logger.info("   - Image processing params: %s", json.dumps(self.imageProcessingParams))
            logger.info("   - Process in Cloud: %s", str(self.cloudProcess))
            logger.info("   - Cloud processing endpoint: %s", self.cloudProcessingEndpoint)
            logger.info("   - Cloud processing params: %s", json.dumps(self.cloudProcessingParams))
            logger.info("   - Show video: %s", str(self.showVideo))
            logger.info("   - Loop video: %s", str(self.loopVideo))
            logger.info("   - Capture width: %s", str(self.captureWidth))
            logger.info("   - Capture height: %s", str(self.captureHeight))
            logger.info("   - Convert to gray: %s", str(self.convertToGray))
            logger.info("   - Resize width: %s", str(self.resizeWidth))
            logger.info("   - Resize height: %s", str(self.resizeHeight))
            logger.info("   - Cloud Resize width: %s", str(self.cloudResizeWidth))
            logger.info("   - Cloud Resize height: %s", str(self.cloudResizeHeight))
            logger.info("   - Wait time: %s", str(self.waitTime))
            logger.info("   - Annotate: %s", str(self.annotate))
            logger.info("   - Send processing results to hub: %s", str(self.sendToHubCallback is not None))

    def __enter__(self):
        #The VideoStream class always gives us the latest frame from the webcam. It uses another thread to read the frames.
        # The self.vs object uses a queue which you pop with self.vs.read()
        self.vs = VideoStream(int(self.videoPath),3,self.captureWidth, self.captureHeight).start()
        time.sleep(1.0) #needed to load at least one frame into the VideoStream class
        self.capture = cv2.VideoCapture(int(self.videoPath))
        return self

    def get_original_frame(self):
        return self.display_originalFrame

    # Getter for self.processedFrame instance variable
    def get_processed_frame(self):
        return self.display_processedFrame
    
    # Continually polls the camera and prepares frames for the ImageServer to consume
    # The execution time for each loop iteration is injected between video frames 
    # therefore, we need to run all dependent tasks on seperate threads to ensure frames can be presented quickly
    def start(self):
        frameCounter = 0
        perfForOneFrameInMs = None

        self.original_frame = self.vs.read()
        self.processed_frame = self.original_frame

        # Create an instance of the ImageProcessor class which will run in an async process
        # The process monitors queues to get work and post processed images
        # The IamgeProcessor will perform those compute intensive actions that would if
        # performed in-process result in an inability to actively monitor the video feed
        self.processor_process = Thread(target=self.processor.continuous_process)
        self.processor_process.daemon = True  # This will ensure that the process is killed when main.py exits

        try:
            self.processor_process.start()
            while True:
                startOverall = time.time()
                startCapture = time.time()

                frameCounter +=1
                self.original_frame = self.vs.read()
                startPreProcessing = time.time()
                logger.debug("Frame number: %d", frameCounter)
                logger.debug("Time to capture (+ straighten up) a frame: %s", Helper.display_time_difference_in_ms(time.time(), startCapture))

                # If the processing engine is not currently processing a frame
                # Then place the current frame into the input queue for image processing
                if self.processor.work_queue.empty():
                    logger.debug("Send image frame to process")
                    self.processor.work_queue.put(self.original_frame)

                if not self.processor.output_queue.empty():
                    try:
                        self.processed_frame = self.processor.output_queue.get(block=False)
                        logger.debug(f"Output queue now has %d elements.", self.processor.output_queue.qsize())
                        # Send any updated states to connected web clients
                        msg = {
                            "local_detections": self.localDetections,
                            "remote_detections": self.remoteDetections,
                            "prompt_response": self.promptResponse
                        }
                        json_string = json.dumps(msg, indent=4)  # `indent` is optional
                        self.imageServer.send_to_clients(json_string)
                    except queue.Empty:
                        pass

                # Get a processed image from the result queue if available
                try:
                    self.processed_frame, _ = self.processor.get_result()
                except:
                    pass

                #Display frames
                if self.showVideo:
                    startDisplaying = time.time()
                    # Prepare a jpg of the current frame for display on the web-server
                    try:
                        # Setting this variable will make it available to the ImageServer web-server
                        self.display_originalFrame = cv2.imencode('.jpg', self.original_frame)[1].tobytes()
                    except Exception as e:
                        pass
                    # Prepare a jpg of the processed frame for display on the web-server
                    try:
                        # Setting this variable will make it available to the ImageServer web-server
                        self.display_processedFrame = cv2.imencode('.jpg', self.processed_frame)[1].tobytes()
                    except Exception as e:
                        pass

            # TODO: Add code to stop/start image processing 
            processor.stop()  # Signal the image processing service to exit
        except Exception as e:
            logger.exception('EXCEPTION')
        finally:
            self.processor_process.join()  # Wait until the image processing service has finished
    
    def __exit__(self, exception_type, exception_value, traceback):
        if not self.isWebcam:
            self.capture.release()
        self.processor.stop()
        if self.showVideo:
            self.imageServer.close()
            cv2.destroyAllWindows()
