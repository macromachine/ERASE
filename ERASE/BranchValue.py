
import string

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

# Compute the branch value of a conditional statement
def branchValue(CDGMap, trace):
    # CDGMap is the static control dependence:<fileName:lineNumber, Set(fileName:lineNumber)>
    # if the node is not dependent on other node, it would not appear in CDGMap
    # reversed control dependence graph
    reversedCDG = {}
    for (key, value) in CDGMap.items():
        for eachValue in value:
            if eachValue in reversedCDG:
                mapValue = reversedCDG[eachValue]
                mapValue.add(key)
            else:
                mapValue = set()
                mapValue.add(key)
                reversedCDG[eachValue] = mapValue
    trueBranchMap = {}
    for (key, value) in reversedCDG.items():
        keyItem = key.split(":")
        keyInt = string.atoi(keyItem[1])
        # used for do{...}while()
        # the statement that is most far away from the key is the target statement of true branch
        beforeValue = "file.c:100000"
        # used for other cases, for example for(){...} and if(){...}
        # the statement that is most near the key is the target statement of true branch
        afterValue = "file.c:100000"
        for eachValue in value:
            valueItem = eachValue.split(":")
            beforeItem = beforeValue.split(":")
            afterItem = afterValue.split(":")
            valueInt = string.atoi(valueItem[1])
            beforeInt = string.atoi(beforeItem[1])
            afterInt = string.atoi(afterItem[1])
            # only consider the statements after the key statement
            # it is possible that keyInt equals to the valueInt
            # if so, it is the loop situation
            if keyInt < valueInt and valueInt < afterInt:
                afterValue = eachValue
            # used to consider the case that is before the key statement
            if valueInt < beforeInt:
                beforeValue = eachValue 
        # it is not the case do{...}while()
        if cmp(afterValue, "file.c:100000") != 0:
            trueBranchMap[key] = afterValue
        else:
            trueBranchMap[key] = beforeValue
        
    branchValueMap = {}
    fileName = ""
    fileNameList = []    
    for traceIndex in range(0, len(trace)):
        master = trace[traceIndex]
        if master.find("#") != -1:
            callRet = callRetAbstract(master)
            if callRet.find("C") != -1:
                fileName = fileNameAbstract(master)
                fileNameList.append(fileName)
            elif callRet.find("R") != -1:
                fileNameList.pop()
                if len(fileNameList) != 0:
                    fileName = fileNameList[-1]
                else:
                    fileName = ""
                functionName = functionNameAbstract(master)
                if cmp(functionName, "main") == 0:
                    return branchValueMap
            continue
        masterStr = "%s:%s" % (fileName, master)
        if masterStr in trueBranchMap:
            if traceIndex+1 < len(trace):
                slave = trace[traceIndex+1]
                if slave.find("#") == -1:
                    slaveStr = "%s:%s" % (fileName, slave)
                    trueBranchStr = trueBranchMap[masterStr]
                    if cmp(slaveStr, trueBranchStr) == 0:
                        branchValueMap[traceIndex] = "T"
                    else:
                        branchValueMap[traceIndex] = "F"
                else:
                    # maybe there is no statement in the else branch
                    branchValueMap[traceIndex] = "F"
            else:
                # maybe there is no statement in the else branch
                branchValueMap[traceIndex] = "F"
    return branchValueMap               
        
if __name__ == '__main__':
    True
    
