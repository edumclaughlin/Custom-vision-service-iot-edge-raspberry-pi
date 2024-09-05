# Base on work from https://github.com/Bronkoknorb/PyImageStream
#import trollius as asyncio
import asyncio
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import base64
import os
import json
import logging
from Helpers import Helper

# Get a logger for this module
logger = logging.getLogger(__name__)

class Handler_messages(tornado.websocket.WebSocketHandler):
    clients = [] # Class level variable, shared by all instances

    def initialize(self, parent):
        self.parent = parent

    def check_origin(self, origin):
        return True

    def open(self):
        Handler_messages.clients.append(self)
        logger.debug("Handler_messages::opened")

    # Call to pass form data back to the server
    def on_message(self, msg):
        logger.info("FORM DATA:%s", msg)
        json_response = json.loads(msg)
        self.parent.localProcess = json_response.get('processLocally', False)
        self.parent.imageProcessingEndpoint = json_response.get('localEndpoint','')
        self.parent.cloudProcess = json_response.get('processRemotely', False)
        self.parent.cloudProcessingEndpoint = json_response.get('cloudEndpoint','')
        self.parent.waitTime = float(json_response.get('waitTime',60))
        self.parent.resizeHeight = int(json_response.get('resizeHeight',''),0)
        self.parent.resizeWidth = int(json_response.get('resizeWidth',''),0)
        self.parent.showLocalDetections = json_response.get('showLocalDetections', False)
        self.parent.showRemoteDetections = json_response.get('showRemoteDetections', False)
        self.parent.sendLocalDetectionsToHub = json_response.get('sendLocalToHub', False)
        self.parent.sendRemoteDetectionsToHub = json_response.get('sendRemoteToHub', False)

        self.parent.convertToGray = json_response.get('convertToGray', False)
        self.parent.removeBackground = json_response.get('removeBackground', False)
        self.parent.performRectification = json_response.get('performRectification', False)
        self.parent.rectificationTopLeftX = int(json_response.get('rectificationTopLeftX',''),0)
        self.parent.rectificationTopLeftY = int(json_response.get('rectificationTopLeftY',''),0)
        self.parent.rectificationTopRightX = int(json_response.get('rectificationTopRightX',''),0)
        self.parent.rectificationTopRightY = int(json_response.get('rectificationTopRightY',''),0)
        self.parent.rectificationBottomLeftX = int(json_response.get('rectificationBottomLeftX',''),0)
        self.parent.rectificationBottomLeftY = int(json_response.get('rectificationBottomLeftY',''),0)
        self.parent.rectificationBottomRightX = int(json_response.get('rectificationBottomRightX',''),0)
        self.parent.rectificationBottomRightY = int(json_response.get('rectificationBottomRightY',''),0)

    def on_close(self):
        Handler_messages.clients.remove(self)
        logger.debug("Handler_messages::closed")

    # Use this to send a message to all connected clients
    @classmethod
    def send_message_to_all(cls, message):
        for client in cls.clients:
            client.write_message(message)
            logger.debug("Message sent to client")

class Handler_currentimage(tornado.websocket.WebSocketHandler):
    def initialize(self, parent):
        self.clients = []
        self.parent = parent

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.append(self)
        logger.debug("Handler_currentimage::opened")

    def on_message(self, msg):
        # print(f"Handler_currentimage::message::{msg}")
        if msg == 'next':
            # print("Handler_currentimage::image requested")
            dframe = self.parent.display_originalFrame
            if dframe != None:
                # print("Handler_currentimage::image available")
                self.write_message(dframe, binary=True)

    def on_close(self):
        self.clients.remove(self)
        logger.debug("Handler_currentimage::closed")

class Handler_processedimage(tornado.websocket.WebSocketHandler):
    def initialize(self, parent):
        self.clients = []
        self.parent = parent

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.append(self)
        logger.debug("Handler_processedimage::opened")

    def on_message(self, msg):
        # print(f"Handler_processedimage::message::{msg}")
        if msg == 'next':
            # print("Handler_processedimage::image requested")
            pframe = self.parent.display_processedFrame
            if pframe != None:
                # print("Handler_processedimage::image available")
                self.write_message(pframe, binary=True)

    def on_close(self):
        self.clients.remove(self)
        logger.debug("Handler_processedimage::closed")

class ImageServer(threading.Thread):

    def __init__(self, port, parent):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.port = port
        self.parent = parent # Parent prcess 'CameraCapture'

    def run(self):
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())

            indexPath = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'templates')
            app = tornado.web.Application([
                (r"/stream", Handler_messages, {'parent': self.parent}),
                (r"/currentimage", Handler_currentimage, {'parent': self.parent}),
                (r"/processedimage", Handler_processedimage, {'parent': self.parent}),
                (r"/(.*)", tornado.web.StaticFileHandler,
                 {'path': indexPath, 'default_filename': 'index.html'})
            ])
            app.listen(self.port)
            logger.debug('ImageServer::Started.')
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            logger.debug('ImageServer::exited run loop. Exception - ' + str(e))

    def send_to_clients(self, message):
        Handler_messages.send_message_to_all(message)

    def close(self):
        logger.debug('ImageServer::Closed.')