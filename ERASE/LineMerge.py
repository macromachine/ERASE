
import os
import re

# if the symbol ")" is matched and there is a key word such as "if", 
# it can be the independent line
def bracketMatch(lineStr):
    bracketNumber = 0
    endPoint = len(lineStr) - 1
    # bracket matching
    while endPoint >= 0:
        eachChar = lineStr[endPoint]
        if cmp(eachChar, ")") == 0:
            bracketNumber = bracketNumber + 1
        elif cmp(eachChar, "(") == 0:
            bracketNumber = bracketNumber - 1
        # bracket matching is finished, 
        # and then we identify the key word
        # there may be the case # define ... if ()
        if bracketNumber == 0:
            endPoint = endPoint - 1
            break
        else:
            endPoint = endPoint - 1
    # skip the blank space
    while endPoint >= 0:
        eachChar = lineStr[endPoint]
        if cmp(eachChar, "\n") == 0 or cmp(eachChar, "\t") == 0 or \
           cmp(eachChar, "\v") == 0 or cmp(eachChar, "\b") == 0 or \
           cmp(eachChar, "\r") == 0 or cmp(eachChar, "\f") == 0 or \
           cmp(eachChar, " ") == 0:
            endPoint = endPoint - 1
        else:
            break
    # identify the key word    
    startPoint = endPoint
    while startPoint >= 0:
        eachChar = lineStr[startPoint]
        if cmp(eachChar, "\n") == 0 or cmp(eachChar, "\t") == 0 or \
           cmp(eachChar, "\v") == 0 or cmp(eachChar, "\b") == 0 or \
           cmp(eachChar, "\r") == 0 or cmp(eachChar, "\f") == 0 or \
           cmp(eachChar, " ") == 0 or cmp(eachChar, ":") == 0 or \
           cmp(eachChar, ";") == 0 or cmp(eachChar, "{") == 0 or \
           cmp(eachChar, "}") == 0:
            break
        else:
            startPoint = startPoint - 1
    keyWord = lineStr[startPoint+1 : endPoint+1]
    
    if cmp(keyWord, "if") == 0 or cmp(keyWord, "for") == 0 or \
       cmp(keyWord, "while") == 0 or cmp(keyWord, "switch") == 0:
        return True
    else:
        return False
 
# matching the operator "?"
# if the statements are connected by "\", they have been handled
# and are concated as in lineStr
def questionMatch(lineStr):
    # the pattern for the char '"'
    quoteCharPattern = re.compile(r'\'\"\'', re.S)
    # delete the char '"'
    leftStr = re.sub(quoteCharPattern, "", lineStr)
    # the pattern for string "....."
    # Here, we do not consider the case such as "....afb\\"
    strPattern = re.compile(r'(?<!\\)\".*?(?<!\\)\"', re.S)
    # delete the string
    leftStr = re.sub(strPattern, "", leftStr)
    # the pattern for the char "?"
    questionCharPattern = re.compile(r'\'\?\'', re.S)
    # delete the char "?", because we need the operator ?
    leftStr = re.sub(questionCharPattern, "", leftStr)
    
    for eachChar in leftStr:
        if cmp(eachChar, "?") == 0:
            return True
    return False 

# identify the key words "else" or "do"
def doElseMatch(curLine):
    keyWord = ""
    for i in range(len(curLine)-1, -1, -1):
        eachChar = curLine[i]
        if cmp(eachChar, "\n") == 0 or cmp(eachChar, "\t") == 0 or \
           cmp(eachChar, "\v") == 0 or cmp(eachChar, "\b") == 0 or \
           cmp(eachChar, "\r") == 0 or cmp(eachChar, "\f") == 0 or \
           cmp(eachChar, " ") == 0 or cmp(eachChar, ":") == 0 or \
           cmp(eachChar, ";") == 0 or cmp(eachChar, "{") == 0 or \
           cmp(eachChar, "}") == 0:
            break
        else:
            keyWord = eachChar + keyWord
    if cmp(keyWord, "do") == 0 or cmp(keyWord, "else") == 0:
        return True
    else:
        return False   
      
# solve the situation in strftime.c in findutils-4.2.18
#    #ifdef __GNUC__
#    __inline__  
#    #endif   
def nextPoundSign(nextLine):
    if len(nextLine) != 0:
        firstChar = nextLine[0]
        if cmp(firstChar, "#") == 0:
            return True
        else:
            return False
    else:
        return False

