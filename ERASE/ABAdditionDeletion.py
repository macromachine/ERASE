
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

# compute the immediately before/next statement of an added/deleted statement
def afterBeforeStatement(addDelSet, fileLinesMap):
    # the form is <fileName:lineNumber, [fileName:lineNumber, fileName:lineNumber]>
    aBStatement = {}
    for eachAddDel in addDelSet:
        eachItem = eachAddDel.split(":")
        fileName = eachItem[0]
        lineNumber = eachItem[1]
        if fileName in fileLinesMap:
            lineSet = fileLinesMap[fileName]
            if lineNumber in lineSet:
                lineInt = int(lineNumber)
                beforeLine = "0"
                # the distance from the target line
                # which is before the target line
                bLeastDistance = 1000000
                afterLine = "1000000"
                # the distance from the target line
                # which is after the target line
                aLeastDistance = 1000000
                for eachLine in lineSet:
                    eachInt = int(eachLine)
                    if eachInt > lineInt:
                        afterDistance = eachInt - lineInt
                        if afterDistance < aLeastDistance:
                            aLeastDistance = afterDistance
                            afterLine = eachLine
                    # we do not consider the equivalence, because it is itself
                    elif eachInt < lineInt:
                        beforeDistance = lineInt - eachInt
                        if beforeDistance < bLeastDistance:
                            bLeastDistance = beforeDistance
                            beforeLine = eachLine 
                afterLineStr = "%s:%s" % (fileName, afterLine)
                beforeLineStr = "%s:%s" % (fileName, beforeLine)
                aBStatement[eachAddDel] = [beforeLineStr, afterLineStr]        
    return aBStatement                
                
# compute the immediately before/next non-added or non-deleted statement, which may be modified statement, 
# of an added/deleted statement
def reComputeAB(aBStatement):
    for eachStatement in aBStatement:
        eachValue = aBStatement[eachStatement]
        beforeStatement = eachValue[0]
        afterStatement = eachValue[1]
        while True:
            if beforeStatement in aBStatement:
                beforeStatement = aBStatement[beforeStatement][0]
            else:
                break
        while True:
            if afterStatement in aBStatement:
                afterStatement = aBStatement[afterStatement][1]
            else:
                break
        eachValue[0] = beforeStatement
        eachValue[1] = afterStatement
                       
# compute the added or deleted statements            
def additionDeletionTrace(addDelFile):
    try:
        addDelTrace = open(addDelFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        addDelSet = set()
        for eachLines in addDelTrace:
            eachLine = eachLines.strip()
            element = eachLine.split("#")
            fileName = element[0].strip()
            lineNumber = element[1].strip()
            fileLineStr = "%s:%s" % (fileName, lineNumber)
            addDelSet.add(fileLineStr)
        return addDelSet

# compute the executable statements of a file  
# which avoids the blank lines of a file
def linesInFile(CFGFile):
    try:
        CFGTrace = open(CFGFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        fileLinesMap = {}
        fileName = ""
        for eachLines in CFGTrace:
            eachLine = eachLines.strip()
            if eachLine.find("*") != -1:
                fileName = fileNameStar(eachLine)
            else:
                lineItem = eachLine.split("#")
                if fileName in fileLinesMap:
                    lineSet = fileLinesMap[fileName]
                    lineSet.add(lineItem[-1])
                else:
                    lineSet = set()
                    lineSet.add(lineItem[-1])
                    fileLinesMap[fileName] = lineSet
        return fileLinesMap
    
def afterBeforeInstance(trace, CFGFile, addDelSet, addDelFile):
    # the added or deleted statements
    additionDeletionSet = additionDeletionTrace(addDelFile)
    for eachAddDel in additionDeletionSet:
        addDelSet.add(eachAddDel) 
    # compute the executable statements of a file  
    # which avoids the blank lines of a file
    fileLinesMap = linesInFile(CFGFile)   
    # compute the immediately before/next statement of an added/deleted statement
    # the form is <fileName:lineNumber, [fileName:lineNumber, fileName:lineNumber]>
    staticABStatement = afterBeforeStatement(addDelSet, fileLinesMap)
    # compute the immediately before/next non-added or non-deleted statement, which may be modified statement, 
    # of an added/deleted statement
    reComputeAB(staticABStatement)
    # the form is <index, [fileName:lineNumber, fileName:lineNumber]>
    dynamicABStatement = {}
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
            if lineStr in staticABStatement:
                dynamicABStatement[traceIndex] = staticABStatement[lineStr]
    return dynamicABStatement
    
if __name__ == '__main__':
    True
    