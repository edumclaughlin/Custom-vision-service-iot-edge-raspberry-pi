# To make python 2 and python 3 compatible code
from __future__ import absolute_import

from threading import Thread
import sys
import cv2
from cv2 import cv2
import logging
from Helpers import Helper
from queue import Queue

# Get a logger for this module
logger = logging.getLogger(__name__)

# pylint: disable=E1101
# pylint: disable=E0401
# Disabling linting that is not supported by Pylint for C extensions such as OpenCV. See issue https://github.com/PyCQA/pylint/issues/1955

# This class reads all the video frames in a separate thread and always has the keeps only the latest frame in its queue to be grabbed by another thread
class VideoStream(object):
    def __init__(self, path, queueSize=2, CaptureWidth=1080, CaptureHeight=1920):
        self.stream = cv2.VideoCapture(path)
        self.stopped = False
        self.Q = Queue(maxsize=queueSize)
        # Should I cask camera to capture in a specified resolution if possible
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, CaptureWidth)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, CaptureHeight)
        self.stream.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000) # Set timeout for frame to 2 seconds

    def start(self):
        # start a thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        try:
            while True:
                if self.stopped:
                    return

                if not self.Q.full():
                    if self.stream.isOpened():
                        (grabbed, frame) = self.stream.read()
                        if not grabbed or frame is None or frame.size == 0:
                            logger.info("Failed to capture a frame or the frame is empty.")
                        else:
                            logger.debug("Captured a valid frame.")
                            self.Q.put(frame)
                    else:
                        logger.info("The video capture object could not be opened.")

                    # Clean the queue to keep only the latest frame
                    while self.Q.qsize() > 1:
                        self.Q.get()
        except Exception as e:
            logger.exception("EXCEPTION")

    def read(self):
        return self.Q.get()

    def more(self):
        return self.Q.qsize() > 0

    def stop(self):
        self.stopped = True

    def __exit__(self, exception_type, exception_value, traceback):
        self.stream.release()
