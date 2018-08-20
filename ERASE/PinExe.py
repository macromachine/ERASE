
import os

        
def pinCFG(exeFile, workspace, parameter, srcDst):
    # change the current workspace
    os.chdir(workspace)
    pinPath = "/home/***/Tools/pin/source/tools/MyPinTool/obj-ia32"
    if srcDst==True:
        CFGCmd = "pin -t %s/srcCFGTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    else:
        CFGCmd = "pin -t %s/dstCFGTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    os.system("echo 206|sudo -S %s" % (CFGCmd))

def pinTraceData(exeFile, workspace, parameter, srcDst):
    # change the current workspace
    os.chdir(workspace)
    pinPath = "/home/***/Tools/pin/source/tools/MyPinTool/obj-ia32"
    if srcDst==True:
        TraceDataCmd = "pin -t %s/srcTraceDataTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    else:
        TraceDataCmd = "pin -t %s/dstTraceDataTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    os.system("echo 206|sudo -S %s" % (TraceDataCmd))      

    
def pinCode(exeFile, workspace, parameter, srcDst):
    # change the current workspace
    os.chdir(workspace)
    pinPath = "/home/***/Tools/pin/source/tools/MyPinTool/obj-ia32"
    if srcDst==True:
        CodeDataCmd = "pin -t %s/srcCodeDataTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    else:
        CodeDataCmd = "pin -t %s/dstCodeDataTool_one.so -- %s %s" % (pinPath, exeFile, parameter)
    os.system("echo 206|sudo -S %s" % (CodeDataCmd))

if __name__ == '__main__':
    pass
    
    