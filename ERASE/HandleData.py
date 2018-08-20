
import os
from ExeTrace import executionTrace

def fileNameAbstract(elementStr):
    elements = elementStr.split("#")
    fileName = elements[0].strip()
    return fileName

def callRetAbstract(elementStr):
    elements = elementStr.split("#")
    callRet = elements[2].strip()
    return callRet

def handleData(appName, trace, dataFile):
    traceIndex = 0
    traceLen = len(trace)
    data = executionTrace(dataFile)
    dataIndex = 0
    dataLen = len(data)
    # indicate whether the main function is finished
    # solve the problem line 388 atexit in find.c of findutils-4.2.18
    # atexit will call a function after the exit of main
    mainFinished = False
    # record the last filename and linenumber in the data file 
    lastDataFile = ""
    lastDataLine = ""
    # record the filename in data trace
    fileName = ""
    fileNameList = []
    # the list of data trace, which has been added the function call and return
    reDataTrace = []
    while traceIndex < traceLen or dataIndex < dataLen:
        # dataIndex >= dataLen
        # if so, we directly append all function calls and returns 
        dataNotFinished = False
        # whether we find new data line that should be matched
        # at this time, data trace may not be over, but there is no new line
        # for example, we now at "diff.c#777#R#0xbfdc98ac#0x00000001", but there is still "diff.c#777#W#0xbfdc9850#0x00000001"
        # diff.c#777#R#0xbfdc98ac#0x00000001
        # diff.c#777#W#0xbfdc9850#0x00000001
        # file end
        newLine = False
        # find a read or written memory that is in different statements
        while dataIndex < dataLen:
            # we add a data element in reDataTrace
            dataNotFinished = True
            dataEle = data[dataIndex] 
            reDataTrace.append(dataEle)
            dataItem = dataEle.split("#")
            if cmp(lastDataFile, dataItem[0]) == 0 and cmp(lastDataLine, dataItem[1]) == 0:
                dataIndex = dataIndex + 1
            else:
                newLine = True
                lastDataFile = dataItem[0]
                lastDataLine = dataItem[1]
                break
        # find a line that matches the candidate data trace
        while traceIndex < traceLen:
            traceEle = trace[traceIndex]                            
            if traceEle.find("#") != -1:  
                callRet = callRetAbstract(traceEle)
                if callRet.find("C") != -1:
                    fileName = fileNameAbstract(traceEle)
                    fileNameList.append(fileName)
                elif callRet.find("R") != -1:
                    fileNameList.pop()
                    if len(fileNameList) != 0:
                        fileName = fileNameList[-1]
                    else:
                        # it only happens at the "...#main#R"
                        fileName = ""
                reLineEle = traceEle.replace("#", "$")
                callLineNum = "-1"
                if dataNotFinished == True:
                    if callRet.find("C") != -1:
                        if traceIndex > 0:
                            callLineNum = trace[traceIndex-1]
                        reLineEle = "%s$%s" % (reLineEle, callLineNum)   
                    if newLine == True:
                        reDataTrace.insert(len(reDataTrace)-1, reLineEle)
                        reLineEleItem = reLineEle.split("$")
                        if cmp(reLineEleItem[1], "main") == 0 and cmp(reLineEleItem[2], "R") == 0:
                            reDataTrace.pop()
                            mainFinished = True  
                            break
                    else: 
                        reDataTrace.append(reLineEle)
                        reLineEleItem = reLineEle.split("$")
                        if cmp(reLineEleItem[1], "main") == 0 and cmp(reLineEleItem[2], "R") == 0:
                            mainFinished = True  
                            break
                else:
                    if callRet.find("C") != -1:
                        if traceIndex > 0:
                            callLineNum = trace[traceIndex-1]
                        reLineEle = "%s$%s" % (reLineEle, callLineNum)   
                    reDataTrace.append(reLineEle)    
                    reLineEleItem = reLineEle.split("$")
                    if cmp(reLineEleItem[1], "main") == 0 and cmp(reLineEleItem[2], "R") == 0:
                        mainFinished = True  
                        break
            else:
                if dataNotFinished == True:
                    # find the matched trace line for the data line
                    if cmp(lastDataFile, fileName) == 0 and cmp(lastDataLine, traceEle) == 0:
                        break           
            traceIndex = traceIndex + 1             
        traceIndex = traceIndex + 1
        dataIndex = dataIndex + 1
        if mainFinished == True:
            break
    # modify the permission of the file such as to rewrite it 
    chmodCmd = "chmod 666 %s" % (dataFile)
    os.system("echo 206|sudo -S %s" % (chmodCmd)) 
    try:
        reDataFile = open(dataFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        for eachData in reDataTrace:
            reDataFile.write(eachData + "\n")
        reDataFile.close()

if __name__ == '__main__':
    pass