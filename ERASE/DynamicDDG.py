
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

# Compute the data dependence, which is through the function return
# the form is <index, [index, ....]>, which is different from the general later data dependence
def returnDDG(returnTogether, trace):
    returnDepen = {}
    for eachEle in returnTogether:
        returns = returnTogether[eachEle]
        for eachReturn in returns:
            # in regular situation, the trace is
            # ....
            # return statement
            # }
            # ...#...#R
            # ....
            dataReturn = eachReturn-3
            # however, pin is not ok for the tail function calling
            # The below example is in find_b
            # pred.c#pred_timewindow#R
            # 987, which is }
            # pred.c#pred_mtime#R
            # ...
            while True:
                if trace[dataReturn].find("#") != -1:
                    dataReturn = dataReturn-2
                else:
                    break
            if eachEle in returnDepen:
                returnValue = returnDepen[eachEle]
                returnValue.append(dataReturn)
            else:
                returnValue = []
                returnValue.append(dataReturn)
                returnDepen[eachEle] = returnValue
    return returnDepen
                      
# compare the register name
# it may be equivalent between 16 bit and 32 bit registers, for example "al" and "ax" 
def regNameCompare(slaveReg, masterReg):
    if cmp(slaveReg, masterReg) == 0:
        return True
    else:
        if cmp(slaveReg, "eax") == 0:
            if cmp(masterReg, "ax") == 0 or cmp(masterReg, "ah") == 0 or cmp(masterReg, "al") == 0:
                return True
        if cmp(slaveReg, "ebx") == 0:
            if cmp(masterReg, "bx") == 0 or cmp(masterReg, "bh") == 0 or cmp(masterReg, "bl") == 0:
                return True
        if cmp(slaveReg, "ecx") == 0:
            if cmp(masterReg, "cx") == 0 or cmp(masterReg, "ch") == 0 or cmp(masterReg, "cl") == 0:
                return True
        if cmp(slaveReg, "edx") == 0:
            if cmp(masterReg, "dx") == 0 or cmp(masterReg, "dh") == 0 or cmp(masterReg, "dl") == 0:
                return True
        if cmp(masterReg, "eax") == 0:
            if cmp(slaveReg, "ax") == 0 or cmp(slaveReg, "ah") == 0 or cmp(slaveReg, "al") == 0:
                return True
        if cmp(masterReg, "ebx") == 0:
            if cmp(slaveReg, "bx") == 0 or cmp(slaveReg, "bh") == 0 or cmp(slaveReg, "bl") == 0:
                return True
        if cmp(masterReg, "ecx") == 0:
            if cmp(slaveReg, "cx") == 0 or cmp(slaveReg, "ch") == 0 or cmp(slaveReg, "cl") == 0:
                return True
        if cmp(masterReg, "edx") == 0:
            if cmp(slaveReg, "dx") == 0 or cmp(slaveReg, "dh") == 0 or cmp(slaveReg, "dl") == 0:
                return True
        return False
    
