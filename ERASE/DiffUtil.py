
import os
import shutil

# the returned path includes its last backslash
def PathAndName(pathFile):
    backslash = pathFile.rfind("/")
    if backslash == -1:
        return ("", pathFile)
    else:
        # The path includes its last backslash
        return (pathFile[:backslash+1], pathFile[backslash+1:])     

def DiffAlign(fileNameLine, fileDiff, corresFile, deletionFile, additionFile):
    # get the file that should be aligned
    fileNameEle = fileNameLine.split(" ")
    fileSrc = fileNameEle[len(fileNameEle)-2]
    fileDst = fileNameEle[len(fileNameEle)-1]
    (fileSrcPath, fileSrcName) = PathAndName(fileSrc)
    (fileDstPath, fileDstName) = PathAndName(fileDst)
    _fileSrc = fileSrcPath + "_" + fileSrcName
    _fileDst = fileDstPath + "_" + fileDstName 
    # we does not align the *.y file
    if os.path.splitext(fileSrcName)[1] == ".y" or os.path.splitext(fileSrcName)[1] == ".Y":
        return
    if os.path.splitext(fileDstName)[1] == ".y" or os.path.splitext(fileDstName)[1] == ".Y":
        return    
    try:
        # Two directory may have different files
        fileSrcIndex = os.path.exists(fileSrc)
        if fileSrcIndex == True:
            fileSrcRead = open(fileSrc)
            # "w": if file exists, empty the content and write the new content
            fileSrcWrite = open(_fileSrc, "w")  
        fileDstIndex = os.path.exists(fileDst)          
        if fileDstIndex == True:
            fileDstRead = open(fileDst)
            # "w": if file exists, empty the content and write the new content
            fileDstWrite = open(_fileDst, "w")
        # "a+", to read and write the file, the content is appended in the file tail 
        corresTrace = open(corresFile, "a+")
        deletionTrace = open(deletionFile, "a+")
        additionTrace = open(additionFile, "a+")
        
    except IOError, e:
        print "*** file open error:", e
    else: 
        corresMap = {} 
        deletionMap = {}
        additionMap = {} 
        srcMap = {}
        dstMap = {}          
        for eachLine in fileDiff:
            # Example: @@ -0,0 +1,272 @@
            element = eachLine.split(" ")
            # delete the "-" and "+"
            infoSrc = element[1][1:]
            infoDst = element[2][1:]
            # splitting line number and number of lines
            elementSrc = infoSrc.split(",")
            elementDst = infoDst.split(",")
            # line number, and number of lines
            # default number of lines is 1
            lineSrc = int(elementSrc[0])
            numSrc = 1
            if len(elementSrc) == 2:
                numSrc = int(elementSrc[1])    
            lineDst = int(elementDst[0])
            numDst = 1
            if len(elementDst) == 2:
                numDst = int(elementDst[1])
            # number of lines is 0, it belongs to the addition or deletion situation    
            if numSrc == 0:
                # the addition or deletion should +1 to locate the position
                lineSrc = lineSrc + 1
                srcMap[lineSrc] = numDst
            else:
                # at the line number lineSrc+numSrc, we add numDst blank lines
                srcMap[lineSrc+numSrc] = numDst
            if numDst == 0:
                # the addition or deletion should +1 to locate the position
                lineDst = lineDst + 1
                dstMap[lineDst] = numSrc
            else:
                # at the line number lineDst, we add numSrc blank lines
                dstMap[lineDst] = numSrc
            # Only considering the changes,not including the addition and deletion
            if numSrc != 0 and numDst != 0:
                corresMap[lineSrc] = [numSrc, numDst]
            elif numSrc != 0:
                deletionMap[lineSrc] = numSrc
            elif lineDst != 0:
                additionMap[lineDst] = numDst
                
        if fileSrcIndex == True:
            # accumulated line number, including the added blank lines        
            lineNumber = 0      
            lastLine = "\n"    
            for (num, value) in enumerate(fileSrcRead): 
                # num begins from 0, it is different from the line number from the tool diff
                num = num + 1
                if num in srcMap:
                    mapValue = srcMap[num]
                    for i in range(0, mapValue):
                        # delete the last character "\n"
                        lastLine = lastLine[0:-1]
                        lastLine = lastLine.strip()
                        if len(lastLine) != 0 and cmp(lastLine[-1], "\\") == 0:
                            fileSrcWrite.writelines("\\\n")
                            lastLine = "\\\n"
                        else:
                            fileSrcWrite.writelines("\n")
                            lastLine = "\n"
                    lineNumber = lineNumber + mapValue
                # the value should be appended after the blank lines
                fileSrcWrite.writelines(value)
                lastLine = value
                lineNumber = lineNumber + 1
                
                if num in corresMap:
                    [numSrc, numDst] = corresMap[num]                                                             
                    for i in range(0, numSrc):
                        for j in range(0, numDst):
                            # the line number starts from 1 not 0
                            corresStr = "%s#%d#%d\n" % (fileSrcName, lineNumber+i, lineNumber+numSrc+j)
                            corresTrace.writelines(corresStr)
                if num in deletionMap:
                    numSrc = deletionMap[num]
                    for i in range(0, numSrc):
                        # the line number starts from 1 not 0
                        deletionStr = "%s#%d\n" % (fileSrcName, lineNumber+i)
                        deletionTrace.writelines(deletionStr)
            fileSrcRead.close()
            fileSrcWrite.close()
                        
        if fileDstIndex == True:
            lineNumber = 0
            lastLine = "\n"
            for (num, value) in enumerate(fileDstRead): 
                num = num + 1
                if num in dstMap:
                    mapValue = dstMap[num]
                    for i in range(0, mapValue):
                        lastLine = lastLine[0:-1]
                        lastLine = lastLine.strip()
                        if len(lastLine) != 0 and lastLine[-1] == "\\":
                            fileDstWrite.writelines("\\\n")
                            lastLine = "\\\n"
                        else:
                            fileDstWrite.writelines("\n")
                            lastLine = "\n"
                    lineNumber = lineNumber + mapValue
                fileDstWrite.writelines(value)
                lastLine = value
                lineNumber = lineNumber + 1
                
                if num in additionMap:
                    numDst = additionMap[num]
                    for i in range(0, numDst):
                        # the line number starts from 1 not 0
                        additionStr = "%s#%d\n" % (fileDstName, lineNumber+i)
                        additionTrace.writelines(additionStr)
            fileDstRead.close()
            fileDstWrite.close()
            
        corresTrace.close()
        deletionTrace.close()
        additionTrace.close()
           
        if fileSrcIndex == True:
            os.remove(fileSrc)  
            shutil.move(_fileSrc, fileSrc)
        if fileDstIndex == True:
            os.remove(fileDst)
            shutil.move(_fileDst, fileDst)  

