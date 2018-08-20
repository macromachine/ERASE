
import os
from ExeTrace import executionTrace

def deleteTrace(appName, traceFile):
    trace = executionTrace(traceFile)
    # modify the permission of the file such as to rewrite it 
    chmodCmd = "chmod 666 %s" % (traceFile)
    os.system("echo 206|sudo -S %s" % (chmodCmd)) 
    try:
        reTraceFile = open(traceFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        deletionSign = False
        traceIndex = 0
        traceLen = len(trace)
        while traceIndex < traceLen:
            traceEle = trace[traceIndex]
            traceIndex = traceIndex + 1
            if traceEle.find("#") != -1:
                traceItem = traceEle.split("#")
                if cmp(traceItem[0], "closeout.c") == 0 and cmp(traceItem[1], "close_stdout") == 0:
                    if cmp(traceItem[2], "C") == 0:
                        deletionSign = True
                    elif cmp(traceItem[2], "R") == 0:
                        deletionSign = False
                    continue
            if deletionSign == False:
                reTraceFile.write(traceEle + "\n")
        reTraceFile.close()
        
def deleteData(appName, dataFile):
    data = executionTrace(dataFile)
    # modify the permission of the file such as to rewrite it 
    chmodCmd = "chmod 666 %s" % (dataFile)
    os.system("echo 206|sudo -S %s" % (chmodCmd)) 
    try:
        reDataFile = open(dataFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        deletionSign = False
        dataIndex = 0
        dataLen = len(data)
        while dataIndex < dataLen:
            dataEle = data[dataIndex]
            dataIndex = dataIndex + 1
            if dataEle.find("$") != -1:
                dataItem = dataEle.split("#")
                if cmp(dataItem[0], "closeout.c") == 0 and cmp(dataItem[1], "close_stdout") == 0:
                    if cmp(dataItem[2], "C") == 0:
                        deletionSign = True
                    elif cmp(dataItem[2], "R") == 0:
                        deletionSign = False
                    continue
            if deletionSign == False:
                reDataFile.write(dataEle + "\n")
        reDataFile.close()
