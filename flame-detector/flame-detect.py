"""
Flame detector - measures how fire-y an image is
@author: Dieter Brehm
"""

import sys
import cv2


def callback(x):
    """
    Callback necessary for the createTrackbar call
    """


cv2.namedWindow('slider control window')
cv2.createTrackbar("h range low", "slider control window", 0, 360, callback)
cv2.createTrackbar("s range low", "slider control window", 30, 255, callback)
cv2.createTrackbar("v range low", "slider control window", 0, 255, callback)
cv2.createTrackbar("h range high", "slider control window", 0, 360, callback)
cv2.createTrackbar("s range high", "slider control window", 30, 255, callback)
cv2.createTrackbar("v range high", "slider control window", 0, 255, callback)

def detect_flame(image, visualize=True):
    """
    Detects flame from an image frame.
    image: an opencv image
    returns: a variable scale of how much flame is in the image
    """

    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # receive values from track bars and apply them to the lower limit of the HSV range
    hmin = cv2.getTrackbarPos("h range low", "slider control window")
    smin = cv2.getTrackbarPos("s range low", "slider control window")
    vmin = cv2.getTrackbarPos("v range low", "slider control window")
    hhigh = cv2.getTrackbarPos("h range high", "slider control window")
    shigh = cv2.getTrackbarPos("s range high", "slider control window")
    vhigh = cv2.getTrackbarPos("v range high", "slider control window")
    # lower ideal for red = (0,135,052)
    lower = (hmin, smin, vmin)
    #upper ideal for red = = (222, 255, 255)
    upper = (hhigh, shigh, vhigh)

    # create a mask filtered by the bounds
    mask = cv2.inRange(hsv, lower, upper)

    # filter to reduce noise
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)

    ret, thresh1 = cv2.threshold(mask, 150, 255, cv2.THRESH_BINARY)

    # find contours and draw them
    contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(image, contours, -1, (0, 255, 0), 3)

    if visualize:
        cv2.imshow("Image", image)
        cv2.imshow('mask', mask)
        cv2.imshow('mask', thresh1)


# Test code for processing data directly from the computer webcam or a
# saved image file
if __name__ == '__main__':
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if filename == 'webcam':
            # Process the webcam in realtime
            # "0" here means "the first webcam on your system"
            camera = cv2.VideoCapture(0)

            while True:
                # Get the latest image from the webcam
                ok, image = camera.read()
                if not ok:
                    print("Unable to open webcam...")
                    break

                # Process it
                coordinates = detect_flame(image)
                print(coordinates)

                # Exit if the "Esc" key is pressed
                key = cv2.waitKey(1)
                if key == 27:
                    break
        else:
            # Read data from an image file
            image = cv2.imread(filename)
            # coordinates = detect_flame(image)
            # print(coordinates)
            cv2.waitKey(0)

    else:
        print('Usage: When you run this script, provide either the filename of an image or the string "webcam"')
#
