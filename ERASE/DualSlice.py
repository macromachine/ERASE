
import os
import types

from LineMerge import lineMergeDir
from LineSplit import lineSplitDir
from DiffUtil import DiffProcess
from CompileWork import compileWork
from PinExe import pinCFG, pinTraceData, pinCode
from ExeTrace import executionTrace
from LNCalling import LNOfFunctionCalling
from Memcpy import StaticMemcpy, handleMemcpyData
from Realloc import StaticRealloc, handleReallocData
from Strcpy import StaticStrcpy, handleStrcpyData
from LoopDet import DynamicLoop
from DynamicCDG import staticCDG, dynamicCDG
from ChangeAlign import modificationAlign, addDelAlign
from TraceAlign import pointToCallName, callGraph
from CallReturnPoint import callReturnPoint
from TraceAlign import traceAlignFunctionPoint, traceAlignBody, traceAlignProgram
from DynamicDDG import returnDDG, dynamicDDEle
from BranchValue import branchValue
from SwitchDet import dynamicSwitch
from ABAdditionDeletion import afterBeforeInstance
from PreProcess import preProcessFileName
from HandleTrace import handleTrace
from HandleData import  handleData
from DeleteExecution import deleteTrace, deleteData
from PointerCompare import pointerCompare
from PointerDet import pointerDet

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

# merge the change information of a file to the other change information
def changeFileMerge(srcDiffFile, dstDiffFile, changeFile, changeFileSig):
    try:
        changeW = open(changeFile, "a+")
        changeSigR = open(changeFileSig, "r")
    except IOError, e:
        print "*** file open error:", e
    else:
        headStr = "diff -NbrU 0 '--exclude-from=/home/***/Experiment/Object/patterns.xo'" + " " + srcDiffFile + " " + dstDiffFile + "\n"
        changeW.write(headStr)
        for eachLine in changeSigR:
            changeW.write(eachLine)
        changeW.close()
        changeSigR.close()
        
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
    
# compute the caller point based on the control dependence
def callPoint(ele, controlDep, callDep):
    while True:
        if ele in controlDep:
            ele = controlDep[ele]
        else:
            break
    if ele in callDep:
        return callDep[ele]
    else:
        # the caller of main function
        return -1
    
# Compute the immediately previous and next elements of the element ele, and which are correspondent
# It is used to compute the key predicate in control difference            
def beforeAfterEle(ele, trace, CRIndex):
    beforeIndex = ele - 1 
    while beforeIndex >= 0:
        if beforeIndex in CRIndex:
            break
        else:
            beforeIndex = beforeIndex - 1
    afterIndex = ele + 1
    while afterIndex < len(trace):
        if afterIndex in CRIndex:
            break
        else:
            afterIndex = afterIndex + 1
    return (beforeIndex, afterIndex)


# Compute the scope of a function
# Only the function body, not including "hello.c#main#C" and "hello.c#main#R"
def functionScope(caller, trace):
    callNumber = 0
    traceIndex = caller + 1
    traceLen = len(trace)
    while traceIndex < traceLen:
        # the first eachLine is the form of "...#...#C"
        eachLine = trace[traceIndex]
        if eachLine.find("#") != -1:
            callRet = callRetAbstract(eachLine)
            if callRet.find("C") != -1:
                callNumber = callNumber + 1
            elif callRet.find("R") != -1:
                callNumber = callNumber - 1   
        if callNumber == 0:  
            return (caller+2, traceIndex-1)           
        traceIndex = traceIndex + 1
    print "Function Scope Error!"
    return (caller+2, traceIndex-1)    
 
# compute the fileName of an element
def fileNameEle(ele, trace):
    fileName = ""
    callNumber = 0
    traceIndex = ele - 1
    while traceIndex >= 0:
        eachLine = trace[traceIndex]
        if eachLine.find("#") != -1:
            callRet = callRetAbstract(eachLine)
            if callRet.find("C") != -1:
                callNumber = callNumber + 1
            elif callRet.find("R") != -1:
                callNumber = callNumber - 1   
        if callNumber == 1:  
            fileName = fileNameAbstract(eachLine)           
            break
        traceIndex = traceIndex - 1
    return fileName
         
# Compute the FileName:LineNumber
def fileLineNumberEle(ele, trace):
    fileName = fileNameEle(ele, trace)
    lineNumber = trace[ele]
    return (fileName, lineNumber)

# add the control dependence, it is used for addition, deletion, and control difference case 
# cWorkList/rWorlist is based on the trace of the element master  
# if ele and master are in two different traces, cWorkLis is the list of trace where master belongs 
# crossVersion represents whether ele and master are in different versions 
def controlDepAdded(ele, master, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                    cCorrespondence, rCorrespondence, cToRIndex, cBVMap, rBVMap, \
                    cSwitchSet, rSwitchSet, cModificationSet, cAddDelSet, crossVersion):
    masterType = typeOfELe(master, cToRIndex, cModificationSet, cAddDelSet)
    # The master is addition, deletion, modification or control difference case
    if masterType == 0 or masterType == 1 or masterType == 2:
        if master not in cWorkSet:
            cWorkList.append(master)
            cWorkSet.add(master)
        if crossVersion == True:
            if ele in rCorrespondence:
                corresValue = rCorrespondence[ele]
                corresValue.add(master)
            else:
                corresValue = set()
                corresValue.add(master)
                rCorrespondence[ele] = corresValue
        else:
            if ele in cDependence:
                depenValue = cDependence[ele]
                depenValue.add(master)
            else:
                depenValue = set()
                depenValue.add(master)
                cDependence[ele] = depenValue  
    # The master is value difference or identical
    elif masterType == 3:
        masterValue = ""
        if master in cBVMap:
            masterValue = cBVMap[master]
        # type == 3, it has the correspondence
        rMasterSet = cToRIndex[master]
        for rMaster in rMasterSet:
            rMasterValue = ""
            if rMaster in rBVMap:
                rMasterValue = rBVMap[rMaster]
            # Switch statement should be specially handled
            # Switch statement has multiple exits
            # the branch value is the same, they should not be added
            if master in cSwitchSet or rMaster in rSwitchSet or cmp(masterValue, rMasterValue) != 0:
                if master not in cWorkSet:
                    cWorkList.append(master)
                    cWorkSet.add(master)
                if crossVersion == True:
                    if ele in rCorrespondence:
                        corresValue = rCorrespondence[ele]
                        corresValue.add(master)
                    else:
                        corresValue = set()
                        corresValue.add(master)
                        rCorrespondence[ele] = corresValue
                else:
                    if ele in cDependence:
                        depenValue = cDependence[ele]
                        depenValue.add(master)
                    else:
                        depenValue = set()
                        depenValue.add(master)
                        cDependence[ele] = depenValue
                        
# Add the data dependence
def dataDepAdded(ele, master, cWorkList, cWorkSet, cDependence, rDependence):
    if master not in cWorkSet:
        cWorkList.append(master)
        cWorkSet.add(master)
    if ele in cDependence:
        depenValue = cDependence[ele]
        depenValue.add(master)
    else:
        depenValue = set()
        depenValue.add(master)
        cDependence[ele] = depenValue 
        
# Compute the key predicate that leads to a statement is not be executed
# The computation is only in a function, otherwise, we return the call point
def keyPredicateComputation(beforeIndex, afterIndex, fileLineStr, caller, trace, CDGMap):
    # the scope of the function, the format: index
    (functionStart, functionEnd) = functionScope(caller, trace)
    # The scope of search is limited in the function
    if functionStart > beforeIndex:
        beforeIndex = functionStart
    if functionEnd < afterIndex:
        # because the search scope is [beforeIndex, afterIndex), we should add 1 to 
        # include the last instance of a function
        afterIndex = functionEnd + 1 
    workList = []
    workSet = set()
    workList.append(fileLineStr)
    workSet.add(fileLineStr)
    while len(workList) != 0:
        ele = workList.pop(0)
        if ele in CDGMap:
            eleCDG = CDGMap[ele]
            for eachCDG in eleCDG:
                if eachCDG not in workSet:
                    workList.append(eachCDG)
                    workSet.add(eachCDG)
    # the static control dependence, including direct and indirect dependence
    staticCDG = set()
    for eachLine in workSet:
        lineItem = eachLine.split(":")
        staticCDG.add(lineItem[1]) 
    callNumber = 0
    # the search scope is [beforeIndex, afterIndex)
    traceIndex = afterIndex - 1
    while traceIndex >= beforeIndex:
        eachLine = trace[traceIndex]
        if eachLine.find("#") != -1:
            callRet = callRetAbstract(eachLine)
            if callRet.find("C") != -1:
                callNumber = callNumber + 1
            elif callRet.find("R") != -1:
                callNumber = callNumber - 1
        if callNumber == 0:
            if eachLine in staticCDG:
                return traceIndex         
        traceIndex = traceIndex - 1
    # function call point
    return caller

# determine whether the beforeRStm and afterRStm are executed between beforeREle and afterREle
def aBExecuted(beforeIndex, afterIndex, beforeStm, afterStm, caller, trace):
    beforeItem = beforeStm.split(":")
    beforeLine = beforeItem[1]
    afterItem = afterStm.split(":")
    afterLine = afterItem[1]
    # the scope of the function, the format: index
    (functionStart, functionEnd) = functionScope(caller, trace)
    # The scope of search is limited in the function
    if functionStart > beforeIndex:
        beforeIndex = functionStart
    if functionEnd < afterIndex:
        afterIndex = functionEnd 
    beforeSign = False
    afterSign = False
    callNumber = 0 
    # the scope is [beforeIndex, afterIndex], which is different from keyPredicate   
    traceIndex = afterIndex 
    while traceIndex >= beforeIndex:
        eachLine = trace[traceIndex]
        if eachLine.find("#") != -1:
            callRet = callRetAbstract(eachLine)
            if callRet.find("C") != -1:
                callNumber = callNumber + 1
            elif callRet.find("R") != -1:
                callNumber = callNumber - 1
        if callNumber == 0:
            if cmp(eachLine, beforeLine) == 0:
                beforeSign = True
            if cmp(eachLine, afterLine) == 0:
                afterSign = True      
            if beforeSign == True and afterSign == True:
                break  
        traceIndex = traceIndex - 1
    return (beforeSign, afterSign)
       
# Handle the addition or deletion case in a function
# in which the function call points are correspondent
def addDeletionInFunction(ele, caller, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                          rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, cCallDep, cControlDep, \
                          cDataDep, cReturnDep, cBVMap, rBVMap, cSwitchSet, rSwitchSet, cPointCallName, rPointCallName, \
                          cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, cABInstance):
    if ele not in cABInstance:
        print "Addition or Deletion Case Error!"
        return
    # Compute the immediately previous and next elements of the element ele, 
    # the previous and next elements are correspondent, or they are -1 or len(list)
    # here, we do not require beforeIndex and afterIndex is non-added/non-deleted, because we require they are correspondent
    (beforeIndex, afterIndex) = beforeAfterEle(ele, cTrace, cToRIndex)
    beforeREleSet = set()
    # it is only a placeholder element
    beforeREleSet.add(0)
    if beforeIndex in cToRIndex:
        beforeREleSet = cToRIndex[beforeIndex]
    afterREleSet = set()
    # it is only a placeholder element
    afterREleSet.add(len(rTrace)-1)
    if afterIndex in cToRIndex:
        afterREleSet = cToRIndex[afterIndex]
    beforeREleList = list(beforeREleSet)
    beforeREleList.sort()
    afterREleList = list(afterREleSet)
    afterREleList.sort()
    beforeRLen = len(beforeREleList)
    afterRLen = len(afterREleList)
    beforeRIndex = 0 
    while beforeRIndex < beforeRLen:
        beforeREle = beforeREleList[beforeRIndex]
        beforeRIndex = beforeRIndex + 1
        afterRIndex = 0
        while afterRIndex < afterRLen:
            afterREle = afterREleList[afterRIndex]
            afterRIndex = afterRIndex + 1
            # afterEle must be greater or equal to beforeREle
            if beforeREle > afterREle:
                continue
            # beforeRIndex has been added by 1
            if beforeRIndex < beforeRLen:
                nextBeforeRELe = beforeREleList[beforeRIndex]
                # it is used to prevent that beforeREle and afterRele are intersected
                if nextBeforeRELe < afterREle:
                    break
            # afterIndex has been added by 1
            if afterRIndex-2 >= 0:
                previousAfterREle = afterREleList[afterRIndex-2]
                # it is used to prevent that beforeREle and afterRele are intersected
                if previousAfterREle > beforeREle:
                    break
            # Here, we consider that the beforeRStm and afterRStm are the same in two versions
            # if they are modified, they should be in the same hunk with the element ele
            # there is a little difference from the comments at the cABInstance computation 
            # in fact, even if beforeRStm or afterRStm are modified, it would not affect the correctness of our implementation
            # because we only add the unnecessary instance
            (beforeRStm, afterRStm) = cABInstance[ele]
            # determine whether the beforeRStm and afterRStm are executed between beforeREle and afterREle
            (beforeExeSign, afterExeSign) = aBExecuted(beforeREle, afterREle, beforeRStm, afterRStm, rCaller, rTrace)
            if beforeExeSign == False:
                # Compute the key predicate that leads to a statement is not be executed
                # The computation is only in a function, otherwise, we return the call point
                keyPredicate = keyPredicateComputation(beforeREle, afterREle, beforeRStm, rCaller, rTrace, rCDGMap)
                if keyPredicate != rCaller:
                    controlDepAdded(ele, keyPredicate, rWorkList, rWorkSet, cWorkList, cWorkSet, rDependence, cDependence, \
                                    rCorrespondence, cCorrespondence, rToCIndex, rBVMap, cBVMap, \
                                    rSwitchSet, cSwitchSet, rModificationSet, rAddDelSet, True) 
            if afterExeSign == False:
                keyPredicate = keyPredicateComputation(beforeREle, afterREle, afterRStm, rCaller, rTrace, rCDGMap)
                if keyPredicate != rCaller:
                    controlDepAdded(ele, keyPredicate, rWorkList, rWorkSet, cWorkList, cWorkSet, rDependence, cDependence, \
                                    rCorrespondence, cCorrespondence, rToCIndex, rBVMap, cBVMap, \
                                    rSwitchSet, cSwitchSet, rModificationSet, rAddDelSet, True) 
            # It represents that the added or deleted statement is also the control flow difference
            # we also add the control dependence of the element ele
            if beforeExeSign == False or afterExeSign == False:                    
                if ele in cControlDep:
                    controlMaster = cControlDep[ele]
                    controlDepAdded(ele, controlMaster, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                    cCorrespondence, rCorrespondence, cToRIndex, cBVMap, rBVMap, \
                                    cSwitchSet, rSwitchSet, cModificationSet, cAddDelSet, False)
    if ele in cDataDep:
        dataDepList = cDataDep[ele]
        for eachDataDep in dataDepList:
            # List([traceIndex, Value, True/False]/[traceIndex, Value, True/False,  [traceIndex,[traceIndex, [...., List([traceIndex, Value, True/False]]))])
            # the data dependence is the general variable definition and usage
            if len(eachDataDep) == 3:
                dataDepAdded(ele, eachDataDep[0], cWorkList, cWorkSet, cDependence, rDependence)
            # the data dependence is through parameter, the form is [traceIndex, Value, True/False, [traceIndex,[traceIndex, [...., List([traceIndex, Value, True/False]]))]
            elif len(eachDataDep) == 4:
                dataDepAdded(ele, eachDataDep[0], cWorkList, cWorkSet, cDependence, rDependence)
                parameterDataSet = eachDataDep[3]
                while type(parameterDataSet[0]) is types.IntType:
                    # parameterDataSet[0] is the function call point
                    dataDepAdded(ele, parameterDataSet[0], cWorkList, cWorkSet, cDependence, rDependence)
                    parameterDataSet = parameterDataSet[1] 
                for parameterData in parameterDataSet:
                    dataDepAdded(ele, parameterData[0], cWorkList, cWorkSet, cDependence, rDependence)
    if ele in cReturnDep:
        # the data dependence derived from function return
        # return data dependence does not include the return value
        returnDataSet = cReturnDep[ele]
        for returnData in returnDataSet:
            dataDepAdded(ele, returnData, cWorkList, cWorkSet, cDependence, rDependence)
    