# changeFile: the changes reported by the tool diff
# corresFile: the corresponding statements, which are modified, in two versions
# deletionFile: the deleted statements in the original version
# additionFile: the added statements in the modified version
def DiffProcess(changeFile, corresFile, deletionFile, additionFile):
    if os.path.exists(corresFile):
        os.remove(corresFile)
    if os.path.exists(deletionFile):
        os.remove(deletionFile)
    if os.path.exists(additionFile):
        os.remove(additionFile)
    try:
        changeTrace = open(changeFile)
    except IOError, e:
        print "*** file open error:", e
    else:
        fileNameLine = ""
        # the list of differences, such as @@ -143,140 +10,8 @@
        fileDiff = []
        for eachLines in changeTrace:
            eachLine = eachLines.strip()
            # Because the diff tool is applied to a directory not a file
            # "diff -NbrU 0" includes the differences of a file 
            if eachLine.startswith("diff -NbrU 0") == True:
                # aligning a file
                if fileNameLine != "":
                    DiffAlign(fileNameLine, fileDiff, corresFile, deletionFile, additionFile)
                fileNameLine = eachLine
                fileDiff = []
            elif eachLine.startswith("@@") == True:
                fileDiff.append(eachLine)
        DiffAlign(fileNameLine, fileDiff, corresFile, deletionFile, additionFile)        
    print "Diff Done!"
       
if __name__ == '__main__':
    True