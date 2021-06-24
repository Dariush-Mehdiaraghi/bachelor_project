import os
import time
#os.system("/Applications/Pd-0.50-2.app/Contents/MacOS/PD pureDataPatch/Main.pd")
import subprocess
import os
jackStatus = os.system('systemctl status jack')
print("jackstatuuus:", jackStatus)

while 0 != os.system('systemctl status jack'):
    print("waiting...")
    time.sleep(1)
pathToPD = 'pd'
pathToPatch = os.path.join(os.path.dirname(__file__), '../pureDataPatch/Main.pd') 
subprocess.Popen([pathToPD, '-nogui', '-noadc', '-jack', '-rt', pathToPatch])