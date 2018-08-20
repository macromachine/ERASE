
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

#Construct the CFG of a function
#If a node has no incoming node, the map will return the empty set
def cfgConstruct(functionTrace):
    #The flowing map, the format: <node, incoming nodes(0X8048419)>
    incomingNodes = {}
    lastJmpBranch = False
    lastNode = ""

    for eachLine in functionTrace:          
        element = eachLine.split('#')
        #General statement or indirect branch, not include direct branch
        if len(element) == 2 or len(element) == 3:
            #The previous statement is not unconditional jump
            if lastJmpBranch == False:
                mapKey = element[0].strip()
                if mapKey in incomingNodes:
                    mapValue = incomingNodes[mapKey]
                    #lastNode must not be empty
                    mapValue.add(lastNode)
                else:
                    if lastNode == "":
                        incomingNodes[mapKey] = set()
                    else:
                        incomingNodes[mapKey] = set([lastNode])
            else:
                mapKey = element[0].strip()
                if mapKey not in incomingNodes:
                    incomingNodes[mapKey] = set()
            lastJmpBranch = False
        #Conditional and unconditional branch                              
        elif len(element) == 4:
            mapKey = element[0].strip()
            if lastJmpBranch == False: 
                if mapKey in incomingNodes:
                    mapValue = incomingNodes[mapKey]
                    mapValue.add(lastNode)
                else:
                    if lastNode == "":
                        incomingNodes[mapKey] = set()
                    else:
                        incomingNodes[mapKey] = set([lastNode])
            else:
                if mapKey not in incomingNodes:
                    incomingNodes[mapKey] = set()
                #Handle conditional and unconditional branch                              
            dstKey = element[1].strip()
            if dstKey in incomingNodes:
                dstValue = incomingNodes[dstKey]
                dstValue.add(mapKey)
            else:
                incomingNodes[dstKey] = set([mapKey]) 
                                       
            CUBranch = element[2].strip()
            #The previous node is unconditional jump
            if cmp(CUBranch, "U") == 0:
                lastJmpBranch = True
            else:
                lastJmpBranch = False
        #Mark the processed node
        lastNode = element[0].strip()
    # fix the indirectBranch situation, because the indirectBranch has no destination address 
    # Don't consider functionTrace[0]
    for i in range(len(functionTrace)-1, 0, -1):
        element = functionTrace[i].split('#')
        mapKey = element[0].strip()
        if mapKey in incomingNodes:
            mapValue = incomingNodes[mapKey]
            if len(mapValue) == 0:
                for j in range(i-1, -1, -1):
                    preEle = functionTrace[j].split("#")
                    if len(preEle) == 3:
                        preValue = preEle[0].strip()
                        incomingNodes[mapKey] = set([preValue])  
                        break         
    return (incomingNodes, lastNode)

#Compute the map from address in binary file to line number in source file
def addrTOLine(functionTrace):
    addressLine  = {}
    for eachLine in functionTrace:
        element = eachLine.split("#")
        if len(element) == 2:
            mapKey = element[0].strip()
            mapValue = element[1].strip()
            addressLine[mapKey] = mapValue
        elif len(element) == 3:
            mapKey = element[0].strip()
            mapValue = element[2].strip()
            addressLine[mapKey] = mapValue            
        elif len(element) == 4:
            mapKey = element[0].strip()
            mapValue = element[3].strip()
            addressLine[mapKey] = mapValue
    return addressLine 

#Compute the unconditional jump, which jump to itself
def pointItself(functionTrace, addressLine):
    pointLine = set()
    for eachLine in functionTrace:
        elements = eachLine.split("#")
        if len(elements) == 4:
            CU = elements[2].strip()
            if CU == "U":
                srcLine = elements[3].strip()
                dstAddr = elements[1].strip()
                if dstAddr in addressLine:
                    dstLine = addressLine[dstAddr]
                    if cmp(srcLine, dstLine) == 0:
                        srcAddr = elements[0].strip()
                        pointLine.add(srcAddr)
    return pointLine            
               
#Compute the postdominated nodes for the node ele
#If a node can not reach end node, when we remove ele, it is postdominated node
def postDominated(ele, incomingNodes, endNode):
    workList = list([endNode])
    workSet = set([endNode])
    while len(workList) != 0:
        curNode = workList.pop(0);
        if curNode == ele:
            continue
        preNodes = incomingNodes[curNode]
        for eachNode in preNodes:
            if eachNode not in workSet:
                workList.append(eachNode)
                workSet.add(eachNode)
    dominateSet = set()
    # incomingNodes is only used to include all nodes of a function body
    for mapKey in incomingNodes:
        if mapKey not in workSet:
            dominateSet.add(mapKey)
    return dominateSet                  

#Compute the direct postDominated nodes, which is used for dominating tree construction
def directPostDominated(ele, postDominateNodes):
    postDominateNode = postDominateNodes[ele]
    replicateNode = set()
    for eachNode in postDominateNode:
        replicateDominateNode = postDominateNodes[eachNode] 
        for eachReplicate in replicateDominateNode:
            replicateNode.add(eachReplicate)
    directNode = set()
    for eachNode in postDominateNode:
        if eachNode not in replicateNode:
            directNode.add(eachNode)
    return directNode              