# compute the data dependence through register
def registerDataDep(codeIndex, codeDataTrace, codeToData, codeToBlock):
    masterDataSet = set()
    masterCodeSet = set()
    workList = []
    workSet = set()
    workList.append(codeIndex)
    workSet.add(codeIndex)
    while len(workList) != 0:
        eachCodeIndex = workList.pop()
        eachCodeEle = codeDataTrace[eachCodeIndex]
        eachCodeItem = eachCodeEle.split("#")
        eachCodeReg = eachCodeItem[3]
        # not consider the data dependence through eflags register
        if cmp(eachCodeReg, "eflags") == 0:
            continue
        masterIndex = eachCodeIndex
        while masterIndex > 0:
            masterIndex = masterIndex - 1
            masterEle = codeDataTrace[masterIndex]
            # "f$C"is the separator of the function call point 
            # the data dependence through register would not cross the function 
            if masterEle.find("$") != -1:
                break
            masterItem = masterEle.split("#")
            if len(masterItem) == 4 and cmp(masterItem[2], "W") == 0:
                masterReg = masterItem[3]
                # cann't directly compare the register name
                # it may be equivalent between 16 bit and 32 bit registers, for example "al" and "ax" 
                regIndex = regNameCompare(eachCodeReg, masterReg)
                if regIndex == True:
                    masterBlock = codeToBlock[masterIndex]
                    for eachMasterIndex in masterBlock:
                        eachMasterEle = codeDataTrace[eachMasterIndex]
                        eachMasterItem = eachMasterEle.split("#")
                        if eachMasterItem[2].find("R") != -1:
                            # it is still the read register
                            if len(eachMasterItem) == 4:
                                if eachMasterIndex not in workSet:
                                    workList.append(eachMasterIndex)
                                    workSet.add(eachMasterIndex)
                            # it is the read memory
                            elif len(eachMasterItem) == 5:
                                masterCodeSet.add(eachMasterIndex)
                    # have found its data dependence
                    break  
    for eachMasterCode in masterCodeSet:
        eachMasterData = codeToData[eachMasterCode]
        masterDataSet.add(eachMasterData)      
    return masterDataSet 

# it represents that masterIndex is the function call point
# compute the data dependence through parameter
def parameterDataDep(dataIndex, masterIndex, dataTraceList, codeDataTrace, \
                    pointerSet, dataToTrace, dataToCode, codeToData, codeToBlock):
    # the indexes of elements in data trace, which are corresponds to element of masterIndex
    masterSet = set()
    if masterIndex in dataToCode:
        codeIndex = dataToCode[masterIndex]
        # block in codeDataFile that is relevant to the element of masterIndex that is in dataFile
        codeBlock = codeToBlock[codeIndex]
        for eachCodeIndex in codeBlock:
            eachCodeEle = codeDataTrace[eachCodeIndex]
            eachItem = eachCodeEle.split("#")
            # eachCodeEle is relevant to the written memory, and we find its read memory to find its data dependence
            if eachItem[2].find("R") != -1:
                # it is the memory
                if len(eachItem) == 5:
                    eachDataIndex = codeToData[eachCodeIndex]
                    masterSet.add(eachDataIndex)  
                # it is the register           
                elif len(eachItem) == 4:
                    masterDataSet = registerDataDep(eachCodeIndex, codeDataTrace, codeToData, codeToBlock)
                    for eachMasterData in masterDataSet:
                        masterSet.add(eachMasterData) 
    # we have compute the data dependence through register, which is not ordered
    # we should reorder the list
    masterList = list(masterSet)
    masterList.sort()                
    secondMasterList = list() 
    # it is used to recored the function call points
    # because they all are be included in the data dependence  
    functionSet = set()  
    if len(masterList) != 0: 
        for eachMaster in masterList:
            (eachParameterDepList, parameterDepIndex, eachFunctionSet) = dynamicDDData(eachMaster, dataTraceList, codeDataTrace, pointerSet, \
                                                                     dataToTrace, dataToCode, codeToData, codeToBlock)
            for eachParameterDep in eachParameterDepList:
                secondMasterList.append(eachParameterDep)
            for eachFunction in eachFunctionSet:
                functionSet.add(eachFunction)
    else:
        # it is the case that the actual parameter is one concrete value, not a variable
        if dataIndex in pointerSet:
            secondMasterList.append((masterIndex, True))
        else:
            secondMasterList.append((masterIndex, False))
    return (secondMasterList, functionSet)

# determine whether it is the function define line
# In fact, it is the "{"
def functionDefine(dataIndex, dataTraceList, dataToTrace, dataToCode):
    functionDefineIndex = False
    startIndex = dataToTrace[dataIndex]
    while dataIndex >= 0:
        traceIndex = dataToTrace[dataIndex]
        if traceIndex != startIndex:
            if dataIndex in dataToCode:
                functionDefineIndex = True
            break
        dataIndex = dataIndex - 1    
    return functionDefineIndex 

