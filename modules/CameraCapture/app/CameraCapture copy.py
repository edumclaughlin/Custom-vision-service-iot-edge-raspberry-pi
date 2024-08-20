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
import numpy
import requests
import json
import time
import base64

import VideoStream
from VideoStream import VideoStream
import AnnotationParser
from AnnotationParser import AnnotationParser
import ImageServer
from ImageServer import ImageServer

class CameraCapture(object):

    def __IsInt(self,string):
        try: 
            int(string)
            return True
        except ValueError:
            return False

    def __init__(
            self,
            videoPath,
            imageProcessingEndpoint = "",
            imageProcessingParams = "", 
            cloudProcessingEndpoint = "",
            cloudProcessingParams = "", 
            showVideo = False, 
            verbose = False,
            loopVideo = True,
            convertToGray = False,
            resizeWidth = 0,
            resizeHeight = 0,
            cloudResizeWidth = 0,
            cloudResizeHeight = 0,
            annotate = False,
            sendToHubCallback = None):
        self.videoPath = videoPath
        if self.__IsInt(videoPath):
            #case of a usb camera (usually mounted at /dev/video* where * is an int)
            self.isWebcam = True
        else:
            #case of a video file
            self.isWebcam = False
        self.imageProcessingEndpoint = imageProcessingEndpoint
        if imageProcessingParams == "":
            self.imageProcessingParams = "" 
        else:
            self.imageProcessingParams = json.loads(imageProcessingParams)
        self.cloudProcessingEndpoint = cloudProcessingEndpoint
        if cloudProcessingParams == "":
            self.cloudProcessingParams = "" 
        else:
            self.cloudProcessingParams = json.loads(cloudProcessingParams)
        self.showVideo = showVideo
        self.verbose = verbose
        self.loopVideo = loopVideo
        self.convertToGray = convertToGray
        self.resizeWidth = resizeWidth
        self.resizeHeight = resizeHeight
        self.cloudResizeWidth = cloudResizeWidth
        self.cloudResizeHeight = cloudResizeHeight
        self.annotate = (self.imageProcessingEndpoint != "") and self.showVideo & annotate
        self.nbOfPreprocessingSteps = 0
        self.autoRotate = False
        self.sendToHubCallback = sendToHubCallback
        self.vs = None

        if self.convertToGray:
            self.nbOfPreprocessingSteps +=1
        if self.resizeWidth != 0 or self.resizeHeight != 0:
            self.nbOfPreprocessingSteps +=1
        if self.verbose:
            print("Initialising the camera capture with the following parameters: ")
            print("   - Video path: " + self.videoPath)
            print("   - Image processing endpoint: " + self.imageProcessingEndpoint)
            print("   - Image processing params: " + json.dumps(self.imageProcessingParams))
            print("   - Cloud processing endpoint: " + self.cloudProcessingEndpoint)
            print("   - Cloud processing params: " + json.dumps(self.cloudProcessingParams))
            print("   - Show video: " + str(self.showVideo))
            print("   - Loop video: " + str(self.loopVideo))
            print("   - Convert to gray: " + str(self.convertToGray))
            print("   - Resize width: " + str(self.resizeWidth))
            print("   - Resize height: " + str(self.resizeHeight))
            print("   - Cloud Resize width: " + str(self.cloudResizeWidth))
            print("   - Cloud Resize height: " + str(self.cloudResizeHeight))
            print("   - Annotate: " + str(self.annotate))
            print("   - Send processing results to hub: " + str(self.sendToHubCallback is not None))
            print()
        
        self.displayFrame = None
        if self.showVideo:
            self.imageServer = ImageServer(5012, self)
            self.imageServer.start()

    def __annotate(self, frame, response):
        AnnotationParserInstance = AnnotationParser()
        #TODO: Make the choice of the service configurable
        listOfRectanglesToDisplay = AnnotationParserInstance.getCV2RectanglesFromProcessingService1(response)
        for rectangle in listOfRectanglesToDisplay:
            cv2.rectangle(frame, (rectangle(0), rectangle(1)), (rectangle(2), rectangle(3)), (0,0,255),4)
        return

    def __sendFrameForProcessing(self, frame):
        headers = {'Content-Type': 'application/octet-stream'}
        try:
            response = requests.post(self.imageProcessingEndpoint, headers = headers, params = self.imageProcessingParams, data = frame)
        except Exception as e:
            print('__sendFrameForProcessing Excepetion -' + str(e))
            return "[]"

        if self.verbose:
            try:
                print("Response from external processing service: (" + str(response.status_code) + ") " + json.dumps(response.json()))
            except Exception:
                print("Response from external processing service (status code): " + str(response.status_code))
        return json.dumps(response.json())

    def __sendFrameForProcessingInCloud(self, frame):
        headers = {'Content-Type': 'application/octet-stream'}
        try:
            response = requests.post(self.cloudProcessingEndpoint, headers = headers, params = self.cloudProcessingParams, data = frame)
            #response = requests.post(self.imageProcessingEndpoint, headers = headers, params = self.imageProcessingParams, data = frame)
        except Exception as e:
            print('__sendFrameForProcessing in cloud Excepetion -' + str(e))
            return "[]"

        if self.verbose:
            try:
                print("Response from cloud processing service: (" + str(response.status_code) + ") " + json.dumps(response.json()))
            except Exception:
                print("Response from cloud processing service (status code): " + str(response.status_code))
        return response

    def __displayTimeDifferenceInMs(self, endTime, startTime):
        return str(int((endTime-startTime) * 1000)) + " ms"

    def __enter__(self):
        if self.isWebcam:
            #The VideoStream class always gives us the latest frame from the webcam. It uses another thread to read the frames.
            self.vs = VideoStream(int(self.videoPath)).start()
            time.sleep(1.0)#needed to load at least one frame into the VideoStream class
            #self.capture = cv2.VideoCapture(int(self.videoPath))
        else:
            #In the case of a video file, we want to analyze all the frames of the video thus are not using VideoStream class
            self.capture = cv2.VideoCapture(self.videoPath)
        return self

    def get_display_frame(self):
        return self.displayFrame

    def start(self):
        frameCounter = 0
        perfForOneFrameInMs = None
        while True:
            if self.showVideo or self.verbose:
                startOverall = time.time()
            if self.verbose:
                startCapture = time.time()

            frameCounter +=1
            if self.isWebcam:
                frame = self.vs.read()
            else:
                frame = self.capture.read()[1]
                if frameCounter == 1:
                    if self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) < self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT):
                        self.autoRotate = True
                if self.autoRotate:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE) #The counterclockwise is random...It coudl well be clockwise. Is there a way to auto detect it?
            if self.verbose:
                if frameCounter == 1:
                    if not self.isWebcam:
                        print("Original frame size: " + str(int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))) + "x" + str(int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
                        print("Frame rate (FPS): " + str(int(self.capture.get(cv2.CAP_PROP_FPS))))
                print("Frame number: " + str(frameCounter))
                print("Time to capture (+ straighten up) a frame: " + self.__displayTimeDifferenceInMs(time.time(), startCapture))
                startPreProcessing = time.time()
            
            #Loop video
            if not self.isWebcam:             
                if frameCounter == self.capture.get(cv2.CAP_PROP_FRAME_COUNT):
                    if self.loopVideo: 
                        frameCounter = 0
                        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        break

            #Pre-process locally
            if self.nbOfPreprocessingSteps == 1 and self.convertToGray:
                preprocessedFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.nbOfPreprocessingSteps == 1 and (self.resizeWidth != 0 or self.resizeHeight != 0):
                preprocessedFrame = cv2.resize(frame, (self.resizeWidth, self.resizeHeight))

            if self.nbOfPreprocessingSteps > 1:
                preprocessedFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                preprocessedFrame = cv2.resize(preprocessedFrame, (self.resizeWidth,self.resizeHeight))
            
            if self.verbose:
                print("Time to pre-process a frame: " + self.__displayTimeDifferenceInMs(time.time(), startPreProcessing))

            #Process externally
            if self.imageProcessingEndpoint != "":
                startEncodingForProcessing = time.time()

                #Encode frame to send over HTTP
                if self.nbOfPreprocessingSteps == 0:
                    encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()
                else:
                    encodedFrame = cv2.imencode(".jpg", preprocessedFrame)[1].tostring()

                if self.verbose:
                    print("Time to encode a frame for processing: " + self.__displayTimeDifferenceInMs(time.time(), startEncodingForProcessing))

                #Send over HTTP for processing
                startProcessingExternally = time.time()
                response = self.__sendFrameForProcessing(encodedFrame)
                if self.verbose:
                    print("Time to process frame externally: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingExternally))

                #forwarding outcome of external processing to the EdgeHub
                if response != "[]" and self.sendToHubCallback is not None:
                    startSendingToEdgeHub = time.time()
                    self.sendToHubCallback(response)
                    if self.verbose:
                        print("Time to message from processing service to edgeHub: " + self.__displayTimeDifferenceInMs(time.time(), startSendingToEdgeHub))

            #Process in cloud
            # TODO: Only process in cloud based on outcome of local analysis
            if self.cloudProcessingEndpoint != "":
                print("Send image to LLM omni model in cloud for processing ")
                #Send over HTTP for processing in cloud
                startProcessingInCloud = time.time()
                cloudFrame = cv2.imencode(".jpg", frame)[1].tostring()
                response = self.__sendFrameForProcessingInCloud(cloudFrame)
                if self.verbose:
                    print("Time to process frame in cloud: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingInCloud))

            #Display frames
            if self.showVideo:
                startDisplaying = time.time()
                try:
                    if self.nbOfPreprocessingSteps == 0:
                        if self.verbose and (perfForOneFrameInMs is not None):
                            cv2.putText(frame, "FPS " + str(round(1000/perfForOneFrameInMs, 2)),(10, 35),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)
                        if self.annotate:
                            #TODO: fix bug with annotate function
                            self.__annotate(frame, response)
                        self.displayFrame = cv2.imencode('.jpg', frame)[1].tobytes()
                    else:
                        if self.verbose and (perfForOneFrameInMs is not None):
                            cv2.putText(preprocessedFrame, "FPS " + str(round(1000/perfForOneFrameInMs, 2)),(10, 35),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)
                        if self.annotate:
                            #TODO: fix bug with annotate function
                            self.__annotate(preprocessedFrame, response)
                        self.displayFrame = cv2.imencode('.jpg', preprocessedFrame)[1].tobytes()
                except Exception as e:
                    print("Could not display the video to a web browser.") 
                    print('Excpetion -' + str(e))
                if self.verbose:
                    print("Time to display frame: " + self.__displayTimeDifferenceInMs(time.time(), startDisplaying))
                perfForOneFrameInMs = int((time.time()-startOverall) * 1000)
                if not self.isWebcam:
                    waitTimeBetweenFrames = max(int(1000 / self.capture.get(cv2.CAP_PROP_FPS))-perfForOneFrameInMs, 1)
                    print("Wait time between frames :" + str(waitTimeBetweenFrames))
                    if cv2.waitKey(waitTimeBetweenFrames) & 0xFF == ord('q'):
                        break

            if self.verbose:
                perfForOneFrameInMs = int((time.time()-startOverall) * 1000)
                print("Total time for one frame: " + self.__displayTimeDifferenceInMs(time.time(), startOverall))

    def __exit__(self, exception_type, exception_value, traceback):
        if not self.isWebcam:
            self.capture.release()
        if self.showVideo:
            self.imageServer.close()
            cv2.destroyAllWindows()