# compute the post dominated nodes and construct the post dominating tree
# postDominateNodes <node, postDominatedNodes>, if a node has no postDominated, it returns the empty set
# postDominateTrees <node, postDominatingNode>, if a node has no direct dominating node, it would not appear in the map
# Two maps are opposite
def postDominatedAnalysis(incomingNodes, endNode):
    postDominateNodes = {}
    for mapKey in incomingNodes:
        dominateSet = postDominated(mapKey, incomingNodes, endNode)
        postDominateNodes[mapKey] = dominateSet 
        
    postDominateTrees = {}
    for mapKey in postDominateNodes:
        #Compute the direct postdominated nodes
        directNode = directPostDominated(mapKey, postDominateNodes)
        for eachNode in directNode:
            postDominateTrees[eachNode] = mapKey
    return (postDominateNodes, postDominateTrees)   

#Compute the least common father node, which dominates both slave and master
def leastCommAnce(slave, master, postDominateTrees):
    curNode = slave
    dominateList = [curNode]
    # compute list of nodes that dominate the slave
    while True:
        if curNode in postDominateTrees:
            fatherNode = postDominateTrees[curNode]
            dominateList.append(fatherNode)
            curNode = fatherNode
        else:
            break
    curNode = master
    #compute the node that dominate both slave and master
    while curNode not in dominateList:
        if curNode in postDominateTrees:
            fatherNode = postDominateTrees[curNode]
            curNode = fatherNode
        else:
            print "least common ancestor error!",curNode
    return (dominateList, curNode)    

def cdgPrint(CDGMap, controlDepen, fileNameLine):
    fileNames = fileNameLine.split("***")
    fileName = fileNames[1].strip()
    for slave in controlDepen:
        slaveStr = "%s:%s" % (fileName, slave)
        masters = controlDepen[slave]
        for master in masters:
            masterStr = "%s:%s" % (fileName, master)
            
            if slaveStr in CDGMap:
                mapValue = CDGMap[slaveStr]
                mapValue.add(masterStr)
            else:
                mapValue = set()
                mapValue.add(masterStr)
                CDGMap[slaveStr] = mapValue 

# construct the static control dependence of a function
# CDGMap: if the node is not dependent on any other node, it would not appear in the map
def cdgConstruct(CDGMap, incomingNodes, postDominateNodes, postDominateTrees, addressLine, pointLine, fileNameLine):
    # Control flow edge, the parent node is not dominated by the son node
    # It may be that cfgEdges only includes the branch information
    cfgEdges = {}
    for slave in incomingNodes:
        incomingNode = incomingNodes[slave]
        for master in incomingNode:
            dominatedNodes = postDominateNodes[slave]
            if master not in dominatedNodes:
                if slave in cfgEdges:
                    mapValue = cfgEdges[slave]
                    mapValue.add(master)
                else:
                    cfgEdges[slave] = set([master])
                    
    # Control dependence map
    controlDepen = {}           
    for slave in cfgEdges:
        incomingNode = cfgEdges[slave]
        #if the code snippet is as follow, it would produce the wrong dependence
        #the while statement would be control dependent on if statement
        #The reason for such error is because the while statement would be translated as some assemble code, including a special unconditional jump 
        #    if()
        #        ....
        #    while()
        #        ....
        for master in incomingNode:
            #compute the least common parent node, which dominates both slave and master
            (dominateList, ancestorNode) = leastCommAnce(slave, master, postDominateTrees)
            # The general control dependence
            if ancestorNode != master:
                masterLine = addressLine[master]
                for eachSlave in dominateList:
                    # it does not include the situation that depends on itself
                    if eachSlave == ancestorNode:
                        break;
                    # handle the above error(if....while....)
                    if eachSlave in pointLine:
                        continue;
                    slaveLine = addressLine[eachSlave]
                    if slaveLine in controlDepen:
                        mapValue = controlDepen[slaveLine]
                        mapValue.add(masterLine)
                    else:
                        controlDepen[slaveLine] = set([masterLine])
            # the loop situation
            elif ancestorNode == master:
                masterLine = addressLine[master]
                for eachSlave in dominateList:
                    #Tackle the above error(if....while....)
                    if eachSlave in pointLine:
                        continue
                    slaveLine = addressLine[eachSlave]
                    if slaveLine in controlDepen:
                        mapValue = controlDepen[slaveLine]
                        mapValue.add(masterLine)
                    else:
                        controlDepen[slaveLine] = set([masterLine])
                    # include the ancestroNode, which means the loop condition depends on itself
                    if eachSlave == ancestorNode:
                        break;
    cdgPrint(CDGMap, controlDepen, fileNameLine)
        
