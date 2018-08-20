
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

def fileNameStar(elementStr):
    eleItem = elementStr.split("*")
    return eleItem[3]

def sourceCodeFile(filePath, sourceCodeSet):
    try:
        programTrace = open(filePath)
    except IOError, e:
        print "*** file open error:", e
    else:
        fileName = os.path.basename(filePath)
        lineNumberSet = []
        for (num, eachLine) in enumerate(programTrace):
            eachLine = eachLine.strip()
            if len(eachLine) != 0:
                lineNumber = num + 1
                lineStr = "%d" % (lineNumber)
                lineNumberSet.append(lineStr)
        programTrace.close()
        sourceCodeSet[fileName] = lineNumberSet
                
# figure out the lines that are not blank in a directory
def sourceCode(directory, sourceCodeSet):
    for (parent, dirNames, fileNames) in os.walk(directory):
        for dirName in dirNames:
            sourceCode(os.path.join(parent, dirName), sourceCodeSet)
        for fileName in fileNames:
            fileExt = fileName[fileName.rfind("."):]
            if fileExt == ".c" or fileExt == ".cpp" or fileExt == ".C" or fileExt == ".CPP":
                sourceCodeFile(os.path.join(parent, fileName), sourceCodeSet)

# Compute the maps of correspondence, the format is <index, set(lineNumber)>
def modificationAlign(appName, srcDirectory, dstDirectory, srcTrace, dstTrace, corresFile):
    # the form is <fileName, set(lineNumber)>
    srcProgramTrace = {}
    sourceCode(srcDirectory, srcProgramTrace)
    dstProgramTrace = {}
    sourceCode(dstDirectory, dstProgramTrace)
    try:
        corresTrace = open(corresFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        # static mapping, the form is <FileName:lineNumber, set(lineNumber)>
        staticSrcToDst = {}
        staticDstToSrc = {}
        # the set(fileName:lineNumber), used to find the deletionSet
        srcModificationSet = set()
        # the form is set(fileName:lineNumber), used to find the additionSet
        dstModificationSet = set()
        # the form is set(fileName:lineNumber)
        # the corresponding statements of the changed statements are blank lines 
        deletionSet = set()
        additionSet = set()
        for eachLines in corresTrace:
            eachLine = eachLines.strip()
            element = eachLine.split("#")
            fileName = element[0].strip()
            srcLine = element[1].strip()
            dstLine = element[2].strip()
            if fileName in srcProgramTrace and fileName in dstProgramTrace:
                srcFileBody = srcProgramTrace[fileName]
                dstFileBody = dstProgramTrace[fileName]
                if srcLine in srcFileBody and dstLine in dstFileBody:
                    srcLineStr = "%s:%s" % (fileName, srcLine)
                    if srcLineStr in staticSrcToDst:
                        mapValue = staticSrcToDst[srcLineStr]
                        mapValue.add(dstLine)
                    else:
                        staticSrcToDst[srcLineStr] = set([dstLine])
                    dstLineStr = "%s:%s" % (fileName, dstLine)   
                    if dstLineStr in staticDstToSrc:
                        mapValue = staticDstToSrc[dstLineStr]
                        mapValue.add(srcLine)
                    else:
                        staticDstToSrc[dstLineStr] = set([srcLine]) 
                if srcLine in srcFileBody:
                    srcLineStr = "%s:%s" % (fileName, srcLine)
                    srcModificationSet.add(srcLineStr)
                if dstLine in dstFileBody:
                    dstLineStr = "%s:%s" % (fileName, dstLine)
                    dstModificationSet.add(dstLineStr)
        # the corresponding statements of the changed statements are blank lines
        for eachSrcModification in srcModificationSet:
            if eachSrcModification not in staticSrcToDst:
                deletionSet.add(eachSrcModification)
        for eachDstModification in dstModificationSet:
            if eachDstModification not in staticDstToSrc:
                additionSet.add(eachDstModification)
        # dynamic mapping, the form is <index, set(lineNumber)>                           
        dynamicSrcToDst = {}
        dynamicDstToSrc = {}
        fileName = ""
        fileNameList = []
        for traceIndex in range(0, len(srcTrace)):
            traceEle = srcTrace[traceIndex]
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
                        fileName = ""
                    functionName = functionNameAbstract(traceEle)
                    if cmp(functionName, "main") == 0:
                        break
            else:
                lineStr = "%s:%s" % (fileName, traceEle)
                if lineStr in staticSrcToDst:
                    dynamicSrcToDst[traceIndex] = staticSrcToDst[lineStr]
        fileName = ""
        fileNameList = []       
        for traceIndex in range(0, len(dstTrace)):
            traceEle = dstTrace[traceIndex]
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
                        fileName = ""
                    functionName = functionNameAbstract(traceEle)
                    if cmp(functionName, "main") == 0:
                        break
            else:
                lineStr = "%s:%s" % (fileName, traceEle)
                if lineStr in staticDstToSrc:
                    dynamicDstToSrc[traceIndex] = staticDstToSrc[lineStr]               
        return (dynamicSrcToDst, dynamicDstToSrc, deletionSet, additionSet)

# Compute the addition/deletion statement instances, the format is set(index)    
def addDelAlign(appName, addDelSet, addDelFile, trace):
    try:
        addDelTrace = open(addDelFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        # static set, the form is set(lineNumber)
        staticAddDelSet = set()
        for eachLine in addDelSet:
            staticAddDelSet.add(eachLine)
        for eachLines in addDelTrace:
            eachLine = eachLines.strip()
            element = eachLine.split("#")
            fileName = element[0].strip()
            srcLine = element[1].strip()
            srcLineStr = "%s:%s" % (fileName, srcLine)
            staticAddDelSet.add(srcLineStr)
        # dynamic set, the form is set(index)      
        dynamicAddDelSet = set()
        fileName = ""
        fileNameList = []
        for traceIndex in range(0, len(trace)):
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
                        fileName = ""
                    functionName = functionNameAbstract(traceEle)
                    if cmp(functionName, "main") == 0:
                        break
            else:
                lineStr = "%s:%s" % (fileName, traceEle)
                if lineStr in staticAddDelSet:
                    dynamicAddDelSet.add(traceIndex)               
        return dynamicAddDelSet  

if __name__ == '__main__':
   True
    