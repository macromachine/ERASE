
import os

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

# find the key word "for" and "while"
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
    
def staticLoopFile(filePath, staticLoopSet):
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
            loopIndex = findKeywords(eachLine, "for", delimiterWords)
            if loopIndex == True:
                loopLine = "%s:%d" % (fileName, num+1)
                staticLoopSet.add(loopLine)
            loopIndex = findKeywords(eachLine, "while", delimiterWords)
            if loopIndex == True:
                loopLine = "%s:%d" % (fileName, num+1)
                staticLoopSet.add(loopLine)

def staticLoop(directory, staticLoopSet):
    for (parent, dirNames, fileNames) in os.walk(directory):
        for dirName in dirNames:
            staticLoop(os.path.join(parent, dirName), staticLoopSet)
        for fileName in fileNames:
            fileExt = fileName[fileName.rfind("."):]
            if fileExt == ".c" or fileExt == ".cpp" or fileExt == ".h" or fileExt == ".C" or fileExt == ".CPP" or fileExt == ".H":
                staticLoopFile(os.path.join(parent, fileName), staticLoopSet)
       
def DynamicLoop(appName, trace, directory):
    staticLoopSet = set()
    staticLoop(directory, staticLoopSet)
    fileName = ""
    fileNameList = []
    dynamicLoopSet = set()
    for traceIndex in range(0, len(trace)):
        traceEle = trace[traceIndex].strip()
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
                functionName = functionNameAbstract(traceEle)
                if cmp(functionName, "main") == 0:
                    break
        else:
            lineStr = "%s:%s" % (fileName, traceEle)
            if lineStr in staticLoopSet:
                dynamicLoopSet.add(traceIndex)
    return dynamicLoopSet
            
if __name__ == '__main__':
    True
    