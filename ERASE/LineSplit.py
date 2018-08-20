
import os

# determine it is the symbol "\""
def doubleQuotation(lineStr, lineLen, index):
    if cmp(lineStr[index], "\"")==0:
        # it is for the cases "\"", "\\\"" and so on
        numBackslash = 0
        while index-numBackslash-1 >= 0:
            if cmp(lineStr[index-numBackslash-1], "\\") == 0:
                numBackslash = numBackslash + 1
            else:
                break
        if numBackslash % 2 == 1:
            return False
        # it is for the case '"'
        if index-1 >= 0 and cmp(lineStr[index-1], "'") == 0 and index+1 < lineLen and cmp(lineStr[index+1], "'") == 0:
            return False
        # the other cases
        return True
    else:
        return False
    
# determine it is the symbol "\'"
def singleQuotation(lineStr, lineLen, index):
    if cmp(lineStr[index], "\'")==0:
        # it is for the cases "\"", "\\\"" and so on
        numBackslash = 0
        while index-numBackslash-1 >= 0:
            if cmp(lineStr[index-numBackslash-1], "\\") == 0:
                numBackslash = numBackslash + 1
            else:
                break
        if numBackslash % 2 == 1:
            return False
        # it is for the case '''
        if index-1 >= 0 and cmp(lineStr[index-1], "'") == 0 and index+1 < lineLen and cmp(lineStr[index+1], "'") == 0:
            return False
        # the other cases
        return True
    else:
        return False
    
# find the key word 
def findKeywords(eachLine, keyWord, delimiterWords):
    keyWordLen = len(keyWord)
    startPoint = 0
    while True:
        wordIndex = eachLine.find(keyWord, startPoint)
        # It does not find the key word
        if wordIndex == -1:
            return -1
        elif wordIndex == 0:
            # the keyword is the first word in eachLine
            if len(eachLine) > keyWordLen:
                nextChar = eachLine[keyWordLen]
                if nextChar in delimiterWords:
                    return wordIndex
            else:
                # eachLine is the key word
                return wordIndex
        else:
            previousChar = eachLine[wordIndex-1]
            if  previousChar in delimiterWords:
                if len(eachLine) > (wordIndex + keyWordLen):
                    nextChar = eachLine[wordIndex + keyWordLen]
                    if nextChar in delimiterWords:
                        return wordIndex
                else:
                    # Key word is the last word
                    return wordIndex
        startPoint = wordIndex + 1  
    return -1 

# it is a sequence, which can not be splitted
def sequenceComputation(eachItem, eachLen, eachIndex, resultStr):
    sequenceIndex = True
    if doubleQuotation(eachItem, eachLen, eachIndex) == True:
        # the case is for "...."
        resultStr = resultStr + eachItem[eachIndex]
        eachIndex = eachIndex + 1
        while eachIndex < eachLen:
            resultStr = resultStr + eachItem[eachIndex]
            if doubleQuotation(eachItem, eachLen, eachIndex) == True:
                eachIndex = eachIndex + 1
                break
            else:
                eachIndex = eachIndex + 1
    elif singleQuotation(eachItem, eachLen, eachIndex) == True:
        # the case is for ';'
        resultStr = resultStr + eachItem[eachIndex]
        eachIndex = eachIndex + 1
        while eachIndex < eachLen:
            resultStr = resultStr + eachItem[eachIndex]
            if singleQuotation(eachItem, eachLen, eachIndex) == True:
                eachIndex = eachIndex + 1
                break
            else:
                eachIndex = eachIndex + 1
    elif cmp(eachItem[eachIndex], "(") == 0:
        # the case is for a = f(a, b,....)
        resultStr = resultStr + eachItem[eachIndex]
        eachIndex = eachIndex + 1
        bracketNum = 1
        while eachIndex < eachLen:
            resultStr = resultStr + eachItem[eachIndex]
            if cmp(eachItem[eachIndex], "(") == 0:
                eachIndex = eachIndex + 1
                bracketNum = bracketNum + 1
            elif cmp(eachItem[eachIndex], ")") == 0:
                eachIndex = eachIndex + 1
                breacketNum = bracketNum - 1
                if breacketNum == 0:
                    break
            else:
                eachIndex = eachIndex + 1    
    elif cmp(eachItem[eachIndex], "{") == 0:
        # the case is for a[] = {1, 3, ....}
        resultStr = resultStr + eachItem[eachIndex]
        eachIndex = eachIndex + 1
        bracketNum = 1
        while eachIndex < eachLen:
            resultStr = resultStr + eachItem[eachIndex]
            if cmp(eachItem[eachIndex], "{") == 0:
                eachIndex = eachIndex + 1
                bracketNum = bracketNum + 1
            elif cmp(eachItem[eachIndex], "}") == 0:
                eachIndex = eachIndex + 1
                breacketNum = bracketNum - 1
                if breacketNum == 0:
                    break
            else:
                eachIndex = eachIndex + 1 
    elif cmp(eachItem[eachIndex], "[") == 0:
        resultStr = resultStr + eachItem[eachIndex]
        eachIndex = eachIndex + 1
        bracketNum = 1
        while eachIndex < eachLen:
            resultStr = resultStr + eachItem[eachIndex]
            if cmp(eachItem[eachIndex], "[") == 0:
                eachIndex = eachIndex + 1
                bracketNum = bracketNum + 1
            elif cmp(eachItem[eachIndex], "]") == 0:
                eachIndex = eachIndex + 1
                breacketNum = bracketNum - 1
                if breacketNum == 0:
                    break
            else:
                eachIndex = eachIndex + 1     
    else:
        sequenceIndex = False
    return (resultStr, eachIndex, sequenceIndex)

