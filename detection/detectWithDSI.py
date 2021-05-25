# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo that runs object detection on camera frames using OpenCV.
TEST_DATA=../all_models
Run face detection model:
python3 detect.py \
  --model ${TEST_DATA}/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite
Run coco model:
python3 detect.py \
  --model ${TEST_DATA}/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ${TEST_DATA}/coco_labels.txt
"""
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
import time
import socket
import sys
from p5 import *

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
           # append_objs_to_img(cv2_im, inference_size, objs, labels)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    detectObjsThread = threading.Thread(target=detectObjs)
    detectObjsThread.start()
    print("after starting objs thread")

if __name__ == '__main__':
    main()
    def setup():
            size(480, 480)
            no_stroke()
            background(0)
            

    def draw():
        background(0,0,0)

      
        text(str(frame_rate), 100, 100)
        
        for index, obj in enumerate(objs):
            bbox = obj.bbox.scale(2, 1.5)
            x0, y0 = int(bbox.xmin), int(bbox.ymin)
            x1, y1 = int(bbox.xmax), int(bbox.ymax)
            position = ((x0+x1)/2)

            text(str(labels.get(obj.id, obj.id)), position, 240 )

       
    def key_pressed(event):
        background(204)   
    run()