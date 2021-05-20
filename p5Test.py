# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
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

import os


#from pyky040 import pyky040
import threading

from p5 import *

synthMode = "Mix"
mixModeVal = 50
arpModeVal = 120
stepInArp = 0
objs = []


    
   
  
    
    # # Rotary encoder setup
    # def encoderInc(scale_position):
    #     global synthMode
    #     global mixModeVal
    #     global arpModeVal
    #     if synthMode == "Mix":
    #         mixModeVal = min(mixModeVal+1, 100)
    #     if synthMode == "Arp":
    #         arpModeVal += 1
    #         os.system("echo '" + str(arpModeVal) + "" + "' | pdsend 3001")
    #     print('Encoder incremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )

    #     print('Encoder incremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )
    # def encoderDec(scale_position):
    #     global synthMode
    #     global mixModeVal
    #     global arpModeVal
    #     if synthMode == "Mix":
    #         mixModeVal = max(mixModeVal-1, 0)
    #     if synthMode == "Arp":
    #         arpModeVal -= 1
    #         os.system("echo '" + str(arpModeVal) + "" + "' | pdsend 3001")
    #     print('Encoder decremented mixVal: {}'.format(mixModeVal) + ' arpVal: {}'.format(arpModeVal) )
    # def encoderClicked():
    #     global synthMode
    #     if synthMode == "Mix":
    #         synthMode = "Arp"
          
    #     else:
    #         synthMode = "Mix"
    #     os.system("echo '" + synthMode + "" + "' | pdsend 3002")
    #     print('Encoder clicked currentMode: {}'.format(synthMode))
    # os.system("echo '" + synthMode + "" + "' | pdsend 3002")
    # my_encoder = pyky040.Encoder(CLK=4, DT=17, SW=27)
    # my_encoder.setup(inc_callback=encoderInc, dec_callback=encoderDec, sw_callback=encoderClicked)

    # my_thread = threading.Thread(target=my_encoder.watch)
    # my_thread.start()




if __name__ == '__main__':
    width = 480
    height = width
    phase = 0
    zoff = 0
    def setup():
            size(width, height)
    def decimal_range(start, stop, increment):
        while start <= stop: # and not math.isclose(start, stop): Py>3.5
            yield start
            start += increment

    def draw():
        text(str(frame_rate), 0, 10)
        fill(0,10)
        rect(0, 0, width, height)
        translate(width / 2, height / 2)
        stroke(255)
        stroke_weight(2)
        no_fill()
        begin_shape()
        noiseMax = 1.2
        for a in decimal_range(0, TWO_PI, radians(6)):
            global phase
            global zoff
            xoff = remap(cos(a + phase), [-1, 1], [0, noiseMax])
            yoff = remap(sin(a + phase), [-1, 1], [0, noiseMax])
            r = remap(noise(xoff, yoff, zoff), [0, 1], [100, height / 2])
            x = r * cos(a)
            y = r * sin(a)
            vertex(x, y)
        
        end_shape(CLOSE)
        phase = phase + 0.003
        zoff = zoff + 0.01
        
       
    run()