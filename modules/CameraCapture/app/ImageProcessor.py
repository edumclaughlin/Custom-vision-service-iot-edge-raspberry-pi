
import queue
from queue import Queue
import threading
from threading import Event
import cv2
import time
import requests
import json
import inspect
import logging
from Helpers import Helper

# Get a logger for this module
logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, parent):
        self.parent = parent
        self.work_queue = Queue(maxsize=2)
        self.output_queue = Queue(maxsize=2)
        self.stop_signal = Event()
        self.lock = threading.Lock()
    
    def _process_in_cloud(self, image):
        if self.parent.cloudProcessingEndpoint != "":
            model = "" # Will be set if the function returns successfully
            
            logger.debug('Send image to cloud for processing')
            start_processing_time_in_cloud = time.time()
            cloud_image = cv2.imencode(".jpg", image)[1].tostring()
            response = self._send_image_for_processing_in_cloud(cloud_image)
            logger.debug("Time to perform processing in cloud: %s" + Helper.display_time_difference_in_ms(time.time(), start_processing_time_in_cloud))

            # Process response from cloud analysis
            if response and isinstance(response, requests.Response) and response.status_code == 200:
                try:
                    json_response = response.json()
                    logger.debug("%s",json.dumps(json_response, indent=4))  # Pretty-print the JSON
                    model = json_response['model']
                    self.parent.productCount = json_response['product count']
                    self.parent.promptResponse = json_response['prompt response']
                    self.parent.remoteDetections = json_response['json response']

                except json.JSONDecodeError:
                    logger.exception("EXCEPTION")
                else:
                    # Handle the case where response is None or not a requests.Response instance
                    if response == None:
                        logger.error("Invalid response received")

            # Determine which model responded and perform any annotation of the image
            if (model == 'Azure'):
                logger.info("Annotate Azure Product Detections")
                image = self._annotate_image_azure_product_detection(image, self.parent.remoteDetections)

            #forwarding outcome of remote AI processing to the EdgeHub
            # TODO: Introduce throttling of these messages (Only send when scheduled e.g. 10 mins from last reading)
            if self.parent.sendRemoteDetectionsToHub == True and self.parent.sendToHubCallback is not None:
                logger.info("Send remote detections to hub")
                startSendingToEdgeHub = time.time()
                msg = json.dumps(json_response)
                self.parent.sendToHubCallback(msg)

            return image
        
    def _send_image_for_processing_in_cloud(self, image):
        headers = {'Content-Type': 'application/octet-stream'}
        try:
            response = requests.post(self.parent.cloudProcessingEndpoint, headers = headers, params = self.parent.cloudProcessingParams, data = image)
        except Exception as e:
            logger.exception('EXCEPTION')
            return None

        try:
            logger.debug('Response:%d:%s',response.status_code,json.dumps(response.json()))
        except Exception:
            pass

        return response
    
    def _annotate_image_azure_product_detection(self, image, json_response):
        # Response in the form
        # {'imageMetadata': {'width': 1280, 'height': 720}, 'products': [{'id': '1', 'boundingBox': {'x': 900, 'y': 0, 'w': 158, 'h': 286}, 'tags': [{'name': 'product', 'confidence': 0.7352957725524902}]}, {'id': '2', 'boundingBox': {'x': 1220, 'y': 0, 'w': 57, 'h': 273}, 'tags': [{'name': 'product', 'confidence': 0.6888278722763062}]}, {'id': '3', 'boundingBox': {'x': 650, 'y': 199, 'w': 96, 'h': 89}, 'tags': [{'name': 'product', 'confidence': 0.6873872876167297}]}, {'id': '4', 'boundingBox': {'x': 1172, 'y': 0, 'w': 56, 'h': 273}, 'tags': [{'name': 'product', 'confidence': 0.6642954349517822}]}, {'id': '5', 'boundingBox': {'x': 1098, 'y': 0, 'w': 72, 'h': 276}, 'tags': [{'name': 'product', 'confidence': 0.6248446106910706}]}, {'id': '6', 'boundingBox': {'x': 967, 'y': 382, 'w': 214, 'h': 313}, 'tags': [{'name': 'product', 'confidence': 0.5721163153648376}]}, {'id': '7', 'boundingBox': {'x': 1173, 'y': 432, 'w': 81, 'h': 247}, 'tags': [{'name': 'product', 'confidence': 0.46560630202293396}]}, {'id': '8', 'boundingBox': {'x': 1047, 'y': 4, 'w': 56, 'h': 274}, 'tags': [{'name': 'product', 'confidence': 0.45639175176620483}]}, {'id': '10', 'boundingBox': {'x': 767, 'y': 515, 'w': 172, 'h': 131}, 'tags': [{'name': 'product', 'confidence': 0.26803919672966003}]}], 'gaps': [{'id': '9', 'boundingBox': {'x': 743, 'y': 5, 'w': 161, 'h': 302}, 'tags': [{'name': 'gap', 'confidence': 0.40706244111061096}]}]}
        num_products_found = 0
        threshold = 0.3
        for product in json_response['products']:
            if product['tags'][0]['confidence'] > threshold:
                l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                if (self.parent.showRemoteDetections == True):
                    cv2.rectangle(image, (l, t), (l + w, t + h), (0, 255, 0), 2)
                    cv2.putText(image, product['tags'][0]['name'][0:15], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1, cv2.LINE_AA)
                num_products_found += 1

        # Loop over the gaps and draw rectangles for each one
        for product in json_response['gaps']:
            if product['tags'][0]['confidence'] > threshold:
                l, t, w, h = product['boundingBox']['x'], product['boundingBox']['y'], product['boundingBox']['w'], product['boundingBox']['h']
                if (self.parent.showRemoteDetections == True):
                    cv2.rectangle(image, (l, t), (l + w, t + h), (255, 0, 0), 2)
                    cv2.putText(image, 'gap', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1, cv2.LINE_AA)

        self.parent.productsDetected = str(num_products_found)
        logger.info("Products Detected: %d", num_products_found)
        return image

    def _process_locally(self, image):
        if self.parent.imageProcessingEndpoint != "":
            model = "" # Will be set if the function returns successfully
            
            logger.debug('Send image to local AI service for processing')
            start_processing_time_local = time.time()
            local_image = cv2.imencode(".jpg", image)[1].tostring()
            response = self._send_image_for_processing_local(local_image)
            logger.debug("Time to perform local AI processing: %s" + Helper.display_time_difference_in_ms(time.time(), start_processing_time_local))

            # Process response from local AI analysis
            if response and isinstance(response, requests.Response) and response.status_code == 200:
                try:
                    json_response = response.json()
                    formatted_response = json.dumps({
                        'model': 'local',
                        'product count': -1, 
                        'prompt response': '', 
                        'json response': json_response 
                    })
                    msg = json.dumps(formatted_response, indent=4)
                    logger.debug("%s",msg)  # Pretty-print the JSON
                    self.parent.localDetections = json_response

                except json.JSONDecodeError:
                    logger.exception("EXCEPTION")
                else:
                    # Handle the case where response is None or not a requests.Response instance
                    if response == None:
                        logger.error("Invalid response received")

            image = self._annotate_image_tensorflow_lite(image, json_response)

            # Forwarding outcome of local AI processing to the EdgeHub
            # TODO: Introduce throttling of these messages (Only send when scheduled e.g. 10 mins from last reading)
            if self.parent.sendLocalDetectionsToHub == True and self.parent.sendToHubCallback is not None:
                logger.info("Send local detections to hub")
                self.parent.sendToHubCallback(msg)

            return image

    def _send_image_for_processing_local(self, image):
        headers = {'Content-Type': 'application/octet-stream'}
        try:
            response = requests.post(self.parent.imageProcessingEndpoint, headers = headers, params = self.parent.imageProcessingParams, data = image)
            try:
                response_json = response.json()  # Try to parse the JSON
                logger.info('Local Processing Response: %s', response_json)
            except ValueError as e:  # If JSON decoding fails
                logger.error('Failed to parse JSON response: %s', e)
                logger.debug('Response content: %s', response.text) 
        except Exception as e:
            logger.exception('EXCEPTION')
            return None

        try:
            logger.debug('Response:%d:%s',response.status_code,json.dumps(response.json()))
        except Exception:
            pass

        return response

    def _annotate_image_tensorflow_lite(self, image, json_response):
        _MARGIN = 10  # pixels
        _ROW_SIZE = 10  # pixels
        _FONT_SIZE = 1
        _FONT_THICKNESS = 1
        _TEXT_COLOR = (0, 0, 255)  # red
        _BOX_COLOR = (0, 255, 0) 

        self.parent.personDetected = False
        # Response in in the form
        #{'detections': [{'bounding_box': {'height': 329, 'origin_x': 993, 'origin_y': 375, 'width': 199}, 'categories': [{'category_name': 'book', 'display_name': '', 'index': 83, 'score': 0.4140625}]}, {'bounding_box': {'height': 302, 'origin_x': 955, 'origin_y': 393, 'width': 161}, 'categories': [{'category_name': 'book', 'display_name': '', 'index': 83, 'score': 0.39453125}]}, {'bounding_box': {'height': 272, 'origin_x': 995, 'origin_y': 7, 'width': 121}, 'categories': [{'category_name': 'book', 'display_name': '', 'index': 83, 'score': 0.37109375}]}]}
        for detection in json_response['detections']:
            # draw label and score
            l, t, w, h = detection['bounding_box']['origin_x'], detection['bounding_box']['origin_y'], detection['bounding_box']['width'], detection['bounding_box']['height']
            category = detection['categories'][0]
            category_name = category['category_name']
            probability = round(category['score'], 2)
            result_text = category_name + ' (' + str(probability) + ')'
            text_location = (_MARGIN + l, _MARGIN + _ROW_SIZE + t)

            if (self.parent.showLocalDetections == True) or (category_name == 'person'):
                cv2.rectangle(image, (l, t), (l + w, t + h), _BOX_COLOR, 2)
                cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

            if category_name == 'person':
                self.parent.personDetected = True
                logger.info("Person Detected")

        return image
        
    def process_image(self, image):
        try:
            logger.debug("ImageProcessor: process_image : Start")

            ######################################################
            # Apply a pipeline of image processing steps
            ######################################################
            processed_image = image

            # ----------------------------------------------------
            # Apply local image processing
            # ----------------------------------------------------
            if self.parent.convertToGray == True:
                logger.info(f"Convert to Gray")
                processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)

            # Perform image rectification
            if (self.parent.performRectification == True):
                processed_image = Helper.unwarp_perspective(processed_image,
                                        [(self.parent.rectificationTopLeftX, self.parent.rectificationTopLeftY),
                                            (self.parent.rectificationTopRightX, self.parent.rectificationTopRightY),
                                            (self.parent.rectificationBottomLeftX, self.parent.rectificationBottomLeftY),
                                            (self.parent.rectificationBottomRightX, self.parent.rectificationBottomRightY)],
                                        [(0,0),(self.parent.rectificationBottomLeftX,0),(0,self.parent.rectificationBottomRightY),(self.parent.rectificationBottomLeftX,self.parent.rectificationBottomRightY)]
                )

            # TODO: Introduce additional input checking for values sent blank from Web UI
            if (self.parent.resizeWidth != 0 or self.parent.resizeHeight != 0):
                logger.info(f"Resize image Height:%s Width:%s", self.parent.resizeWidth, self.parent.resizeHeight)
                processed_image = cv2.resize(processed_image, (int(self.parent.resizeWidth), int(self.parent.resizeHeight)))

            # ----------------------------------------------------
            # Apply AI analysis locally
            # ----------------------------------------------------
            if self.parent.localProcess == True:
                logger.info(f"Local Process")
                processed_image = self._process_locally(processed_image)

            # ----------------------------------------------------
            # Apply AI analysis in the cloud
            # ----------------------------------------------------
            # Only send images to the cloud that contain no images of persons
            if self.parent.cloudProcess == True and self.parent.personDetected == False:
                logger.info(f"Cloud Process")
                processed_image = self._process_in_cloud(processed_image)

            # All processing complete
            # Put the processed image into the output queue
            # We only hold the latest processed image on the output queue
            logger.info(f"New processed image available")
            if self.output_queue.empty():
                self.output_queue.put(processed_image,block=True,timeout=0.02)
                logger.info(f"New processed image queued")

            logger.debug("ImageProcessor: process_image : End")
        except Exception as e:
            logger.exception('EXCEPTION')
            return None

    def continuous_process(self):
        while not self.stop_signal.is_set():
            # print(f"ImageProcessor: Work Queue has {self.work_queue.qsize()} elements")
            try:
                image = self.work_queue.get(block=False)
                # print(f"ImageProcessor: Work Queue now has {self.work_queue.qsize()} elements")
                self.process_image(image)
            except queue.Empty:
                time.sleep(0.1)  # Wait for an image to be available in the queue

            logger.debug('ImageProcessor: Sleep Start')
            time.sleep(float(self.parent.waitTime))  # Add a delay to avoid consuming CPU and reduce API costs
            logger.debug('ImageProcessor: Sleep End')

    def stop(self):
        self.stop_signal.set()

