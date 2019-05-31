from collections import deque
import numpy as np
import cv2
import time
from timeit import default_timer as timer
import warnings
import matplotlib.pyplot as plt
import math
import serial
from math import tan
from math import pi
import sys

#   Initialize the serial port
#   --------
ser = serial.Serial('COM3', 57600, timeout=0, parity=serial.PARITY_NONE, rtscts=1) # uncomment once PSOC exists
print(ser.is_open)
time.sleep(1)
#   --------

warnings.simplefilter('ignore', np.RankWarning)
# warnings.filterwarnings('error')
# np.seterr(all='raise')


#   Set the threshold for color black in HSV space`
blackLower = np.array([90, 100, 30])
blackUpper = np.array([110, 255, 255])


#   Initialize the length for tracking coordinates
my_buffer = 64
ptsYZL = deque(maxlen=my_buffer)  # comes from laptop camera (bad coords)
ptsXZJ = deque(maxlen=my_buffer)  # comes from Josh camera (bad coords)


ptsRealX = deque(maxlen=my_buffer)
ptsRealY = deque(maxlen=my_buffer)
ptsRealZ = deque(maxlen=my_buffer)

#   Turn on the camera
camera1 = cv2.VideoCapture(1)  # Josh's Camera <-- will be looking at the ball, the ball will be crossing the frame
camera2 = cv2.VideoCapture(0)  # Laptop's Camera <-- will be in front of the camera, the ball will be in the frame

#   Wait for 2 seconds
time.sleep(2)

#   Make the camera data Arrays

# ---------------------------
time_lst = np.array([0])
timeTilPrediction = 0
bufferTime = 0
movement = np.array([0])
other_camera = np.array([0])
# ---------------------------

# For testing purposes, the Matplotlib graph
# ---------------------------
showXCoords = np.array([])
showYCoords = np.array([])
showZCoords = np.array([])
predictedXArray = np.array([])
predictedZArray = np.array([])
# ---------------------------

# the function to get the data from the psoc. IE the reading function
# ---------------------------
def getData():
    # time.sleep(.03) # No longer will use this line
    # time.sleep(.05)
    read = ser.read(8)
    if (read[0] == 0) and (read[1]) == 0 and (read[6] == 0) and (read[7] == 0):
        a = read[2]
        b = read[3]
        c = int.from_bytes([a, b], byteorder='big', signed=True)
        d = int.from_bytes([read[4], read[5]], byteorder='big', signed=True)
        ser.reset_input_buffer()
        return c, d
    ser.reset_input_buffer()
    print("didnt get iterable")
    return (0, 0)
# ---------------------------

