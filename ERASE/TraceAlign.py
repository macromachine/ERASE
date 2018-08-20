
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

def pointToCallName(trace):
    pointCallName = {}
    for traceIndex in range(0, len(trace)):
        traceEle = trace[traceIndex]
        if traceEle.find("#") != -1:
            callRet = callRetAbstract(traceEle)
            if callRet.find("C") != -1 and traceIndex > 0:
                if traceIndex > 0:
                    functionName = functionNameAbstract(traceEle)
                    pointCallName[traceIndex-1] = functionName;
    return pointCallName      

# the main function is assumed to be called by -1
# call graph, the key of map is calling point, the value of map is function body instances
# the form is <index, [index1, index2 ...]>
def callGraph(trace, startPoint, callG, reversedCallG):
    # the function body instances
    callee = []
    traceIndex = startPoint + 1
    while traceIndex < len(trace):
        traceEle = trace[traceIndex]
        if traceEle.find("#") != -1:
            callRet = callRetAbstract(traceEle)
            if callRet.find("C") != -1:
                # the returned traceIndex is the next instance of the "...#...#R"
                traceIndex = callGraph(trace, traceIndex, callG, reversedCallG)
            elif callRet.find("R") != -1:
                # the function body is finished
                callG[startPoint-1] = callee
                for eachEle in callee:
                    reversedCallG[eachEle] = startPoint-1
                traceIndex = traceIndex + 1
                return traceIndex
        else:
            callee.append(traceIndex)
            traceIndex = traceIndex + 1
    # the function call and return are not matched
    print "Call Graph Error!"        
    return traceIndex

# determine whether srcControlList is correspondent to dstControlList
# srcTraceIndex and srcLoopSet is used to determine whether it is a loop instance
def controlListCompare(srcControlList, dstControlList, srcTraceIndex, dstTraceIndex, srcLoopSet, dstLoopSet):
    srcLen = len(srcControlList)
    dstLen = len(dstControlList)
    # if srcCLLen is less than dstCLLen, srcControlList should be completely matched
    if srcLen < dstLen:
        srcIndex = 0
        dstIndex = 0
        while True:
            # two end conditions
            # the first: dstIndex reaches the end condition
            if dstIndex == dstLen:
                if srcIndex == srcLen:
                    break
                else:
                    return False
            # the second: srcIndex reaches the end condition
            if srcIndex == srcLen:
                while dstIndex < dstLen:
                    dstEle = dstControlList[dstIndex]
                    # after comparison with srcControlList, the left element must be 1
                    if dstEle != 1:
                        return False
                    dstIndex = dstIndex + 1
                break
            # the following is the comparison process
            srcEle = srcControlList[srcIndex]
            dstEle = dstControlList[dstIndex]
            if srcEle != dstEle:
                if dstEle == 1:
                    dstIndex = dstIndex + 1
                else:
                    # the left element is not 1
                    return False
            else:
                # srcEle is equivalent to dstEle
                srcIndex = srcIndex + 1
                dstIndex = dstIndex + 1
    elif srcLen == dstLen:
        for index in range(0, srcLen):
            srcEle = srcControlList[index]
            dstEle = dstControlList[index]
            if srcEle != dstEle:
                return False           
    elif srcLen > dstLen:
        srcIndex = 0
        dstIndex = 0
        while True:
            if srcIndex == srcLen:
                if dstIndex == dstLen:
                    break
                else:
                    return False
            if dstIndex == dstLen:
                while srcIndex < srcLen:
                    srcEle = srcControlList[srcIndex]
                    if srcEle != 1:
                        return False
                    srcIndex = srcIndex + 1
                break
            srcEle = srcControlList[srcIndex]
            dstEle = dstControlList[dstIndex]
            if srcEle != dstEle:
                if srcEle == 1:
                    srcIndex = srcIndex + 1
                else:
                    # the left element is not 1
                    return False
            else:
                # srcEle is equivalent to dstEle
                srcIndex = srcIndex + 1
                dstIndex = dstIndex + 1
    # The case for the criterion statement that is a loop instance
    if srcTraceIndex in srcLoopSet:
        if dstTraceIndex in dstLoopSet:
            # the last element is not equivalent
            if srcLen > 0 and dstLen > 0 and srcControlList[srcLen-1] != dstControlList[dstLen-1]:
                return False
        else:
            # it is the case that the loop instance corresponds the non-loop instance
            # the last loop instance must be 1
            if srcLen > 0 and srcControlList[srcLen-1] != 1:
                return False
    if dstTraceIndex in dstLoopSet:
        if srcTraceIndex in srcLoopSet:
            if srcLen > 0 and dstLen > 0 and srcControlList[srcLen-1] != dstControlList[dstLen-1]:
                return False
        else:
            if dstLen > 0 and dstControlList[dstLen-1] != 1:
                return False 
    # this is the default case         
    return True   

