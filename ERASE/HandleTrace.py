
import os
from ExeTrace import executionTrace

def fileNameAbstract(elementStr):
    elements = elementStr.split("#")
    fileName = elements[0].strip()
    return fileName

def functionNameAbstract(elementStr):
    elements = elementStr.split("#")
    functionName = elements[1].strip()
    return functionName

def callRetAbstract(elementStr):
    elements = elementStr.split("#")
    callRet = elements[2].strip()
    return callRet


def handleTrace(appName, traceFileName):               
    trace = executionTrace(traceFileName)
    # change the privilege of the file such that we can write some into it
    chmodCmd = "chmod 666 %s" % (traceFileName)
    os.system("echo 206|sudo -S %s" % (chmodCmd))
    try:
        reTraceFile = open(traceFileName, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        # Simulate the function call stack, used to find the file name
        fileNameList = []   
        functionNameList = [] 
        # the list which indicates whether fileName and functionName is added by our analysis
        # this list is corresponding to fileNameList and functionNameList
        # in the program gettext_1, multiple different function is called by system API
        addEleList = []
        # indicate whether the main function is finished
        # solve the problem line 388 atexit in find.c of findutils-4.2.18
        # atexit will call a function after the exit of main
        mainFinished = False
        lastEle = ""
        lastAddEle = ""
        firstLineOfFunction = set()
        traceIndex = 0
        traceLen = len(trace)
        while traceIndex < traceLen:
            traceEle = trace[traceIndex]
            if traceEle.find("#") != -1:
                # determine it is a function call or return
                callRet = callRetAbstract(traceEle)
                if callRet.find("C") != -1:
                    fileName = fileNameAbstract(traceEle)
                    fileNameList.append(fileName)
                    functionName = functionNameAbstract(traceEle)
                    functionNameList.append(functionName)
                    addEleList.append(lastEle)
                    if traceIndex+1 < traceLen:
                        nextEle = trace[traceIndex+1]
                        firstLineOfFunction.add(nextEle)
                elif callRet.find("R") != -1:
                    # delete an function return, because it may be added due to system calling
                    # for example, in find_b
                    # qsort(costlookup, sizeof(costlookup)/sizeof(costlookup[0]), sizeof(costlookup[0]), cost_table_comparison);
                    # qsort is system call, but it can call "cost_table_comparison" multiple times, and the function call points that
                    # are not the first time has no the corresponding function call point in the trace
                    if traceIndex+1 < traceLen:
                        nextEle = trace[traceIndex+1]
                        if nextEle in firstLineOfFunction:
                            if nextEle.find(":") != -1 and lastEle.find(":") != -1:
                                lastItem = lastEle.split(":")
                                nextItem = nextEle.split(":")
                                if cmp(lastItem[0], nextItem[0]) == 0 and cmp(lastItem[1], nextItem[1]) == 0:
                                    traceIndex = traceIndex + 1
                                    continue
                    fileNameList.pop()
                    functionNameList.pop()
                    lastAddEle = addEleList.pop()
                    # solve the problem line 388 atexit in find.c of findutils-4.2.18
                    # atexit will call a function after the exit of main
                    functionName = functionNameAbstract(traceEle)
                    if cmp(functionName, "main") == 0:
                        mainFinished = True    
                reTraceFile.write(traceEle + "\n")
            elif traceEle.find(":") != -1:
                traceItem = traceEle.split(":")
                # add the extra function calling, because it may be missed due to system calling
                # for example, in find_b
                # qsort(costlookup, sizeof(costlookup)/sizeof(costlookup[0]), sizeof(costlookup[0]), cost_table_comparison);
                # qsort is system call, but it can call "cost_table_comparison"
                if lastEle.find(":") != -1:
                    lastItem = lastEle.split(":")
                    if cmp(lastItem[0], traceItem[0]) != 0 or cmp(lastItem[1], traceItem[1]) != 0:
                        addedEle = "%s#%s#C" % (traceItem[0], traceItem[1])
                        reTraceFile.write(addedEle + "\n")
                        fileNameList.append(traceItem[0])
                        functionNameList.append(traceItem[1]) 
                        addEleList.append(lastEle)
                        firstLineOfFunction.add(traceEle)
                elif lastEle.find("#") != -1:
                    lastItem = lastEle.split("#")
                    if cmp(lastItem[2], "R") == 0:
                        lastAddItem = lastAddEle.split(":")
                        if cmp(lastAddItem[0], traceItem[0]) != 0 or cmp(lastAddItem[1], traceItem[1]) != 0:
                            reTraceFile.write(lastAddItem[2] + "\n")
                            addedEle = "%s#%s#C" % (traceItem[0], traceItem[1])
                            reTraceFile.write(addedEle + "\n")
                            fileNameList.append(traceItem[0])
                            functionNameList.append(traceItem[1]) 
                            addEleList.append(lastAddEle)
                            firstLineOfFunction.add(traceEle)
                reTraceFile.write(traceItem[2] + "\n")        
            lastEle = traceEle
            traceIndex = traceIndex + 1
            if mainFinished == True:
                break
        # handle the case that the program is exited through the exit(-1)
        # if program is returned with exit(-1), it would not execute the remaining statements
        stackIndex = len(fileNameList) -1
        while stackIndex >= 0:
            fileName = fileNameList.pop()
            functionName = functionNameList.pop()
            stackStr = "%s#%s#R" % (fileName, functionName)
            reTraceFile.write(stackStr + "\n")
            stackIndex = stackIndex - 1               
        reTraceFile.close()

if __name__ == '__main__':
    pass