# Handle the addition or deletion case
def addDeletionCase(ele, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                    rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, cCallDep, \
                    cControlDep, cDataDep, cReturnDep, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                    cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, cABInstance):
    # the caller of main function is set to -1
    # we first consider the its call point
    caller = callPoint(ele, cControlDep, cCallDep)
    callType = typeOfELe(caller, cToRIndex, cModificationSet, cAddDelSet)
    # the function call point is addition, deletion or control difference case
    if callType == 0 or callType == 2:
        # if the call point is still addition/deletion or control difference, 
        # we only add the call point
        if caller not in cWorkSet:
            cWorkList.append(caller)
            cWorkSet.add(caller)
        if ele in cDependence:
            depenValue = cDependence[ele]
            depenValue.add(caller)
        else:
            depenValue = set()
            depenValue.add(caller)
            cDependence[ele] = depenValue     
    # it is for modification, there are two cases:
    # if the call point has the correspondence, we should enter the function and compare the statement instances 
    # if the call point has no correspondence, we only add the call point
    elif callType == 1:
        functionCorrespondent = False
        # the correspondence of call points has been computed
        # maybe the correspondence is not complete, but its correspondent function call point is complete
        if caller in cToRIndex:
            cFunctionName = cPointCallName[caller]
            rCallerSet = cToRIndex[caller]
            for rCaller in rCallerSet:
                if rCaller in rPointCallName:
                    rFunctionName = rPointCallName[rCaller]
                    # Both traces call the same function 
                    # The function call point is correspondent, we enter the function 
                    if cmp(cFunctionName, rFunctionName) == 0:
                        functionCorrespondent = True    
                        # Handle the addition or deletion case in a function
                        # in which the function call points are correspondent
                        addDeletionInFunction(ele, caller, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                                              rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, cCallDep, cControlDep, \
                                              cDataDep, cReturnDep, cBVMap, rBVMap, cSwitchSet, rSwitchSet, cPointCallName, rPointCallName, \
                                              cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, cABInstance) 
        # The function call point is not correspondent to any modification statement
        # We only add the function call point 
        if functionCorrespondent == False:
            if caller not in cWorkSet:
                cWorkList.append(caller)
                cWorkSet.add(caller)
            if ele in cDependence:
                depenValue = cDependence[ele]
                depenValue.add(caller)
            else:
                depenValue = set()
                depenValue.add(caller)
                cDependence[ele] = depenValue   
    elif callType == 3:
        rCallerSet = cToRIndex[caller]
        for rCaller in rCallerSet:
            addDeletionInFunction(ele, caller, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                                  rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, cCallDep, cControlDep, \
                                  cDataDep, cReturnDep, cBVMap, rBVMap, cSwitchSet, rSwitchSet, cPointCallName, rPointCallName, \
                                  cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, cABInstance)

# compute the statement that are not executed because of modification
def statementNotExecuted(ele, cToRLN, cToRIndex, rTrace):
    stmNotExecutedSet = set()
    statementSet = cToRLN[ele]
    instanceSet = set()
    if ele in cToRIndex:
        instanceSet = cToRIndex[ele]
    for eachStatement in statementSet:
        matched = False
        for eachInstance in instanceSet:
            instanceLN = rTrace[eachInstance]
            if cmp(instanceLN, eachStatement) == 0:
                matched = True
                break
        if matched == False:
            stmNotExecutedSet.add(eachStatement)
    # the format: set(lineNumber), not include the fileName
    return stmNotExecutedSet    
    
# Compute the key predicate for the modification
# the function "addKeyPredicateForModification" is called under the situation that their function call points are correspondent
def addKeyPredicateForModification(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                   cCorrespondence, rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, \
                                   cToRLN, rCDGMap, cCallDep, cControlDep, cPointCallName, rPointCallName, \
                                   cBVMap, rBVMap, cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, \
                                   cAddDelSet, rAddDelSet): 
    # Compute the immediately previous and next elements of the element ele, 
    # the previous and next elements are correspondent, or they are -1 or len(list)
    (beforeIndex, afterIndex) = beforeAfterEle(ele, cTrace, cToRIndex)
    beforeREleSet = set()
    # it is only a placeholder element
    beforeREleSet.add(0)
    if beforeIndex in cToRIndex:
        beforeREleSet = cToRIndex[beforeIndex]
    afterREleSet = set()
    # it is only a placeholder element
    afterREleSet.add(len(rTrace)-1)
    if afterIndex in cToRIndex:
        afterREleSet = cToRIndex[afterIndex]
    beforeREleList = list(beforeREleSet)
    beforeREleList.sort()
    afterREleList = list(afterREleSet)
    afterREleList.sort()
    beforeRLen = len(beforeREleList)
    afterRLen = len(afterREleList)
    beforeRIndex = 0 
    while beforeRIndex < beforeRLen:
        beforeREle = beforeREleList[beforeRIndex]
        beforeRIndex = beforeRIndex + 1
        afterRIndex = 0
        while afterRIndex < afterRLen:
            afterREle = afterREleList[afterRIndex]
            afterRIndex = afterRIndex + 1
            # afterEle must be greater or equal to beforeREle
            if beforeREle > afterREle:
                continue
            # beforeRIndex has been added by 1
            if beforeRIndex < beforeRLen:
                nextBeforeRELe = beforeREleList[beforeRIndex]
                # it is used to prevent that beforeREle and afterRele are intersected
                if nextBeforeRELe < afterREle:
                    break
            # afterIndex has been added by 1
            if afterRIndex-2 >= 0:
                previousAfterREle = afterREleList[afterRIndex-2]
                # it is used to prevent that beforeREle and afterRele are intersected
                if previousAfterREle > beforeREle:
                    break
            # compute the statements that are not executed because of the modification
            stmNotExecutedSet = statementNotExecuted(ele, cToRLN, cToRIndex, rTrace)
            # if the corresponding modified statements are all executed, the control dependence 
            # of the element ele would not be added. This function comes form the function modificationInFunction
            if len(stmNotExecutedSet) != 0 and ele in cControlDep:
                controlMaster = cControlDep[ele]
                controlDepAdded(ele, controlMaster, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                cCorrespondence, rCorrespondence, cToRIndex, cBVMap, rBVMap, \
                                cSwitchSet, rSwitchSet, cModificationSet, cAddDelSet, False)
            # get the file name of the element ele
            fileName = fileNameEle(ele, cTrace)
            for stmNotExecuted in stmNotExecutedSet:
                stmNotExecuted = "%s:%s" % (fileName, stmNotExecuted)
                # Compute the key predicate that leads to a statement is not be executed
                # The computation is only in a function, otherwise, we return the call point
                keyPredicate = keyPredicateComputation(beforeREle, afterREle, stmNotExecuted, rCaller, rTrace, rCDGMap)
                if keyPredicate != rCaller:
                    controlDepAdded(ele, keyPredicate, rWorkList, rWorkSet, cWorkList, cWorkSet, rDependence, \
                                    cDependence, rCorrespondence, cCorrespondence, rToCIndex, rBVMap, cBVMap, \
                                    rSwitchSet, cSwitchSet, rModificationSet, rAddDelSet, True) 

# Handle the modification case in a function
def modificationInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                           cCorrespondence, rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, \
                           cCallDep, cControlDep, cDataDep, cReturnDep, cReturnCallMap, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                           cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet):  
    # if the element has no correspondence, we do not add the data dependence, which is similar to control flow difference 
    if ele in cToRIndex:
        # the following two if condition is used to add the data dependence
        if ele in cDataDep:
            dataDepList = cDataDep[ele]
            for eachDataDep in dataDepList:
                # List([traceIndex, Value, True/False]/[traceIndex, Value, True/False,  [traceIndex,[traceIndex, [...., List([traceIndex, Value, True/False]]))])
                # the data dependence is the general variable definition and usage
                if len(eachDataDep) == 3:
                    dataDepAdded(ele, eachDataDep[0], cWorkList, cWorkSet, cDependence, rDependence)
                # the data dependence is through parameter, the form is [traceIndex, Value, True/False, [traceIndex,[traceIndex, [...., List([traceIndex, Value, True/False]]))]
                elif len(eachDataDep) == 4:
                    dataDepAdded(ele, eachDataDep[0], cWorkList, cWorkSet, cDependence, rDependence)
                    parameterDataSet = eachDataDep[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        # parameterDataSet[0] is the function call point
                        dataDepAdded(ele, parameterDataSet[0], cWorkList, cWorkSet, cDependence, rDependence)
                        parameterDataSet = parameterDataSet[1] 
                    for parameterData in parameterDataSet:
                        dataDepAdded(ele, parameterData[0], cWorkList, cWorkSet, cDependence, rDependence)
        if ele in cReturnDep:
            # the data dependence derived from function return
            # return data dependence does not include the return value
            returnDataSet = cReturnDep[ele]
            for returnData in returnDataSet:
                dataDepAdded(ele, returnData, cWorkList, cWorkSet, cDependence, rDependence)        
    functionCorrespondent = False
    # if the function call point is modified, and there is the corresponding function call point
    # it is similar to the value difference, we do not add the control dependence
    if ele in cPointCallName and ele in cToRIndex:
        cFunctionName = cPointCallName[ele]
        rCallerSet = cToRIndex[ele]
        for rCaller in rCallerSet:
            if rCaller in rPointCallName:
                rFunctionName = rPointCallName[rCaller]
                if cmp(cFunctionName, rFunctionName) == 0:
                    functionCorrespondent = True
                    break
    # if the ele is function return point, we consider its corresponding call point
    if ele in cReturnCallMap:
        controlMaster = cReturnCallMap[ele]
        if controlMaster in cPointCallName and controlMaster in cToRIndex:
            cFunctionName = cPointCallName[controlMaster]
            rCallerSet = cToRIndex[controlMaster]
            for rCaller in rCallerSet:
                if rCaller in rPointCallName:
                    rFunctionName = rPointCallName[rCaller]
                    if cmp(cFunctionName, rFunctionName) == 0:
                        functionCorrespondent = True
                        break
    if functionCorrespondent == False:
        # We have removed this function into the addKeyPredicateForModification
        """
        if ele in cControlDep:
            controlMaster = cControlDep[ele]
            controlDepAdded(ele, controlMaster, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                            cCorrespondence, rCorrespondence, cToRIndex, cBVMap, rBVMap, \
                            cSwitchSet, rSwitchSet, cModificationSet, cAddDelSet, False)
        """                    
        # it is similar to the control flow difference
        addKeyPredicateForModification(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                       cCorrespondence, rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, \
                                       rCDGMap, cCallDep, cControlDep, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                                       cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet)
                       
# Handle the modification case
def modificationCase(ele, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                     rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, cCallDep, \
                     cControlDep, cDataDep, cReturnDep, cReturnCallMap, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                     cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet):
    # the caller of main function is set to -1
    # we first consider the its call point
    caller = callPoint(ele, cControlDep, cCallDep)
    callType = typeOfELe(caller, cToRIndex, cModificationSet, cAddDelSet)
    # the modification type of the element has higher priority than the control flow difference
    # therefore, the modification type can also be control flow difference
    # the function call point is addition, deletion or control difference case
    if callType == 0 or callType == 2:
        if caller not in cWorkSet:
            cWorkList.append(caller)
            cWorkSet.add(caller)
        if ele in cDependence:
            depenValue = cDependence[ele]
            depenValue.add(caller)
        else:
            depenValue = set()
            depenValue.add(caller)
            cDependence[ele] = depenValue 
    # it is for modification, there are two cases:
    # if the call point has the correspondence, we should enter the function and compare the statement instances 
    # if the call point has no correspondence, we only add the call point
    elif callType == 1:
        functionCorrespondent = False
        if caller in cToRIndex:
            cFunctionName = cPointCallName[caller]
            rCallerSet = cToRIndex[caller]
            for rCaller in rCallerSet:
                # rCallerSet may include the elements that are not function call points
                if rCaller in rPointCallName:
                    rFunctionName = rPointCallName[rCaller]
                    # The function call is correspondent, handle the control difference into the function 
                    if cmp(cFunctionName, rFunctionName) == 0:
                        modificationInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                                cCorrespondence, rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, \
                                                cCallDep, cControlDep, cDataDep, cReturnDep, cReturnCallMap, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                                                cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet)    
                        functionCorrespondent = True
                        break
        # The function calling is not correspondent to any modification statement
        # We only add the function call point 
        if functionCorrespondent == False:
            if caller not in cWorkSet:
                cWorkList.append(caller)
                cWorkSet.add(caller) 
            if ele in cDependence:
                depenValue = cDependence[ele]
                depenValue.add(caller)
            else:
                depenValue = set()
                depenValue.add(caller)
                cDependence[ele] = depenValue      
    # the function call points are not modified
    # the correspondent call points have the same function calling
    elif callType == 3:
        if caller in cToRIndex:
            rCallerSet = cToRIndex[caller]
            for rCaller in rCallerSet:        
                modificationInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                                       cCorrespondence, rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rCDGMap, \
                                       cCallDep, cControlDep, cDataDep, cReturnDep, cReturnCallMap, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                                       cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet)  

# Handle the control difference in a function 
def controlInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence,  cCorrespondence, \
                      rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, rCDGMap, cControlDep, cBVMap, \
                      rBVMap, cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet):
    if ele in cControlDep:
        controlMaster = cControlDep[ele]
        controlDepAdded(ele, controlMaster, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, \
                        cCorrespondence, rCorrespondence, cToRIndex, cBVMap, rBVMap, \
                        cSwitchSet, rSwitchSet, cModificationSet, cAddDelSet, False)    
    # the correspondent fileName:lineNumber is the same
    (fileName, lineNumber) = fileLineNumberEle(ele, cTrace)
    stmNotExecuted = "%s:%s" % (fileName, lineNumber)
    # Compute the immediately previous and next elements of the element ele, 
    # the previous and next elements are correspondent, or they are -1 or len(list)
    (beforeIndex, afterIndex) = beforeAfterEle(ele, cTrace, cToRIndex)
    beforeREleSet = set()
    # it is only a placeholder element
    beforeREleSet.add(0)
    if beforeIndex in cToRIndex:
        beforeREleSet = cToRIndex[beforeIndex]
    afterREleSet = set()
    # it is only a placeholder element
    afterREleSet.add(len(rTrace)-1)
    if afterIndex in cToRIndex:
        afterREleSet = cToRIndex[afterIndex]
    beforeREleList = list(beforeREleSet)
    beforeREleList.sort()
    afterREleList = list(afterREleSet)
    afterREleList.sort()
    beforeRLen = len(beforeREleList)
    afterRLen = len(afterREleList)
    beforeRIndex = 0 
    while beforeRIndex < beforeRLen:
        beforeREle = beforeREleList[beforeRIndex]
        beforeRIndex = beforeRIndex + 1
        afterRIndex = 0
        while afterRIndex < afterRLen:
            afterREle = afterREleList[afterRIndex]
            afterRIndex = afterRIndex + 1
            # afterEle must be greater or equal to beforeREle
            if beforeREle > afterREle:
                continue
            # beforeRIndex has been added by 1
            if beforeRIndex < beforeRLen:
                nextBeforeRELe = beforeREleList[beforeRIndex]
                # it is used to prevent that beforeREle and afterRele are intersected
                if nextBeforeRELe < afterREle:
                    break
            # afterIndex has been added by 1
            if afterRIndex-2 >= 0:
                previousAfterREle = afterREleList[afterRIndex-2]
                # it is used to prevent that beforeREle and afterRele are intersected
                if previousAfterREle > beforeREle:
                    break
            # Compute the key predicate that leads to a statement is not be executed
            # The computation is only in a function, otherwise, we return the call point
            keyPredicate = keyPredicateComputation(beforeREle, afterREle, stmNotExecuted, rCaller, rTrace, rCDGMap)
            if keyPredicate != rCaller:
                controlDepAdded(ele, keyPredicate, rWorkList, rWorkSet, cWorkList, cWorkSet, rDependence, cDependence, \
                                rCorrespondence, cCorrespondence, rToCIndex, rBVMap, cBVMap, \
                                rSwitchSet, cSwitchSet, rModificationSet, rAddDelSet, True) 
      
