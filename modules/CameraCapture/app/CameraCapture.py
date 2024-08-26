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

# class will continually poll the camera and raise events for the ImageServer (after start is called)
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

        # Instance variable used to hold the current web-cam frame and accessed by the ImageServer     
        self.displayFrame = None
        # Instance variable used to hold the current processed frame and accessed by the ImageServer     
        self.processedFrame = None

        # Create an ImageServer (When configured) web-socket server on port 5012 and send it a start message
        if self.showVideo:
            self.imageServer = ImageServer(5012, self)
            self.imageServer.start()
        
        # Getter for self.displayFrame instance variable
        self.display_originalFrame = None
        self.display_processedFrame = None

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
        # The self.vs object uses a queue which you pop with self.vs.read()
        self.vs = VideoStream(int(self.videoPath)).start()
        time.sleep(1.0) #needed to load at least one frame into the VideoStream class
        self.capture = cv2.VideoCapture(int(self.videoPath))
        return self

    def get_original_frame(self):
        return self.display_originalFrame

    # Getter for self.processedFrame instance variable
    def get_processed_frame(self):
        return self.display_processedFrame
    
    # Continually polls the camera and prepares frames for the ImageServer to consume
    # TODO: The execution time for each loop iteration is injected between video frames 
    # therefore, we need to run all dependent tasks on seperate threads to ensure frames can be presented quickly
    def start(self):
        frameCounter = 0
        perfForOneFrameInMs = None

        self.original_frame = self.vs.read()
        self.processed_frame = self.original_frame

        # Create an instance of the ImageProcessor class which will run in an async process
        # The process monitors queues to get work an post processed images
        # The IamgeProcessor will perform those compute intensive actions that would if
        # performed in-process result in an inability to actively monitor the video feed
        self.processor = ImageProcessor()
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
                # if self.verbose:
                #     print("Frame number: " + str(frameCounter))
                #     print("Time to capture (+ straighten up) a frame: " + self.__displayTimeDifferenceInMs(time.time(), startCapture))

                # If the processing engine is not currently processing a frame
                # Then place the current frame into the input queue for image processing
                # print(f"Queue has {processor.image_queue.qsize()} elements.")
                if self.processor.work_queue.empty():
                    # print("Send image frame to process")
                    self.processor.work_queue.put(self.original_frame)
                    # print(f"Queue now has {processor.work_queue.qsize()} elements.")

                print(f"Client output Queue has {self.processor.output_queue.qsize()} elements.")
                if not self.processor.output_queue.empty():
                    try:
                        self.processed_frame = self.processor.output_queue.get(block=False)
                        print(f"Queue now has {self.processor.output_queue.qsize()} elements.")
                        self.imageServer.send_to_clients("Processed Frame Ready")
                    except queue.Empty:
                    #except Exception:
                        pass

                # Get a processed image from the result queue if available
                try:
                    self.processed_frame, _ = self.processor.get_result()
                except:
                    pass

                # #Pre-process locally
                # if self.convertToGray:
                #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # if (self.resizeWidth != 0 or self.resizeHeight != 0):
                #     frame = cv2.resize(frame, (self.resizeWidth, self.resizeHeight))

                # if self.verbose:
                #     print("Time to pre-process a frame: " + self.__displayTimeDifferenceInMs(time.time(), startPreProcessing))

                # #Process using local vision model
                # if self.imageProcessingEndpoint != "":
                #     startEncodingForProcessing = time.time()

                #     #Encode frame to send over HTTP
                #     encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()

                #     if self.verbose:
                #         print("Time to encode a frame for processing: " + self.__displayTimeDifferenceInMs(time.time(), startEncodingForProcessing))

                #     #Send over HTTP for processing
                #     startProcessingExternally = time.time()
                #     response = self.__sendFrameForProcessing(encodedFrame)
                #     if self.verbose:
                #         print("Time to process frame externally: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingExternally))

                #     #forwarding outcome of external processing to the EdgeHub
                #     if response != "[]" and self.sendToHubCallback is not None:
                #         startSendingToEdgeHub = time.time()
                #         self.sendToHubCallback(response)
                #         if self.verbose:
                #             print("Time to message from processing service to edgeHub: " + self.__displayTimeDifferenceInMs(time.time(), startSendingToEdgeHub))

                # #Process in cloud
                # # TODO: Only process in cloud based on outcome of local analysis
                # if self.cloudProcessingEndpoint != "":
                #     print("Send image cloud model for processing ")
                #     startProcessingInCloud = time.time()
                #     cloudFrame = cv2.imencode(".jpg", frame)[1].tostring()
                #     response = self.__sendFrameForProcessingInCloud(cloudFrame)
                #     if self.verbose:
                #         print("Time to process frame in cloud: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingInCloud))

                # # Process response from cloud analysis
                # if response and isinstance(response, requests.Response) and response.status_code == 200:
                #     try:
                #         json_response = response.json()
                #         print(json.dumps(json_response, indent=4))  # Pretty-print the JSON
                #         cloud_model = json_response['model']
                #         cloud_productcount = json_response['product count']
                #         cloud_promptresponse = json_response['prompt response']
                #         cloud_jsonresponse = json_response['json response']
                #         print(f"Found {cloud_productcount} products")

                #         # Annotate the frame with the analysis result
                #         if (cloud_model == 'Azure Product Recognition'):
                #             #base64image = cloud_jsonresponse['base64image']
                #             #frame = base64.b64decode(base64image)
                #             #decoded_bytes = base64.b64decode(base64image)
                #             #frame = cv2.imdecode(np.frombuffer(decoded_bytes, dtype=np.uint8), 1)
                #             num_products_found = 0
                #             threshold = 0.3
                #             for product in cloud_jsonresponse['products']:
                #                 if product['tags'][0]['confidence'] > threshold:
                #                     l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                #                     #img = cv2.rectangle(img, (l, t), (l + w, t + h), (0, 255, 0), 5)
                #                     cv2.rectangle(frame, (l, t), (l + w, t + h), (0, 255, 0), 5)
                #                     # For better visualization, only show the first 15 characters of the label
                #                     #img = cv2.putText(img, product['tags'][0]['name'][0:15], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                #                     cv2.putText(frame, product['tags'][0]['name'][0:15], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                #                     num_products_found += 1

                #             # Loop over the gaps and draw rectangles for each one
                #             for product in cloud_jsonresponse['gaps']:
                #                 if product['tags'][0]['confidence'] > threshold:
                #                     l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                #                     #img = cv2.rectangle(img, (l, t), (l + w, t + h), (255, 0, 0), 5)
                #                     cv2.rectangle(frame, (l, t), (l + w, t + h), (255, 0, 0), 5)
                #                     #img = cv2.putText(img, 'gap', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)
                #                     cv2.putText(frame, 'gap', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)


                #     except json.JSONDecodeError:
                #         print("Failed to parse JSON")
                # else:
                #     # Handle the case where response is None or not a requests.Response instance
                #     if response == None:
                #         print("Invalid response received")
                #     elif isinstance(response, requests.Response):
                #         print(f"Server returned status code {response.status_code}")

                #Display frames
                if self.showVideo:
                    startDisplaying = time.time()
                    # Prepare a jpg of the current frame for display on the web-server
                    try:
                        # Setting this variable will make it available to the ImageServer web-server
                        self.display_originalFrame = cv2.imencode('.jpg', self.original_frame)[1].tobytes()
                    except Exception as e:
                        print("Could not display the video to a web browser.") 
                        print('Exception -' + str(e))
                    # Prepare a jpg of the processed frame for display on the web-server
                    try:
                        # Setting this variable will make it available to the ImageServer web-server
                        self.display_processedFrame = cv2.imencode('.jpg', self.processed_frame)[1].tobytes()
                    except Exception as e:
                        print("Could not display processed frame to a web browser.") 
                        print('Exception -' + str(e))

                    # if self.verbose:
                    #     print("Time to display frame: " + self.__displayTimeDifferenceInMs(time.time(), startDisplaying))
                    perfForOneFrameInMs = int((time.time()-startOverall) * 1000)

                # if self.verbose:
                #     perfForOneFrameInMs = int((time.time()-startOverall) * 1000)
                #     print("Total time for one frame: " + self.__displayTimeDifferenceInMs(time.time(), startOverall))

            # TODO: Add code to stop/start image processing 
            processor.stop()  # Signal the image processing service to exit
        except Exception as e:
            print('Exception -' + str(e))
        finally:
            processor_process.join()  # Wait until the image processing service has finished
    
    def __exit__(self, exception_type, exception_value, traceback):
        if not self.isWebcam:
            self.capture.release()
        self.processor.stop()
        if self.showVideo:
            self.imageServer.close()
            cv2.destroyAllWindows()
