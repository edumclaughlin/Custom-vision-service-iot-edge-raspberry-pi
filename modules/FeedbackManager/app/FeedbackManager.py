import time
from enum import Enum

class FeedbackManager(object):

    def __init__(self):
        print("Feedback Initialised")
        time.sleep(1)

    def displayFeedback(self, strDetection):
        print("Detection : " + strDetection)
