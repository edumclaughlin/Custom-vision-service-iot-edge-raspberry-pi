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


class CurrentImageStreamHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, camera):
        self.clients = []
        self.camera = camera
        self.busy_lock = threading.Lock()  # Lock for accessing busy flag
        self.busy = False

    # Allow call from any origin - This may need to be reviewed for security
    def check_origin(self, origin):
        return True

    # When a client connects to the WebSocket server, the `open` method is called.
    # In this method, the connected client is added to the `clients` list.
    def open(self):
        self.clients.append(self)
        print("Image Server Connection::opened")

    # The `on_message` method handles incoming messages from clients.
    # It checks for three specific message types:
    # 'next': When a client sends this message, it retrieves an image frame from the camera using the `get_display_frame()` 
    def on_message(self, msg):
        # This message is raised when the client requests new data from the server
        if msg == 'next':
            # Send the current web-cam frame
            frame = self.camera.get_display_frame()
            if frame != None:
                encoded_frame = base64.b64encode(frame)
                metadata = {
                    'type': 'currentimg'
                }
                metadata_bytes = json.dumps(metadata).encode('utf-8')
                combined_data = metadata_bytes + b'\0' + frame
                self.write_message(combined_data, binary=True)
            # Send any processed/annotated images
            # frame = self.camera.get_processed_frame()
            # if frame != None:
            #     encoded_frame = base64.b64encode(frame)
            #     data = {
            #         'type': 'encodedimg',
            #         'data': encoded_frame
            #     }
            #     self.write_message(data, binary=False)

        if msg == 'start':
            print('Start button pressed')
        if msg == 'pause':
            print('Pause button pressed')

    def on_close(self):
        self.clients.remove(self)
        print("Image Server Connection::closed")

class ImageStreamHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, camera):
        self.clients = []
        self.camera = camera
        self.busy_lock = threading.Lock()  # Lock for accessing busy flag
        self.busy = False

    # Allow call from any origin - This may need to be reviewed for security
    def check_origin(self, origin):
        return True

    # When a client connects to the WebSocket server, the `open` method is called.
    # In this method, the connected client is added to the `clients` list.
    def open(self):
        self.clients.append(self)
        print("Image Server Connection::opened")

    # The `on_message` method handles incoming messages from clients.
    # It checks for three specific message types:
    # 'next': When a client sends this message, it retrieves an image frame from the camera using the `get_display_frame()` 
    def on_message(self, msg):
        # This message is raised when the client requests new data from the server
        if msg == 'next':
            # Send the current web-cam frame
            frame = self.camera.get_display_frame()
            if frame != None:
                encoded_frame = base64.b64encode(frame)
                self.write_message(encoded_frame, binary=False)
                
        if msg == 'start':
            print('Start button pressed')
        if msg == 'pause':
            print('Pause button pressed')

    def on_close(self):
        self.clients.remove(self)
        print("Image Server Connection::closed")

# This image server runs in its own thread 
class ImageServer(threading.Thread):

    def __init__(self, port, cameraObj):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.port = port
        self.camera = cameraObj

    def run(self):
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())

            indexPath = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'templates')
            app = tornado.web.Application([
                (r"/stream", ImageStreamHandler, {'camera': self.camera}),
                (r"/(.*)", tornado.web.StaticFileHandler,
                 {'path': indexPath, 'default_filename': 'index.html'})
            ])
            app.listen(self.port)
            print('ImageServer::Started.')
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            print('ImageServer::exited run loop. Exception - ' + str(e))

    def close(self):
        print('ImageServer::Closed.')