# if bodyELe is a loop instance, it itself is also be included
# the control list is computed in a function, because controlDep does not include the calling dependence
def controlListCalculation(bodyEle, trace, controlDep, loopSet):
    controlList = []
    lastLoopLN = ""
    count = 0
    while True:
        # Only considering the loops, even if-statement is executed multiple times, for example
        # while () {....if(){break...}...}
        if bodyEle in loopSet:
            loopLN = trace[bodyEle]
            if lastLoopLN == "":
                count = count + 1
            elif lastLoopLN == loopLN:
                count = count + 1               
            else:
                controlList.insert(0, count)
                count = 1
            lastLoopLN = loopLN
        if bodyEle in controlDep:
            master = controlDep[bodyEle]
            bodyEle = master
        else:
            # if there is loop that is control dependent on, we here add the first level loop
            # if there is no loop that is control dependent on, we keep controlList empty
            if count > 0:    
                controlList.insert(0, count)
            break
    return controlList 
           
def traceToControlList(trace, callBody, controlDep, loopSet):
    controlListMap = {}
    for bodyIndex in range(0, len(callBody)):
        bodyEle = callBody[bodyIndex]
        controlList = controlListCalculation(bodyEle, trace, controlDep, loopSet)
        controlListMap[bodyEle] = controlList
    return controlListMap