def lineEndsWithBackslash(curLine, nextLine):
    # delete the last backslash
    curLine = curLine[0:len(curLine)-1].strip()
    if len(curLine) != 0:
        firstChar = curLine[0]
        lastChar = curLine[-1]
        # Here, we do not consider the case that last char is still "\\" as it is not the correct grammar 
        # it is the independent line, when it ends with "{", "}" and ";"
        if cmp(lastChar, "{")== 0 or cmp(lastChar, "}") == 0 or cmp(lastChar, ";") == 0:
            return True
        # if the symbol ")" is matched and there is a key word such as "if", it can be the independent line
        elif cmp(lastChar, ")") == 0:
            matched = bracketMatch(curLine)
            if matched == True:
                return True
            else:
                return False 
        # it is for the ?: operator
        # maybe the goto statement also has the symbol ":"
        elif cmp(lastChar, ":") == 0:
            matched = questionMatch(curLine)
            # if it is not matched, it is another case such as goto statement
            # it can be a independent line 
            if matched == False:
                return True
            else:
                return False
        # it is the statement while....do or if....else    
        elif doElseMatch(curLine) == True:
            return True
        # the next line begins with "#"
        elif nextPoundSign(nextLine) == True:
            return True 
        # the symbol "#" and "\\" would lead to merging
        # its priority is lowest
        # for example # define ....... if() { \ would not be merged
        elif cmp(firstChar, "#") == 0:
            return False
        else:
            return False       
    else:
        return True

# Maybe it is the multiple lines of the #define, we should specially consider its last line
# for example
#        #define cpy(n, s) \
#            add ((n),                                      \
#             if (to_lowcase)                              \
#               memcpy_lowcase (p, (s), _n LOCALE_ARG);                  \
#             else if (to_uppcase)                              \
#               memcpy_uppcase (p, (s), _n LOCALE_ARG);                  \
#             else                                      \
#               MEMCPY ((void *) p, (void const *) (s), _n)
#         void f(...).....
def lastLineOfDefine(resultStr):
    lines = resultStr.split("\n")
    for i in range(len(lines)-1, -1, -1):
        line = lines[i].strip()
        if len(line) != 0:
            firstChar = line[0]
            lastChar = line[-1]
            if cmp(lastChar, "\\") == 0:
                if cmp(firstChar, "#") == 0:
                    return True
            else:
                return False
    return False   
            
              
# determine whether the line is independent
# the returned value 0: this line is independent
# the returned value 1: this line is dependent, and the last char is "\\"
# the returned value 2: this line is dependent, and the next should be appended
def lineType(resultStr, curStr, nextStr):
    # delete the space character
    curLine = curStr.strip()
    nextLine = nextStr.strip()
    if len(curLine) != 0:
        firstChar = curLine[0]
        lastChar = curLine[-1]
        # the last char is "\\", which have the highest priority 
        # for example, # define ..... \
        #                      .....   
        if cmp(lastChar, "\\") == 0:
            endBackslash = lineEndsWithBackslash(curLine, nextLine)
            # if endBackslash is True, it is an independent line 
            if endBackslash == True:
                return 0
            else:
                return 1   
        # Maybe it is the multiple lines of the #define, we should specially consider its last line
        elif lastLineOfDefine(resultStr) == True:
            return 0
        # the line begins with "#" is an independent line 
        elif cmp(firstChar, "#") == 0:
            return 0
        # the next line begins with "#" is an independent line 
        elif nextPoundSign(nextLine) == True:
            return 0
        # the line ends with "{", "}" and ";" is an independent line
        elif cmp(lastChar, "{") == 0 or cmp(lastChar, "}") == 0 or cmp(lastChar, ";") == 0:
            return 0
        # if the symbol ")" is matched and there is a key word such as "if", it can be the independent line
        elif cmp(lastChar, ")") == 0:
            matched = bracketMatch(curLine)
            if matched == True:
                return 0
            else:
                return 2 
        # it is for the ?: operator
        # maybe the goto statement also has the symbol ":"
        elif cmp(lastChar, ":") == 0:
            matched = questionMatch(curLine)
            if matched == False:
                return 0
            else:
                return 2
        # the key words "do" and "else" is an independent line
        elif doElseMatch(curLine) == True:
            return 0
        else:
            return 2        
    else:
        return 0

