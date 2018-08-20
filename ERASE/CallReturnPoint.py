
def callRetAbstract(elementStr):
    elements = elementStr.split("#")
    callRet = elements[2].strip()
    return callRet

# find the corresponding function call and function return, the form is [(index, index), ....]
# the function call has no corresponding function return, it would not appear in callReturnPair
def callReturnMap(trace, startPoint, callReturnPair):
    callPointStr = ""
    if startPoint-1 >= 0:
        callPointStr = trace[startPoint-1]     
    traceIndex = startPoint + 1
    traceLen = len(trace)
    while traceIndex < traceLen:
        traceEle = trace[traceIndex]
        if traceEle.find("#") != -1:
            callRet = callRetAbstract(traceEle)
            if callRet.find("C") != -1:
                # the returned traceIndex is the next instance of the "...#...#R"
                traceIndex = callReturnMap(trace, traceIndex, callReturnPair)
            elif callRet.find("R") != -1:
                if traceIndex+1 < traceLen:
                    returnPointStr = trace[traceIndex+1]
                    # we do not compare the file name, because these two elements must be in the same file
                    if cmp(callPointStr, returnPointStr) == 0:
                        callReturnPair.append((startPoint-1, traceIndex+1))
                traceIndex = traceIndex + 1
                return traceIndex
        else:
            traceIndex = traceIndex + 1
    print "Call Return Pair ERROR!"
    return traceIndex 

def callReturnPoint(trace):
    # the format [(function call, function return),....]
    # callReturnPair is ordered by the sequence of the function return
    callReturnPair = []
    callReturnMap(trace, 0, callReturnPair)
    # find the function call point based on the function return point
    returnCallMap = {}
    # the form is <index, sign>, the sign is used to represent it is a 
    # function call, function return, or both
    # is is used to align the function calling, because we should know it's function call, return or both 
    # in fact, we can see that how many function calling in a statement through callReturnBoth
    callReturnBoth = {}
    # the form is <index, [index,....]>
    # we can determine that an statement is data dependent on which function returns through returnDepen
    returnTogether = {}
    # the pure function call points, does not include the points that are simultaneously calling and returning 
    pureCallSet = set()
    # the pure function return points, does not include the points that are simultaneously calling and returning
    pureReturnSet = set()
    for eachPair in callReturnPair:
        master = eachPair[0]
        slave = eachPair[1]
        # find the function call point based on the function return point
        returnCallMap[slave] = master
        if master in callReturnBoth:
            value = callReturnBoth[master]
            callReturnBoth[slave] = value + 1
            if master in returnTogether:
                returnValue = returnTogether[master]
                returnValue.append(slave)
                returnTogether[slave] = returnValue
                # it is not the final assignment instance
                # it is only the middle function return
                del returnTogether[master]
            # master must be the slave of another callReturnPair
            pureReturnSet.remove(master)
        else:
            callReturnBoth[master] = 0
            callReturnBoth[slave] = 1
            returnTogether[slave] = [slave]
            pureCallSet.add(master)
        pureReturnSet.add(slave)
    return (returnCallMap, callReturnBoth, pureCallSet, pureReturnSet, returnTogether)             

if __name__ == '__main__':
    True