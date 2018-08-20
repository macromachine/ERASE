/*BEGIN_LEGAL 
Intel Open Source License 

Copyright (c) 2002-2015 Intel Corporation. All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.  Redistributions
in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.  Neither the name of
the Intel Corporation nor the names of its contributors may be used to
endorse or promote products derived from this software without
specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE INTEL OR
ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
END_LEGAL */
//
// This tool prints the Instruction information
//
#include <fstream>
#include <iostream>
#include <cassert>
#include <string.h>
#include "pin.H"
#include <set>

FILE * LINETrace;
static INT32 lastNumber = 0;
static string lastFile = "";
static bool lastCall = false;
static bool lastSysIns = false;
static ADDRINT address = 0;
static INT processId = -1;
static UINT threadId = UINT_MAX;

class LineInfo{
public:
	string fileName;
    string callName;
	INT32 lineNumber;

	LineInfo(string fn, string cn, INT32 ln): 
	fileName(fn), callName(cn), lineNumber(ln){}

};

typedef set<LineInfo *> LineInfoSet;
static LineInfoSet lineInfoSet;

// Store the function call information
class CallInfo{
  public:
    // the dirct address of the call instruction
    ADDRINT address;

    CallInfo(ADDRINT addr) :
    address(addr) {}
};

typedef set<CallInfo *> CallInfoSet;
static CallInfoSet callInfoSet;

// obtain the fileName from the path
const char * StripPath(const char * path)
{
    const char * file = strrchr(path,'/');
    if (file){
        return file+1;
    }
    else{
        return path;
    }
}