# merging the statements that should be in a line
# merging is required, because the transmission of dependencies between statements
def lineMerge(fileStr):
    resultStr = ""
    fileList = fileStr.split("\n")
    fileListLen = len(fileList)
    if fileListLen != 0:
        index = 0
        curStr = fileList[index]
        while index < fileListLen-1:
            nextStr = fileList[index+1]
            operator = lineType(resultStr, curStr, nextStr)
            if operator == 0:
                resultStr = resultStr + curStr + "\n"
                curStr = nextStr
            elif operator == 1:
                slashIndex = curStr.rindex("\\")
                curStr = curStr[0:slashIndex] + nextStr          
            elif operator == 2:  
                curStr = curStr.rstrip()
                # it is for trap.c in the program bash 
                if curStr.endswith("GETORIGSIG(sig)") == True:
                    curStr = curStr + "\n" + nextStr.lstrip()   
                else:
                    curStr = curStr + " " + nextStr.lstrip()            
            index = index + 1 
        # the last line is directly appended 
        resultStr = resultStr + curStr + "\n"
    return resultStr
  
# determine it is the symbol "/*"
def leftComment(fileStr, fileStrLen, index):
    if cmp(fileStr[index],"/") == 0 and index+1 < fileStrLen and cmp(fileStr[index+1], "*") == 0:
        return True
    else:
        return False

# determine it is the symbol "*/"
def rightComment(fileStr, fileStrLen, index):
    if cmp(fileStr[index], "/") == 0 and index-1 >= 0 and cmp(fileStr[index-1], "*") == 0:
        return True
    else:
        return False
    
# determine it is the symbol "//"
def doubleSlash(fileStr, fileStrLen, index):
    if cmp(fileStr[index], "/") == 0 and index+1 < fileStrLen and cmp(fileStr[index+1], "/") == 0:
        return True
    else:
        return False
    
# determine it is the symbol "\""
def semicolon(fileStr, fileStrLen, index):
    if cmp(fileStr[index], "\"")==0:
        # it is for the cases "\"", "\\\"" and so on
        numBackslash = 0
        while index-numBackslash-1 >= 0:
            if cmp(fileStr[index-numBackslash-1], "\\") == 0:
                numBackslash = numBackslash + 1
            else:
                break
        if numBackslash % 2 == 1:
            return False
        # it is for the case '"'
        if index-1 >= 0 and cmp(fileStr[index-1], "'") == 0 and index+1 < fileStrLen and cmp(fileStr[index+1], "'") == 0:
            return False
        # the other cases
        return True
    else:
        return False
    
# delete the comment lines of a file, such /*...*/ and //....
def deleteComment(fileStr):
    resultStr = ""
    fileStrLen = len(fileStr)
    index = 0
    while index < fileStrLen:
        # it is used to delete the comment that is /*...*/
        if leftComment(fileStr, fileStrLen, index) == True:
            # used to forbid the case /*/
            index = index + 3
            while index < fileStrLen:
                if rightComment(fileStr, fileStrLen, index) == True:
                    index = index + 1
                    break
                else:
                    index = index + 1
        # it is used to delete the comment that is //.....
        elif doubleSlash(fileStr, fileStrLen, index) == True:
            index = index + 2
            while index < fileStrLen:
                if cmp(fileStr[index], "\n") == 0:
                    # note: symbol "\n" would not be deleted
                    break
                else:
                    index = index + 1          
        # it is for the case "......"
        elif semicolon(fileStr, fileStrLen, index) == True:
            resultStr = resultStr + fileStr[index]
            index = index + 1
            while index < fileStrLen:
                resultStr = resultStr + fileStr[index]
                if semicolon(fileStr, fileStrLen, index) == True:
                    index = index + 1
                    break
                else:
                    index = index + 1
        else:
            resultStr = resultStr + fileStr[index]
            index = index + 1
            
    return resultStr                
                              
