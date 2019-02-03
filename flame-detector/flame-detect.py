"""
Flame detector - measures how fire-y an image is
@author: Dieter Brehm
"""

import sys
import cv2
import asyncio
import os.path
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from datetime import timedelta


def callback(x):
    """
    Callback necessary for the createTrackbar call
    """


def detect_flame(image, visualize=True):
    """
    Detects flame from an image frame.
    image: an opencv image
    returns: a variable scale of how much flame is in the image
    """

    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # receive values from track bars and apply them to the lower limit of the HSV range
    #hmin = cv2.getTrackbarPos("h range low", "slider control window")
    #smin = cv2.getTrackbarPos("s range low", "slider control window")
    #vmin = cv2.getTrackbarPos("v range low", "slider control window")
    #hhigh = cv2.getTrackbarPos("h range high", "slider control window")
    #shigh = cv2.getTrackbarPos("s range high", "slider control window")
    #vhigh = cv2.getTrackbarPos("v range high", "slider control window")
    lower  = (0,135,52)
    #lower = (hmin, smin, vmin)
    upper = (222, 255, 255)
    #upper = (hhigh, shigh, vhigh)

    # create a mask filtered by the bounds
    mask = cv2.inRange(hsv, lower, upper)

    # filter to reduce noise
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)

    ret, thresh1 = cv2.threshold(mask, 150, 255, cv2.THRESH_BINARY)

    # find contours and draw them
    contours, hierarchy = cv2.findContours(thresh1,
                                           cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) != 0:
        cv2.drawContours(image, contours, -1, (0, 255, 0), 3)
        c = max(contours, key=cv2.contourArea)
        largest_area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 5)

    if visualize:
        cv2.imshow("Image", image)
        cv2.imshow('mask', mask)
        cv2.imshow('mask', thresh1)

    if 'largest_area' in locals():
        return largest_area
    return 0


### Test code for processing data directly from the computer webcam or a saved image file
# if __name__ == '__main__':
#     if len(sys.argv) == 2:
#         filename = sys.argv[1]
#         if filename == 'webcam':
#             # Process the webcam in realtime
#             camera = cv2.VideoCapture(0)  # "0" here means "the first webcam on your system"

#             while True:
#                 # Get the latest image from the webcam
#                 ok, image = camera.read()
#                 if not ok:
#                     print("Unable to open webcam...")
#                     break

#                 # Process it
#                 coordinates = detect_helmet_coordinates(image)
#                 print(coordinates)

#                 # Exit if the "Esc" key is pressed
#                 key = cv2.waitKey(1)
#                 if key == 27:
#                     break
#         else:
#             # Read data from an image file
#             image = cv2.imread(filename)
#             coordinates = detect_helmet_coordinates(image)
#             print(coordinates)
#             cv2.waitKey(0)

#     else:
#         print('Usage: When you run this script, provide either the filename of an image or the string "webcam"')

cap = cv2.VideoCapture(0)
success, image = cap.read()
flame = detect_flame(image, visualize=True)
clients = []

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        print("origin: " + origin)
        return True

    # the client connected
    def open(self):
        print("New client connected")
        self.write_message("You are connected")
        clients.append(self)

    # the client sent the message
    def on_message(self, message):
        print("message: " + message)
        self.write_message(message)

    # client disconnected
    def on_close(self):
        print("Client disconnected")
        clients.remove(self)

        
def translate(value, leftMin, leftMax, rightMin, rightMax):
    left = leftMax - leftMin
    right = rightMax - rightMin
    scaled = float(value - leftMin) / float(left)
    return rightMin + (scaled * right)


def send_message_to_clients():
    old_val = 0
    alpha = 0.6
    try:
        success, image = cap.read()
        flame = detect_flame(image, visualize=True)
        val = int(100 * (0.3 * flame + (1 - alpha) * old_val)) / 100
        old_val = val
        val = translate(val, 0, 40000, 0, 1)
        for client in clients:
            print("sending a message")
            if val > 0.3:
                client.write_message("1")
            else:
                client.write_message("0")
    finally:
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=1),
                                                     send_message_to_clients)


socket = tornado.web.Application([(r"/", WebSocketHandler), ])
if __name__ == "__main__":
    socket.listen(8888)
    tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=0.05),
                                                 send_message_to_clients)
    tornado.ioloop.IOLoop.instance().start()