def semicolonHandle(eachItem, eachLen, eachIndex, resultStr):
    resultStr = resultStr + eachItem[eachIndex]
    nextIndex = eachIndex + 1
    while nextIndex < eachLen:
        nextEle = eachItem[nextIndex]
        if cmp(nextEle, "\t") == 0 or cmp(nextEle, "\n") == 0 or cmp(nextEle, "\v") == 0 or cmp(nextEle, "\f") == 0 or \
         cmp(nextEle, "\r") == 0 or cmp(nextEle, "\b") == 0 or cmp(nextEle, " ") == 0:                     
            nextIndex = nextIndex + 1
        else:
            break
    # there is a next element and it is not a backslash
    if nextIndex < eachLen and cmp(eachItem[nextIndex], "\\") != 0:
        if eachItem.endswith(";") == False:
            resultStr = resultStr + "\\" + "\n"
        else:
            resultStr = resultStr + "\n"
    return resultStr

def commaHandle(eachItem, eachLen, eachIndex, resultStr):
    resultStr = resultStr + eachItem[eachIndex]
    nextIndex = eachIndex + 1
    while nextIndex < eachLen:
        nextEle = eachItem[nextIndex]
        if cmp(nextEle, "\t") == 0 or cmp(nextEle, "\n") == 0 or cmp(nextEle, "\v") == 0 or cmp(nextEle, "\f") == 0 or \
         cmp(nextEle, "\r") == 0 or cmp(nextEle, "\b") == 0 or cmp(nextEle, " ") == 0:                     
            nextIndex = nextIndex + 1
        else:
            break
    if nextIndex < eachLen and cmp(eachItem[nextIndex], "\\") != 0:
        resultStr = resultStr + "\\" + "\n"
    return resultStr

