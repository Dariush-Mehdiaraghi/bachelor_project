import os
foundObjs = "2 "
# foundObjs += str(1) + " " + str(0.0631249) + " "
# foundObjs += str(0) + " " + str(0.03) + " "
# foundObjs += str(2) + " " + str(0.09) + " "
# foundObjs += str(9) + " " + str(0.9) + " "
# foundObjs += str(3) + " " + str(0.4) + " "
# foundObjs += str(3) + " " + str(0.5) + " "
foundObjs += str(0) + " " + str(0.0631249) + " "
foundObjs += str(0) + " " + str(0.03) + " "
foundObjs += str(0) + " " + str(0.09) + " "
foundObjs += str(0) + " " + str(0.9) + " "
foundObjs += str(0) + " " + str(0.4) + " "
foundObjs += str(0) + " " + str(0.5) + " "
#foundObjs += str(0) + " " + str(0) + " "
os.system("echo '" + str(foundObjs) + ";" + "' | pdsend 3000")
#os.system("echo '" + str(1)  + " " + str(0.222) + ";" + "' | pdsend 3000")