# Compute the alignment of two traces
# Here, we only consider the function calling
# Later, we still add other alignments into these two maps
def traceAlignFunctionPoint(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, srcToDstLN, dstToSrcLN, \
                            srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, dstPureCallSet, srcPureReturnSet, \
                            dstPureReturnSet, srcPointCallName, dstPointCallName, srcCallPoint, dstCallPoint):
    # The body of a function calling   
    srcList = []                 
    srcList_complete = srcCallG[srcCallPoint]
    for eachEle in srcList_complete:
        # only including the instance that is function calling
        if eachEle in srcPointCallName:
            srcList.append(eachEle)
    dstList = []
    dstList_complete = dstCallG[dstCallPoint]
    for eachEle in dstList_complete:
        if eachEle in dstPointCallName:
            dstList.append(eachEle)
    # each element is an index and its control list
    # in fact, the control list only includes the conditional loop statements
    srcControlListMap = traceToControlList(srcTrace, srcList, srcControlDep, srcLoopSet)
    dstControlListMap = traceToControlList(dstTrace, dstList, dstControlDep, dstLoopSet)
    
    for srcIndex in range(0, len(srcList)):
        srcTraceIndex = srcList[srcIndex]
        # the corresponding line numbers
        corresLines = set()
        if srcTraceIndex in srcToDstLN:
            dstLines = srcToDstLN[srcTraceIndex]
            for eachLine in dstLines:
                corresLines.add(eachLine)
        else:
            # in fact, we should not add the deletion instance
            # but, it does not cause any error
            corresLines.add(srcTrace[srcTraceIndex])  
        srcControlList = srcControlListMap[srcTraceIndex] 
        for dstIndex in range(0, len(dstList)):
            dstTraceIndex = dstList[dstIndex]
            dstLine = dstTrace[dstTraceIndex]
            if dstLine in corresLines:
                dstControlList = dstControlListMap[dstTraceIndex]
                # determine whether srcControlList is correspondent to dstControlList
                corresIndex = controlListCompare(srcControlList, dstControlList, srcTraceIndex, dstTraceIndex, srcLoopSet, dstLoopSet)                          
                if corresIndex == True:
                    # for the unmodified statements, we should compare the call level as a statement may call multiple functions
                    # for the modified statements, even if it call multiple functions, we also directly compare because the function calling may be modified
                    if srcTraceIndex not in srcToDstLN.keys() and dstTraceIndex not in dstToSrcLN.keys():
                        srcCallLevel = 0
                        if srcTraceIndex in srcCallReturnBoth:
                            srcCallLevel = srcCallReturnBoth[srcTraceIndex]
                        dstCallLevel = 0
                        if dstTraceIndex in dstCallReturnBoth:
                            dstCallLevel = dstCallReturnBoth[dstTraceIndex]  
                        if srcCallLevel != dstCallLevel:
                            continue       
                    # the pure call point must not correspond to the pure call return point
                    if srcTraceIndex in srcPureCallSet and dstTraceIndex in dstPureReturnSet:
                        continue
                    if srcTraceIndex in srcPureReturnSet and dstTraceIndex in dstPureCallSet:
                        continue
                    # Compute the correspondence between srcList and dstList
                    if srcTraceIndex in srcToDstIndex:
                        srcMapValue = srcToDstIndex[srcTraceIndex]
                        srcMapValue.add(dstTraceIndex)
                    else:
                        srcMapValue = set()
                        srcMapValue.add(dstTraceIndex)
                        srcToDstIndex[srcTraceIndex] = srcMapValue
                    if dstTraceIndex in dstToSrcIndex:
                        dstMapValue = dstToSrcIndex[dstTraceIndex]
                        dstMapValue.add(srcTraceIndex)
                    else:
                        dstMapValue = set()
                        dstMapValue.add(srcTraceIndex)
                        dstToSrcIndex[dstTraceIndex] = dstMapValue   
    # Iteratively align the body instances of a function calling    
    for srcEle in srcList:
        if srcEle in srcToDstIndex:
            # srcEle must be a calling instance
            srcCallName = srcPointCallName[srcEle]
            dstEleSet = srcToDstIndex[srcEle]
            for dstEle in dstEleSet:
                # maybe calling instance corresponds to a general instance
                if dstEle in dstPointCallName and dstEle in dstList:                    
                    dstCallName = dstPointCallName[dstEle]
                    if cmp(srcCallName, dstCallName) == 0:
                        traceAlignFunctionPoint(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, \
                                   srcToDstLN, dstToSrcLN, srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, \
                                   dstPureCallSet, srcPureReturnSet, dstPureReturnSet, srcPointCallName, dstPointCallName, srcEle, dstEle)    