# delete the comment lines of a file, such /*...*/ and //....
def _deleteComment(fileStr):
    resultStr = ""
    # string patter, we can see that there is no \ before "
    #strPattern = re.compile(r'(?<![\\\'])\".*?(?<![\\\'])\"', re.S)
    # There can be a ' before ", but cannot be \
    # For example, error (1, 0, _("invalid predicate `%s'"), predicate_name); in find.c
    # For example, char c = '"'
    #strPattern = re.compile(r'(?<![\\\'])\".*?(?<!\\)\"', re.S)
    # For example, "/:\\"
    strList = []
    leftList = []
    #strPattern1 = re.compile(r'(?<![\\\'])\".*?\\\\\"', re.S)
    # in bashline.c of the program bash
    #_filename_quote_characters = " \t\n\\\"'@<>=;|&()#$`?*[!:{";
    strPattern1 = re.compile(r'(?<![\\\'])\".*?(?<!\\)\\\\\"', re.S)
    strPattern2 = re.compile(r'(?<![\\\'])\".*?(?<!\\)\"|(?<![\\\'])\".*?\\\\\"', re.S)
    strList1 = strPattern1.findall(fileStr)
    leftList1 = re.split(strPattern1, fileStr)
    strList1_Len = len(strList1)
    leftList1_Len = len(leftList1)
    listIndex1 = 0
    while True:
        if listIndex1 < leftList1_Len:
            leftStr2 = leftList1[listIndex1]
            strList2 = strPattern2.findall(leftStr2)
            leftList2 = re.split(strPattern2, leftStr2)
            strList.append("")
            for eachStr2 in strList2:
                strList.append(eachStr2)
            for eachLeft2 in leftList2:
                leftList.append(eachLeft2)
        if listIndex1 < strList1_Len:
            leftStr2 = strList1[listIndex1]
            strList2 = strPattern2.findall(leftStr2)
            leftList2 = re.split(strPattern2, leftStr2)
            strList.append("")
            for eachStr2 in strList2:
                strList.append(eachStr2)
            for eachLeft2 in leftList2:
                leftList.append(eachLeft2)    
        listIndex1 = listIndex1 + 1
        if listIndex1 >= leftList1_Len and listIndex1 >= strList1_Len:
            del strList[0]
            break

    # comment /*....*/
    # require the signal re.S to change the behavior of .
    commentMPattern = re.compile(r"/\*.*?\*/", re.S)
    #comment //....
    commentSPattern = re.compile(r"//.*?\n", re.S)
    startIndex = 0
    startComment = False
    startTruncate = False
    for i in range(0, len(leftList)):
        eachStr = leftList[i]
        if startComment == True:
            #solve the format /*.....fs"fsfsfsdf"fsdfds....*/
            endIndex = eachStr.find("*/")
            if endIndex != -1:
                eachChangeStr = eachStr[endIndex+2:len(eachStr)]
                eachChangeStr = re.sub(commentMPattern, "", eachChangeStr)
                eachChangeStr = re.sub(commentSPattern, "\n", eachChangeStr)
                
                eachChangeStr = eachStr[0:endIndex+2] + eachChangeStr
                endIndex = len(resultStr) + endIndex                
                startComment = False 
                startTruncate = True             
            else:
                eachChangeStr = re.sub(commentSPattern, "\n", eachStr)    
        else:
            eachChangeStr = re.sub(commentMPattern, "", eachStr)
            eachChangeStr = re.sub(commentSPattern, "\n", eachChangeStr)
            
        startFind = len(resultStr)
        resultStr = resultStr + eachChangeStr
        # Only find */, we truncate the comment
        if startTruncate == True:
            resultStr = resultStr[0:startIndex] + resultStr[endIndex+2:len(resultStr)]
            startFind = startIndex
            startTruncate = False
        
        #solve the format /*.....fs"fsfsfsdf"fsdfds....*/  
        #prevent the multiple /* 
        if startComment == False:  
            startIndex = resultStr.find("/*", startFind, -1)
            if startIndex != -1:
                startComment = True          
        
        if i < len(strList):
            resultStr = resultStr + strList[i]
    return resultStr

def lineMergeFile(sourceFile, destinationFile):
    try:
        srcFile = open(sourceFile, "r")
        dstFile = open(destinationFile, "w")
    except IOError, e:
        print "*** file open error:", e
    else:
        fileStr = srcFile.read()
        fileStr = deleteComment(fileStr)
        fileStr = lineMerge(fileStr)
        dstFile.write(fileStr)        
        srcFile.close()
        dstFile.close()
        os.remove(sourceFile)
        os.rename(destinationFile, sourceFile)
        
def lineMergeDir(fileDir):
    if os.path.isdir(fileDir):
        for eachFile in os.listdir(fileDir):
            if os.path.isfile(os.path.join(fileDir, eachFile)):
                fileItem = os.path.splitext(eachFile)
                if fileItem[1] == ".c" or fileItem[1] == ".C":
                    filePath = os.path.join(fileDir, eachFile)
                    _fileName = "_" + eachFile
                    _filePath = os.path.join(fileDir, _fileName)
                    lineMergeFile(filePath, _filePath)
            elif os.path.isdir(os.path.join(fileDir, eachFile)):
                lineMergeDir(os.path.join(fileDir, eachFile))
    else:
        print "Not Directory Error!"
                
if __name__ == '__main__':
    True