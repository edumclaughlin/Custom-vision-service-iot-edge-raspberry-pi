
import queue
from queue import Queue
import threading
from threading import Event
import cv2
import time

class ImageProcessor:
    def __init__(self):
        self.work_queue = Queue(maxsize=2)
        self.output_queue = Queue(maxsize=2)
        self.stop_signal = Event()
        self.lock = threading.Lock()
    
    def process_image(self, image):
        # print("ImageProcessor: process_image : Start")
        # Apply image filters
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Put the processed image into the output queue
        # We only hold the latest processed image on the output queue
        print(f"ImageProcessor: Output Queue has {self.output_queue.qsize()} elements")
        if self.output_queue.empty():
            self.output_queue.put(gray_image,block=True,timeout=0.2)
            print(f"ImageProcessor: Output Queue now has {self.output_queue.qsize()} elements")

        # print("ImageProcessor: process_image : End")
    
    def continuous_process(self):
        while not self.stop_signal.is_set():
            # print(f"ImageProcessor: Work Queue has {self.work_queue.qsize()} elements")
            try:
                image = self.work_queue.get(block=False)
                # print(f"ImageProcessor: Work Queue now has {self.work_queue.qsize()} elements")
                self.process_image(image)
            except queue.Empty:
                time.sleep(0.1)  # Wait for an image to be available in the queue

            # print ('ImageProcessor: Sleep Start')
            time.sleep(0.05)  # Add a delay to avoid consuming CPU
            # print ('ImageProcessor: Sleep End')

    def stop(self):
        self.stop_signal.set()

