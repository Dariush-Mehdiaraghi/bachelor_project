#!/bin/bash

pd -noadc -nogui -jack -rt /home/patch/bachelor_project/pureDataPatch/Main.pd &
python3 detection/main.py