//print the call instructin information
VOID LINECallInfo(VOID * ip, CallInfo * callInfo, LineInfo *lineInfo){ 
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    INT32 lineNumber = lineInfo->lineNumber;
    string fileName = lineInfo->fileName;  
    if(lineNumber != lastNumber || fileName != lastFile){
        if(lastFile == ""){
            //fprintf(LINETrace, "%s#C\n", fileName.c_str());
            fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
            fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
        }
        else{
            if(lastCall == true){
                char * bufferIP = new char[20];
                sprintf(bufferIP, "%p", ip);
                char * bufferAddr = new char[20];
                sprintf(bufferAddr, "0x%x", address);
                //Determine that the statement is the first statement of the user-defined function(direct function call)
                //It does not consider the system function call
                if(strcmp(bufferIP, bufferAddr) == 0){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // indirect function call (such as function pointer)
                else if(lastSysIns == false){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // system funcnction call
                else{
                   fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber); 
                }
                delete [] bufferIP;
                delete [] bufferAddr; 
            }
            else{
                fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
            }
                
        }
        lastNumber = lineNumber;
        lastFile = fileName;
    } 
    // Used to determine the user-defined function call
    lastCall = true;
    lastSysIns = false;
    address = callInfo->address;

}

// print the indirect call information, such as function pointer
VOID LINEIndirectCallInfo(VOID * ip, LineInfo *lineInfo){ 
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    INT32 lineNumber = lineInfo->lineNumber;
    string fileName = lineInfo->fileName;  
  
    if(lineNumber != lastNumber || fileName != lastFile){
        if(lastFile == ""){
            //fprintf(LINETrace, "%s#C\n", fileName.c_str());
            fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
            fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
        }
        else{

            if(lastCall == true){
                char * bufferIP = new char[20];
                sprintf(bufferIP, "%p", ip);
                char * bufferAddr = new char[20];
                sprintf(bufferAddr, "0x%x", address);
                //Determine that the statement is the first statement of the user-defined function(direct function call)
                //It does not consider the system function call
                if(strcmp(bufferIP, bufferAddr) == 0){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // indirect function call (such as function point)
                else if(lastSysIns == false){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // system funcnction call
                else{
                   fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber); 
                }
                delete [] bufferIP;
                delete [] bufferAddr;  
            }
            else{
                fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
            }
               
        }
        lastNumber = lineNumber;
        lastFile = fileName;
    } 
    lastCall = true;
    lastSysIns = false;
    address = 0;

}

// print the call ret information
VOID LINERetInfo(VOID * ip, LineInfo *lineInfo){
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    INT32 lineNumber = lineInfo->lineNumber;
    string fileName = lineInfo->fileName; 
    
    if(lineNumber != lastNumber || fileName != lastFile){
        if(lastFile == ""){
            //fprintf(LINETrace, "%s#C\n", fileName.c_str());
            fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
            fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
        }
        else{

            if(lastCall == true){
                char * bufferIP = new char[20];
                sprintf(bufferIP, "%p", ip);
                char * bufferAddr = new char[20];
                sprintf(bufferAddr, "0x%x", address);
                //Determine that the statement is the first statement of the user-defined function(direct function call)
                //It does not consider the system function call
                if(strcmp(bufferIP, bufferAddr) == 0){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // indirect function call (such as function point)
                else if(lastSysIns == false){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // system funcnction call
                else{
                   fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber); 

                }
                delete [] bufferIP;
                delete [] bufferAddr;
            }
            else{
                fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
            }

        }
        lastNumber = lineNumber;
        lastFile = fileName;
    }
    //It represents that the function is finished
    //fprintf(LINETrace, "%s#R\n", fileName.c_str());
    fprintf(LINETrace, "%s#%s#R\n", fileName.c_str(), lineInfo->callName.c_str());
    lastCall = false;
    lastSysIns = false;
}

// print the general instruction information
VOID LINEGenInfo(VOID * ip, LineInfo *lineInfo){
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    INT32 lineNumber = lineInfo->lineNumber;
    string fileName = lineInfo->fileName; 
    
    if(lineNumber != lastNumber || fileName != lastFile){
        if(lastFile == ""){
            //fprintf(LINETrace, "%s#C\n", fileName.c_str());
            fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
            fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
        }
        else{
            if(lastCall == true){
                char * bufferIP = new char[20];
                sprintf(bufferIP, "%p", ip);
                char * bufferAddr = new char[20];
                sprintf(bufferAddr, "0x%x", address);
                //Determine that the statement is the first statement of the user-defined function(direct function call)
                //It does not consider the system function call
                if(strcmp(bufferIP, bufferAddr) == 0){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // indirect function call (such as function point)
                else if(lastSysIns == false){
                    //fprintf(LINETrace, "%s#C\n", fileName.c_str());
                    fprintf(LINETrace, "%s#%s#C\n", fileName.c_str(), lineInfo->callName.c_str());
                    fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
                }
                // system funcnction call
                else{
                   fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber); 
                }
                delete [] bufferIP;
                delete [] bufferAddr;
            }
            else{
                fprintf(LINETrace,"%s:%s:%d\n", fileName.c_str(), lineInfo->callName.c_str(), lineNumber);
            }

        }
        lastNumber = lineNumber;
        lastFile = fileName;
    }
    lastCall = false;
    lastSysIns = false;
}

// Mark this instructiion is system code
VOID SysCodeInfo(){
    lastSysIns = true;
}

static VOID Instruction(INS ins, VOID *v)
{    
    string fileName;
    string rtnName;
    INT32 lineNumber; 

    PIN_GetSourceLocation(INS_Address(ins), NULL, &lineNumber, &fileName);
    if(lineNumber == 0){
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)SysCodeInfo, IARG_END);
		return;
    }

    RTN rtn = INS_Rtn(ins);
    if(!RTN_Valid(rtn)){
        return;
    }
    rtnName = RTN_Name(rtn);

    LineInfo *lineInfo = new LineInfo(StripPath(fileName.c_str()), rtnName, lineNumber); 
    lineInfoSet.insert(lineInfo);

    // Insert the analysis component, which record the line sequence
    // The format: function call, 1, 2, 3, function call, 8, 9, function return, 3, 4, function return
    if(INS_IsDirectCall(ins)){
        // function call
        ADDRINT addr = INS_DirectBranchOrCallTargetAddress(ins);
        CallInfo * callInfo = new CallInfo(addr);
        callInfoSet.insert(callInfo);
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)LINECallInfo, IARG_INST_PTR, IARG_ADDRINT, callInfo, IARG_ADDRINT, lineInfo, IARG_END);
    }
    else if(INS_IsCall(ins)){
        //indirect function call, such as function pointer
        //Line 601 in find.c of findutils-4.2.18
        // If the last instruction is call instruction and the immideate instruction is the user-defined instruction
        // It is the user-defined function call
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)LINEIndirectCallInfo, IARG_INST_PTR, IARG_ADDRINT, lineInfo, IARG_END);
    }
    else{
        // general statement
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)LINEGenInfo, IARG_INST_PTR, IARG_ADDRINT, lineInfo, IARG_END);
        // return statement
        if(INS_IsRet(ins)){
            INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)LINERetInfo, IARG_INST_PTR, IARG_ADDRINT, lineInfo, IARG_END);
        }   
    } 
}

// This function is called when the application exits
// It deletes the object space and closes the files
VOID Fini(INT32 code, VOID *v)
{
	set<LineInfo *>::iterator itLine;
	for(itLine = lineInfoSet.begin(); itLine != lineInfoSet.end(); itLine++){
		delete *itLine;
	}
    set<CallInfo *>::iterator itCall;
    for(itCall = callInfoSet.begin(); itCall != callInfoSet.end(); itCall++){
        delete *itCall;
    }

    fclose(LINETrace);	
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr << "This Pintool prints the trace inforamtion" << endl;
    cerr << endl << KNOB_BASE::StringKnobSummary() << endl;
    return -1;
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char * argv[])
{
    LINETrace = fopen("/home/***/Experiment/Result/dstLINETrace.out", "w");

    // Initialize symbol table code, needed for rtn instrumentation
    PIN_InitSymbols();
    // Initialize pin
    if (PIN_Init(argc, argv)){
		return Usage();
    }

    // Register Routine to be called to instrument instruction
    INS_AddInstrumentFunction(Instruction, 0);

    // Register Fini to be called when the application exits
    PIN_AddFiniFunction(Fini, 0);
    
    // Start the program, never returns
    PIN_StartProgram();
    
    return 0;
}
