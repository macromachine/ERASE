
import os

# change the compile option "CFLAGS = -g -O2" to "CFLAGS = -g -O0"
def getMakeFileList(makeFilePath):
    if os.path.isfile(makeFilePath):
        fileName = os.path.basename(makeFilePath)
        if cmp(fileName, "Makefile") == 0:
            _makeFilePath = os.path.join(os.path.dirname(makeFilePath), "_Makefile")
            try:
                makeFile = open(makeFilePath, "r")
                _makeFile = open(_makeFilePath, "w")
            except IOError, e:
                print "file open error:", e
            else:
                for eachLine in makeFile:
                    if eachLine.find("CFLAGS = -g -O2") != -1:
                        eachLine = eachLine.replace("CFLAGS = -g -O2", "CFLAGS = -g -O0")
                    _makeFile.write(eachLine)
                makeFile.close()
                _makeFile.close()
                os.remove(makeFilePath)
                os.rename(_makeFilePath, makeFilePath)
    elif os.path.isdir(makeFilePath):
        for eachFile in os.listdir(makeFilePath):
            getMakeFileList(os.path.join(makeFilePath, eachFile))

def compileWork(directory, exeDirectory):
    if os.path.exists(exeDirectory) == True:
        os.system("echo 206 | sudo -S rm -r %s" % (exeDirectory))
    os.system("echo 206 | sudo -S mkdir -p %s" % (exeDirectory))
    # change the current workspace
    os.chdir(directory)
    configureCmd = "./configure --prefix=%s" % (exeDirectory)
    os.system(configureCmd)
    # change the compile option "CFLAGS = -g -O2" to "CFLAGS = -g -O0"
    getMakeFileList(directory)
    makeCmd = "make"
    os.system(makeCmd)
    installCmd = "make install"
    os.system("echo 206|sudo -S %s" % (installCmd))

if __name__ == '__main__':
    pass