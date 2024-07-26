# Copyright (c) Emmanuel Bertrand. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import json
from azure.iot.device import IoTHubModuleClient, Message, MethodResponse

import FeedbackManager
from FeedbackManager import FeedbackManager
import MessageParser
from MessageParser import MessageParser

RECEIVE_CALLBACKS = 0
THRESHOLD = 0.5  # Example threshold, adjust as necessary

def receive_message_callback(message):
    global RECEIVE_CALLBACKS
    RECEIVE_CALLBACKS += 1
    print("Received message #: " + str(RECEIVE_CALLBACKS))
    message_buffer = message.data
    body = message_buffer.decode('utf-8')
    allTagsAndProbability = json.loads(body)
    try:
        FEEDBACK_MANAGER.displayFeedback(MESSAGE_PARSER.highestProbabilityTagMeetingThreshold(
            allTagsAndProbability, THRESHOLD))
    except Exception as error:
        print("Message body: " + body)
        print(error)

    return

class HubManager(object):

    def __init__(self):
        # Defines settings of the IoT SDK
        self.client = IoTHubModuleClient.create_from_edge_environment()
        self.client.connect()

        # sets the callback when a message arrives on "input1" queue.  Messages sent to
        # other inputs or to the default will be silently discarded.
        self.client.on_message_received = receive_message_callback
        print("Module is now waiting for messages in the input1 queue.")

def main():
    try:
        print("Starting the Feedback module...")

        global FEEDBACK_MANAGER
        global MESSAGE_PARSER
        FEEDBACK_MANAGER = FeedbackManager()
        MESSAGE_PARSER = MessageParser()
        hubManager = HubManager()

        while True:
            time.sleep(1000)

    except Exception as iothub_error:
        print("Unexpected error %s from IoTHub" % iothub_error)
        return
    except KeyboardInterrupt:
        print("IoTHubClient sample stopped")

if __name__ == "__main__":
    main()