# Handle the control difference case                     
def controlDiffCase(ele, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                    rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rToCLN, \
                    rCDGMap, cCallDep, cControlDep, cPointCallName, rPointCallName, cBVMap, rBVMap, \
                    cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet):
    # the caller of main function is set to -1
    # we first consider the its call point
    caller = callPoint(ele, cControlDep, cCallDep)
    callType = typeOfELe(caller, cToRIndex, cModificationSet, cAddDelSet)
    # the modification type of the element has higher priority than the control flow difference
    # therefore, the modification type can also be control flow difference
    # the function call point is addition, deletion or control difference case
    if callType == 0 or callType == 2:
        if caller not in cWorkSet:
            cWorkList.append(caller)
            cWorkSet.add(caller)
        if ele in cDependence:
            depenValue = cDependence[ele]
            depenValue.add(caller)
        else:
            depenValue = set()
            depenValue.add(caller)
            cDependence[ele] = depenValue 
    # it is for modification, there are two cases:
    # if the call point has the correspondence, we should enter the function and compare the statement instances 
    # if the call point has no correspondence, we only add the call point
    elif callType == 1:
        functionCorrespondent = False
        if caller in cToRIndex:
            cFunctionName = cPointCallName[caller]
            rCallerSet = cToRIndex[caller]
            for rCaller in rCallerSet:
                if rCaller in rPointCallName:
                    rFunctionName = rPointCallName[rCaller]
                    # The function calling is correspondent, handle the control difference into the function 
                    if cmp(cFunctionName, rFunctionName) == 0:
                        controlInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence,  cCorrespondence, \
                                          rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, rCDGMap, cControlDep, cBVMap, \
                                          rBVMap, cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet)    
                        functionCorrespondent = True
        # The function calling is not correspondent to any modification statement
        # We only add the function calling 
        if functionCorrespondent == False:
            if caller not in cWorkSet:
                cWorkList.append(caller)
                cWorkSet.add(caller) 
            if ele in cDependence:
                depenValue = cDependence[ele]
                depenValue.add(caller)
            else:
                depenValue = set()
                depenValue.add(caller)
                cDependence[ele] = depenValue        
    elif callType == 3:
        # the statement that are not modified
        # the correspondent has the same function calling
        rCallerSet = cToRIndex[caller]
        for rCaller in rCallerSet:
            controlInFunction(ele, rCaller, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence,  cCorrespondence, \
                             rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, rCDGMap, cControlDep, cBVMap, \
                              rBVMap, cSwitchSet, rSwitchSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet)  

# compute the data dependence chain
def dataDepChain(ele, dataDep, returnDep):
    workList = []
    workSet = set()
    workList.append(ele)
    workSet.add(ele)
    while len(workList) != 0:
        ele = workList.pop(0)
        if ele in dataDep:
            dataSet = dataDep[ele]
            for eachData in dataSet:
                dataIndex = eachData[0]
                if dataIndex not in workSet:
                    workList.append(dataIndex)
                    workSet.add(dataIndex)
        if ele in returnDep:
            dataSet = returnDep[ele]
            for eachData in dataSet:
                if eachData not in workSet:
                    workList.append(eachData)
                    workSet.add(eachData)
    return workSet    

# compare whether the data dependence chain is equivalent
# if the statement is modification, it is not matched
def compareDataList(cDataList, rDataList, cSrcDstMap, cModificationSet, rSrcDstMap, rModificationSet):
    for eachEle in cDataList:
        if eachEle in cModificationSet:
            return False
        if eachEle in cSrcDstMap:
            matched = False
            corresEle = cSrcDstMap[eachEle]
            for eachCorres in corresEle:
                if eachCorres in rDataList:
                    matched = True
                    break
            if matched == False:
                return False
        else:
            return False
    for eachEle in rDataList:
        if eachEle in rModificationSet:
            return False
        if eachEle in rSrcDstMap:
            matched = False
            corresEle = rSrcDstMap[eachEle]
            for eachCorres in corresEle:
                if eachCorres in cDataList:
                    matched = True
                    break
            if matched == False:
                return False
        else:
            return False
    return True

# find the immediately next instance that is correspondent
def afterEleCalculation(ele, trace, cRIndex):
    afterIndex = ele + 1
    while afterIndex < len(trace):
        if afterIndex in cRIndex:
            break
        else:
            afterIndex = afterIndex + 1
    return afterIndex

# if dataEle is before rDataEle, it would not be added
# because the difference is caused by rDataDepEle[0]
def ABCompareEle(dataEle, rDataEle, cTrace, cToRIndex):
    if dataEle in cToRIndex:
        corresDataEleSet = cToRIndex[dataEle]
        for corresDataEle in corresDataEleSet:
            # it represents that dataEle is after rDataEle
            if corresDataEle >= rDataEle:
                return True
        return False
    else:
        # maybe dataEle has no the correspondence
        # find the immediately next instance that is correspondent
        afterEle = afterEleCalculation(dataEle, cTrace, cToRIndex)
        # cToRIndex is computed based on the requirement
        # if afterEle is not in cToRIndex, maybe it is cross the function
        if afterEle in cToRIndex: 
            corresAfterEleSet = cToRIndex[afterEle]
            for corresAfterEle in corresAfterEleSet:
                if corresAfterEle > rDataEle:
                    return True
            return False 
        else:
            return True      
                
# Handle the value difference case
def valueDiffCase(appName, ele, cWorkList, cWorkSet, rWorkList, rWorkSet, cDependence, rDependence, cCorrespondence, \
                  rCorrespondence, cTrace, rTrace, cToRIndex, rToCIndex, cToRLN, rToCLN, rCDGMap, \
                  cCallDep, cControlDep, rControlDep, cDataDep, rDataDep, cReturnDep, rReturnDep, cPointCallName, \
                  rPointCallName, cBVMap, rBVMap, cSwitchSet, rSwitchSet, cModificationSet, \
                  rModificationSet, cAddDelSet, rAddDelSet, cDataTrace, rDataTrace, cCodeDataTrace, rCodeDataTrace, \
                  cDataToTrace, rDataToTrace, cTraceToData, rTraceToData, cDataToCode, rDataToCode, \
                  cCodeToData, rCodeToData, cCodeToBlock, rCodeToBlock, cPointerSet, rPointerSet, \
                  cCallG, rCallG, cReversedCallG, rReversedCallG, cLoopSet, rLoopSet, cCallReturnBoth, \
                  rCallReturnBoth, cPureCallSet, rPureCallSet, cPureReturnSet, rPureReturnSet):
    if ele in cDataDep:
        dataDepList = cDataDep[ele]
        dataDepLen = len(dataDepList)
        # dataLen is the data dependence length that can be compared, which is used to prevent the short circuit operator
        dataLen = dataDepLen
        # value difference must have the correspondent instance
        rEleSet = cToRIndex[ele]
        for rEle in rEleSet:
            if rEle in rDataDep:
                rDataDepList = rDataDep[rEle]
                rDataDepLen = len(rDataDepList)
                if rDataDepLen < dataLen:
                    dataLen = rDataDepLen
                for dataIndex in range(0, dataLen):
                    dataDepEle = dataDepList[dataIndex]
                    rDataDepEle = rDataDepList[dataIndex]
                    # the used variable is an pointer
                    if dataDepEle[2] == True and rDataDepEle[2] == True:
                        cDataSet = set()
                        if len(dataDepEle) == 3:
                            cDataSet.add(dataDepEle[0])
                        elif len(dataDepEle) == 4:
                            parameterDataSet = dataDepEle[3]
                            while type(parameterDataSet[0]) is types.IntType:
                                parameterDataSet = parameterDataSet[1]
                            for parameterData in parameterDataSet:
                                if parameterData[2] == True:
                                    cDataSet.add(parameterData[0])
                        rDataSet = set()
                        if len(rDataDepEle) == 3:
                            rDataSet.add(rDataDepEle[0])
                        elif len(rDataDepEle) == 4:
                            parameterDataSet = rDataDepEle[3]
                            while type(parameterDataSet[0]) is types.IntType:
                                parameterDataSet = parameterDataSet[1]                           
                            for parameterData in parameterDataSet:
                                if parameterData[2] == True:
                                    rDataSet.add(parameterData[0])
                        # the pointer comparison is still based on the offset technique
                        pointerEqual = pointerCompare(appName, cDataSet, rDataSet, dataDepEle[1], rDataDepEle[1], cToRIndex, rToCIndex, cDataDep, \
                                                       rDataDep, cReturnDep, rReturnDep, cDataTrace, rDataTrace, cCodeDataTrace, rCodeDataTrace, \
                                                       cDataToTrace, rDataToTrace, cTraceToData, rTraceToData, cDataToCode, rDataToCode, \
                                                       cCodeToData, rCodeToData, cCodeToBlock, rCodeToBlock, cPointCallName, rPointCallName, \
                                                       cPointerSet, rPointerSet, cModificationSet, rModificationSet, cAddDelSet, rAddDelSet, \
                                                       cTrace, rTrace, cCallG, rCallG, cReversedCallG, rReversedCallG, cControlDep, rControlDep, \
                                                       cToRLN, rToCLN, cLoopSet, rLoopSet, cCallReturnBoth, rCallReturnBoth, cPureCallSet, \
                                                       rPureCallSet, cPureReturnSet, rPureReturnSet)
                        if pointerEqual == False:
                            if len(dataDepEle) == 3:
                                # if dataDepEle[0] is before rDataDepEle[0], it would not be added
                                # because the difference is caused by rDataDepEle[0]
                                dataAdded = ABCompareEle(dataDepEle[0], rDataDepEle[0], cTrace, cToRIndex)
                                if dataAdded == True:
                                    dataDepAdded(ele, dataDepEle[0], cWorkList, cWorkSet, cDependence, rDependence)
                            elif len(dataDepEle) == 4:
                                dataDepAdded(ele, dataDepEle[0], cWorkList, cWorkSet, cDependence, rDependence)
                                parameterDataSet = dataDepEle[3]
                                while type(parameterDataSet[0]) is types.IntType:
                                    dataDepAdded(ele, parameterDataSet[0], cWorkList, cWorkSet, cDependence, rDependence)
                                    parameterDataSet = parameterDataSet[1]
                                for parameterData in parameterDataSet:
                                    dataDepAdded(ele, parameterData[0], cWorkList, cWorkSet, cDependence, rDependence)
                    else:
                        # determine whether the values are the same
                        if cmp(dataDepEle[1], rDataDepEle[1]) != 0:
                            if len(dataDepEle) == 3:
                                # if dataDepEle[0] is before rDataDepEle[0], it would not be added
                                # because the difference is caused by rDataDepEle[0]
                                dataAdded = ABCompareEle(dataDepEle[0], rDataDepEle[0], cTrace, cToRIndex)
                                if dataAdded == True:
                                    dataDepAdded(ele, dataDepEle[0], cWorkList, cWorkSet, cDependence, rDependence)
                            elif len(dataDepEle) == 4:
                                dataDepAdded(ele, dataDepEle[0], cWorkList, cWorkSet, cDependence, rDependence)
                                parameterDataSet = dataDepEle[3]
                                while type(parameterDataSet[0]) is types.IntType:
                                    dataDepAdded(ele, parameterDataSet[0], cWorkList, cWorkSet, cDependence, rDependence)
                                    parameterDataSet = parameterDataSet[1]
                                for parameterData in parameterDataSet:
                                    dataDepAdded(ele, parameterData[0], cWorkList, cWorkSet, cDependence, rDependence)                
    if ele in cReturnDep:
        # the data dependence derived from function return
        # return data dependence does not include the return value
        returnDataSet = cReturnDep[ele]
        for returnData in returnDataSet:
            dataDepAdded(ele, returnData, cWorkList, cWorkSet, cDependence, rDependence)
    # the instance that has no data dependence or main function call point are also handled
    # because they are not in cDataDep and cReturnDep
        
