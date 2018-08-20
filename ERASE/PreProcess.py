
import os
from ExeTrace import executionTrace

def preProcessFileName(appName, traceFile):
    renameMap = {}
    trace = executionTrace(traceFile)
    # change the privilege of the file such that we can write some into it
    chmodCmd = "chmod 666 %s" % (traceFile)
    os.system("echo 206|sudo -S %s" % (chmodCmd))
    try:
        reTrace = open(traceFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:    
        traceIndex = 0
        traceLen = len(trace)
        while traceIndex < traceLen:
            traceEle = trace[traceIndex]
            traceIndex = traceIndex + 1
            if traceEle.find("indent.gperf") != -1:
                reTraceEle = traceEle.replace("indent.gperf", "gperf.c")
                reTrace.write(reTraceEle + "\n")
                traceItem = traceEle.split(":")
                reTraceItem = reTraceEle.split(":")
                if len(traceItem) == 3 and len(reTraceItem) == 3:
                    originalStr = traceItem[0] + ":" + traceItem[2] + "\n"
                    modifiedStr = reTraceItem[0] + ":" + reTraceItem[2] + "\n"
                    renameMap[modifiedStr] = originalStr
            else:
                reTrace.write(traceEle + "\n")
        reTrace.close()
        return renameMap
    