# Compute the alignment of the function body based on the requirement
def traceAlignBody(ele, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, \
                   srcReversedCallG, dstReversedCallG, srcControlDep, dstControlDep, srcToDstLN, dstToSrcLN, \
                   srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, dstPureCallSet, \
                   srcPureReturnSet, dstPureReturnSet):
    # notice that we also align the function call point,because the function call point may correspond the general instance,
    # which has not been computed
    # the element must be in srcReversedCallG
    if ele not in srcReversedCallG:
        # in fact, ele is -1
        return
    callPoint = srcReversedCallG[ele] 
    srcList = srcCallG[callPoint]
    hasComputed = True
    for srcIndex in srcList:
        if srcIndex not in srcToDstIndex:
            hasComputed = False
            break
    # the body alignment has been computed
    if hasComputed == True:
        return        
    if callPoint in srcToDstIndex:
        dstCallPointSet = srcToDstIndex[callPoint]
        for dstCallPoint in dstCallPointSet:
            # the function call point may correspond to the general instance because of modification
            if dstCallPoint not in dstCallG:
                continue
            dstList = dstCallG[dstCallPoint]
            # each element is an index and its control list
            # in fact, the control list only includes the conditional loop statements
            srcControlListMap = traceToControlList(srcTrace, srcList, srcControlDep, srcLoopSet)
            dstControlListMap = traceToControlList(dstTrace, dstList, dstControlDep, dstLoopSet)
            for srcIndex in range(0, len(srcList)):
                srcTraceIndex = srcList[srcIndex]
                # the corresponding line numbers
                corresLines = set()
                if srcTraceIndex in srcToDstLN:
                    dstLines = srcToDstLN[srcTraceIndex]
                    for eachLine in dstLines:
                        corresLines.add(eachLine)
                else:
                    # in fact, we should not add the deletion instance
                    # but, it does not cause any error
                    corresLines.add(srcTrace[srcTraceIndex])  
                srcControlList = srcControlListMap[srcTraceIndex] 
                for dstIndex in range(0, len(dstList)):
                    dstTraceIndex = dstList[dstIndex]
                    dstLine = dstTrace[dstTraceIndex]
                    if dstLine in corresLines:
                        dstControlList = dstControlListMap[dstTraceIndex]
                        # determine whether srcControlList is correspondent to dstControlList
                        corresIndex = controlListCompare(srcControlList, dstControlList, srcTraceIndex, dstTraceIndex, srcLoopSet, dstLoopSet)                          
                        if corresIndex == True:
                            # for the unmodified statements, we should compare the call level as a statement may call multiple functions
                            # for the modified statements, even if it call multiple functions, we also directly compare because the function calling may be modified
                            if srcTraceIndex not in srcToDstLN.keys() and dstTraceIndex not in dstToSrcLN.keys():
                                srcCallLevel = 0
                                if srcTraceIndex in srcCallReturnBoth:
                                    srcCallLevel = srcCallReturnBoth[srcTraceIndex]
                                dstCallLevel = 0
                                if dstTraceIndex in dstCallReturnBoth:
                                    dstCallLevel = dstCallReturnBoth[dstTraceIndex]  
                                if srcCallLevel != dstCallLevel:
                                    continue        
                            # the pure call point must not correspond to the pure call return point
                            if srcTraceIndex in srcPureCallSet and dstTraceIndex in dstPureReturnSet:
                                continue
                            if srcTraceIndex in srcPureReturnSet and dstTraceIndex in dstPureCallSet:
                                continue    
                            # Compute the correspondence between srcList and dstList
                            if srcTraceIndex in srcToDstIndex:
                                srcMapValue = srcToDstIndex[srcTraceIndex]
                                srcMapValue.add(dstTraceIndex)
                            else:
                                srcMapValue = set()
                                srcMapValue.add(dstTraceIndex)
                                srcToDstIndex[srcTraceIndex] = srcMapValue
                            if dstTraceIndex in dstToSrcIndex:
                                dstMapValue = dstToSrcIndex[dstTraceIndex]
                                dstMapValue.add(srcTraceIndex)
                            else:
                                dstMapValue = set()
                                dstMapValue.add(srcTraceIndex)
                                dstToSrcIndex[dstTraceIndex] = dstMapValue 