# Make the function to give the data to the PSOC
# TODO: get the working function from the other file
# ---------------------------
def sendData(upAndDown, LeftAndRight):
    # changed the sending to only sleep for .01, instead of .05
    if upAndDown > 100:
        upAndDown = 99

    firstByte = bytes(str(upAndDown // 10), 'ascii')
    secondByte = bytes(str(upAndDown % 10), 'ascii')
    # letter4send = b'1'
    ser.write(firstByte)
    # time.sleep(.003)
    ser.write(secondByte)
    # time.sleep(.003)
    letter6send = b'x'
    ser.write(letter6send)
    # time.sleep(.003)
    # ser.reset_output_buffer() # this might be needed

    # print(highNumber // 1000)
    if LeftAndRight < 0:
        LeftAndRight = 0
    if LeftAndRight > 9999:
        LeftAndRight = 9999

    largestDigit = bytes(str(LeftAndRight // 1000), 'ascii')
    ser.write(largestDigit)
    # time.sleep(.003)
    LeftAndRight = LeftAndRight % 1000
    # print(LeftAndRight // 100)
    hundreds = bytes(str(LeftAndRight // 100), 'ascii')
    ser.write(hundreds)
    # time.sleep(.003)
    LeftAndRight = LeftAndRight % 100
    # print(LeftAndRight // 10)
    tens = bytes(str(LeftAndRight // 10), 'ascii')
    ser.write(tens)
    # time.sleep(.003)
    LeftAndRight = LeftAndRight % 10
    # print(LeftAndRight // 1)
    ones = bytes(str(LeftAndRight // 1), 'ascii')
    ser.write(ones)
    # time.sleep(.003)

    letter8send = b'y'
    ser.write(letter8send)
    time.sleep(.001)
    ser.reset_output_buffer()
    return
# ---------------------------

# Basic control for the flipping motor
# ---------------------------
def flippingMotor():
    # number = [7]
    # bts = bytes(number)
    ser.reset_output_buffer()
    bts = b'H'  # will now send an H whenever it runs, to match the code Caeser did
    ser.write(bts)
    # time.sleep(0.001)
    ser.reset_output_buffer()
    # print("sent a flip")
    # time.sleep(.005) # eliminate this line for now because there should be no sending conflict
    return
# ---------------------------


# need to make a function that takes the data from the deque and returns an array
# ---------------------------
def toLst(dequeArray):
    returnLst = []
    # for integer, _ in enumerate(dequeArray):
    for _, item in enumerate(dequeArray):
        returnLst.append(item)
        # print(type(item))
    return returnLst


# ---------------------------
# Define camera constants (NOTE: make sure that the robot is a distance 2A from the laptop camera)
# NOTE: these are in decimeters. Why? because that is what I chose
# ---------------------------
A = 17.78  #
B = 14.732  # 58in
C = 10.16  #
distanceToRobot = 30.734
LRMoveTick = .014  # .013, .015, .022
startingPositionHorizontal = B - 3.91
debuggingCount = 0
flag = True
# ---------------------------

#   Detect color black

# set the robot at a certain value
initSend = int((startingPositionHorizontal / LRMoveTick) // 1)
sendData(0, initSend)  # send the data to start the robot in the middle6
LeftAndRight = 0

while True:

    if bufferTime > .01:
        upAndDown, LeftAndRight = getData()
        print(upAndDown, " <-  upAndDown === ", debuggingCount, "==== left and right ->", LeftAndRight)
        bufferTime = 0
        # debuggingCount += 1

    #   --------
    before = timer()
    #   --------
    #   Read the frames
    _, frame = camera1.read()
    _, frame2 = camera2.read()

    #   Change the frames to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)

    #   Build a mask based on threshold
    mask = cv2.inRange(hsv, blackLower, blackUpper)
    mask2 = cv2.inRange(hsv2, blackLower, blackUpper)

    #   Erosion
    mask = cv2.erode(mask, None, iterations=2)
    mask2 = cv2.erode(mask2, None, iterations=2)

    #   Dilation, remove the noise by erosion and dilation
    mask = cv2.dilate(mask, None, iterations=2)
    mask2 = cv2.dilate(mask2, None, iterations=2)

    #   Detect the contour
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    contours2 = cv2.findContours(mask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    #   Initialize the centroid
    center = None
    center2 = None

    #   If there is a contour
    if len(contours) > 0:  # Josh's camera for ball crossing the frame
        #   Find the contour with the largest area
        c = max(contours, key=cv2.contourArea)

        #   Determine the circle of the largest contour
        ((y, z1), radius) = cv2.minEnclosingCircle(c)

        #   Calculate the moment of the contour
        M = cv2.moments(c)

        #   Calculate the centroid
        center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))

        #   Plot only when the radius is greater than 0
        if radius > 0:
            cv2.circle(frame, (int(y), int(z1)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            # print('y coordinate: %s, z1 coordinate: %s'%(y, z1))

            #  Add the centroid to the left of the list
            ptsYZL.appendleft(center)

    if len(contours2) > 0:
        #   Find the contour with the largest area
        c2 = max(contours2, key=cv2.contourArea)

        #   Determine the circle of the largest contour
        ((x, z2), radius2) = cv2.minEnclosingCircle(c2)

        #   Calculate the moment of the contour
        M2 = cv2.moments(c2)

        #   Calculate the centroid
        center2 = (int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"]))

        #   Plot only when the radius is greater than 0
        if radius2 > 0:
            cv2.circle(frame2, (int(x), int(z2)), int(radius2), (0, 255, 255), 2)
            cv2.circle(frame2, center2, 5, (0, 0, 255), -1)
            #   print('y coordinate: %s, z1 coordinate: %s'%(y, z2))

            #   Add the centroid to the left of the list
            ptsXZJ.appendleft(center2)

    #   Covert pixel coordinates (x,y,z1,z2) to real world coordinates (X,Y,Z)
    # since we are adding to the front of the list, we are always taking the most recent coords
    # this works:
    if len(ptsXZJ) > 1 and len(ptsYZL) > 1:
        x_convert = ptsXZJ[0][0]  # take most recent recorded X coord from Josh Camera
        y_convert = ptsYZL[0][0]  # the most recent recorded Y coord from Laptop camera
        z1_convert = ptsYZL[0][1]  # the most recorded Z coord from the laptop camera
        # print("The pixel coordinate of x is: ", x_convert)
        # print("The pixel coordinate of y is: ", y_convert)
        # print("The pixel coordinate of z1 is: ", z1_convert)
        X_real = (B + tan(1.92e-3*x_convert - .614)*A) / (1 - tan(1.92e-3*x_convert - .614)*tan(1.415 - 2.2111e-3*y_convert - .708))
        Y_real = tan(1.415 - 2.21e-3*y_convert - .708)*X_real + A
        Z_real = tan(0.941 - 1.96e-3*z1_convert - .4704)*X_real + C
        Real_world_coordinate = (X_real, Y_real, Z_real)
        # print("The real X coordinate is: ", X_real)
        # print("The real Y coordinate is: ", Y_real)
        # print("The real Z coordinate is: ", Z_real)
        # ptsXYZ.appendleft(Real_world_coordinate)

        ptsRealX.appendleft(Real_world_coordinate[0])
        # print("This is real x coords points", ptsRealX)
        ptsRealY.appendleft(Real_world_coordinate[1])
        ptsRealZ.appendleft(Real_world_coordinate[2])

        showXCoords = np.append(showXCoords, [Real_world_coordinate[0]])
        showYCoords = np.append(showYCoords, [Real_world_coordinate[1]])
        showZCoords = np.append(showZCoords, [Real_world_coordinate[2]])

        if Real_world_coordinate[1] > (A + 2) and flag:
            flippingMotor()
            flag = False

    cv2.imshow('YZ', frame)
    cv2.imshow('XZ', frame2)
    after = timer()
    tme = after - before
    time_lst = np.append(time_lst, [tme])
    timeTilPrediction += tme
    bufferTime += tme
    #   print(ptsXY, len(ptsXY))
    # moveX_array = np.array([0])
    # moveY_array = np.array([0])
    # moveX = 0
    # moveY = 0
    #
    # Prediction Starts

    if len(ptsXZJ) > 2 and len(ptsYZL) > 2:
        # print(debuggingCount)
        if timeTilPrediction > .0025:
            timeTilPrediction = 0  # Once this part of code is executed, we will start the time again from zero
            # the following code will take our 64 coords points and put them into a python list
            # we will then use this list to make a numpy A array for our linear least squares
            realXCoords = toLst(ptsRealX)
            # print("This is real X coords =======", realXCoords)
            realYCoords = toLst(ptsRealY)
            realZCoords = toLst(ptsRealZ)

            # x = np.array(realXCoords, dtype=np.float64)
            # xArray = np.array(realXCoords, dtype='float64')
            xArray = np.array(realXCoords)
            del realXCoords
            yArray = np.array(realYCoords)
            del realYCoords
            # print("This is the X Array", xArray, "End X array ==========")
            AMatrix = np.vstack((xArray, np.ones(len(xArray)))).T  # this is our linear least squares matrix
            # print("this is the A matrix", AMatrix, "End A matrix ~~~~~~~~~~~~~~~~")
            del xArray
            # A.metrics = []
            # A.astype(np.float32)
            # A = np.matrix(x, np.ones(len(x), dtype=np.float64), dtype=np.float64).T
            m, b = np.linalg.lstsq(AMatrix, yArray, rcond=None)[0]  # a tuple to satisfy the equation y = mx + b
            del AMatrix

            # assuming our (zero, zero) is on the same line as our laptop cameray
            """
                                        [Robot]
                ⌄     |~~~~~~~~~~~~~~~~~~~{X}~~~~~~~~~~~~~~~~~~~~~
                      |                  /
                      |                 /
                A     |                /
                      |               /
                ^     |              /
            [Josh's]  |             /
            camera]   |            /
                ⌄     |           /
                      |          /
                A     |         /
                      |        /
                      |_______/__________________________________
                ^      [-    B     -][laptop camera][-    B     -]
                _
              / ⌄ \
             |>{C}<|
              \ ^ /
            The above is what the following line of code predicts:
            """
            # distanceToRobot = 25.9
            predictedX = (distanceToRobot - b) / m  # change to 2A when doing the demo
            if predictedX < 0:
                predictedX = 0
            if predictedX > 17:
                predictedX = 17
            predictedXArray = np.append(predictedXArray, [predictedX])
            # print("This is the number where it will land", predictedX)

            # from above we already have y
            # we now need z
            zArray = np.array(realZCoords, dtype='float32')
            function = np.polyfit(yArray, zArray, 2)
            polynomial = np.poly1d(function)
            predictedZ = polynomial(20.5)  # change to 2A for the
            # the Threshold for the max arm length
            if predictedZ < 4.826:
                predictedZ = 4.826
            if predictedZ > 6.5:
                predictedZ = 6.5

            predictedZArray = np.append(predictedZArray, [predictedZ])
            del yArray
            del zArray
            # sendData(up and down, left and right)
            sendXMotorCount = int((predictedX / LRMoveTick) // 1)
            if sendXMotorCount < 10:
                sendXMotorCount = initSend

            sendData(int(((predictedZ - 4.826) / .18) // 1), sendXMotorCount)

            # print("we are sending: ", sendXMotorCount, ". We currently have: ", LeftAndRight)
            # print("after if debugging count", debuggingCount)


    # print("These are the coordinates. X position is: ", moveX, "\n", "Y Position is: ", moveY)
    # sentData = ser.write([moveX, moveY])
    # print(sentData)
    # # send one array of data at a time, will block until the number of bytes is read
    # # Ethan thinks the while loop will not continue until after the number of bytes is read
    # # but Ethan could be wrong
    # # Ethan is wrong.
    # byteArray = ser.read(16)
    # print(byteArray)

    # Exit when press the esc button
    k = cv2.waitKey(3) & 0xFF
    if k == 27:
        break

    if k == 32:
        sys.exit()

#   Release the camera
camera1.release()
#   Destroy the windows
cv2.destroyAllWindows()
print(1/np.mean(time_lst))

f = open("dataXCoords.txt", "w+")

length = max(showXCoords.size, showYCoords.size)

for _, integer in enumerate(range(length)):
    writeString = "({}, {})".format(showXCoords[integer], showYCoords[integer])
    f.write(writeString)
    f.write("\r\n")

f.close()

plt.plot(showXCoords, showYCoords, 'o-', label='XY axis')
plt.xlabel('real life x coords')
plt.ylabel('real life y coords')
plt.show()
plt.plot(showYCoords, showZCoords, 'ko-', label='YZ axis')
plt.xlabel('real life y coords')
plt.ylabel('real life z coords')
plt.show()

plt.plot(predictedXArray, 'go-', label='predicted x ')
plt.xlabel('time')
plt.ylabel('predicted x location')
plt.show()
plt.plot(predictedZArray, 'bo-', label='predicted y')
plt.xlabel('time')
plt.ylabel('predicted z location')
plt.show()

# sendData(1, 10)

# plt.plot(moveX_array, moveY_array, 'r--', label='raw coordinates')
# plt.show()
