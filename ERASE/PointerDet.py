
# dataTrace: the form is [["W/R", address, value], ....]
# pointerSet: the form is set(index), note that the index is the same with dataTrace
# which does not count the function call and return 
def pointerDet(pointerSet, dataTrace):
    addrMin = long("0xFFFFFFFF", 16)
    addrMax = long("0x00000000", 16)
    valueList = []
    dataIndex = 0
    dataLen = len(dataTrace)
    while dataIndex < dataLen:
        dataEle = dataTrace[dataIndex]
        dataIndex = dataIndex + 1
        # the address may not be obtained in some cases
        # it is the problem of pin tool
        if dataEle[1].find("nil") == -1:
            addrItem = long(dataEle[1], 16)
            if addrItem > addrMax:
                addrMax = addrItem
            if addrItem < addrMin:
                addrMin = addrItem
        valueItem = long(dataEle[2], 16)
        valueList.append(valueItem)
    valueIndex = 0
    valueLen = len(valueList)
    while valueIndex < valueLen:
        valueEle = valueList[valueIndex]
        if valueEle >= addrMin and valueEle <= addrMax:
            pointerSet.add(valueIndex)
        valueIndex = valueIndex + 1              

if __name__ == '__main__':
    True
    