# it is the function define line
# we continue to find the function call point
def functionHandle(dataIndex, dataTraceList, dataToCode): 
    resultIndex = dataIndex
    while dataIndex >= 0:
        if dataIndex in dataToCode:
            # it is beyond the boundary of function define line
            # the search is limited in the function define line
            print "Data dependence error at function define line!"
            print "But it is tolerant, we consider its data dependence is function define line!"
            return resultIndex
        else:
            dataEle = dataTraceList[dataIndex]
            dataRW = dataEle[0]
            # we do not know why firstly encountered read memory is OK?
            if dataRW.find("R") != -1:
                dataAddr = dataEle[1]
                break 
        dataIndex = dataIndex - 1    
    enterFunctionParameter = False  
    while dataIndex >= 0:
        # when we reach the function parameter, we are limited in the function parameter scope.
        if enterFunctionParameter == False:
            if dataIndex in dataToCode:
                enterFunctionParameter = True
        else:
            if dataIndex not in dataToCode:
                print "Data dependence error at function define line!"
                print "But it is tolerant, we consider its data dependence is function define line!"
                return resultIndex  
        dataEle = dataTraceList[dataIndex]
        dataRW = dataEle[0]
        dataAddrValue = long(dataAddr, 16)
        dataEleValue = long(dataEle[1], 16)
        if dataRW.find("W") != -1 and dataAddrValue == dataEleValue:
            if enterFunctionParameter == True:
                return dataIndex
            else:
                print "Data dependence error at function define line!"
                print "But it is tolerant, we consider its data dependence is function define line!"
                return resultIndex
        dataIndex = dataIndex - 1
    print "Data dependence error at function define line!"
    print "But it is tolerant, we consider its data dependence is function define line!"
    return resultIndex

# compute the data dependence of an element of data trace
# dataIndex: is the index element that are computed
# masterList's form is list((masterIndex, True/False)), where True/False represents whether it is the pointer
# paraDepIndex represents whether it is the data dependence through parameter
# functionSet is the set of function call points that are gone through by parameter
def dynamicDDData(dataIndex, dataTraceList, codeDataTrace, pointerSet, \
                  dataToTrace, dataToCode, codeToData, codeToBlock):
    # masterList's form is list((masterIndex, True/False)), where True/False represents whether it is the pointer
    masterList = list()
    functionSet = set()
    # it represents that whether the master is the function call point
    parameterDepIndex = False
    slave = dataTraceList[dataIndex]
    slaveAddr = slave[1]
    for masterIndex in range(dataIndex-1, -1, -1):
        if masterIndex in dataToTrace:
            master = dataTraceList[masterIndex]
            masterRW = master[0]
            if masterRW.find("W") != -1:
                masterAddr = master[1]
                slaveAddrValue = long(slaveAddr, 16)
                masterAddrValue = long(masterAddr, 16)
                if slaveAddrValue == masterAddrValue:
                    # it represents it is the function call point
                    if masterIndex in dataToCode:
                        parameterDepIndex = True
                        (parameterDepList, functionSet) = parameterDataDep(dataIndex, masterIndex, dataTraceList, codeDataTrace, \
                                                                pointerSet, dataToTrace, dataToCode, codeToData, codeToBlock)
                        for eachParameterDep in parameterDepList:
                            masterList.append(eachParameterDep)
                        functionSet.add(masterIndex)
                    else:
                        # masterIndex sometimes is the function definition line
                        # therefore, we continue to find its function call point
                        functionDefineIndex = functionDefine(masterIndex, dataTraceList, dataToTrace, dataToCode)
                        if functionDefineIndex == True:
                            # if it is the function define line
                            # we continue to find the corresponding function call point
                            masterIndex = functionHandle(masterIndex, dataTraceList, dataToCode)
                            parameterDepIndex = True
                            (parameterDepList, functionSet) = parameterDataDep(dataIndex, masterIndex, dataTraceList, codeDataTrace, \
                                                                   pointerSet, dataToTrace, dataToCode, codeToData, codeToBlock)
                            for eachParameterDep in parameterDepList:
                                masterList.append(eachParameterDep)
                            functionSet.add(masterIndex)   
                        else:
                            if dataIndex in pointerSet:
                                masterList.append((masterIndex, True))
                            else:
                                masterList.append((masterIndex, False))                   
                    # find its data dependence, and return
                    return (masterList, parameterDepIndex, functionSet)
    # there is no data dependence
    if dataIndex in pointerSet:
        masterList.append((-1, True))
    else:
        masterList.append((-1, False))
    return (masterList, parameterDepIndex, functionSet)
    