# CDGMap is the static control dependence:<fileName:lineNumber, Set(fileName:lineNumber)>
# if the node is not dependent on other node, it would not appear in CDGMap
def staticCDG(cfgFile): 
    CDGMap = {}
    try:
        cfgTrace = open(cfgFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        #The file name, such as hello.c from "***hello.c***"
        fileNameLine = ""
        #The function body trace, not include the file name information "***hello.c***"
        functionTrace = []
        for eachLine in cfgTrace:
            eachLine = eachLine.strip()
            #Represent that it is a new function
            if eachLine.find("***") != -1:
                #handle the previous function
                if len(functionTrace) != 0: 
                    # the map from the address to the line number of source file
                    addressLine = addrTOLine(functionTrace)
                    # Handle the jump statement that jump to the same line statement(the line number is the same)
                    pointLine = pointItself(functionTrace, addressLine)
                    # incomingNodes: <node, incomingNodes>, if node has no incoming nodes, the map returns empty set
                    # callingNodes: <node, callingNodes>, only the first node of the function body has calling node
                    # endNode: the end node of the function, which is used for postdominated analysis
                    (incomingNodes, endNode) = cfgConstruct(functionTrace)
                    # postDominateNodes: <node, domiantedNodes> and postDominateTrees <node, dominatingNodes>
                    (postDominateNodes, postDominateTrees) = postDominatedAnalysis(incomingNodes, endNode)
                    # compute the static CDG, the format: fileName:lineNumber--->fileName:lineNumber
                    cdgConstruct(CDGMap, incomingNodes, postDominateNodes, postDominateTrees, addressLine, pointLine, fileNameLine)
                #Ready for the next function
                fileNameLine = eachLine
                functionTrace = []
            else:     
                functionTrace.append(eachLine)
        #Handle the last function
        # the map from the address to the line number of source file
        addressLine = addrTOLine(functionTrace)
        # Handle the jump statement that jump to the same line statement(the line number is the same)
        pointLine = pointItself(functionTrace, addressLine)
        # incomingNodes: <node, incomingNodes>, if node has no incoming nodes, the map returns empty set
        # callingNodes: <node, callingNodes>, only the first node of the function body has calling node
        # endNode: the end node of the function, which is used for postdominated analysis
        (incomingNodes, endNode) = cfgConstruct(functionTrace)
        # postDominateNodes: <node, domiantedNodes> and postDominateTrees <node, dominatingNodes>
        (postDominateNodes, postDominateTrees) = postDominatedAnalysis(incomingNodes, endNode)
        # compute the static CDG, the format: fileName:lineNumber--->fileName:lineNumber
        cdgConstruct(CDGMap, incomingNodes, postDominateNodes, postDominateTrees, addressLine, pointLine, fileNameLine)

    return CDGMap

#Compute the dynamic control dependence
#The inputs are: the control flow graph and the execution trace, obtained through pintool  
def dynamicCDG(CDGMap, trace):  
    # CDGMap is the static control dependence:<fileName:lineNumber, Set(fileName:lineNumber)>
    # if the node is not dependent on other node, it would not appear in CDGMap        
    fileName = ""
    fileNameList = []
    # dependence is the dynamic control dependence: <index, index>
    controlDepen = {}
    callDepen = {}
    for i in range(0, len(trace)):
        slave = trace[i]
        if slave.find("#") != -1:
            callRet = callRetAbstract(slave)
            if callRet.find("C") != -1:
                fileName = fileNameAbstract(slave)
                fileNameList.append(fileName)
            elif callRet.find("R") != -1:
                fileNameList.pop()
                if len(fileNameList) != 0:
                    fileName = fileNameList[-1]
                else:
                    fileName = ""
                functionName = functionNameAbstract(slave)
                if cmp(functionName, "main") == 0:
                    return (controlDepen, callDepen)
            continue
        slaveStr = "%s:%s" % (fileName, slave)
        callNumber = 0;
        for j in range(i-1, -1, -1):
            master = trace[j]
            if master.find("#") != -1:
                callRet = callRetAbstract(master)
                if callRet.find("C") != -1:
                    callNumber = callNumber + 1
                elif callRet.find("R") != -1:
                    callNumber = callNumber - 1
                # function call dependence    
                if callNumber == 1 and j > 0:  
                    callDepen[i] = j-1           
                    break
            else:
                if callNumber == 0:
                    # The general control dependence
                    masterStr = "%s:%s" % (fileName, master)
                    if slaveStr in CDGMap:
                        mapValue = CDGMap[slaveStr]
                        if masterStr in mapValue:
                            controlDepen[i] = j
                            break
    return (controlDepen, callDepen)

def DCDGPrint(controlDepen, callDepen, trace, CDGFile):
    try:
        cdgFile = open(CDGFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        for i in range(0, len(trace)):
            if i in controlDepen:
                slave = trace[i]
                masterID = controlDepen[i]
                master = trace[masterID]
                controlDepenStr = "%s-->%s\n" % (slave, master)
                cdgFile.writelines(controlDepenStr)
            elif i in callDepen:
                slave = trace[i]
                masterID = callDepen[i]
                master = trace[masterID]
                controlDepenStr = "%s-->%s\n" % (slave, master)
                cdgFile.writelines(controlDepenStr)
        cdgFile.close()
    
if __name__ == '__main__':
    True