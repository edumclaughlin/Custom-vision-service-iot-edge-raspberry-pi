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

        if self.convertToGray:
            self.nbOfPreprocessingSteps +=1
        if self.resizeWidth != 0 or self.resizeHeight != 0:
            self.nbOfPreprocessingSteps +=1
        if self.verbose:
            print("Initialising the camera capture with the following parameters: ")
            print("   - Video path: " + self.videoPath)
            print("   - Process Locally: " + str(self.localProcess))
            print("   - Image processing endpoint: " + self.imageProcessingEndpoint)
            print("   - Image processing params: " + json.dumps(self.imageProcessingParams))
            print("   - Process in Cloud: " + str(self.cloudProcess))
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
            print('__sendFrameForProcessing Exception -' + str(e))
            return None

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
        except Exception as e:
            print('__sendFrameForProcessing in cloud Excepetion -' + str(e))
            return None

        if self.verbose:
            try:
                print("Response from cloud processing service: (" + str(response.status_code) + ") " + json.dumps(response.json()))
            except Exception:
                print("Response from cloud processing service (status code): " + str(response.status_code))
        return response

    def __displayTimeDifferenceInMs(self, endTime, startTime):
        return str(int((endTime-startTime) * 1000)) + " ms"

    def __enter__(self):
        #The VideoStream class always gives us the latest frame from the webcam. It uses another thread to read the frames.
        self.vs = VideoStream(int(self.videoPath)).start()
        time.sleep(1.0)#needed to load at least one frame into the VideoStream class
        #self.capture = cv2.VideoCapture(int(self.videoPath))
        return self

    def get_display_frame(self):
        return self.displayFrame

    def start(self):
        frameCounter = 0
        perfForOneFrameInMs = None
        while True:
            startOverall = time.time()
            startCapture = time.time()

            frameCounter +=1
            originalframe = self.vs.read()
            frame = originalframe
            startPreProcessing = time.time()
            if self.verbose:
                print("Frame number: " + str(frameCounter))
                print("Time to capture (+ straighten up) a frame: " + self.__displayTimeDifferenceInMs(time.time(), startCapture))
            
            #Pre-process locally
            if self.convertToGray:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if (self.resizeWidth != 0 or self.resizeHeight != 0):
                frame = cv2.resize(frame, (self.resizeWidth, self.resizeHeight))

            if self.verbose:
                print("Time to pre-process a frame: " + self.__displayTimeDifferenceInMs(time.time(), startPreProcessing))

            #Process using local vision model
            if self.imageProcessingEndpoint != "":
                startEncodingForProcessing = time.time()

                #Encode frame to send over HTTP
                encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()

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
                print("Send image cloud model for processing ")
                startProcessingInCloud = time.time()
                cloudFrame = cv2.imencode(".jpg", frame)[1].tostring()
                response = self.__sendFrameForProcessingInCloud(cloudFrame)
                if self.verbose:
                    print("Time to process frame in cloud: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingInCloud))

            # Process response from cloud analysis
            if response and isinstance(response, requests.Response) and response.status_code == 200:
                try:
                    json_response = response.json()
                    print(json.dumps(json_response, indent=4))  # Pretty-print the JSON
                    cloud_model = json_response['model']
                    cloud_productcount = json_response['product count']
                    cloud_promptresponse = json_response['prompt response']
                    cloud_jsonresponse = json_response['json response']
                    print(f"Found {cloud_productcount} products")

                    # Annotate the frame with the analysis result
                    if (cloud_model == 'Azure Product Recognition'):
                        #base64image = cloud_jsonresponse['base64image']
                        #frame = base64.b64decode(base64image)
                        #decoded_bytes = base64.b64decode(base64image)
                        #frame = cv2.imdecode(np.frombuffer(decoded_bytes, dtype=np.uint8), 1)
                        num_products_found = 0
                        threshold = 0.3
                        for product in cloud_jsonresponse['products']:
                            if product['tags'][0]['confidence'] > threshold:
                                l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                                #img = cv2.rectangle(img, (l, t), (l + w, t + h), (0, 255, 0), 5)
                                cv2.rectangle(frame, (l, t), (l + w, t + h), (0, 255, 0), 5)
                                # For better visualization, only show the first 15 characters of the label
                                #img = cv2.putText(img, product['tags'][0]['name'][0:15], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                                cv2.putText(frame, product['tags'][0]['name'][0:15], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                                num_products_found += 1

                        # Loop over the gaps and draw rectangles for each one
                        for product in cloud_jsonresponse['gaps']:
                            if product['tags'][0]['confidence'] > threshold:
                                l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                                #img = cv2.rectangle(img, (l, t), (l + w, t + h), (255, 0, 0), 5)
                                cv2.rectangle(frame, (l, t), (l + w, t + h), (255, 0, 0), 5)
                                #img = cv2.putText(img, 'gap', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)
                                cv2.putText(frame, 'gap', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)


                except json.JSONDecodeError:
                    print("Failed to parse JSON")
            else:
                # Handle the case where response is None or not a requests.Response instance
                if response == None:
                    print("Invalid response received")
                elif isinstance(response, requests.Response):
                    print(f"Server returned status code {response.status_code}")

            #Display frames
            if self.showVideo:
                startDisplaying = time.time()
                try:
                    #if self.verbose and (perfForOneFrameInMs is not None):
                    #    cv2.putText(frame, "FPS " + str(round(1000/perfForOneFrameInMs, 2)),(10, 35),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)
                    if self.annotate:
                        #TODO: fix bug with annotate function
                        self.__annotate(frame, response)
                    self.displayFrame = cv2.imencode('.jpg', frame)[1].tobytes()
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