# dataDepen: it is the data dependence, the form is <traceIndex, 
# List([traceIndex, Value, True/False]/[traceIndex, Value, True/False,  [traceIndex,[traceIndex, [...., List([traceIndex, Value, True/False]]))])
def dynamicDDEle(ele, dataDepen, returnDepen, dataTraceList, codeDataTrace, pointerSet, pointCallName, \
                 dataToTrace, traceToData, dataToCode, codeToData, codeToBlock, regression):
    # the data dependence of  element has not been computed
    # the element has used/defined the variables 
    if ele not in dataDepen and ele in traceToData:
        dataList = traceToData[ele]
        workList = []
        workSet = set()
        for eachData in dataList:
            workList.append(eachData)
            workSet.add(eachData)
        while len(workList) != 0:
            eachData = workList.pop(0)
            # functionIndex represents whether it is the function call
            # we do not compute the data dependence of the function parameter
            functionIndex = False
            # regression represents whether it is used to compute regression slice or dynamic slice
            # if regression is False, which represents this is used for dynamic slice, and functionIndex is False for ever
            # if eachData in dataToCode, the eachData is function parameter
            if regression == True and eachData in dataToCode:
                functionIndex = True
            if functionIndex == False and eachData in dataToTrace:
                slaveTraceIndex =  dataToTrace[eachData]
                """
                # continue to compute the data dependence, maybe they are required by the pointer comparison
                if slaveTraceIndex in returnDepen:
                    returnTraceSet = returnDepen[slaveTraceIndex]
                    for eachReturnTrace in returnTraceSet:
                        if eachReturnTrace not in dataDepen and eachReturnTrace in traceToData:
                            returnDataSet = traceToData[eachReturnTrace]
                            for eachReturnData in returnDataSet:
                                if eachReturnData not in workSet:
                                    workSet.add(eachReturnData)
                                    workList.append(eachReturnData)  
                """
                slave = dataTraceList[eachData]
                slaveRW = slave[0]
                # here, we only consider "R", because we compute its data dependence
                if slaveRW.find("R") != -1:
                    # masterList's form is list((masterIndex, True/False)), where True/False represents whether it is the pointer
                    # paraDepIndex represents whether it is the data dependence through parameter
                    # functionSet is the set of function call points that are gone through by parameter
                    (masterList, paraDepIndex, functionSet) = dynamicDDData(eachData, dataTraceList, codeDataTrace, pointerSet, \
                                                                           dataToTrace, dataToCode, codeToData, codeToBlock)
                    if paraDepIndex == True:                    
                        parameterValue = []
                        # add the data dependencies that are generated through parameters
                        for eachDataMaster in masterList:
                            masterValue = ""  
                            if eachDataMaster[0] >= 0 and eachDataMaster[0] < len(dataTraceList):
                                masterDataEle = dataTraceList[eachDataMaster[0]]
                                masterValue = masterDataEle[2]                      
                            masterTraceIndex = -1
                            if eachDataMaster[0] in dataToTrace:
                                masterTraceIndex = dataToTrace[eachDataMaster[0]]
                            if slaveTraceIndex != masterTraceIndex:
                                if eachDataMaster[1] == True:
                                    parameterValue.append([masterTraceIndex, masterValue, True])
                                else:
                                    parameterValue.append([masterTraceIndex, masterValue, False])
                        # functionSet is a set of function call points
                        # we order them, and they are the form a->b->c where -> represents the function calling
                        functionList = list(functionSet)
                        functionList.sort()
                        functionListLen = len(functionList)
                        functionListIndex = 0
                        # the last function call point is handled especially
                        while functionListIndex < functionListLen - 1:
                            eachParameterTraceIndex = -1
                            if functionList[functionListIndex] in dataToTrace:
                                eachParameterTraceIndex = dataToTrace[functionList[functionListIndex]]
                            # the form is [index, [index, [...[List([traceIndex, Value]]]]]
                            parameterValue = [eachParameterTraceIndex, parameterValue]
                            functionListIndex = functionListIndex + 1
                        # especially handle the last function call point               
                        parameterTraceIndex = -1
                        if functionList[-1] in dataToTrace:
                            parameterTraceIndex = dataToTrace[functionList[-1]]
                        if slaveTraceIndex != parameterTraceIndex:
                            if slaveTraceIndex in dataDepen:
                                mapValue = dataDepen[slaveTraceIndex]  
                                # determine whether it is the pointer based on the slave
                                if eachData in pointerSet:   
                                    # using the slave[2], as the read variable is more reliable than the written variable
                                    mapValue.append([parameterTraceIndex, slave[2], True, parameterValue])
                                else:
                                    mapValue.append([parameterTraceIndex, slave[2], False, parameterValue])
                                
                            else:
                                mapValue = []
                                if eachData in pointerSet:
                                    mapValue.append([parameterTraceIndex, slave[2], True, parameterValue])
                                else:
                                    mapValue.append([parameterTraceIndex, slave[2], False, parameterValue])
                                dataDepen[slaveTraceIndex] = mapValue    
                            """"    
                            # continue to compute the data dependence, maybe they are required by the pointer comparison
                            # strip the traceIndex that are the function call points, and only keep the original form of data dependence
                            while type(parameterValue[0]) is types.IntType:
                                parameterValue = parameterValue[1] 
                            for eachParameterValue in parameterValue:
                                if eachParameterValue[0] not in dataDepen and eachParameterValue[0] in traceToData:
                                        masterDataIndexSet = traceToData[eachParameterValue[0]]
                                        for masterDataIndex in masterDataIndexSet:
                                            if masterDataIndex not in workSet:
                                                workSet.add(masterDataIndex)
                                                workList.append(masterDataIndex)    
                            """                                   
                    else:
                        for eachDataMaster in masterList:
                            masterTraceIndex = -1
                            if eachDataMaster[0] in dataToTrace:
                                masterTraceIndex = dataToTrace[eachDataMaster[0]]
                            # preventing the data dependence that is caused by the temporary variable within the same statement
                            if slaveTraceIndex != masterTraceIndex:
                                if slaveTraceIndex in dataDepen:
                                    mapValue = dataDepen[slaveTraceIndex]  
                                    # consider the master, because a line may be data dependent on many lines through parameter
                                    if eachDataMaster[1] == True:   
                                        # using the slave[2], as the read value is more reliable than the written value
                                        mapValue.append([masterTraceIndex, slave[2], True])
                                    else:
                                        mapValue.append([masterTraceIndex, slave[2], False])
                                else:
                                    mapValue = []
                                    if eachDataMaster[1] == True:
                                        mapValue.append([masterTraceIndex, slave[2], True])
                                    else:
                                        mapValue.append([masterTraceIndex, slave[2], False])
                                    dataDepen[slaveTraceIndex] = mapValue
                                """
                                # continue to compute the data dependence, maybe they are required by the pointer comparison
                                if masterTraceIndex not in dataDepen and masterTraceIndex in traceToData:
                                    masterDataIndexSet = traceToData[masterTraceIndex]
                                    for masterDataIndex in masterDataIndexSet:
                                        if masterDataIndex not in workSet:
                                            workSet.add(masterDataIndex)
                                            workList.append(masterDataIndex)  
                                """
if __name__ == '__main__':
    True    