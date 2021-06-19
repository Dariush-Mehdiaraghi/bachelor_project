import sys
import pygame
import math
from pygame import gfxdraw
import argparse
import cv2
import os

from easing_functions import *

from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference
from pyky040 import pyky040
import threading
import socket
import time

import mido
port = mido.open_input()

synthMode = "Mix"
mixModeVal = 50
arpModeVal = 120
stepInArp = 0
objs = []
labels = []
lastTimeClicked = time.time()
lastTimeEncoderPressed = time.time()

def main():

    default_model_dir = os.path.join(
        os.path.dirname(__file__), 'models/bottleDetector')
    default_model = 'ssdlite_mobiledet_bottle_detector.tflite'
    default_labels = 'labels.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir, default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of categories with highest score to display')
    parser.add_argument('--camera_idx', type=int,
                        help='Index of which video source to use. ', default=0)
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='classifier score threshold')
    args = parser.parse_args()

    print('Loading {} with {} labels.'.format(args.model, args.labels))
    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    global labels
    labels = read_label_file(args.labels)
    inference_size = input_size(interpreter)
    print("inference_size: ", inference_size)
    cap = cv2.VideoCapture(args.camera_idx)

    # Rotary encoder
    def encoderInc(scale_position):
        global synthMode
        global mixModeVal
        global arpModeVal
        wakeUp()
        if synthMode == "Mix":
            mixModeVal = min(mixModeVal+1, 100)
        if synthMode == "Arp":
            arpModeVal = min(arpModeVal+10, 1500)
            os.system("echo '" + str(arpModeVal) + ";" + "' | pdsend 3001")
        print('Encoder incremented mixVal: {}'.format(
            mixModeVal) + ' arpVal: {}'.format(arpModeVal))

    def encoderDec(scale_position):
        global synthMode
        global mixModeVal
        global arpModeVal
        wakeUp()
        if synthMode == "Mix":
            mixModeVal = max(mixModeVal-1, 0)
        if synthMode == "Arp":
            arpModeVal = max(1, arpModeVal - 10)
            os.system("echo '" + str(arpModeVal) + ";" + "' | pdsend 3001")
        print('Encoder decremented mixVal: {}'.format(
            mixModeVal) + ' arpVal: {}'.format(arpModeVal))

    def encoderClicked():
        global synthMode
        global lastTimeEncoderPressed
        
        lastTimeEncoderPressed = time.time()
        wakeUp()
        if synthMode == "Mix":
            synthMode = "Arp"
        else:
            synthMode = "Mix"
        if detectionPaused:
            resumeDetection()
        os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
        print('Encoder clicked currentMode: {}'.format(synthMode))
    def wakeUp():
        global lastTimeClicked
        lastTimeClicked = time.time()
        if detectionPaused:
            resumeDetection()
    os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
    encoder = pyky040.Encoder(CLK=4, DT=17, SW=27)
    encoder.setup(inc_callback=encoderInc,
                  dec_callback=encoderDec, sw_callback=encoderClicked)

    encoderThread = threading.Thread(target=encoder.watch)
    encoderThread.start()

    # getting messages from PD

    def serverWatcher():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 3003)
        print(f'starting up on {server_address[0]} port {server_address[1]}')

        sock.bind(server_address)
        sock.listen(1)
        while True:
            print('waiting for a connection')
            connection, client_address = sock.accept()

            try:
                print('client connected:', client_address)
                os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
                while True:
                    data = connection.recv(16)
                    data = data.decode("utf-8")
                    data = data.replace('\n', '').replace(
                        '\t', '').replace('\r', '').replace(';', '')
                    global stepInArp
                    if data != '':
                        stepInArp = int(data)
                    if not data:
                        break
            finally:
                connection.close()
    watcherThread = threading.Thread(target=serverWatcher)
    watcherThread.start()

    # inferencing
    pauseCondition = threading.Condition(threading.Lock())
    detectionPaused = False

    def pauseDetection():
        if notesPressed <= 0:
            os.system("echo '" + "Sleep" + ";" + "' | pdsend 3002")
            nonlocal detectionPaused
            detectionPaused = True
            pauseCondition.acquire()
            print("going to sleep")

    def resumeDetection():
        global lastTimeClicked
        lastTimeClicked = time.time()
        nonlocal detectionPaused
        if detectionPaused:
            os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
            detectionPaused = False
            pauseCondition.notify()
            pauseCondition.release()
            print("waking up")

    def detectObjs():
        while cap.isOpened():
            with pauseCondition:
                while detectionPaused:
                    pauseCondition.wait()
                    print("after wait")

            ret, frame = cap.read()
            if not ret:
                break
            cv2_im = frame

            cv2_im_rgb = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
            cv2_im_rgb = cv2.resize(cv2_im_rgb, inference_size)
            run_inference(interpreter, cv2_im_rgb.tobytes())
            global objs
            objs = get_objects(interpreter, mixModeVal/100)[:args.top_k]
            height, width, channels = cv2_im.shape
            scale_x, scale_y = width / \
                inference_size[0], height / inference_size[1]
            foundObjs = ""
            for obj in objs:
                bbox = obj.bbox.scale(scale_x, scale_y)
                x0 = round(bbox.xmin)
                x1 = round(bbox.xmax)
                position = ((x0+x1)/2) / 640  # image_width
                foundObjs += str(obj.id) + " " + str(position) + " "
            os.system("echo '" + str(foundObjs) + ";" + "' | pdsend 3000")
        # append_objs_to_img(cv2_im, inference_size, objs, labels)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

    detectObjsThread = threading.Thread(target=detectObjs)
    detectObjsThread.start()

    os.system("echo '" + "120" + ";" + "' | pdsend 3001")

    # drawing GUI with pygame
    pygame.init()
    clock = pygame.time.Clock()

    # SO answer by Yannis Assael https://stackoverflow.com/questions/30578068/pygame-draw-anti-aliased-thick-line for drawing a antialiased line
    def drawAALine(X0, X1, color, strokeWidth):

        center_L1 = ((X0[0] + X1[0]) / 2, (X0[1] + X1[1]) / 2)
        length = lCircleRadius
        thickness = strokeWidth
        angle = math.atan2(X0[1] - X1[1], X0[0] - X1[0])
        UL = (center_L1[0] + (length / 2.) * math.cos(angle) - (thickness / 2.) * math.sin(angle),
              center_L1[1] + (thickness / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
        UR = (center_L1[0] - (length / 2.) * math.cos(angle) - (thickness / 2.) * math.sin(angle),
              center_L1[1] + (thickness / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))
        BL = (center_L1[0] + (length / 2.) * math.cos(angle) + (thickness / 2.) * math.sin(angle),
              center_L1[1] - (thickness / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
        BR = (center_L1[0] - (length / 2.) * math.cos(angle) + (thickness / 2.) * math.sin(angle),
              center_L1[1] - (thickness / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))
        pygame.gfxdraw.aapolygon(screen, (UL, UR, BR, BL), color)
        pygame.gfxdraw.filled_polygon(screen, (UL, UR, BR, BL), color)

    def drawAACircle(surface, pos, radius, color, strokeWidth, strokeColor):
        pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius, strokeColor)
        pygame.gfxdraw.filled_circle(
            surface, pos[0], pos[1], radius, strokeColor)
        pygame.gfxdraw.aacircle(
            surface, pos[0], pos[1], radius-strokeWidth, color)
        pygame.gfxdraw.filled_circle(
            surface,  pos[0], pos[1], radius-strokeWidth, color)

    size = width, height = 480, 480
    backgroundColor = (0, 0, 0)
    primaryColor = (255, 255, 255)
    center = (round(width/2), round(height/2))
    circleFactor = (math.pi*2) / 640
    sCircleStroke = 3
    sCircleRadius = 35
    lCircleStroke = 3
    lCircleRadius = round(width/2 - sCircleRadius)
    colorIdArray = [(255, 202, 98), (200, 11, 47), (196, 196, 196), (255, 230, 0), (255, 98, 98),
                    (24, 242, 125), (89, 106, 255), (237, 48, 139), (201, 255, 132), (19, 136, 0)]
    screen = pygame.display.set_mode(size)
    screen.fill(backgroundColor)
    background = pygame.Surface((width, height))
    background.fill(backgroundColor)
    drawAACircle(background, center, lCircleRadius,
                 backgroundColor, lCircleStroke, primaryColor)
    notesPressed = 0
    imageDir = os.path.join(
        os.path.dirname(__file__), 'images')
    sleepImage = pygame.image.load(imageDir + "/sleeping.png")
    sleepImageSize = sleepImage.get_rect().size

    mixImage = pygame.image.load(imageDir + "/mix.png")
    mixImageSize = mixImage.get_rect().size

    recycleImage = pygame.image.load(imageDir + "/recycle.png")
    recycleImageSize = recycleImage.get_rect().size

    def update_fps():
        fps = str(round(clock.get_fps()))
        print("fps: ", fps)

    def getPosOnCircle(position):
        x = lCircleRadius * math.cos(position * circleFactor) + center[0]
        y = lCircleRadius * math.sin(position * circleFactor) + center[1]
        return (round(x), round(y))

    def drawDetectionCircle(obj):
        bbox = obj.bbox.scale(2, 1.5)
        pos = getPosOnCircle((bbox.xmin+bbox.xmax)/2)
        circleColor = colorIdArray[obj.id]
        if synthMode == "Mix":
            drawAALine(pos, center, primaryColor, lCircleStroke/2)
        drawAACircle(screen, pos, round(sCircleRadius - sCircleRadius / 2 +  (sCircleRadius * (obj.score - mixModeVal/100))), circleColor,
                     sCircleStroke, backgroundColor)

    def drawArpModeLine():
        xPosition = (stepInArp / 16) * (inference_size[0]*2)
        posOnCircle = getPosOnCircle(xPosition)
        drawAALine(posOnCircle, center, primaryColor, lCircleStroke/2)

    animationLength = 10
    animationArray = BackEaseInOut(start=0, end=10, duration=animationLength)
    posInAnimation = 0

    def drawStateModal():
        if (time.time() - lastTimeEncoderPressed) < 1:
            if synthMode == "Mix":
                screen.blit(
                    mixImage, (center[0]-(mixImageSize[0]/2), center[1]-(mixImageSize[1]/2)))
            if synthMode == "Arp":
                screen.blit(
                    recycleImage, (center[0]-(recycleImageSize[0]/2), center[1]-(recycleImageSize[1]/2)))
        if detectionPaused:
            screen.blit(
                sleepImage, (center[0]-(sleepImageSize[0]/2), center[1]-(sleepImageSize[1]/2)))

    def drawMiddleCircle():
        if notesPressed > 0:
            nonlocal posInAnimation
            posInAnimation = min(posInAnimation + 1, animationLength)
        else:
            posInAnimation = max(posInAnimation - 1, 0)
        drawAACircle(screen, center, sCircleRadius + round(animationArray.ease(
            posInAnimation)), backgroundColor, lCircleStroke, primaryColor)

    def mainDrawLoop():
        while 1:
            screen.blit(background, (0, 0))
            if not detectionPaused and (time.time() - lastTimeClicked) > 30:
                pauseDetection()

            for msg in port.iter_pending():
                nonlocal notesPressed
                if msg.type == "note_on":
                    notesPressed += 1
                    resumeDetection()
                if msg.type == "note_off":
                    notesPressed = max(notesPressed - 1, 0)
                    resumeDetection()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            if not detectionPaused:
                for index, obj in enumerate(objs):
                    drawDetectionCircle(obj)

                if synthMode == "Arp":
                    drawArpModeLine()
                drawMiddleCircle()
                clock.tick(60)
            drawStateModal()
            if detectionPaused:
                clock.tick(1)
            
            pygame.display.flip()
        pygame.quit()

    mainDrawLoopThread = threading.Thread(target=mainDrawLoop)
    mainDrawLoopThread.start()


if __name__ == '__main__':
    main()
