
def callRetAbstract(elementStr):
    elements = elementStr.split("#")
    callRet = elements[2].strip()
    return callRet

def fileNameAbstract(elementStr):
    elements = elementStr.split("#")
    fileName = elements[0].strip()
    return fileName

def functionNameAbstract(elementStr):
    elements = elementStr.split("#")
    functionName = elements[1].strip()
    return functionName

# identify the line number of the function calling
# it is used to guide the codedata analysis of pin tool    
def LNOfFunctionCalling(appName, trace, LNFile, renameMap):
    try:
        LNCalling = open(LNFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        LNCallingSet = set()
        lastEle = "-1"
        fileName = "main.c"
        fileNameList = []
        for eachEle in trace:
            if eachEle.find("#") != -1:
                callRet = callRetAbstract(eachEle)
                if callRet.find("C") != -1:
                    # fileName and lastEle is the information at the last element in trace
                    LNCallingStr = "%s:%s\n" % (fileName, lastEle)
                    if LNCallingStr not in LNCallingSet:    
                        if LNCallingStr in renameMap:
                            LNCallingStr = renameMap[LNCallingStr]                       
                        LNCalling.write(LNCallingStr)
                        LNCallingSet.add(LNCallingStr)
                    fileName = fileNameAbstract(eachEle)
                    fileNameList.append(fileName)
                elif callRet.find("R") != -1:
                    fileNameList.pop()
                    if len(fileNameList) != 0:
                        fileName = fileNameList[-1]
                    else:
                        # it only happens at the "...#main#R"
                        fileName = "main.c"
                    functionName = functionNameAbstract(eachEle)
                    if cmp(functionName, "main") == 0:
                        break
            lastEle = eachEle 
        LNCalling.close()

if __name__ == '__main__':
    pass