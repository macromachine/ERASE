
import types
from DynamicDDG import dynamicDDEle
from TraceAlign import traceAlignEle

# compute the locations of pointer variable, where the memory is allocated
def pointerDataMallock(dataSet, dataDep, returnDep, dataTrace, codeDataTrace, pointerSet, pointCallName, \
                       dataToTrace, traceToData, dataToCode, codeToData, codeToBlock):
    # pointerMalloc is the set of points that allocate the memory
    pointerMalloc = set()
    workList = []
    workSet = set()
    for eachData in dataSet:
        workList.append(eachData)
        workSet.add(eachData)
    while len(workList) != 0:
        ele = workList.pop(0)
        # compute the dynamic data dependence of element ele
        dynamicDDEle(ele, dataDep, returnDep, dataTrace, codeDataTrace, pointerSet, pointCallName, \
                     dataToTrace, traceToData, dataToCode, codeToData, codeToBlock, True)
        returnMatch = False
        if ele in returnDep:
            returnMatch = True
            returnDataSet = returnDep[ele]
            for returnData in returnDataSet:
                if returnData in traceToData:
                    if returnData not in workSet:
                        workList.append(returnData)
                        workSet.add(returnData)
                else:
                    # the case is that the return statement has no read or written memory
                    # in fact, the return data dependence is through register
                    # for example, the return data dependence at line 860 in file list.c of program tar
                    pointerMalloc.add(ele)
        preciseMatch = False
        if returnMatch == False and ele in dataDep:
            eleValueSet = set()
            eleDataIndexSet = traceToData[ele]
            for eleDataIndex in eleDataIndexSet:
                if eleDataIndex in pointerSet:
                    eleData = dataTrace[eleDataIndex]
                    if cmp(eleData[0], "W") == 0:
                        eleValue = long(eleData[2], 16)
                        if eleValue not in eleValueSet:
                            eleValueSet.add(eleValue)
            dataDepList = dataDep[ele]
            dataDepLen = len(dataDepList)
            dataDepIndex = dataDepLen - 1
            while dataDepIndex >= 0:
                dataDepEle = dataDepList[dataDepIndex]
                dataDepIndex = dataDepIndex - 1
                if len(dataDepEle) == 3 and dataDepEle[2] == True:
                    dataIndex = dataDepEle[0]
                    # if we cannot find the data dependence, we return -1
                    if dataIndex != -1:
                        dataValue = long(dataDepEle[1], 16)
                        if dataValue in eleValueSet or dataValue+1 in eleValueSet or dataValue-1 in eleValueSet:
                            preciseMatch = True
                            if dataIndex not in workSet:
                                workList.append(dataIndex)
                                workSet.add(dataIndex)
                elif len(dataDepEle) == 4 and dataDepEle[2] == True:
                    parameterDataSet = dataDepEle[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        parameterDataSet = parameterDataSet[1]
                    parameterDataLen = len(parameterDataSet)
                    parameterDataIndex = parameterDataLen - 1
                    while parameterDataIndex >= 0:
                        parameterData = parameterDataSet[parameterDataIndex]
                        parameterDataIndex = parameterDataIndex - 1
                        if parameterData[2] == True:
                            dataIndex = parameterData[0]
                            if dataIndex != -1:
                                dataValue = long(parameterData[1], 16)
                                if eleValue == dataValue or eleValue == dataValue + 1 or eleValue == dataValue - 1:
                                    preciseMatch = True
                                    if dataIndex not in workSet:
                                        workList.append(dataIndex)
                                        workSet.add(dataIndex)
        if returnMatch == False and preciseMatch == False and ele in dataDep:
            # indicate whether it is a pointer and it does not depend on other statement instance
            # in fact, ele must be a pointer 
            pointerMallocSign = True
            dataDepList = dataDep[ele]
            dataDepLen = len(dataDepList)
            dataDepIndex = dataDepLen - 1
            while dataDepIndex >= 0:
                dataDepEle = dataDepList[dataDepIndex]
                dataDepIndex = dataDepIndex - 1
                if len(dataDepEle) == 3 and dataDepEle[2] == True:
                    pointerMallocSign = False
                    dataIndex = dataDepEle[0]
                    # if we cannot find the data dependence, we return -1
                    if dataIndex != -1:
                        if dataIndex not in workSet:
                            workList.append(dataIndex)
                            workSet.add(dataIndex)
                    else:
                        # there is a statement that has multiple pointers and one pointer has no data dependence
                        # we consider this case is also malloc site
                        # for example, char const *p = current->prefix_end in io.c of program diff 
                        pointerMalloc.add(ele)
                elif len(dataDepEle) == 4 and dataDepEle[2] == True:
                    parameterDataSet = dataDepEle[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        parameterDataSet = parameterDataSet[1]
                    parameterDataLen = len(parameterDataSet)
                    parameterDataIndex = parameterDataLen - 1
                    while parameterDataIndex >= 0:
                        parameterData = parameterDataSet[parameterDataIndex]
                        parameterDataIndex = parameterDataIndex - 1
                        if parameterData[2] == True:
                            pointerMallocSign = False
                            dataIndex = parameterData[0]
                            if dataIndex != -1:
                                if dataIndex not in workSet:
                                    workList.append(dataIndex)
                                    workSet.add(dataIndex)
                            else:
                                pointerMalloc.add(ele)
            # it is a pointer, and it does not depend on other instance
            if pointerMallocSign == True:
                pointerMalloc.add(ele)
        # function parameter has no data/return dependence
        # for example: void f(..., &a, ....), where "a" is an integer variable
        # function call point has no data and return dependence
        if ele != -1 and ele not in dataDep and ele not in returnDep:
            pointerMalloc.add(ele)
    return pointerMalloc 

# this function is commented out in the experiment of gettext, which is added after ICSE17
# compute the locations of pointer variable, where the memory is allocated
def _pointerDataMallock(dataSet, dataDep, returnDep, dataTrace, codeDataTrace, pointerSet, pointCallName, \
                       dataToTrace, traceToData, dataToCode, codeToData, codeToBlock):
    # pointerMalloc is the set of points that allocate the memory
    pointerMalloc = set()
    workList = []
    workSet = set()
    for eachData in dataSet:
        workList.append(eachData)
        workSet.add(eachData)
    while len(workList) != 0:
        ele = workList.pop(0)
        # compute the dynamic data dependence of element ele
        dynamicDDEle(ele, dataDep, returnDep, dataTrace, codeDataTrace, pointerSet, pointCallName, \
                     dataToTrace, traceToData, dataToCode, codeToData, codeToBlock, True)
        if ele in dataDep:
            # indicate whether it is a pointer and it does not depend on other statement instance
            # in fact, ele must be a pointer 
            pointerMallocSign = True
            dataDepList = dataDep[ele]
            for dataDepEle in dataDepList:
                if len(dataDepEle) == 3 and dataDepEle[2] == True:
                    dataIndex = dataDepEle[0]
                    # if we cannot find the data dependence, we return -1
                    if dataIndex != -1:
                        pointerMallocSign = False
                        if dataIndex not in workSet:
                            workList.append(dataIndex)
                            workSet.add(dataIndex)
                    else:
                        # there is a statement that has multiple pointers and one pointer has no data dependence
                        # we consider this case is also malloc site
                        # for example, char const *p = current->prefix_end in io.c of program diff 
                        pointerMalloc.add(ele)
                elif len(dataDepEle) == 4 and dataDepEle[2] == True:
                    parameterDataSet = dataDepEle[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        parameterDataSet = parameterDataSet[1]
                    for parameterData in parameterDataSet:
                        if parameterData[2] == True:
                            dataIndex = parameterData[0]
                            if dataIndex != -1:
                                pointerMallocSign = False
                                if dataIndex not in workSet:
                                    workList.append(dataIndex)
                                    workSet.add(dataIndex)
                            else:
                                pointerMalloc.add(ele)
            # it is a pointer, and it does not depend on other instance
            if pointerMallocSign == True:
                pointerMalloc.add(ele)
        if ele in returnDep:
            returnDataSet = returnDep[ele]
            for returnData in returnDataSet:
                if returnData in traceToData:
                    if returnData not in workSet:
                        workList.append(returnData)
                        workSet.add(returnData)
                else:
                    # the case is that the return statement has no read or written memory
                    # in fact, the return data dependence is through register
                    # for example, the return data dependence at line 860 in file list.c of program tar
                    pointerMalloc.add(ele)
        # function parameter has no data/return dependence
        # for example: void f(..., &a, ....), where "a" is an integer variable
        # function call point has no data and return dependence
        if ele != -1 and ele not in dataDep and ele not in returnDep:
            pointerMalloc.add(ele)
    return pointerMalloc 

# Determine the type of the element    
def typeOfELe(ele, srcDstIndex, modificationSet, addDelSet):
    # The addition, deletion, and modification is higher priority than the control and value difference
    if ele in addDelSet:
        # addition or deletion statement instance
        # Maybe the added or deleted statement instance is also the control difference
        return 0
    elif ele in modificationSet:
        # modification statement instance
        # Maybe the modified statement instance is also the control difference
        return 1
    elif ele not in srcDstIndex.keys():
        # control difference
        return 2
    else:
        # including value difference and identical
        # identical would not produce the side effect
        return 3
    
# compare whether two pointers point the same object
# the pointer comparison is still based on the offset technique
# cDataSet/rDataSet only includes the data dependencies through the pointer variable
def pointerCompare(appName, cDataSet, rDataSet, cValue, rValue, cToRIndex, rToCIndex, cDataDep, \
                   rDataDep, cReturnDep, rReturnDep, cDataTrace, rDataTrace, cCodeDataTrace, rCodeDataTrace, \
                   cDataToTrace, rDataToTrace, cTraceToData, rTraceToData, cDataToCode, rDataToCode, \
                   cCodeToData, rCodeToData, cCodeToBlock, rCodeToBlock, cPointCallName, rPointCallName, \
                   cPointerSet, rPointerSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, \
                   cTrace, rTrace, cCallG, rCallG, cReversedCallG, rReversedCallG, cControlDep, rControlDep, \
                   cToRLN, rToCLN, cLoopSet, rLoopSet, cCallReturnBoth, rCallReturnBoth, cPureCallSet, \
                   rPureCallSet, cPureReturnSet, rPureReturnSet):
    # cPointerMalloc/rPointMalloc is the set of points that allocate the memory
    # the form is set(index), where index is the sequence in the trace list
    cPointerMallocSet = pointerDataMallock(cDataSet, cDataDep, cReturnDep, cDataTrace, cCodeDataTrace, cPointerSet, \
                                        cPointCallName, cDataToTrace, cTraceToData, cDataToCode, cCodeToData, cCodeToBlock)
    rPointerMallocSet = pointerDataMallock(rDataSet, rDataDep, rReturnDep, rDataTrace, rCodeDataTrace, rPointerSet, \
                                        rPointCallName, rDataToTrace, rTraceToData, rDataToCode, rCodeToData, rCodeToBlock)
    
    # three conditions that can lead to pointer difference
    if len(cPointerMallocSet) != len(rPointerMallocSet):
        return False  
    for cPointerMallocEle in cPointerMallocSet:
        traceAlignEle(cPointerMallocEle, cToRIndex, rToCIndex, cTrace, rTrace, cCallG, rCallG, cReversedCallG, \
                      rReversedCallG, cControlDep, rControlDep, cToRLN, rToCLN, cLoopSet, rLoopSet, cCallReturnBoth, \
                      rCallReturnBoth, cPureCallSet, rPureCallSet, cPureReturnSet, rPureReturnSet, cPointCallName)
    for rPointerMallocEle in rPointerMallocSet:
        traceAlignEle(rPointerMallocEle, rToCIndex, cToRIndex, rTrace, cTrace, rCallG, cCallG, rReversedCallG, \
                      cReversedCallG, rControlDep, cControlDep, rToCLN, cToRLN, rLoopSet, cLoopSet, rCallReturnBoth, \
                      cCallReturnBoth, rPureCallSet, cPureCallSet, rPureReturnSet, cPureReturnSet, rPointCallName)    
    for cPointerMallocEle in cPointerMallocSet:
        matched = False
        if cPointerMallocEle in cToRIndex:
            rIndexSet = cToRIndex[cPointerMallocEle]
            for rPointerMallocEle in rPointerMallocSet:
                if  rPointerMallocEle in rIndexSet:
                    matched = True
                    break
        if matched == False:
            return False
    for rPointerMallocEle in rPointerMallocSet:
        matched = False
        if rPointerMallocEle in rToCIndex:
            cIndexSet = rToCIndex[rPointerMallocEle]
            for cPointerMallocEle in cPointerMallocSet:
                if  cPointerMallocEle in cIndexSet:
                    matched = True
                    break
        if matched == False:
            return False               
    # the current address    
    cValueLong = long(cValue, 16)
    # the offset compared to the basic address
    cOffsetSet = set()
    for cPointerMalloc in cPointerMallocSet:
        if cPointerMalloc in cTraceToData:
            cPointerDataSet = cTraceToData[cPointerMalloc]
            for cPointerData in cPointerDataSet:
                if cPointerData in cPointerSet:
                    cPointerDataItem = cDataTrace[cPointerData]
                    if cPointerDataItem[0].find("W") != -1:
                        # find the element that reads the value of address cPointerDataItem[1]
                        # because the value of read is more reliable than the value of written 
                        cDataValue = cPointerDataItem[2]
                        cDataValueLong = long(cDataValue, 16)
                        cOffsetSet.add((cPointerMalloc, cDataValueLong-cValueLong))
        else:
            # in fact, "cPointerMalloc" is -1
            print "Address is Allocated in Main Function Parameter!"
    # the current address    
    rValueLong = long(rValue, 16)
    # the offset compared to the basic address
    rOffsetSet = set()
    for rPointerMalloc in rPointerMallocSet:
        if rPointerMalloc in rTraceToData:
            rPointerDataSet = rTraceToData[rPointerMalloc]
            for rPointerData in rPointerDataSet:
                if rPointerData in rPointerSet:
                    rPointerDataItem = rDataTrace[rPointerData]
                    if rPointerDataItem[0].find("W") != -1:
                        rDataValue = rPointerDataItem[2]
                        rDataValueLong = long(rDataValue, 16)
                        rOffsetSet.add((rPointerMalloc, rDataValueLong-rValueLong))
        else:
            # in fact, "rPointerMalloc" is -1
            print "Address is Allocated in Main Function Parameter!"
    for cOffset in cOffsetSet:
        if cOffset[0] in cToRIndex:
            rIndexSet = cToRIndex[cOffset[0]]
            for rOffset in rOffsetSet:
                # the offset is the same
                if cOffset[1] == rOffset[1]:  
                    # cOffset[0] and rOffset[0] are correspondent
                    if rOffset[0] in rIndexSet:
                        return True
    return False
    
if __name__ == '__main__':
    pass