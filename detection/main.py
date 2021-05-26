import sys, pygame, math
from pygame import gfxdraw
import argparse
import cv2
import os



from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference
from pyky040 import pyky040
import threading
import socket


synthMode = "Mix"
mixModeVal = 50
arpModeVal = 120
stepInArp = 0
objs = []
labels = []


def main():
    
    default_model_dir = os.path.join(os.path.dirname(__file__), 'models/bottleDetector') 
    default_model = 'ssdlite_mobiledet_secondRun_edgetpu.tflite'
    default_labels = 'labels.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of categories with highest score to display')
    parser.add_argument('--camera_idx', type=int, help='Index of which video source to use. ', default = 0)
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
    
  
    
    # Rotary encoder setup
    def encoderInc(scale_position):
        global synthMode
        global mixModeVal
        global arpModeVal
        if synthMode == "Mix":
            mixModeVal = min(mixModeVal+1, 100)
        if synthMode == "Arp":
            arpModeVal += 1
            os.system("echo '" + str(arpModeVal) + ";" + "' | pdsend 3001")
        print('Encoder incremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )

        print('Encoder incremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )
    def encoderDec(scale_position):
        global synthMode
        global mixModeVal
        global arpModeVal
        if synthMode == "Mix":
            mixModeVal = max(mixModeVal-1, 0)
        if synthMode == "Arp":
            arpModeVal -= 1
            os.system("echo '" + str(arpModeVal) + ";" + "' | pdsend 3001")
        print('Encoder decremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )
    def encoderClicked():
        global synthMode
        if synthMode == "Mix":
            synthMode = "Arp"
          
        else:
            synthMode = "Mix"
        os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
        print('Encoder clicked currentMode: {}'.format(synthMode))
    os.system("echo '" + synthMode + ";" + "' | pdsend 3002")
    my_encoder = pyky040.Encoder(CLK=4, DT=17, SW=27)
    my_encoder.setup(inc_callback=encoderInc, dec_callback=encoderDec, sw_callback=encoderClicked)

    my_thread = threading.Thread(target=my_encoder.watch)
    my_thread.start()

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

    def detectObjs():
        while cap.isOpened():
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
            scale_x, scale_y = width / inference_size[0], height / inference_size[1]
            foundObjs = ""
            for obj in objs:
                bbox = obj.bbox.scale(scale_x, scale_y)
                x0 = int(bbox.xmin)
                x1 = int(bbox.xmax)
                position= ((x0+x1)/2) / 640 #image_width
                foundObjs += str(obj.id) + " " + str(position) + " "
            os.system("echo '" + str(foundObjs) + ";" + "' | pdsend 3000")
           # append_objs_to_img(cv2_im, inference_size, objs, labels)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    detectObjsThread = threading.Thread(target=detectObjs)
    detectObjsThread.start()

    os.system("echo '" + "120" + ";" + "' | pdsend 3001")
    pygame.init()
    clock = pygame.time.Clock()

    def drawAALine(X0, X1, color, strokeWidth):
        #SO answer by Yannis Assael https://stackoverflow.com/questions/30578068/pygame-draw-anti-aliased-thick-line
        center_L1 = ((X0[0] + X1[0])/ 2, (X0[1] + X1[1])/ 2) 
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
        pygame.gfxdraw.filled_circle(surface, pos[0], pos[1], radius, strokeColor)
        pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius-strokeWidth, color)
        pygame.gfxdraw.filled_circle(surface,  pos[0], pos[1], radius-strokeWidth, color)

    size = width, height = 480, 480
    backgroundColor = (33,33,33)
    center = (round(width/2), round(height/2))
    circleFactor = (math.pi*2) / 640
    sCircleStroke = 12
    sCircleRadius = 35
    lCircleStroke = round(sCircleStroke/2)
    lCircleRadius = round(width/2 - sCircleRadius) 
    primaryColor = (255,255,255)
    colorIdArray = [(255, 202, 98),(200,11,47),(196,196,196), (255,230,0), (255, 98, 98), (24, 242, 125), (89, 106, 255), (237, 48,139), (201,255,132), (19,136,0)]
    screen = pygame.display.set_mode(size)
    screen.fill(backgroundColor)
    background = pygame.Surface((width, height))
    background.fill(backgroundColor)
    drawAACircle(background, center, lCircleRadius, backgroundColor, lCircleStroke, primaryColor)

    def update_fps():
        fps = str(round(clock.get_fps()))
        print("fps: ", fps)

    def drawDetectionCircle(positionX, objID):
        x = lCircleRadius * math.cos(positionX * circleFactor) + center[0]
        y = lCircleRadius * math.sin(positionX * circleFactor) + center[1]
        pos = (round(x), round(y))
        circleColor = colorIdArray[objID]
        drawAALine(pos, center, primaryColor, lCircleStroke/2)
        drawAACircle(screen, pos, sCircleRadius, circleColor, sCircleStroke, backgroundColor)
        
    def drawMiddleCircle():
        drawAACircle(screen, center, sCircleRadius, backgroundColor, lCircleStroke, primaryColor)
    def mainDrawLoop():
        while 1:
        # update_fps()
            screen.blit(background, (0,0))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
            
            for index, obj in enumerate(objs):
                bbox = obj.bbox.scale(2, 1.5)
                drawDetectionCircle(((round(bbox.xmin)+round(bbox.xmax))/2), obj.id)
            drawMiddleCircle()
        # clock.tick(60)
            pygame.display.flip()
        pygame.quit()
    mainDrawLoopThread = threading.Thread(target=mainDrawLoop)
    mainDrawLoopThread.start()
if __name__ == '__main__':
    main()

    