# Compute the alignment of one element based on the requirement
def traceAlignEle(ele, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, \
                  srcReversedCallG, dstReversedCallG, srcControlDep, dstControlDep, srcToDstLN, dstToSrcLN, \
                  srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, dstPureCallSet, \
                  srcPureReturnSet, dstPureReturnSet, srcPointCallName):
    if ele in srcToDstIndex and ele not in srcPointCallName:
        # the element alignment has been computed
        return  
    # note that we also align the function call point,because the function call point may correspond the general instance,
    # which has not been computed
    # the element must be in srcReversedCallG
    callPoint = srcReversedCallG[ele] 
    srcList = [ele]
    if callPoint in srcToDstIndex:
        dstCallPointSet = srcToDstIndex[callPoint]
        for dstCallPoint in dstCallPointSet:
            # the function call point may correspond to the general instance because of modification
            if dstCallPoint not in dstCallG:
                continue
            dstList = dstCallG[dstCallPoint]
            # each element is an index and its control list
            # in fact, the control list only includes the conditional loop statements
            srcControlListMap = traceToControlList(srcTrace, srcList, srcControlDep, srcLoopSet)
            dstControlListMap = traceToControlList(dstTrace, dstList, dstControlDep, dstLoopSet)
            for srcIndex in range(0, len(srcList)):
                srcTraceIndex = srcList[srcIndex]
                # the corresponding line numbers
                corresLines = set()
                if srcTraceIndex in srcToDstLN:
                    dstLines = srcToDstLN[srcTraceIndex]
                    for eachLine in dstLines:
                        corresLines.add(eachLine)
                else:
                    # in fact, we should not add the deletion instance
                    # but, it does not cause any error
                    corresLines.add(srcTrace[srcTraceIndex])  
                srcControlList = srcControlListMap[srcTraceIndex] 
                for dstIndex in range(0, len(dstList)):
                    dstTraceIndex = dstList[dstIndex]
                    dstLine = dstTrace[dstTraceIndex]
                    if dstLine in corresLines:
                        dstControlList = dstControlListMap[dstTraceIndex]
                        # determine whether srcControlList is correspondent to dstControlList
                        corresIndex = controlListCompare(srcControlList, dstControlList, srcTraceIndex, dstTraceIndex, srcLoopSet, dstLoopSet)                          
                        if corresIndex == True:
                            # for the unmodified statements, we should compare the call level as a statement may call multiple functions
                            # for the modified statements, even if it call multiple functions, we also directly compare because the function calling may be modified
                            if srcTraceIndex not in srcToDstLN.keys() and dstTraceIndex not in dstToSrcLN.keys():
                                srcCallLevel = 0
                                if srcTraceIndex in srcCallReturnBoth:
                                    srcCallLevel = srcCallReturnBoth[srcTraceIndex]
                                dstCallLevel = 0
                                if dstTraceIndex in dstCallReturnBoth:
                                    dstCallLevel = dstCallReturnBoth[dstTraceIndex]  
                                if srcCallLevel != dstCallLevel:
                                    continue        
                            # the pure call point must not correspond to the pure call return point
                            if srcTraceIndex in srcPureCallSet and dstTraceIndex in dstPureReturnSet:
                                continue
                            if srcTraceIndex in srcPureReturnSet and dstTraceIndex in dstPureCallSet:
                                continue    
                            # Compute the correspondence between srcList and dstList
                            if srcTraceIndex in srcToDstIndex:
                                srcMapValue = srcToDstIndex[srcTraceIndex]
                                srcMapValue.add(dstTraceIndex)
                            else:
                                srcMapValue = set()
                                srcMapValue.add(dstTraceIndex)
                                srcToDstIndex[srcTraceIndex] = srcMapValue
                            if dstTraceIndex in dstToSrcIndex:
                                dstMapValue = dstToSrcIndex[dstTraceIndex]
                                dstMapValue.add(srcTraceIndex)
                            else:
                                dstMapValue = set()
                                dstMapValue.add(srcTraceIndex)
                                dstToSrcIndex[dstTraceIndex] = dstMapValue 
                                