def dataTraceHandle(dataFile, trace):
    try:
        dataTrace = open(dataFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        # the address and corresponding value, the form is [["W/R", address, value], ....]
        # the function call and return are not included
        dataTraceList = []
        # the map between data and trace, the form is <index, index>
        dataToTrace = {}
        # the map between trace and data, the format is <index: set(index)>
        traceToData = {} 
        fileName = ""
        fileNameList = []
        dataIndex = 0
        traceIndex = 0
        traceLen = len(trace)    
        for eachLines in dataTrace:
            # String that includes "$" is the function call or return
            if eachLines.find("$") != -1:
                continue
            eachLine = eachLines.strip()
            element = eachLine.split("#")
            fN = element[0]
            lN = element[1]
            dataInfo = element[2:]
            dataTraceList.append(dataInfo)
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
                            fileName = ""
                        functionName = functionNameAbstract(traceEle)
                        if cmp(functionName, "main") == 0:
                            return (dataTraceList, dataToTrace, traceToData)
                    traceIndex = traceIndex + 1
                else:
                    if cmp(fN, fileName) == 0 and cmp(lN, traceEle) == 0:
                        dataToTrace[dataIndex] = traceIndex
                        if traceIndex in traceToData:
                            dataValue = traceToData[traceIndex]
                            dataValue.append(dataIndex)     
                        else:
                            dataValue = []
                            dataValue.append(dataIndex)
                            traceToData[traceIndex] = dataValue
                        break
                    else:
                        traceIndex = traceIndex + 1     
            dataIndex = dataIndex + 1
        dataTrace.close()
        return (dataTraceList, dataToTrace, traceToData)
         
# blockForData: a block for read/written function parameters, the format is [[(index,eachLine), ....]/[], ...]
# index does not count the function call and return, and the eachLine is the string of dataOrCodeFile
# the element of list may be empty, because function call may have no parameter 
def blockForFunctionCall(dataOrCodeFile):
    try:
        dataOrCodeTrace = open(dataOrCodeFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        parameterBlock = []
        lineBlock = []
        lastLine = ""
        lastFile = ""
        dataOrCodeIndex = 0
        for eachLines in dataOrCodeTrace:
            eachLine = eachLines.strip()
            if eachLine.find("$") != -1:
                eachItem = eachLine.split("$")
                if eachItem[2].find("C") != -1:
                    # eachItem[3] is the lineNumber of the function call
                    if cmp(eachItem[3], lastLine) == 0:
                        parameterBlock.append(lineBlock)
                    else:
                        parameterBlock.append([])
                lineBlock = []
                lastLine = ""
                lastFile = ""
            else:
                eachItem = eachLine.split("#")
                curFile = eachItem[0]
                curLine = eachItem[1]
                if cmp(lastFile, curFile) == 0 and cmp(lastLine, curLine) == 0:
                    lineBlock.append((dataOrCodeIndex, eachLine))
                else:
                    lineBlock = []
                    lineBlock.append((dataOrCodeIndex, eachLine))
                    lastFile = curFile
                    lastLine = curLine    
                # the function call and return are not counted
                dataOrCodeIndex = dataOrCodeIndex + 1
        dataOrCodeTrace.close()
        return parameterBlock
    
def regNameFromCode(asmIns):
    if asmIns.find("ptr [eax") != -1:
        return "eax"
    elif asmIns.find("ptr [ebx") != -1:
        return "ebx"
    elif asmIns.find("ptr [ecx") != -1:
        return "ecx"
    elif asmIns.find("ptr [edx") != -1:
        return "edx"
    elif asmIns.find("ptr [esi") != -1:
        return "esi"
    elif asmIns.find("ptr [edi") != -1:
        return "edi"
    elif asmIns.find("ptr [esp") != -1:
        return "esp"
    elif asmIns.find("ptr [ebp") != -1:
        return "ebp"
    elif asmIns.find("ptr [es") != -1:
        return "es"
    elif asmIns.find("ptr [cs") != -1:
        return "cs"
    elif asmIns.find("ptr [fs") != -1:
        return "fs"
    elif asmIns.find("ptr [gs") != -1:
        return "gs"
    elif asmIns.find("ptr [eip") != -1:
        return "eip"
    elif asmIns.find("ptr [eflags") != -1:
        return "eflags"    
    elif asmIns.find("ptr [ax") != -1:
        return "ax" 
    elif asmIns.find("ptr [bx") != -1:
        return "bx" 
    elif asmIns.find("ptr [cx") != -1:
        return "cx" 
    elif asmIns.find("ptr [dx") != -1:
        return "dx" 
    else:
        return ""

# CodeTrace: the list that includes the code and read/written memory/register
# the code trace list is separated by the symbol "f$C", but the first element is not "f$C"
# reBlockForCode: its form is [[(index,eachLine), ...., "f$C"]/[], ...]
# index represents the sequence of CodeTrace
# especially, we add the register reading in the case: ptr [ebp + ...]
def reBlockForFunctionCall(blockForCode):
    codeTrace = []
    reBlockForCode = []
    blockIndex = 0
    for blockEle in blockForCode:
        reBlockEle = []
        for eachEle in blockEle:
            codeTrace.append(eachEle[1])
            reBlockEle.append((blockIndex, eachEle[1]))
            blockIndex = blockIndex + 1
            eachItem = eachEle[1].split("#")
            # sometimes the register is used to find the memory address
            # it is not independent used, and we should be extracted additionally
            # For example, the usage of register in: ptr [ebp + ...]
            if len(eachItem) == 3:
                regName = regNameFromCode(eachItem[2])
                if cmp(regName, "") != 0:
                    # additionally add the register that are read
                    regStr = eachItem[0] + "#" + eachItem[1] + "#" + "R" + "#" + regName
                    codeTrace.append(regStr)
                    reBlockEle.append((blockIndex, regStr))
                    blockIndex = blockIndex + 1
        # used to separate different function parameters that are read or written
        callingStr = "f$C"
        codeTrace.append(callingStr)
        reBlockEle.append((blockIndex, callingStr))
        blockIndex = blockIndex + 1
        reBlockForCode.append(reBlockEle)
    return (codeTrace, reBlockForCode)

# dataToCode/codeToData: the form is <index, index>
# especially, the index in data trace does not count the function call and return
# the index in codeData trace, we have inserted the "f$C" as the separator
# codeDataTrace: the list that includes the code and read/written memory/register, the form is [eachLine, ..."f$C", eachLine,...]        
def corresDataAndCode(dataFile, codeDataFile, dataToCode, codeToData): 
    # blockForData: a block for read/written function parameters, the format is [[(index,eachLine), ....]/[], ...]
    # index does not count the function call and return, and the eachLine is the string of dataOrCodeFile
    # the element of list may be empty, because function call may have no parameter 
    blockForData = blockForFunctionCall(dataFile)
    blockForCode = blockForFunctionCall(codeDataFile)
    # codeDataTrace: the list that includes the code and read/written memory/register, the form is [eachLine, ..."f$C", eachLine,...]
    # the code data trace list is separated by the symbol "f$C", but the first element is not "f$C"
    # blockForCode: its form is [[(index,eachLine), ...., "f$C"]/[], ...]
    # index represents the sequence of CodeTrace
    # especially, we add the register reading in the case: ptr [ebp + ...]
    (codeDataTrace, blockForCode) = reBlockForFunctionCall(blockForCode)
    blockIndex = 0
    # dataLen and codeLen must be equivalent
    dataLen = len(blockForData)
    codeLen = len(blockForCode)
    while blockIndex < dataLen and blockIndex < codeLen:
        eachDataBlock = blockForData[blockIndex]
        eachCodeBlock = blockForCode[blockIndex]
        eachDataIndex = 0
        eachCodeIndex = 0
        eachDataLen = len(eachDataBlock)
        eachCodelen = len(eachCodeBlock)
        while eachDataIndex < eachDataLen and eachCodeIndex < eachCodelen:
            eachDataEle = eachDataBlock[eachDataIndex]
            while True:
                eachCodeEle = eachCodeBlock[eachCodeIndex]
                eachCodeItem = eachCodeEle[1].split("#")
                if len(eachCodeItem) != 5:
                    # eachCodeEle is not the read/written memory
                    eachCodeIndex = eachCodeIndex + 1
                else:
                    break
            dataToCode[eachDataEle[0]] = eachCodeEle[0]
            codeToData[eachCodeEle[0]] = eachDataEle[0]        
            eachDataIndex = eachDataIndex + 1
            eachCodeIndex = eachCodeIndex + 1  
        blockIndex = blockIndex + 1     
    return codeDataTrace

# used to compute an index and the block that index belongs to
# the block is the list of read/written memory/register that belongs to an assembly instruction
# codeToBlock: the form is <index, [index, ...]>
def codeToBlock(codeDataTrace, codeToBlock):
    oneOfCode = []
    codeDataIndex = 0
    codeDataLen = len(codeDataTrace)
    while codeDataIndex < codeDataLen:
        codeDataEle = codeDataTrace[codeDataIndex]
        if codeDataEle.find("$") != -1:
            codeDataIndex = codeDataIndex + 1
            continue
        codeDataItem = codeDataEle.split("#")
        if len(codeDataItem) == 3:
            for eachEle in oneOfCode:
                codeToBlock[eachEle] = oneOfCode
            oneOfCode = []
        else:
            oneOfCode.append(codeDataIndex)
        codeDataIndex = codeDataIndex + 1
    for eachEle in oneOfCode:
        codeToBlock[eachEle] = oneOfCode
 
# srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile is used to compute the required data dependence               
# srcCDGMap, dstCDGMap: static control dependence graph and its the format is <fileName:lineNumber, set(fileName:lineNumber)>
# srcTrace, dstTrace: the format is [index, ....]
# srcToDstIndex, dstToSrcIndex: the trace alignment and it's format is <index, set(index)>
# at present, we only compute the alignment of the function call points
# srcToDstLN, dstToSrcLN: the index and its corresponding statement, it's format is <index, set(fileName:lineNumber)>
# srcControlDep, dstControlDep: dynamic control dependence, the format is <index, index>
# srcCallDep, dstCallDep: dynamic function call dependence, the format:<index, index>
# and the instances in the body of main function has no function call dependence
# srcReturnDep, dstReturnDep: dynamic function return dependence, the format is <index, [index, ...]>
# srcPoinCalltName, dstPointCallName: the function call point and it's corresponding function name, it's format is <index, functionName>
# srcModificationSet, dstModificationSet: the set of instances that are modified, the format is set<index>
# srcDeletionSet, dstAdditionSet: the set of instances that are deleted or added, the format is set<index>
# srcABInstance, dstABInstance: the instance and it's immediately before/next non-added/non-deleted statement, which may be modified
# the form is <index, [fileName:lineNumber, fileName:lineNumber]>
# srcBVMap, dstBVMap: the branch value of the conditional instances, the format: <index, "T/F">
# srcSwitchSet, dstSwitchSet: the set of switch instances, the format: set<index>
# sTarget, dTarget: the target differences, the form is set(index)
def dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, dstToSrcIndex, \
              srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
              srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
              srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, sTarget, dTarget): 
    # dataTrace: the form is [["W/R", address, value], ....], the function call and return are not counted
    # dataToTrace: the index of data to trace, the form is  <index, index>
    # traceToData: the index of trace to data, the form is <index, set(index)>
    (srcDataTrace, srcDataToTrace, srcTraceToData) = dataTraceHandle(srcDataFile, srcTrace)
    (dstDataTrace, dstDataToTrace, dstTraceToData) = dataTraceHandle(dstDataFile, dstTrace)
    # pointerSet: the form is set(index), note that the index is the same with srcDataTrace/dstDataTrace
    # which does not count the function call and return
    srcPointerSet = set()
    pointerDet(srcPointerSet, srcDataTrace)
    dstPointerSet = set()
    pointerDet(dstPointerSet, dstDataTrace)
    # srcDataToCode/srcCodeToData: the form is <index, index>
    # especially, the index in data trace does not count the function call and return
    # the index in codeData trace, we have inserted the "f$C" as the separator
    srcDataToCode = {}
    srcCodeToData = {}
    # codeDataTrace: the list that includes the code and read/written memory/register, the form is [eachLine, ..."f$C", eachLine,...]        
    srcCodeDataTrace = corresDataAndCode(srcDataFile, srcCodeDataFile, srcDataToCode, srcCodeToData)
    dstDataToCode = {}
    dstCodeToData = {}
    dstCodeDataTrace = corresDataAndCode(dstDataFile, dstCodeDataFile, dstDataToCode, dstCodeToData)
    # used to compute an index and the block that index belongs to
    # the block is the list of read/written memory/register that belongs to an assembly instruction
    # codeToBlock: the form is <index, [index, ...]>    
    srcCodeToBlock = {}
    codeToBlock(srcCodeDataTrace, srcCodeToBlock)  
    dstCodeToBlock = {}
    codeToBlock(dstCodeDataTrace, dstCodeToBlock)  
    # the dynamic data dependence, which is computed when required 
    srcDataDep = {}
    sWorkList = []
    sWorkSet = set()
    # the type of the element
    srcEleType = {}
    # the dependence map, only including the dependencies that are difference between two versions 
    srcDependence = {}
    # the element that are added through the corresponding trace
    srcCorrespondence = {}
    dstDataDep = {}
    dWorkList = []
    dWorkSet = set()
    dstEleType = {}
    dstDependence = {}
    dstCorrespondence = {}
    # the target differences that we begin with
    for eachTarget in sTarget:
        sWorkList.append(eachTarget)
        sWorkSet.add(eachTarget)
    for eachTarget in dTarget:
        dWorkList.append(eachTarget)
        dWorkSet.add(eachTarget)   
    while len(sWorkList) != 0 or len(dWorkList) != 0:
        while len(sWorkList) != 0:
            ele = sWorkList.pop()
            # compute the trace alignment of function body where the element ele belongs 
            # because addDeletionCase may use the alignment of other elements of such function body
            traceAlignBody(ele, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, \
                           srcReversedCallG, dstReversedCallG, srcControlDep, dstControlDep, srcToDstLN, dstToSrcLN, \
                           srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, dstPureCallSet, \
                           srcPureReturnSet, dstPureReturnSet)
            # the type of the element
            # 0 is added/deleted type; 1 is modified type; 2 is control flow difference; 3 is value difference or identical
            eleType = typeOfELe(ele, srcToDstIndex, srcModificationSet, srcDeletionSet)
            srcEleType[ele] = eleType
            if eleType == 0:
                # compute the dynamic data dependence of element ele
                dynamicDDEle(ele, srcDataDep, srcReturnDep, srcDataTrace, srcCodeDataTrace, srcPointerSet, srcPointCallName, \
                              srcDataToTrace, srcTraceToData, srcDataToCode, srcCodeToData, srcCodeToBlock, True)
                addDeletionCase(ele, sWorkList, sWorkSet, dWorkList, dWorkSet, srcDependence, dstDependence, srcCorrespondence, \
                                dstCorrespondence, srcTrace, dstTrace, srcToDstIndex, dstToSrcIndex, srcToDstLN, dstCDGMap, srcCallDep, \
                                srcControlDep, srcDataDep, srcReturnDep, srcPointCallName, dstPointCallName, srcBVMap, dstBVMap, \
                                srcSwitchSet, dstSwitchSet, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, srcABInstance)                                         
            elif eleType == 1:
                dynamicDDEle(ele, srcDataDep, srcReturnDep, srcDataTrace, srcCodeDataTrace, srcPointerSet, srcPointCallName, \
                              srcDataToTrace, srcTraceToData, srcDataToCode, srcCodeToData, srcCodeToBlock, True)
                modificationCase(ele, sWorkList, sWorkSet, dWorkList, dWorkSet, srcDependence, dstDependence, srcCorrespondence, \
                                 dstCorrespondence, srcTrace, dstTrace, srcToDstIndex, dstToSrcIndex, srcToDstLN, dstCDGMap, srcCallDep, \
                                 srcControlDep, srcDataDep, srcReturnDep, srcReturnCallMap, srcPointCallName, dstPointCallName, srcBVMap, dstBVMap, \
                                 srcSwitchSet, dstSwitchSet, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet)
            elif eleType == 2:
                controlDiffCase(ele, sWorkList, sWorkSet, dWorkList, dWorkSet, srcDependence, dstDependence, srcCorrespondence, \
                                dstCorrespondence, srcTrace, dstTrace, srcToDstIndex, dstToSrcIndex, srcToDstLN, dstToSrcLN, \
                                dstCDGMap, srcCallDep, srcControlDep, srcPointCallName, dstPointCallName, srcBVMap, dstBVMap, \
                                srcSwitchSet, dstSwitchSet, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet)
            elif eleType == 3:
                dynamicDDEle(ele, srcDataDep, srcReturnDep, srcDataTrace, srcCodeDataTrace, srcPointerSet, srcPointCallName, \
                              srcDataToTrace, srcTraceToData, srcDataToCode, srcCodeToData, srcCodeToBlock, True)
                if ele in srcToDstIndex:
                    dstEleSet = srcToDstIndex[ele]
                    for dstEle in dstEleSet:
                        dynamicDDEle(dstEle, dstDataDep, dstReturnDep, dstDataTrace, dstCodeDataTrace, dstPointerSet, dstPointCallName, \
                                      dstDataToTrace, dstTraceToData, dstDataToCode, dstCodeToData, dstCodeToBlock, True)                    
                valueDiffCase(appName, ele, sWorkList, sWorkSet, dWorkList, dWorkSet, srcDependence, dstDependence, srcCorrespondence, \
                              dstCorrespondence, srcTrace, dstTrace, srcToDstIndex, dstToSrcIndex, srcToDstLN, dstToSrcLN, dstCDGMap, \
                              srcCallDep, srcControlDep, dstControlDep, srcDataDep, dstDataDep, srcReturnDep, dstReturnDep, srcPointCallName, \
                              dstPointCallName, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, srcModificationSet, \
                              dstModificationSet, srcDeletionSet, dstAdditionSet, srcDataTrace, dstDataTrace, srcCodeDataTrace, dstCodeDataTrace, \
                              srcDataToTrace, dstDataToTrace, srcTraceToData, dstTraceToData, srcDataToCode, dstDataToCode, \
                              srcCodeToData, dstCodeToData, srcCodeToBlock, dstCodeToBlock, srcPointerSet, dstPointerSet, \
                              srcCallG, dstCallG, srcReversedCallG, dstReversedCallG, srcLoopSet, dstLoopSet, srcCallReturnBoth, \
                              dstCallReturnBoth, srcPureCallSet, dstPureCallSet, srcPureReturnSet, dstPureReturnSet)    
        while len(dWorkList)!=0:
            ele = dWorkList.pop()
            # compute the trace alignment of function body where the element ele belongs 
            # because addDeletionCase may use the alignment of other elements of such function body
            traceAlignBody(ele, dstToSrcIndex, srcToDstIndex, dstTrace, srcTrace, dstCallG, srcCallG, \
                           dstReversedCallG, srcReversedCallG, dstControlDep, srcControlDep, dstToSrcLN, srcToDstLN, \
                           dstLoopSet, srcLoopSet, dstCallReturnBoth, srcCallReturnBoth, dstPureCallSet, srcPureCallSet, \
                           dstPureReturnSet, srcPureReturnSet)
            # the type of the element
            # 0 is added/deleted type; 1 is modified type; 2 is control flow difference; 3 is value difference or identical
            eleType = typeOfELe(ele, dstToSrcIndex, dstModificationSet, dstAdditionSet)
            dstEleType[ele] = eleType
            if eleType == 0:
                # compute the dynamic data dependence of element ele
                dynamicDDEle(ele, dstDataDep, dstReturnDep, dstDataTrace, dstCodeDataTrace, dstPointerSet, dstPointCallName, \
                              dstDataToTrace, dstTraceToData, dstDataToCode, dstCodeToData, dstCodeToBlock, True)
                addDeletionCase(ele, dWorkList, dWorkSet, sWorkList, sWorkSet, dstDependence, srcDependence, dstCorrespondence, \
                                srcCorrespondence, dstTrace, srcTrace, dstToSrcIndex, srcToDstIndex, dstToSrcLN, srcCDGMap, dstCallDep, \
                                dstControlDep, dstDataDep, dstReturnDep, dstPointCallName, srcPointCallName, dstBVMap, srcBVMap, \
                                dstSwitchSet, srcSwitchSet, dstModificationSet, srcModificationSet, dstAdditionSet, srcDeletionSet, dstABInstance)                                         
            elif eleType == 1:
                dynamicDDEle(ele, dstDataDep, dstReturnDep, dstDataTrace, dstCodeDataTrace, dstPointerSet, dstPointCallName, \
                              dstDataToTrace, dstTraceToData, dstDataToCode, dstCodeToData, dstCodeToBlock, True)
                modificationCase(ele, dWorkList, dWorkSet, sWorkList, sWorkSet, dstDependence, srcDependence, dstCorrespondence, \
                                 srcCorrespondence, dstTrace, srcTrace, dstToSrcIndex, srcToDstIndex, dstToSrcLN, srcCDGMap, dstCallDep, \
                                 dstControlDep, dstDataDep, dstReturnDep, dstReturnCallMap, dstPointCallName, srcPointCallName, dstBVMap, srcBVMap, \
                                 dstSwitchSet, srcSwitchSet, dstModificationSet, srcModificationSet, dstAdditionSet, srcDeletionSet)
            elif eleType == 2:
                controlDiffCase(ele, dWorkList, dWorkSet, sWorkList, sWorkSet, dstDependence, srcDependence, dstCorrespondence, \
                                srcCorrespondence, dstTrace, srcTrace, dstToSrcIndex, srcToDstIndex, dstToSrcLN, srcToDstLN, \
                                srcCDGMap, dstCallDep, dstControlDep, dstPointCallName, srcPointCallName, dstBVMap, srcBVMap, \
                                dstSwitchSet, srcSwitchSet, dstModificationSet, srcModificationSet, dstAdditionSet, srcDeletionSet)
            elif eleType == 3:
                dynamicDDEle(ele, dstDataDep, dstReturnDep, dstDataTrace, dstCodeDataTrace, dstPointerSet, dstPointCallName, \
                              dstDataToTrace, dstTraceToData, dstDataToCode, dstCodeToData, dstCodeToBlock, True)
                if ele in dstToSrcIndex:
                    srcEleSet = dstToSrcIndex[ele]
                    for srcEle in srcEleSet:
                        dynamicDDEle(srcEle, srcDataDep, srcReturnDep, srcDataTrace, srcCodeDataTrace, srcPointerSet, srcPointCallName, \
                                      srcDataToTrace, srcTraceToData, srcDataToCode, srcCodeToData, srcCodeToBlock, True)                    
                valueDiffCase(appName, ele, dWorkList, dWorkSet, sWorkList, sWorkSet, dstDependence, srcDependence, dstCorrespondence, \
                              srcCorrespondence, dstTrace, srcTrace, dstToSrcIndex, srcToDstIndex, dstToSrcLN, srcToDstLN, srcCDGMap, \
                              dstCallDep, dstControlDep, srcControlDep, dstDataDep, srcDataDep, dstReturnDep, srcReturnDep, dstPointCallName, \
                              srcPointCallName, dstBVMap, srcBVMap, dstSwitchSet, srcSwitchSet, dstModificationSet, \
                              srcModificationSet, dstAdditionSet, srcDeletionSet, dstDataTrace, srcDataTrace, dstCodeDataTrace, srcCodeDataTrace, \
                              dstDataToTrace, srcDataToTrace, dstTraceToData, srcTraceToData, dstDataToCode, srcDataToCode, \
                              dstCodeToData, srcCodeToData, dstCodeToBlock, srcCodeToBlock, dstPointerSet, srcPointerSet, \
                              dstCallG, srcCallG, dstReversedCallG, srcReversedCallG, dstLoopSet, srcLoopSet, dstCallReturnBoth, \
                              srcCallReturnBoth, dstPureCallSet, srcPureCallSet, dstPureReturnSet, srcPureReturnSet)
    # order the regression slice
    srcRegressionSlice = list(sWorkSet)
    srcRegressionSlice.sort()
    dstRegressionSlice = list(dWorkSet)
    dstRegressionSlice.sort()
    return (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, dstCorrespondence, \
            srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData)

def printRegressionSlice(srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
               dstCorrespondence, srcTrace, dstTrace, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData):
    srcSliceFile = "/home/***/Experiment/Result/srcSlice.out"
    dstSliceFile = "/home/***/Experiment/Result/dstSlice.out"
    srcValueFile = "/home/***/Experiment/Result/srcValue.out"
    dstValueFile = "/home/***/Experiment/Result/dstValue.out" 
    srcDepenFile = "/home/***/Experiment/Result/srcDepen.out"
    dstDepenFile = "/home/***/Experiment/Result/dstDepen.out"
    srcCorresFile = "/home/***/Experiment/Result/srcCorres.out"
    dstCorresFile = "/home/***/Experiment/Result/dstCorres.out"
    try:
        sSliceFile = open(srcSliceFile, "w")
        dSliceFile = open(dstSliceFile, "w")
        sValueFile = open(srcValueFile, "w")
        dValueFile = open(dstValueFile, "w")
        sDepenFile = open(srcDepenFile, "w")
        dDepenFile = open(dstDepenFile, "w")
        sCorresFile = open(srcCorresFile, "w")
        dCorresFile = open(dstCorresFile, "w")

    except IOError, e:
        print "*** file open error:", e
    else:
        for srcTraceIndex in srcRegressionSlice:
            if srcTraceIndex != -1:
                fileName = fileNameEle(srcTraceIndex, srcTrace)
                srcTraceEle = srcTrace[srcTraceIndex]
                eleType = srcEleType[srcTraceIndex]
                if eleType == 0 or eleType == 1:
                    typeStr = "SRC"
                elif eleType == 2:
                    typeStr = "CTL"
                elif eleType == 3:
                    typeStr = "VAL"
                lineStr = "%d:%s:%s:%s\n" % (srcTraceIndex, fileName, srcTraceEle, typeStr)
                sSliceFile.write(lineStr)
        sSliceFile.close()
        for dstTraceIndex in dstRegressionSlice:
            if dstTraceIndex != -1:
                fileName = fileNameEle(dstTraceIndex, dstTrace)
                dstTraceEle = dstTrace[dstTraceIndex]
                eleType = dstEleType[dstTraceIndex]
                if eleType == 0 or eleType == 1:
                    typeStr = "SRC"
                elif eleType == 2:
                    typeStr = "CTL"
                elif eleType == 3:
                    typeStr = "VAL"
                lineStr = "%d:%s:%s:%s\n" % (dstTraceIndex, fileName, dstTraceEle, typeStr)
                dSliceFile.write(lineStr)
        dSliceFile.close()        
        for srcTraceIndex in srcRegressionSlice:
            if srcTraceIndex != -1:
                fileName = fileNameEle(srcTraceIndex, srcTrace)
                srcTraceEle = srcTrace[srcTraceIndex]
                if srcTraceIndex in srcTraceToData:
                    dataIndexSet = srcTraceToData[srcTraceIndex] 
                    for dataIndex in dataIndexSet:
                        dataValue = srcDataTrace[dataIndex]
                        lineStr = "%d:%s:%s@%s:%s:%s\n" % (srcTraceIndex, fileName, srcTraceEle, dataValue[0], dataValue[1], dataValue[2])
                        sValueFile.write(lineStr)
        sValueFile.close()   
        for dstTraceIndex in dstRegressionSlice:
            fileName = fileNameEle(dstTraceIndex, dstTrace)
            dstTraceEle = dstTrace[dstTraceIndex]
            if dstTraceIndex in dstTraceToData:
                dataIndexSet = dstTraceToData[dstTraceIndex] 
                for dataIndex in dataIndexSet:
                    dataValue = dstDataTrace[dataIndex]
                    lineStr = "%d:%s:%s@%s:%s:%s\n" % (dstTraceIndex, fileName, dstTraceEle, dataValue[0], dataValue[1], dataValue[2])
                    dValueFile.write(lineStr)
        dValueFile.close()                   
        for srcKey in srcDependence:
            keyFileName = fileNameEle(srcKey, srcTrace)
            keyEle = srcTrace[srcKey]
            depenValueSet = srcDependence[srcKey]
            for depenValue in depenValueSet:
                valueFileName = fileNameEle(depenValue, srcTrace)
                valueEle = srcTrace[depenValue]
                lineStr = "%d:%s:%s@%d:%s:%s\n" % (srcKey, keyFileName, keyEle, depenValue, valueFileName, valueEle)
                sDepenFile.write(lineStr)
        sDepenFile.close()
        for dstKey in dstDependence:
            keyFileName = fileNameEle(dstKey, dstTrace)
            keyEle = dstTrace[dstKey]
            depenValueSet = dstDependence[dstKey]
            for depenValue in depenValueSet:
                valueFileName = fileNameEle(depenValue, dstTrace)
                valueEle = dstTrace[depenValue]
                lineStr = "%d:%s:%s@%d:%s:%s\n" % (dstKey, keyFileName, keyEle, depenValue, valueFileName, valueEle)
                dDepenFile.write(lineStr)
        dDepenFile.close()        
        for srcKey in srcCorrespondence:
            keyFileName = fileNameEle(srcKey, srcTrace)
            keyEle = srcTrace[srcKey]
            corresValueSet = srcCorrespondence[srcKey]
            for corresValue in corresValueSet:
                valueFileName = fileNameEle(corresValue, dstTrace)
                valueEle = dstTrace[corresValue]
                lineStr = "%d:%s:%s@%d:%s:%s\n" % (srcKey, keyFileName, keyEle, corresValue, valueFileName, valueEle)
                sCorresFile.write(lineStr)
        sCorresFile.close()
        for dstKey in dstCorrespondence:
            keyFileName = fileNameEle(dstKey, dstTrace)
            keyEle = dstTrace[dstKey]
            corresValueSet = dstCorrespondence[dstKey]
            for corresValue in corresValueSet:
                valueFileName = fileNameEle(corresValue, srcTrace)
                valueEle = srcTrace[corresValue]
                lineStr = "%d:%s:%s@%d:%s:%s\n" % (dstKey, keyFileName, keyEle, corresValue, valueFileName, valueEle)
                dCorresFile.write(lineStr)
        dCorresFile.close()     
        
# compute the differences between two traces    
def _differenceCompute(srcRegressionSlice, dstRegressionSlice, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, \
                      srcDataFile, dstDataFile, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet):
    # dataTrace: the form is [["W/R", address, value], ....], the function call and return are not counted
    # dataToTrace: the index of data to trace, the form is  <index, index>
    # traceToData: the index of trace to data, the form is <index, set(index)>
    (srcDataTrace, srcDataToTrace, srcTraceToData) = dataTraceHandle(srcDataFile, srcTrace)
    (dstDataTrace, dstDataToTrace, dstTraceToData) = dataTraceHandle(dstDataFile, dstTrace)
    srcFlowNum = 0
    srcSameNum = 0
    dstFlowNum = 0
    dstSameNum = 0
    for eachEle in srcRegressionSlice:
        eleType = typeOfELe(eachEle, srcToDstIndex, srcModificationSet, srcDeletionSet)
        # the element is control flow difference
        if eleType == 2:
            srcFlowNum = srcFlowNum + 1
        # the element is value difference or identical
        # we should delete the identical instances
        if eleType == 3:
            if eachEle in srcTraceToData:
                srcDataSet = srcTraceToData[eachEle]
                rEleSet = srcToDstIndex[eachEle]
                for rEle in rEleSet:
                    if rEle in dstTraceToData:
                        dstDataSet = dstTraceToData[rEle]
                        srcDataLen = len(srcDataSet)
                        dstDataLen = len(dstDataSet)
                        if srcDataLen == dstDataLen:
                            dataIndex = 0
                            while dataIndex < srcDataLen:
                                srcDataEle = srcDataTrace[dataIndex]
                                dstDataEle = dstDataTrace[dataIndex]
                                if cmp(srcDataEle[0], dstDataEle[0]) != 0 or cmp(srcDataEle[1], dstDataEle[1]) != 0 or cmp(srcDataEle[2], dstDataEle[2]) != 0:
                                    break
                                dataIndex = dataIndex + 1
                            # there is an identical instance in other trace, we consider it is identical
                            # here, we don't need its all correspondent instances are the same 
                            if dataIndex == srcDataLen:
                                srcSameNum = srcSameNum + 1
                                break
            else:
                # the instance does not read or write the memory, therefore they are identical
                srcSameNum = srcSameNum + 1
    for eachEle in dstRegressionSlice:
        eleType = typeOfELe(eachEle, dstToSrcIndex, dstModificationSet, dstAdditionSet)
        if eleType == 2:
            dstFlowNum = dstFlowNum + 1
        if eleType == 3:
            if eachEle in dstTraceToData:
                dstDataSet = dstTraceToData[eachEle]
                rEleSet = dstToSrcIndex[eachEle]
                for rEle in rEleSet:
                    if rEle in srcTraceToData:
                        srcDataSet = srcTraceToData[rEle]
                        srcDataLen = len(srcDataSet)
                        dstDataLen = len(dstDataSet)
                        if srcDataLen == dstDataLen:
                            dataIndex = 0
                            while dataIndex < srcDataLen:
                                srcDataEle = srcDataTrace[dataIndex]
                                dstDataEle = dstDataTrace[dataIndex]
                                if cmp(srcDataEle[0], dstDataEle[0]) != 0 or cmp(srcDataEle[1], dstDataEle[1]) != 0 or cmp(srcDataEle[2], dstDataEle[2]) != 0:
                                    break
                                dataIndex = dataIndex + 1
                            if dataIndex == srcDataLen:
                                dstSameNum = dstSameNum + 1
                                break
            else:
                dstSameNum = dstSameNum + 1
    # compute the difference between two regression slices
    srcLen = len(srcRegressionSlice) - srcSameNum + dstFlowNum
    dstLen = len(dstRegressionSlice) - dstSameNum + srcFlowNum
    if -1 in srcRegressionSlice and -1 not in dstRegressionSlice:
        srcLen = srcLen - 1
    if -1 in dstRegressionSlice and -1 not in srcRegressionSlice:
        dstLen = dstLen - 1
    if srcLen > dstLen:
        return (srcLen, srcFlowNum, dstFlowNum)
    else:
        return (dstLen, srcFlowNum, dstFlowNum)  
    
# compute the differences between two traces    
def differenceCompute(srcSlice, dstSlice, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, \
                      srcDataFile, dstDataFile, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet):
    srcIdenticalNum = 0
    dstIdenticalNum = 0
    for eachEle in srcSlice:
        eleType = typeOfELe(eachEle, srcToDstIndex, srcModificationSet, srcDeletionSet)
        # the element is identical
        if eleType == 3:
            dstEleSet = srcToDstIndex[eachEle]
            for eachDstEle in dstEleSet:
                if eachDstEle in dstSlice:
                    srcIdenticalNum = srcIdenticalNum + 1
                    break
    for eachEle in dstSlice:
        eleType = typeOfELe(eachEle, dstToSrcIndex, dstModificationSet, dstAdditionSet)
        # the element is identical
        if eleType == 3:
            srcEleSet = dstToSrcIndex[eachEle]
            for eachSrcEle in srcEleSet:
                if eachSrcEle in srcSlice:
                    dstIdenticalNum = dstIdenticalNum + 1
                    break
    # the number of differences  
    # dstDiffLen is to subtract srcIdenticalNum
    # srcDiffLen is to subtract dstIndenticalNum
    dstDiffLen = len(srcSlice) + len(dstSlice) - srcIdenticalNum
    srcDiffLen = len(srcSlice) + len(dstSlice) - dstIdenticalNum
    if -1 in srcSlice or -1 in dstSlice:
        dstDiffLen = dstDiffLen - 1
        srcDiffLen = srcDiffLen - 1 
    # srcDiffLen may be different form dstDiffLen
    # because one element of srcSlice may correspond to multiple elements of dstSlice, vice versa.
    if srcDiffLen > dstDiffLen:
        return srcDiffLen
    else:
        return dstDiffLen
        
def dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, sTarget, dTarget):
    # dataTrace: the form is [["W/R", address, value], ....], the function call and return are not counted
    # dataToTrace: the index of data to trace, the form is  <index, index>
    # traceToData: the index of trace to data, the form is <index, set(index)>
    (srcDataTrace, srcDataToTrace, srcTraceToData) = dataTraceHandle(srcDataFile, srcTrace)
    (dstDataTrace, dstDataToTrace, dstTraceToData) = dataTraceHandle(dstDataFile, dstTrace)
    # pointerSet: the form is set(index), note that the index is the same with srcDataTrace/dstDataTrace
    # which does not count the function call and return
    srcPointerSet = set()
    pointerDet(srcPointerSet, srcDataTrace)
    dstPointerSet = set()
    pointerDet(dstPointerSet, dstDataTrace)
    # srcDataToCode/srcCodeToData: the form is <index, index>
    # especially, the index in data trace does not count the function call and return
    # the index in codeData trace, we have inserted the "f$C" as the separator
    srcDataToCode = {}
    srcCodeToData = {}
    # codeDataTrace: the list that includes the code and read/written memory/register, the form is [eachLine, ..."f$C", eachLine,...]        
    srcCodeDataTrace = corresDataAndCode(srcDataFile, srcCodeDataFile, srcDataToCode, srcCodeToData)
    dstDataToCode = {}
    dstCodeToData = {}
    dstCodeDataTrace = corresDataAndCode(dstDataFile, dstCodeDataFile, dstDataToCode, dstCodeToData)
    # used to compute an index and the block that index belongs to
    # the block is the list of read/written memory/register that belongs to an assembly instruction
    # codeToBlock: the form is <index, [index, ...]>    
    srcCodeToBlock = {}
    codeToBlock(srcCodeDataTrace, srcCodeToBlock)  
    dstCodeToBlock = {}
    codeToBlock(dstCodeDataTrace, dstCodeToBlock)  
    srcDataDep = {}
    sWorkList = []
    sWorkSet = set()
    dstDataDep = {}
    dWorkList = []
    dWorkSet = set()
    for eachTarget in sTarget:
        sWorkList.append(eachTarget)
        sWorkSet.add(eachTarget)
    while len(sWorkList) != 0:
        ele = sWorkList.pop(0)
        dynamicDDEle(ele, srcDataDep, srcReturnDep, srcDataTrace, srcCodeDataTrace, srcPointerSet, srcPointCallName, \
                      srcDataToTrace, srcTraceToData, srcDataToCode, srcCodeToData, srcCodeToBlock, False)
        if ele in srcDataDep:
            dataSet = srcDataDep[ele]
            for eachData in dataSet:
                if len(eachData) == 3:
                    if eachData[0] not in sWorkSet:
                        sWorkList.append(eachData[0])
                        sWorkSet.add(eachData[0])
                elif len(eachData) == 4:
                    if eachData[0] not in sWorkSet:
                        sWorkList.append(eachData[0])
                        sWorkSet.add(eachData[0])
                    parameterDataSet = eachData[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        if parameterDataSet[0] not in sWorkSet:
                            sWorkList.append(parameterDataSet[0])
                            sWorkSet.add(parameterDataSet[0])
                        parameterDataSet = parameterDataSet[1]
                    for parameterData in parameterDataSet:
                        if parameterData[0] not in sWorkSet:
                            sWorkList.append(parameterData[0])
                            sWorkSet.add(parameterData[0])
        if ele in srcReturnDep:
            returnDataSet = srcReturnDep[ele]
            for returnData in returnDataSet:
                if returnData not in sWorkSet:
                    sWorkList.append(returnData)
                    sWorkSet.add(returnData)
        if ele in srcCallDep:
            callDep = srcCallDep[ele]
            if callDep not in sWorkSet:
                sWorkList.append(callDep)
                sWorkSet.add(callDep)
        if ele in srcControlDep:
            controlDep = srcControlDep[ele]
            if controlDep not in sWorkSet:
                sWorkList.append(controlDep)
                sWorkSet.add(controlDep)
    print "Dynamic Slicing is finished in the original version!"
    for eachTarget in dTarget:
        dWorkList.append(eachTarget)
        dWorkSet.add(eachTarget)
    while len(dWorkList) != 0:
        ele = dWorkList.pop(0)
        dynamicDDEle(ele, dstDataDep, dstReturnDep, dstDataTrace, dstCodeDataTrace, dstPointerSet, dstPointCallName, \
                      dstDataToTrace, dstTraceToData, dstDataToCode, dstCodeToData, dstCodeToBlock, False)
        if ele in dstDataDep:
            dataSet = dstDataDep[ele]
            for eachData in dataSet:
                if len(eachData) == 3:
                    if eachData[0] not in dWorkSet:
                        dWorkList.append(eachData[0])
                        dWorkSet.add(eachData[0])
                elif len(eachData) == 4:
                    if eachData[0] not in dWorkSet:
                        dWorkList.append(eachData[0])
                        dWorkSet.add(eachData[0])
                    parameterDataSet = eachData[3]
                    while type(parameterDataSet[0]) is types.IntType:
                        if parameterDataSet[0] not in dWorkSet:
                            dWorkList.append(parameterDataSet[0])
                            dWorkSet.add(parameterDataSet[0])
                        parameterDataSet = parameterDataSet[1]
                    for parameterData in parameterDataSet:
                        if parameterData[0] not in dWorkSet:
                            dWorkList.append(parameterData[0])
                            dWorkSet.add(parameterData[0])
        if ele in dstReturnDep:
            returnDataSet = dstReturnDep[ele]
            for returnData in returnDataSet:
                if returnData not in dWorkSet:
                    dWorkList.append(returnData)
                    dWorkSet.add(returnData)
        if ele in dstCallDep:
            callDep = dstCallDep[ele]
            if callDep not in dWorkSet:
                dWorkList.append(callDep)
                dWorkSet.add(callDep)
        if ele in dstControlDep:
            controlDep = dstControlDep[ele]
            if controlDep not in dWorkSet:
                dWorkList.append(controlDep)
                dWorkSet.add(controlDep)
    print "Dynamic Slicing is finished in the modified version!"
    # order the regression slice
    srcDynamicSlice = list(sWorkSet)
    srcDynamicSlice.sort()
    dstDynamicSlice = list(dWorkSet)
    dstDynamicSlice.sort()
    return (srcDynamicSlice, dstDynamicSlice)

def printDynamicSlice(srcDynamicSlice, dstDynamicSlice, srcTrace, dstTrace):
    srcSliceFile = "/home/***/Experiment/Result/srcDynamicSlice.out"
    dstSliceFile = "/home/***/Experiment/Result/dstDynamicSlice.out"
    try:
        srcFile = open(srcSliceFile, "w")
        dstFile = open(dstSliceFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        for eachIndex in srcDynamicSlice:
            if eachIndex != -1:
                fileName = fileNameEle(eachIndex, srcTrace)
                eachEle = srcTrace[eachIndex]
                lineStr = "%d#%s:%s\n" % (eachIndex, fileName, eachEle)
                srcFile.write(lineStr)
        srcFile.close()
        for eachIndex in dstDynamicSlice:
            if eachIndex != -1:
                fileName = fileNameEle(eachIndex, dstTrace)
                eachEle = dstTrace[eachIndex]
                lineStr = "%d#%s:%s\n" % (eachIndex, fileName, eachEle)
                dstFile.write(lineStr)
        dstFile.close()      
        
def printResult(srcRegressionSliceLen, dstRegressionSliceLen, diffRegressionNum, \
                srcDynamicSliceLen, dstDynamicSliceLen, diffDynamicNum):
    resultFilePath = "/home/***/Experiment/Result/result.out"
    try:
        resultFile = open(resultFilePath, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        srcRegressionLen = "src Regression Slicing: %d\n" % (srcRegressionSliceLen)
        dstRegressionLen = "dst Regression Slicing: %d\n" % (dstRegressionSliceLen)
        diffRegressionLen = "Difference Number in Regression Slicing: %d\n" % (diffRegressionNum)
        resultFile.write(srcRegressionLen)
        resultFile.write(dstRegressionLen)
        resultFile.write(diffRegressionLen)        
        resultFile.write("Regression Slice Done!\n")
        srcDynamicLen = "src Dynamic Slicing: %d\n" % (srcDynamicSliceLen)
        dstDynamicLen = "dst Dynamic Slicing: %d\n" % (dstDynamicSliceLen)
        diffDynamicLen = "Difference Number in Dynamic Slicing: %d\n" % (diffDynamicNum)
        resultFile.write(srcDynamicLen)
        resultFile.write(dstDynamicLen)
        resultFile.write(diffDynamicLen)        
        resultFile.write("Dynamic Slice Done!\n")
                        
if __name__ == '__main__':
    #the programs that are analyzed
    appName = "find_b"
    if cmp(appName, "test") == 0:
        #test
        srcDirectory = "/home/***/Experiment/Object/test/original"
        dstDirectory = "/home/***/Experiment/Object/test/modified"
    elif cmp(appName, "find_a") == 0:
        #find_a
        srcDirectory = "/home/***/Experiment/Object/find_a/findutils-4.2.15"
        dstDirectory = "/home/***/Experiment/Object/find_a/findutils-4.2.18"
    elif cmp(appName, "find_b") == 0 or cmp(appName, "find_c") == 0:
        #find_b find_c
        srcDirectory = "/home/***/Experiment/Object/find_b_c/findutils-4.3.5"
        dstDirectory = "/home/***/Experiment/Object/find_b_c/findutils-4.3.6"
    elif cmp(appName, "make") == 0:
        #make
        srcDirectory = "/home/***/Experiment/Object/make/make-3.80"
        dstDirectory = "/home/***/Experiment/Object/make/make-3.81"
    elif cmp(appName, "bc") == 0:
        #bc 
        srcDirectory = "/home/***/Experiment/Object/bc/bc-1.05"
        dstDirectory = "/home/***/Experiment/Object/bc/bc-1.06"  
    elif cmp(appName, "diff") == 0:     
        #diff
        srcDirectory = "/home/***/Experiment/Object/diff/diffutils-2.8.1"
        dstDirectory = "/home/***/Experiment/Object/diff/diffutils-2.9"
    elif cmp(appName, "grep") == 0:
        #grep
        srcDirectory = "/home/***/Experiment/Object/grep/grep-2.5.4"
        dstDirectory = "/home/***/Experiment/Object/grep/grep-2.6"  
    elif cmp(appName, "indent") == 0:
        #indent
        srcDirectory = "/home/***/Experiment/Object/indent/indent-2.2.9"
        dstDirectory = "/home/***/Experiment/Object/indent/indent-2.2.10"  
    elif cmp(appName, "tar") == 0:  
        #tar
        srcDirectory = "/home/***/Experiment/Object/tar/tar-1.13.25"
        dstDirectory = "/home/***/Experiment/Object/tar/tar-1.13.90" 
    elif cmp(appName, "ls") == 0:
        #ls
        srcDirectory = "/home/***/Experiment/Object/ls/coreutils-6.7"
        dstDirectory = "/home/***/Experiment/Object/ls/coreutils-6.8"
    elif cmp(appName, "gawk") == 0:
        #gawk
        srcDirectory = "/home/***/Experiment/Object/gawk/gawk-3.1.0"
        dstDirectory = "/home/***/Experiment/Object/gawk/gawk-3.1.1"
    elif cmp(appName, "bash") == 0:
        #bash
        srcDirectory = "/home/***/Experiment/Object/bash/bash-3.2.48"
        dstDirectory = "/home/***/Experiment/Object/bash/bash-4.0" 
    elif cmp(appName, "gettext") == 0:
        #gettext
        srcDirectory = "/home/***/Experiment/Object/gettext/gettext-0.18.3"
        dstDirectory = "/home/***/Experiment/Object/gettext/gettext-0.19.6" 
    elif cmp(appName, "gettext_1") == 0:
        #gettext_1
        srcDirectory = "/home/***/Experiment/Object/gettext_1/gettext-0.19.6"
        dstDirectory = "/home/***/Experiment/Object/gettext_1/gettext-0.19.7" 
    elif cmp(appName, "gettext_2") == 0:
        #gettext_2
        srcDirectory = "/home/***/Experiment/Object/gettext_2/gettext-0.18.1"
        dstDirectory = "/home/***/Experiment/Object/gettext_2/gettext-0.18.2" 
    elif cmp(appName, "global") == 0:
        #global
        srcDirectory = "/home/***/Experiment/Object/global/global-6.3.3"
        dstDirectory = "/home/***/Experiment/Object/global/global-6.3.4" 
    elif cmp(appName, "global_1") == 0:
        #global_1
        srcDirectory = "/home/***/Experiment/Object/global_1/global-6.2.2"
        dstDirectory = "/home/***/Experiment/Object/global_1/global-6.2.3"         
    #the changes reported by the tool diff
    changeFile = "/home/***/Experiment/Result/ChangeFile.patch"
    #the corresponding statements, which are modified, in two versions
    corresFile = "/home/***/Experiment/Result/CorresFile.out"
    #the deleted statements in the original version
    deletionFile = "/home/***/Experiment/Result/DeletionFile.out"
    #the added statements in the modified version
    additionFile = "/home/***/Experiment/Result/AdditionFile.out"  
    """
    # because we would modify the source codes of the project, we regenerate the project
    if os.path.exists(srcDirectory) == True:
        os.system("echo 206 | sudo -S rm -r %s" % (srcDirectory))
    srcDirectoryParent = os.path.dirname(srcDirectory)
    srcDirectoryTar = "%s.tar.gz" % (srcDirectory)
    srcTarCmd = "tar -zxvf %s -C %s" % (srcDirectoryTar, srcDirectoryParent)
    os.system(srcTarCmd)
    if os.path.exists(dstDirectory) == True:
        os.system("echo 206 | sudo -S rm -r %s" % (dstDirectory))
    dstDirectoryParent = os.path.dirname(dstDirectory)
    dstDirectoryTar = "%s.tar.gz" % (dstDirectory)
    dstTarCmd = "tar -zxvf %s -C %s" % (dstDirectoryTar, dstDirectoryParent)
    os.system(dstTarCmd)
    print "Tar is Finished!"
    # Merging the statements that should be in a line
    lineMergeDir(srcDirectory)
    lineMergeDir(dstDirectory)
    print "Merge Done!" 
    # Split the line that are connected via ","
    # for example  char const *base = line[0], *limit = line[1];  in util.c of program diff
    lineSplitDir(srcDirectory)
    lineSplitDir(dstDirectory)
    print "Split Done!"
    #the directories that are compared by the tool diff    
    if cmp(appName, "test") == 0:
        # test
        srcDiffDir = "/home/***/Experiment/Object/test/original"
        dstDiffDir = "/home/***/Experiment/Object/test/modified"    
    elif cmp(appName, "find_a") == 0:
        # find_a
        srcDiffDir = "/home/***/Experiment/Object/find_a/findutils-4.2.15/find"
        dstDiffDir = "/home/***/Experiment/Object/find_a/findutils-4.2.18/find"
    elif cmp(appName, "find_b") == 0 or cmp(appName, "find_c") == 0:
        #find_b find_c
        srcDiffDir = "/home/***/Experiment/Object/find_b_c/findutils-4.3.5/find"
        dstDiffDir = "/home/***/Experiment/Object/find_b_c/findutils-4.3.6/find"
    elif cmp(appName, "make") == 0:
        # make
        srcDiffDir = "/home/***/Experiment/Object/make/make-3.80"
        dstDiffDir = "/home/***/Experiment/Object/make/make-3.81"
    elif cmp(appName, "bc") == 0:
        #bc
        srcDiffDir = "/home/***/Experiment/Object/bc/bc-1.05/bc"
        dstDiffDir = "/home/***/Experiment/Object/bc/bc-1.06/bc"
    elif cmp(appName, "diff") == 0:
        #diff
        srcDiffDir = "/home/***/Experiment/Object/diff/diffutils-2.8.1/src"
        dstDiffDir = "/home/***/Experiment/Object/diff/diffutils-2.9/src"
    elif cmp(appName, "grep") == 0:
        #grep
        srcDiffDir = "/home/***/Experiment/Object/grep/grep-2.5.4/src"
        dstDiffDir = "/home/***/Experiment/Object/grep/grep-2.6/src"   
    elif cmp(appName, "indent") == 0:
        #indent
        srcDiffDir = "/home/***/Experiment/Object/indent/indent-2.2.9/src"
        dstDiffDir = "/home/***/Experiment/Object/indent/indent-2.2.10/src"  
    elif cmp(appName, "tar") == 0:  
        #tar
        srcDiffDir = "/home/***/Experiment/Object/tar/tar-1.13.25/src"
        dstDiffDir = "/home/***/Experiment/Object/tar/tar-1.13.90/src" 
    elif cmp(appName, "ls") == 0:
        #ls
        srcDiffDir = "/home/***/Experiment/Object/ls/coreutils-6.7/src"
        dstDiffDir = "/home/***/Experiment/Object/ls/coreutils-6.8/src"
    elif cmp(appName, "bash") == 0:
        #bash
        srcDiffDir = "/home/***/Experiment/Object/bash/bash-3.2.48"
        dstDiffDir = "/home/***/Experiment/Object/bash/bash-4.0"  
    elif cmp(appName, "gettext") == 0:
        #gettext
        srcDiffDir = "/home/***/Experiment/Object/gettext/gettext-0.18.3/gettext-tools/src"
        dstDiffDir = "/home/***/Experiment/Object/gettext/gettext-0.19.6/gettext-tools/src"      
    elif cmp(appName, "gettext_1") == 0:
        #gettext_1
        srcDiffDir = "/home/***/Experiment/Object/gettext_1/gettext-0.19.6/gettext-tools/src"
        dstDiffDir = "/home/***/Experiment/Object/gettext_1/gettext-0.19.7/gettext-tools/src"      
    elif cmp(appName, "gettext_2") == 0:
        #gettext_2
        srcDiffDir = "/home/***/Experiment/Object/gettext_2/gettext-0.18.1/gettext-tools/src"
        dstDiffDir = "/home/***/Experiment/Object/gettext_2/gettext-0.18.2/gettext-tools/src"   
    elif cmp(appName, "global") == 0:
        #global
        srcDiffDir = "/home/***/Experiment/Object/global/global-6.3.3"
        dstDiffDir = "/home/***/Experiment/Object/global/global-6.3.4"   
    elif cmp(appName, "global_1") == 0:
        #global_1
        srcDiffDir = "/home/***/Experiment/Object/global_1/global-6.2.2"
        dstDiffDir = "/home/***/Experiment/Object/global_1/global-6.2.3"  
    patterns = "/home/***/Experiment/Object/patterns.xo"
    diffCmd= "diff -NbrU 0 --exclude-from=%s %s %s > %s" % (patterns, srcDiffDir, dstDiffDir, changeFile)    
    os.system(diffCmd)
    #Additionally comparing the differences of the file quotearg
    if cmp(appName, "ls") == 0:
        srcDiffFile = "/home/***/Experiment/Object/ls/coreutils-6.7/lib/quotearg.c"
        dstDiffFile = "/home/***/Experiment/Object/ls/coreutils-6.8/lib/quotearg.c"
        changeFileSig = "/home/***/Experiment/Result/ChangeFileSig.patch"
        diffCmdSig = "diff -NbrU 0 %s %s > %s" % (srcDiffFile, dstDiffFile, changeFileSig)
        os.system(diffCmdSig)
        changeFileMerge(srcDiffFile, dstDiffFile, changeFile, changeFileSig)
    #Analyse the changeFile, and assign to corresFile, deletionFile and additonaFile     
    DiffProcess(changeFile, corresFile, deletionFile, additionFile)  
    print "Diff Done!"
    
    #the directories where the programs are installed
    if cmp(appName, "test") == 0:
        #test
        srcExeDirectory = "/home/***/Experiment/Object/test/original"
        dstExeDirectory = "/home/***/Experiment/Object/test/modified"    
    elif cmp(appName, "find_a") == 0:
        #find_a
        srcExeDirectory = "/usr/local/find_a/15"
        dstExeDirectory = "/usr/local/find_a/18"
    elif cmp(appName, "find_b") == 0 or cmp(appName, "find_c") == 0:
        #find_b and find_c
        srcExeDirectory = "/usr/local/find_b_c/35"
        dstExeDirectory = "/usr/local/find_b_c/36"
    elif cmp(appName, "make") == 0:
        #make
        srcExeDirectory = "/usr/local/make/380"
        dstExeDirectory = "/usr/local/make/381"
    elif cmp(appName, "bc") == 0:
        #bc
        srcExeDirectory = "/usr/local/bc/105"
        dstExeDirectory = "/usr/local/bc/106"  
    elif cmp(appName, "diff") == 0:
        #diff
        srcExeDirectory = "/usr/local/diff/28"
        dstExeDirectory = "/usr/local/diff/29"
    elif cmp(appName, "grep") == 0:
        #grep
        srcExeDirectory = "/usr/local/grep/25"
        dstExeDirectory = "/usr/local/grep/26"  
    elif cmp(appName, "indent") == 0:  
        #indent
        srcExeDirectory = "/usr/local/indent/09"
        dstExeDirectory = "/usr/local/indent/10"
    elif cmp(appName, "tar") == 0:
        #tar
        srcExeDirectory = "/usr/local/tar/25"
        dstExeDirectory = "/usr/local/tar/90"
    elif cmp(appName, "ls") == 0:
        #ls
        srcExeDirectory = "/usr/local/ls/67"
        dstExeDirectory = "/usr/local/ls/68"
    elif cmp(appName, "gawk") == 0:
        #gawk
        srcExeDirectory = "/usr/local/gawk/310"
        dstExeDirectory = "/usr/local/gawk/311"
    elif cmp(appName, "bash") == 0:
        #bash
        srcExeDirectory = "/usr/local/bash/32"
        dstExeDirectory = "/usr/local/bash/40"
    elif cmp(appName, "gettext") == 0:
        #gettext
        srcExeDirectory = "/usr/local/gettext/18"
        dstExeDirectory = "/usr/local/gettext/19"
    elif cmp(appName, "gettext_1") == 0:
        #gettext_1
        srcExeDirectory = "/usr/local/gettext_1/6"
        dstExeDirectory = "/usr/local/gettext_1/7" 
    elif cmp(appName, "gettext_2") == 0:
        #gettext_2
        srcExeDirectory = "/usr/local/gettext_2/1"
        dstExeDirectory = "/usr/local/gettext_2/2" 
    elif cmp(appName, "global") == 0:
        #global
        srcExeDirectory = "/usr/local/global/33"
        dstExeDirectory = "/usr/local/global/34" 
    elif cmp(appName, "global_1") == 0:
        #global_1
        srcExeDirectory = "/usr/local/global_1/22"
        dstExeDirectory = "/usr/local/global_1/23" 
    compileWork(srcDirectory, srcExeDirectory)
    compileWork(dstDirectory, dstExeDirectory)
    print "Compile, Install Done!"
    """
    #the executable programs and their parameters
    if cmp(appName, "test") == 0:
        #test
        srcExeFile = "/home/***/Experiment/Object/test/original/test"
        dstExeFile = "/home/***/Experiment/Object/test/modified/test"
        workspace = "/home/***/Experiment/Input/test"
        parameter = ""
    elif cmp(appName, "find_a") == 0:
        #find_a
        srcExeFile = "/usr/local/find_a/15/bin/find"
        dstExeFile = "/usr/local/find_a/18/bin/find"
        workspace = "/home/***/Experiment/Input/find_a"
        parameter = "-H link"
    elif cmp(appName, "find_b") == 0:
        #find_b
        srcExeFile = "/usr/local/find_b_c/35/bin/find"
        dstExeFile = "/usr/local/find_b_c/36/bin/find"
        workspace = "/home/***/Experiment/Input/find_b"
        parameter = "-mtime -100 -ls"
    elif cmp(appName, "find_c") == 0:
        #find_c
        srcExeFile = "/usr/local/find_b_c/35/bin/find"
        dstExeFile = "/usr/local/find_b_c/36/bin/find"
        workspace = "/home/***/Experiment/Input/find_c"
        parameter = "-size b40"
    elif cmp(appName, "make") == 0:
        #make
        srcExeFile = "/usr/local/make/380/bin/make"
        dstExeFile = "/usr/local/make/381/bin/make"
        workspace = "/home/***/Experiment/Input/make"
        parameter = "-r bad"
    elif cmp(appName, "bc") == 0:
        #bc
        srcExeFile = "/usr/local/bc/105/bin/bc"
        dstExeFile = "/usr/local/bc/106/bin/bc"
        workspace = "/home/***/Experiment/Input/bc"
        parameter = "--mathlib input.bc"  
    elif cmp(appName, "diff") == 0:
        #diff
        srcExeFile = "/usr/local/diff/28/bin/diff"
        dstExeFile = "/usr/local/diff/29/bin/diff"
        workspace = "/home/***/Experiment/Input/diff"
        parameter = "-u srcDiff dstDiff" 
    elif cmp(appName, "grep") == 0:
        #grep
        srcExeFile = "/usr/local/grep/25/bin/grep"
        # the program has not correctly installed in "/usr/local/grep/26/bin/grep"
        #dstExeFile = "/usr/local/grep/26/bin/grep"
        dstExeFile = "/home/***/Experiment/Object/grep/grep-2.6/src/grep"
        workspace = "/home/***/Experiment/Input/grep"
        # --include=1: it is to includes the file 1
        # x 1: it is to find the character x in the file 1
        parameter = "--include=1 x 1"
    elif cmp(appName, "indent") == 0:
        #indent
        srcExeFile = "/usr/local/indent/09/bin/indent"
        dstExeFile = "/usr/local/indent/10/bin/indent"
        workspace = "/home/***/Experiment/Input/indent"
        parameter = "--blank-lines-after-declarations input.c"
    elif cmp(appName, "tar") == 0:
        #tar
        srcExeFile = "/usr/local/tar/25/bin/tar"
        dstExeFile = "/usr/local/tar/90/bin/tar"
        workspace = "/home/***/Experiment/Input/tar"
        parameter = "tvfz x.tar.gz"
    elif cmp(appName, "ls") == 0:
        #ls
        srcExeFile = "/usr/local/ls/67/bin/ls"
        dstExeFile = "/usr/local/ls/68/bin/ls"
        workspace = "/home/***/Experiment/Input/ls"
        parameter = "-x"
    elif cmp(appName, "gawk") == 0:
        # gawk
        srcExeFile = "/usr/local/find_b/35/bin/find"
        dstExeFile = "/usr/local/find_b/36/bin/find"
        workspace = "/home/***/Experiment/Input"
        parameter = "\"BEGIN {print strtonum(\"13\")};\""
    elif cmp(appName, "bash") == 0:
        #bash
        srcExeFile = "/usr/local/bash/32/bin/bash"
        dstExeFile = "/usr/local/bash/40/bin/bash"
        workspace = "/home/***/Experiment/Input/bash"
        parameter = "input.sh"
    elif cmp(appName, "gettext") == 0:
        #gettext
        srcExeFile = "/usr/local/gettext/18/bin/xgettext"
        dstExeFile = "/usr/local/gettext/19/bin/xgettext"
        workspace = "/home/***/Experiment/Input/gettext"
        parameter = "--keyword=N_ --add-comments --directory=. --default-domain=foo --from-code=UTF-8 --files-from=./POTFILES.in"
    elif cmp(appName, "gettext_1") == 0:
        #gettext_1
        srcExeFile = "/usr/local/gettext_1/6/bin/xgettext"
        dstExeFile = "/usr/local/gettext_1/7/bin/xgettext"
        workspace = "/home/***/Experiment/Input/gettext_1"
        parameter = "--add-comments --directory=. --default-domain=add.glade --from-code=UTF-8 --files-from=./POTFILES.in"
    elif cmp(appName, "gettext_2") == 0:
        #gettext_2
        srcExeFile = "/usr/local/gettext_2/1/bin/xgettext"
        dstExeFile = "/usr/local/gettext_2/2/bin/xgettext"
        workspace = "/home/***/Experiment/Input/gettext_2"
        parameter = "--keyword=N_ --add-comments --directory=. --default-domain=foo --from-code=UTF-8 --files-from=./POTFILES.in"
    elif cmp(appName, "global") == 0:
        #global
        srcExeFile = "/usr/local/global/33/bin/gtags"
        dstExeFile = "/usr/local/global/34/bin/gtags"
        workspace = "/home/***/Experiment/Input/global"
        parameter = ""
    elif cmp(appName, "global_1") == 0:
        #global_1
        srcExeFile = "/usr/local/global_1/22/bin/gtags"
        dstExeFile = "/usr/local/global_1/23/bin/gtags"
        workspace = "/home/***/Experiment/Input/global_1"
        parameter = "-f file.list"
    # the input of programs make and indent are specially handled, because they would modify the input files
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile)    
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinCFG(srcExeFile, workspace, parameter, True)
    # the input of programs make and indent are specially handled, because they would modify the input files
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile) 
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinTraceData(srcExeFile, workspace, parameter, True)
    # the input of programs make and indent are specially handled, because they would modify the input files
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile) 
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinCFG(dstExeFile, workspace, parameter, False)
    # the input of programs make and indent are specially handled, because they would modify the input files
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile) 
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinTraceData(dstExeFile, workspace, parameter, False)
    # the execution traces of two versions
    srcTraceFile = "/home/***/Experiment/Result/srcLINETrace.out"
    dstTraceFile = "/home/***/Experiment/Result/dstLINETrace.out"
    # the traces of memory that are read or written by the program statements
    srcDataFile = "/home/***/Experiment/Result/srcDATATrace.out"
    dstDataFile = "/home/***/Experiment/Result/dstDATATrace.out"
    # some segments that record the assemble codes and their memory read or written
    srcCodeDataFile = "/home/***/Experiment/Result/srcCodeDATATrace.out"
    dstCodeDataFile = "/home/***/Experiment/Result/dstCodeDATATrace.out"
    # preprocess the name of the file, at present, it is only for the progrma indent
    # for example, "indent.gperf:is_reserved:16" is "gperf.c:is_reserved:16"
    srcRenameMap = preProcessFileName(appName, srcTraceFile)
    dstRenameMap = preProcessFileName(appName, dstTraceFile)
    # handle the trace
    # adding the omissive function calling
    # adding the function return  after exit(-1)
    handleTrace(appName, srcTraceFile)
    handleTrace(appName, dstTraceFile)
    # deleting the execution trace after the returned main
    # which is caused by atexit(close_stdout)
    deleteTrace(appName, srcTraceFile)
    deleteTrace(appName, dstTraceFile)
    # Compute the execution trace
    srcTrace = executionTrace(srcTraceFile)
    dstTrace = executionTrace(dstTraceFile)
    print "Get the Trace!"
    preProcessFileName(appName, srcDataFile)
    preProcessFileName(appName, dstDataFile)
    # add the memory read/written in the statement memcpy
    srcMemcpySet = set()
    dstMemcpySet = set()
    StaticMemcpy(srcDirectory, srcMemcpySet)
    StaticMemcpy(dstDirectory, dstMemcpySet)
    handleMemcpyData(srcDataFile, srcMemcpySet)
    handleMemcpyData(dstDataFile, dstMemcpySet)
    # add teh memory read/written in the statement realloc
    srcReallocSet = set()
    dstReallocSet = set()
    StaticRealloc(srcDirectory, srcReallocSet)
    StaticRealloc(dstDirectory, dstReallocSet)
    handleReallocData(srcDataFile, srcReallocSet)
    handleReallocData(dstDataFile, dstReallocSet)
    # add teh memory read/written in the statement realloc
    srcStrcpySet = set()
    dstStrcpySet = set()
    StaticStrcpy(srcDirectory, srcStrcpySet)
    StaticStrcpy(dstDirectory, dstStrcpySet)
    handleStrcpyData(srcDataFile, srcStrcpySet)
    handleStrcpyData(dstDataFile, dstStrcpySet)
    # handle the dataFile
    # add the function call and return
    handleData(appName, srcTrace, srcDataFile)
    handleData(appName, dstTrace, dstDataFile)
    deleteData(appName, srcDataFile)
    deleteData(appName, dstDataFile)    
    # Compute the line number of source file, which is the function calling
    srcLNFile = "/home/***/Experiment/Result/srcLNFunCalling.out"
    dstLNFile = "/home/***/Experiment/Result/dstLNFunCalling.out"    
    LNOfFunctionCalling(appName, srcTrace, srcLNFile, srcRenameMap)
    LNOfFunctionCalling(appName, dstTrace, dstLNFile, dstRenameMap)
    # compute the code and data at the function calling
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile) 
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinCode(srcExeFile, workspace, parameter, True)
    if cmp(appName, "make") == 0:
        TFile = "/home/***/Experiment/Input/make/T"
        if os.path.exists(TFile):
            os.remove(TFile)
        TOutFile = "/home/***/Experiment/Input/make/T.out"
        if os.path.exists(TOutFile):
            os.remove(TOutFile) 
    elif cmp(appName, "indent") == 0:
        inputFile = "/home/***/Experiment/Input/indent/input.c"
        if os.path.exists(inputFile):
            os.remove(inputFile)
        cpCmd = "cp /home/***/Experiment/Input/indent/input_backup.c /home/***/Experiment/Input/indent/input.c"
        os.system(cpCmd)
    pinCode(dstExeFile, workspace, parameter, False)
    print "Program Instrumentatin Done!"
    preProcessFileName(appName, srcCodeDataFile)
    preProcessFileName(appName, dstCodeDataFile)
    # handle the codedata File
    handleData(appName, srcTrace, srcCodeDataFile)
    handleData(appName, dstTrace, dstCodeDataFile)
    deleteData(appName, srcCodeDataFile)
    deleteData(appName, dstCodeDataFile)
    # Compute the loop statement instances, we store the index of trace
    srcLoopSet = DynamicLoop(appName, srcTrace, srcDirectory)
    dstLoopSet = DynamicLoop(appName, dstTrace, dstDirectory)
    print "Loop Detection Done!" 
    # Compute the correspondence of the changes, the format is <index, set(lineNumber)>
    # lineNumber begins with 1 not 0
    # Here, deletionSet and additionSet includes the statements (not instances) that are correspondent to the blank lines
    (srcToDstLN, dstToSrcLN, srcDeletionLN, dstAdditionLN) = modificationAlign(appName, srcDirectory, dstDirectory, srcTrace, dstTrace, corresFile)
    # Compute the set of the modification instances, the format is set(index)
    srcModificationSet = srcToDstLN.keys()
    dstModificationSet = dstToSrcLN.keys()
    # Compute the set of the deletion statement instances, the format is set(index)
    srcDeletionSet = addDelAlign(appName, srcDeletionLN, deletionFile, srcTrace)
    # Compute the set of the addition statement instances, the format is set(index)
    dstAdditionSet = addDelAlign(appName, dstAdditionLN, additionFile, dstTrace)
    print "Changes Corresponding Done!"    
    srcCFGFile = "/home/***/Experiment/Result/srcCFGTrace.out"
    dstCFGFile = "/home/***/Experiment/Result/dstCFGTrace.out"
    # Compute the static control dependence, the format is <fileName:lineNumber, Set(fileName:lineNumber)>
    # if the node is not dependent on the other node, it would not be included in CDGMap
    srcCDGMap = staticCDG(srcCFGFile)
    dstCDGMap = staticCDG(dstCFGFile)
    # Compute the control dependence, the form is <index, index> 
    (srcControlDep, srcCallDep) = dynamicCDG(srcCDGMap, srcTrace)
    (dstControlDep, dstCallDep) = dynamicCDG(dstCDGMap, dstTrace) 
    print "Control Dependence Done!" 
    # Compute the procedure name of a calling point, the form is <index, procedureName>
    srcPointCallName = pointToCallName(srcTrace)
    dstPointCallName = pointToCallName(dstTrace)
    # call graph, the key of map is calling point, the value of map is function body instances
    # the form is <index, [index1, index2 ...]>
    srcCallG = {}
    dstCallG = {}
    srcReversedCallG = {}
    dstReversedCallG = {}
    callGraph(srcTrace, 0, srcCallG, srcReversedCallG)
    callGraph(dstTrace, 0, dstCallG, dstReversedCallG) 
    print "Call Graph Done!"  
    # returnCallMap: find the function call point based on the function return point
    # srcCallReturnBoth: its form is <index, sign>, the sign is used to represent it is a 
    # function call, function return, or both
    # is is used to align the function calling, because we should know it's function call, return or both 
    # srcReturnDepen: its form is <index, [index,....]>
    # we can determine that an statement is data dependent on which function returns through returnDepen
    # pureCallSet/pureReturnSet is the pure function call/return points, does not include the points that are simultaneously calling and returning 
    (srcReturnCallMap, srcCallReturnBoth, srcPureCallSet, srcPureReturnSet, srcReturnTogether) = callReturnPoint(srcTrace)
    (dstReturnCallMap, dstCallReturnBoth, dstPureCallSet, dstPureReturnSet, dstReturnTogether) = callReturnPoint(dstTrace) 
    # Compute the alignment of two traces
    # Here, we only consider the function callings
    # Later, we still add other alignments into these two maps
    srcToDstIndex = {}
    dstToSrcIndex = {}
    srcToDstIndex[-1] = {-1}
    dstToSrcIndex[-1] = {-1}
    traceAlignFunctionPoint(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, \
               srcToDstLN, dstToSrcLN, srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, \
               dstPureCallSet, srcPureReturnSet, dstPureReturnSet, srcPointCallName, dstPointCallName, -1, -1)
    print "Trace Align Done!"
    # Compute the data dependence, which is through the function return
    # the form is <index, [index, ....]>, which is different from the general later data dependence
    srcReturnDep = returnDDG(srcReturnTogether, srcTrace)
    dstReturnDep = returnDDG(dstReturnTogether, dstTrace)
    # Compute the branch value of a conditional statement
    srcBVMap = branchValue(srcCDGMap, srcTrace)
    dstBVMap = branchValue(dstCDGMap, dstTrace)
    # Compute the switch instances, the form is set(index)
    srcSwitchSet = dynamicSwitch(appName, srcTrace, srcDirectory)
    dstSwitchSet = dynamicSwitch(appName, dstTrace, dstDirectory)
    # Compute the immediately before/next non-added/non-deleted statement, which may be modified statement, 
    # of an added/deleted instance
    # the form of srcABInstance is <index, [fileName:lineNumber, fileName, lineNumber]>
    # the default lineNumber in srcABInstance is "0" and "1000000"
    # deletionLN included the deleted statements that are corresponding to the blank lines
    # deletionFile includes the deleted statements computed from the tool diff 
    srcABInstance = afterBeforeInstance(srcTrace, srcCFGFile, srcDeletionLN, deletionFile)
    dstABInstance = afterBeforeInstance(dstTrace, dstCFGFile, dstAdditionLN, additionFile)
    # Compute the alignment slice 
    # If the statement instance is not specified, it is set to -1   
    if cmp(appName, "test") == 0:
        #it is for test 
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([7]), set([7]))   
    elif cmp(appName, "find_a") == 0:
        #it is for find_a 
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([-1]), set([799]))
    elif cmp(appName, "find_b") == 0:
        # it is for find_b
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([5609]), set([-1]))
    elif cmp(appName, "find_c") == 0:
        # it is for find_c
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([631]), set([626]))
    elif cmp(appName, "make") == 0:
        # it is for make
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([-1]), set([33048]))
    elif cmp(appName, "bc") == 0:
        # it is for bc
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([-1]), set([23]))
    elif cmp(appName, "diff") == 0:
        # it is for diff
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([2672]), set([-1]))
    elif cmp(appName, "grep") == 0:
        # it is for grep          
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([2099]), set([-1]))
    elif cmp(appName, "indent") == 0:
        # it is for indent
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([-1]), set([10459]))
    elif cmp(appName, "tar") == 0:
        # it is for tar
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([2584]), set([2720]))
    elif cmp(appName, "ls") == 0:
        # it is for ls         
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([1166]), set([1118]))              
    elif cmp(appName, "gawk") == 0:
        # it is for gawk
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([8818]), set([-1]))  
    elif cmp(appName, "gettext") == 0:
        # it is for gettext
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([198447]), set([212197]))     
    elif cmp(appName, "gettext_1") == 0:
        # it is for gettext_1
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([114646]), set([185449]))  
    elif cmp(appName, "gettext_2") == 0:
        # it is for gettext_2
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([222737]), set([222685])) 
    elif cmp(appName, "global") == 0:
        # it is for global
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([101195]), set([101124])) 
    elif cmp(appName, "global_1") == 0:
        # it is for global_1
        (srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
        dstCorrespondence, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData) = \
        dualSlice(appName, srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcCDGMap, dstCDGMap, srcTrace, dstTrace, srcToDstIndex, \
                  dstToSrcIndex, srcToDstLN, dstToSrcLN, srcControlDep, dstControlDep, srcCallDep, dstCallDep, srcReturnDep, dstReturnDep, srcReturnCallMap, dstReturnCallMap, \
                  srcPointCallName, dstPointCallName, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet, \
                  srcABInstance, dstABInstance, srcBVMap, dstBVMap, srcSwitchSet, dstSwitchSet, set([33255]), set([25663]))  
    printRegressionSlice(srcRegressionSlice, dstRegressionSlice, srcEleType, dstEleType, srcDependence, dstDependence, srcCorrespondence, \
               dstCorrespondence, srcTrace, dstTrace, srcDataTrace, dstDataTrace, srcTraceToData, dstTraceToData)
    # diffNum is the total differences between two traces
    diffRegressionNum = differenceCompute(srcRegressionSlice, dstRegressionSlice, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, \
                                                          srcDataFile, dstDataFile, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet)
    srcRegressionSliceLen = len(srcRegressionSlice)
    if -1 in srcRegressionSlice:
        srcRegressionSliceLen = srcRegressionSliceLen - 1
    dstRegressionSliceLen = len(dstRegressionSlice)
    if -1 in dstRegressionSlice:
        dstRegressionSliceLen = dstRegressionSliceLen - 1
    #print "src Regression Slicing:", srcRegressionSliceLen
    #print "dst Regression Slicing:", dstRegressionSliceLen
    #print "Difference Number in Regression Slicing:", diffRegressionNum
    #print "Regression Slice Done!"
    # compute the dynamic slicing
    if cmp(appName, "test") == 0:
        # it is for test
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([-1]), set([-1]))
    elif cmp(appName, "find_a") == 0:
        # it is for find_a
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([2605]), set([799]))
    elif cmp(appName, "find_b") == 0:
        # it is for find_b
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([5609]), set([5717]))                                  
    elif cmp(appName, "find_c") == 0:
        # it is for find_c
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([631]), set([626]))
    elif cmp(appName, "make") == 0:
        # it is for make
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([42956]), set([33048])) 
    elif cmp(appName, "bc") == 0:
        # it is for bc
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([22]), set([23]))
    elif cmp(appName, "diff") == 0:
        # if is for diff
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([2664]), set([2807]))
    elif cmp(appName, "grep") == 0:
        # it is for grep
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([2099]), set([1354])) 
    elif cmp(appName, "indent") == 0:
        # it is for indent
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([10287]), set([10459])) 
    elif cmp(appName, "tar") == 0:
        # it is for tar
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([2584]), set([2720]))   
    elif cmp(appName, "ls") == 0:
        # it is for ls         
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([1166]), set([1118]))   
    elif cmp(appName, "gettext") == 0:
        # it is for gettext        
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([198447]), set([212197])) 
    elif cmp(appName, "gettext_1") == 0:
        # it is for gettext_1      
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([114646]), set([185449])) 
    elif cmp(appName, "gettext_2") == 0:
        # it is for gettext_2      
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([222737]), set([222685])) 
    elif cmp(appName, "global") == 0:
        # it is for global      
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([101195]), set([101124])) 
    elif cmp(appName, "global_1") == 0:
        # it is for global_1   
        (srcDynamicSlice, dstDynamicSlice) = dynamicSlice(srcDataFile, dstDataFile, srcCodeDataFile, dstCodeDataFile, srcTrace, dstTrace, srcCallDep, \
                                                          dstCallDep, srcControlDep, dstControlDep, srcReturnDep, dstReturnDep, set([33255]), set([25663])) 
    printDynamicSlice(srcDynamicSlice, dstDynamicSlice, srcTrace, dstTrace)
    traceAlignProgram(srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, srcCallG, dstCallG, srcControlDep, dstControlDep, \
                      srcToDstLN, dstToSrcLN, srcLoopSet, dstLoopSet, srcCallReturnBoth, dstCallReturnBoth, srcPureCallSet, \
                      dstPureCallSet, srcPureReturnSet, dstPureReturnSet, srcPointCallName, dstPointCallName, -1, -1)
    diffDynamicNum = differenceCompute(srcDynamicSlice, dstDynamicSlice, srcToDstIndex, dstToSrcIndex, srcTrace, dstTrace, \
                                                          srcDataFile, dstDataFile, srcModificationSet, dstModificationSet, srcDeletionSet, dstAdditionSet)
    srcDynamicSliceLen = len(srcDynamicSlice)
    if -1 in srcDynamicSlice:
        srcDynamicSliceLen = srcDynamicSliceLen - 1
    dstDynamicSliceLen = len(dstDynamicSlice)
    if -1 in dstDynamicSlice:
        dstDynamicSliceLen = dstDynamicSliceLen - 1
    #print "src Dynamic Slicing:", srcDynamicSliceLen
    #print "dst Dynamic Slicing:", dstDynamicSliceLen
    #print "Difference Number in Dynamic Slicing:", diffDynamicNum
    #print "Dynamic Slice Done!"
    printResult(srcRegressionSliceLen, dstRegressionSliceLen, diffRegressionNum, srcDynamicSliceLen, dstDynamicSliceLen, diffDynamicNum)