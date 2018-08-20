
def executionTrace(traceFileName):
    try:
        traceFile = open(traceFileName)
    except IOError, e:
        print "*** file open error:", e
    else:
        trace = []
        for eachLines in traceFile:
            eachLine = eachLines.strip()
            if len(eachLine) != 0:
                trace.append(eachLine)
        traceFile.close()
        return trace

if __name__ == '__main__':
    pass