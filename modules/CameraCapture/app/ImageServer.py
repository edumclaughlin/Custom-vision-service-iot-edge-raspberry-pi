# Base on work from https://github.com/Bronkoknorb/PyImageStream
#import trollius as asyncio
import asyncio
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import base64
import os


class Handler_messages(tornado.websocket.WebSocketHandler):
    clients = [] # Class level variable, shared by all instances

    def initialize(self, camera):
        self.camera = camera

    def check_origin(self, origin):
        return True

    def open(self):
        Handler_messages.clients.append(self)
        print("Handler_messages::opened")

    def on_message(self, msg):
        if msg == 'start':
            print('Start button pressed')
        if msg == 'pause':
            print('Pause button pressed')

    def on_close(self):
        Handler_messages.clients.remove(self)
        print("Handler_messages::closed")

    @classmethod
    def send_message_to_all(cls, message):
        for client in cls.clients:
            client.write_message(message)
            print("Message sent to client")

class Handler_currentimage(tornado.websocket.WebSocketHandler):
    def initialize(self, camera):
        self.clients = []
        self.camera = camera

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.append(self)
        print("Handler_currentimage::opened")

    def on_message(self, msg):
        # print(f"Handler_currentimage::message::{msg}")
        if msg == 'next':
            # print("Handler_currentimage::image requested")
            dframe = self.camera.display_originalFrame
            if dframe != None:
                # print("Handler_currentimage::image available")
                self.write_message(dframe, binary=True)

    def on_close(self):
        self.clients.remove(self)
        print("Handler_currentimage::closed")


class Handler_processedimage(tornado.websocket.WebSocketHandler):
    def initialize(self, camera):
        self.clients = []
        self.camera = camera

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.append(self)
        print("Handler_processedimage::opened")

    def on_message(self, msg):
        # print(f"Handler_processedimage::message::{msg}")
        if msg == 'next':
            # print("Handler_processedimage::image requested")
            pframe = self.camera.display_processedFrame
            if pframe != None:
                # print("Handler_processedimage::image available")
                self.write_message(pframe, binary=True)

    def on_close(self):
        self.clients.remove(self)
        print("Handler_processedimage::closed")

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
                (r"/stream", Handler_messages, {'camera': self.camera}),
                (r"/currentimage", Handler_currentimage, {'camera': self.camera}),
                (r"/processedimage", Handler_processedimage, {'camera': self.camera}),
                (r"/(.*)", tornado.web.StaticFileHandler,
                 {'path': indexPath, 'default_filename': 'index.html'})
            ])
            app.listen(self.port)
            print('ImageServer::Started.')
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            print('ImageServer::exited run loop. Exception - ' + str(e))

    def send_to_clients(self, message):
        Handler_messages.send_message_to_all(message)

    def close(self):
        print('ImageServer::Closed.')