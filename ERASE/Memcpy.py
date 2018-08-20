
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

# find the key word "memcpy"
def findKeywords(eachLine, keyWord, delimiterWords):
    keyWordLen = len(keyWord)
    startPoint = 0
    while True:
        wordIndex = eachLine.find(keyWord, startPoint)
        # It does not find the key word
        if wordIndex == -1:
            return False
        elif wordIndex == 0:
            # the keyword is the first word in eachLine
            if len(eachLine) > keyWordLen:
                nextChar = eachLine[keyWordLen]
                if nextChar in delimiterWords:
                    return True
            else:
                # eachLine is the key word
                return True
        else:
            previousChar = eachLine[wordIndex-1]
            if  previousChar in delimiterWords:
                if len(eachLine) > (wordIndex + keyWordLen):
                    nextChar = eachLine[wordIndex + keyWordLen]
                    if nextChar in delimiterWords:
                        return True
                else:
                    # Key word is the last word
                    return True
        startPoint = wordIndex + 1  
    return False   
    
def staticMemcpyFile(filePath, staticMemcpySet):
    # the delimiter for the key word    
    delimiterWords = set()
    delimiterWords.add("\t")
    delimiterWords.add("\n")
    delimiterWords.add("\v")
    delimiterWords.add("\f")
    delimiterWords.add("\r")
    delimiterWords.add("\b")
    delimiterWords.add(" ")
    delimiterWords.add("(")
    delimiterWords.add(")")
    delimiterWords.add("{")
    delimiterWords.add("}")
    delimiterWords.add("[")
    delimiterWords.add("]")
    delimiterWords.add(";")
    delimiterWords.add(":")
    delimiterWords.add(",")
    try:
        fileContent = open(filePath)
    except IOError, e:
        print "*** file open error:", e
    else:
        fileName = os.path.basename(filePath)
        for (num, eachLine) in enumerate(fileContent):
            memcpyIndex = findKeywords(eachLine, "memcpy", delimiterWords)
            if memcpyIndex == True:
                memcpyLine = "%s:%d" % (fileName, num+1)
                staticMemcpySet.add(memcpyLine)

def StaticMemcpy(directory, staticMemcpySet):  
    for (parent, dirNames, fileNames) in os.walk(directory):
        for dirName in dirNames:
            StaticMemcpy(os.path.join(parent, dirName), staticMemcpySet)
        for fileName in fileNames:
            fileExt = fileName[fileName.rfind("."):]
            if fileExt == ".c" or fileExt == ".cpp" or fileExt == ".h" or fileExt == ".C" or fileExt == ".CPP" or fileExt == ".H":
                staticMemcpyFile(os.path.join(parent, fileName), staticMemcpySet)

def valueComputationForward(data, dataIndex, addrStr):
    addrValue = long(addrStr, 16)
    dataLen = len(data)
    while dataIndex < dataLen:
        dataEle = data[dataIndex]
        dataItem = dataEle.split("#")
        address = long(dataItem[3], 16)
        if addrValue == address:
            return dataItem[4]
        dataIndex = dataIndex + 1
    return "-1"
                
def handleMemcpyData(dataFile, memcpySet):
    data = executionTrace(dataFile)
    dataLen = len(data)
    dataIndex = dataLen - 1
    # the list of data trace, which has been added memory read/written
    reDataTrace = []
    while dataIndex >= 0:
        dataEle = data[dataIndex] 
        dataItem = dataEle.split("#")
        dataLine = dataItem[0] + ":" + dataItem[1]
        if dataLine in memcpySet:
            lastDataLine = dataLine
            memcpyList = []
            memcpyList.append(dataItem)
            while True:
                dataIndex = dataIndex - 1
                dataEle = data[dataIndex]
                dataItem = dataEle.split("#")
                dataLine = dataItem[0] + ":" + dataItem[1] 
                if cmp(lastDataLine, dataLine) != 0:
                    dataIndex = dataIndex + 1
                    break
                memcpyList.append(dataItem)
            writtenList = []
            for eachMem in memcpyList:
                if cmp(eachMem[2], "W") == 0:
                    writtenList.append(eachMem)
            if len(writtenList) == 3:
                size_n = long(writtenList[2][4], 16)
                src_addr = long(writtenList[1][4], 16)
                dst_addr = long(writtenList[0][4], 16)
                for i in range(size_n):
                    srcAddr = src_addr + i
                    # there is character "L" in the end of srcAddr
                    srcAddrStr = "%s" % (hex(srcAddr))
                    srcAddrStr = srcAddrStr[0:len(srcAddrStr)-1]
                    dstAddr = dst_addr + i
                    dstAddrStr = "%s" % (hex(dstAddr))
                    dstAddrStr = dstAddrStr[0:len(dstAddrStr)-1]
                    value = valueComputationForward(data, dataIndex, dstAddrStr)
                    readEle = [writtenList[1][0], writtenList[1][1], "R", srcAddrStr, value]
                    writtenEle = [writtenList[0][0], writtenList[0][1], "W", dstAddrStr, value]
                    memcpyList.insert(0, readEle)
                    memcpyList.insert(0, writtenEle)
            for eachMem in memcpyList:
                reDataTrace.append(eachMem[0] + "#" + eachMem[1] + "#" + eachMem[2] + "#" + eachMem[3] + "#" + eachMem[4])
        else:
            reDataTrace.append(dataEle)                      
        dataIndex = dataIndex - 1   
    # modify the permission of the file such as to rewrite it 
    chmodCmd = "chmod 666 %s" % (dataFile)
    os.system("echo 206|sudo -S %s" % (chmodCmd)) 
    try:
        reDataFile = open(dataFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        reDataLen = len(reDataTrace)
        reDataIndex = reDataLen - 1
        while reDataIndex >= 0:
            eachData = reDataTrace[reDataIndex]
            reDataFile.write(eachData + "\n")
            reDataIndex = reDataIndex - 1
        reDataFile.close()
    
       
if __name__ == '__main__':
    pass