def lineSplitAll(fileStr):
    # the delimiter for the key word    
    delimiterWords = set()
    delimiterWords.add("\t")
    delimiterWords.add("\n")
    delimiterWords.add("\v")
    delimiterWords.add("\f")
    delimiterWords.add("\r")
    delimiterWords.add("\b")
    delimiterWords.add(" ")
    delimiterWords.add("(")
    delimiterWords.add(")")
    delimiterWords.add("{")
    delimiterWords.add("}")
    delimiterWords.add("[")
    delimiterWords.add("]")
    delimiterWords.add(";")
    delimiterWords.add(":")
    delimiterWords.add(",")
    strItem = fileStr.split("\n")
    fileStr = ""
    for eachItem in strItem:
        eachItem = eachItem.rstrip()
        resultStr = ""
        eachIndex = 0
        eachLen = len(eachItem)
        if findKeywords(eachItem, "struct", delimiterWords) != -1 and eachItem.endswith("{") == True:
            # it is for program gettext
            # in many *.oo.c files, the symbol "{" cannot be append to the above statement, otherwise it cannot pass compiling
            # for example: 
            # struct fd_ostream : struct ostream
            # {
            # fields:
            # ....
            # }
            while eachIndex < eachLen-1:
                resultStr = resultStr + eachItem[eachIndex]
                eachIndex = eachIndex + 1
            resultStr = resultStr + "\n" + "{"
            eachItem = resultStr
            resultStr = ""
        eachIndex = 0
        eachLen = len(eachItem)
        forWordIndex = findKeywords(eachItem, "for", delimiterWords)
        if forWordIndex != -1:
            # the comma operation will be splitted in the for statement
            # for example for (a=1, b =5; a < b; a++, b++)
            while eachIndex < forWordIndex:
                resultStr = resultStr + eachItem[eachIndex]
                eachIndex = eachIndex + 1
            enterZone = False       
            while eachIndex < eachLen:
                if enterZone == False:
                    if cmp(eachItem[eachIndex], "(") == 0:
                        resultStr = resultStr + eachItem[eachIndex]
                        enterZone = True
                        eachIndex = eachIndex + 1
                        continue
                if enterZone == True:
                    if cmp(eachItem[eachIndex], ")") == 0:
                        resultStr = resultStr + eachItem[eachIndex]
                        eachIndex = eachIndex + 1
                        break
                (resultStr, eachIndex, sequenceIndex) = sequenceComputation(eachItem, eachLen, eachIndex, resultStr)
                if sequenceIndex == False:
                    if enterZone == True and cmp(eachItem[eachIndex], ",") == 0:
                        resultStr = commaHandle(eachItem, eachLen, eachIndex, resultStr)
                    else:
                        resultStr = resultStr + eachItem[eachIndex]
                    eachIndex = eachIndex + 1
            while eachIndex < eachLen:
                resultStr = resultStr + eachItem[eachIndex]
                eachIndex = eachIndex + 1
            eachItem = resultStr
            resultStr = ""
        eachIndex = 0
        eachLen = len(eachItem)
        while eachIndex < eachLen:
            (resultStr, eachIndex, sequenceIndex) = sequenceComputation(eachItem, eachLen, eachIndex, resultStr)
            if sequenceIndex == False:          
                if cmp(eachItem[eachIndex], ";") == 0:
                    resultStr = semicolonHandle(eachItem, eachLen, eachIndex, resultStr)
                elif cmp(eachItem[eachIndex], ",") == 0:
                    resultStr = commaHandle(eachItem, eachLen, eachIndex, resultStr)
                else:
                    resultStr = resultStr + eachItem[eachIndex]
                eachIndex = eachIndex + 1
        fileStr = fileStr + resultStr + "\n"            
    return fileStr   

def lineSplitFile(sourceFile, destinationFile):
    try:
        srcFile = open(sourceFile, "r")
        dstFile = open(destinationFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        fileStr = srcFile.read()
        fileStr = lineSplitAll(fileStr)
        dstFile.write(fileStr)        
        srcFile.close()
        dstFile.close()
        os.remove(sourceFile)
        os.rename(destinationFile, sourceFile)

def lineSplitDir(fileDir):                
    if os.path.isdir(fileDir):
        for eachFile in os.listdir(fileDir):
            if os.path.isfile(os.path.join(fileDir, eachFile)):
                fileItem = os.path.splitext(eachFile)
                if fileItem[1] == ".c" or fileItem[1] == ".C":
                    filePath = os.path.join(fileDir, eachFile)
                    _fileName = "_" + eachFile
                    _filePath = os.path.join(fileDir, _fileName)
                    lineSplitFile(filePath, _filePath)
            elif os.path.isdir(os.path.join(fileDir, eachFile)):
                lineSplitDir(os.path.join(fileDir, eachFile))
    else:
        print "Not Directory Error!"

if __name__ == '__main__':
    pass