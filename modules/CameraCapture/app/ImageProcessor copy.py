from queue import Queue
import threading
from threading import Event
from multiprocessing import Process
import cv2
import time

class ImageProcessor:
    def __init__(self):
        self.image_queue = Queue(maxsize=2)
        self.processing_queue = Queue(maxsize=2)
        self.stop_signal = Event()
        self.lock = threading.Lock()
        self.busy = False
    
    def process_image(self, image):
        print("ImageProcessor: process_image : Start")
        
        # Apply image filters
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
        
        # Put the processed image into the result queue
        #self.processing_queue.put((gray_image, "ImageProcessor: Processed Image"))
        print("ImageProcessor: process_image : End")
    
    def continuous_process(self):
        while True:
            self.busy = True
            with self.lock:
                try:
                    # Get a processed image from the result queue if available
                    # block=False forces an exception rather than a wait if the queue is empty
                    print(f"ImageProcessor: Queue has {self.image_queue.qsize()} elements")
                    try:
                        #image = self.image_queue.get(block=False)
                        image = self.image_queue.get(block=True, timeout=0.1)  # Wait for an image to be available in the queue
                        #image = self.image_queue.get(block=True, timeout=0.1)  # Wait for an image to be available in the queue
                        print ("ImageProcessor: Dequeued Image")
                        print(f"ImageProcessor: Queue now has {self.image_queue.qsize()} elements")
                    except:
                        pass
                    else:
                        if self.stop_signal.is_set():  # Check if the stop signal is set before processing an image
                            break # Break out of the loop and exit
                        #self.process_image(image)
                except Exception as e:
                    print(f"Error: {e}")

            print ('ImageProcessor: Sleep Start')
            time.sleep(5)  # Add a delay to avoid consuming CPU
            print ('ImageProcessor: Sleep End')
            self.busy = False

    def is_busy(self):
        return self.busy

    def get_result(self):
        return self.processing_queue.get()
    
    def stop(self):
        self.stop_signal.set()