# Compute the alignment of two traces
# Later, we still add other alignments into these two maps
def traceAlignProgram(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, srcToDstLN, dstToSrcLN, \
               srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, dstPureCallSet, srcPureReturnSet, \
               dstPureReturnSet, srcPointCallName, dstPointCallName, srcCallPoint, dstCallPoint):
    # The body of a function calling   
    srcList = srcCallG[srcCallPoint]
    dstList = dstCallG[dstCallPoint]
    # each element is an index and its control list
    # in fact, the control list only includes the conditional loop statements
    srcControlListMap = traceToControlList(srcTrace, srcList, srcControlDep, srcLoopSet)
    dstControlListMap = traceToControlList(dstTrace, dstList, dstControlDep, dstLoopSet)
    for srcIndex in range(0, len(srcList)):
        srcTraceIndex = srcList[srcIndex]
        # the corresponding line numbers
        corresLines = set()
        if srcTraceIndex in srcToDstLN:
            dstLines = srcToDstLN[srcTraceIndex]
            for eachLine in dstLines:
                corresLines.add(eachLine)
        else:
            # in fact, we should not add the deletion instance
            # but, it does not cause any error
            corresLines.add(srcTrace[srcTraceIndex])  
        srcControlList = srcControlListMap[srcTraceIndex] 
        for dstIndex in range(0, len(dstList)):
            dstTraceIndex = dstList[dstIndex]
            dstLine = dstTrace[dstTraceIndex]
            if dstLine in corresLines:
                dstControlList = dstControlListMap[dstTraceIndex]
                # determine whether srcControlList is correspondent to dstControlList
                corresIndex = controlListCompare(srcControlList, dstControlList, srcTraceIndex, dstTraceIndex, srcLoopSet, dstLoopSet)                          
                if corresIndex == True:
                    # for the unmodified statements, we should compare the call level as a statement may call multiple functions
                    # for the modified statements, even if it call multiple functions, we also directly compare because the function calling may be modified
                    if srcTraceIndex not in srcToDstLN.keys() and dstTraceIndex not in dstToSrcLN.keys():
                        srcCallLevel = 0
                        if srcTraceIndex in srcCallReturnBoth:
                            srcCallLevel = srcCallReturnBoth[srcTraceIndex]
                        dstCallLevel = 0
                        if dstTraceIndex in dstCallReturnBoth:
                            dstCallLevel = dstCallReturnBoth[dstTraceIndex]  
                        if srcCallLevel != dstCallLevel:
                            continue       
                    # the pure call point must not correspond to the pure call return point
                    if srcTraceIndex in srcPureCallSet and dstTraceIndex in dstPureReturnSet:
                        continue
                    if srcTraceIndex in srcPureReturnSet and dstTraceIndex in dstPureCallSet:
                        continue
                    # Compute the correspondence between srcList and dstList
                    if srcTraceIndex in srcToDstIndex:
                        srcMapValue = srcToDstIndex[srcTraceIndex]
                        srcMapValue.add(dstTraceIndex)
                    else:
                        srcMapValue = set()
                        srcMapValue.add(dstTraceIndex)
                        srcToDstIndex[srcTraceIndex] = srcMapValue
                    if dstTraceIndex in dstToSrcIndex:
                        dstMapValue = dstToSrcIndex[dstTraceIndex]
                        dstMapValue.add(srcTraceIndex)
                    else:
                        dstMapValue = set()
                        dstMapValue.add(srcTraceIndex)
                        dstToSrcIndex[dstTraceIndex] = dstMapValue   
    # Iteratively align the body instances of a function calling    
    for srcEle in srcList:
        if srcEle in srcToDstIndex and srcEle in srcPointCallName:
            # srcEle must be a calling instance
            srcCallName = srcPointCallName[srcEle]
            dstEleSet = srcToDstIndex[srcEle]
            for dstEle in dstEleSet:
                # maybe calling instance corresponds to a general instance
                if dstEle in dstPointCallName and dstEle in dstList:                    
                    dstCallName = dstPointCallName[dstEle]
                    if cmp(srcCallName, dstCallName) == 0:
                        traceAlignProgram(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, \
                                   srcToDstLN, dstToSrcLN, srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, \
                                   dstPureCallSet, srcPureReturnSet, dstPureReturnSet, srcPointCallName, dstPointCallName, srcEle, dstEle)        
if __name__ == '__main__':
    True
