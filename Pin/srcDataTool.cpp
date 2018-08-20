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

#define byte unsigned char

FILE * DATATrace;
static INT processId = -1;
static UINT threadId = UINT_MAX;

class LineInfo{
public:
    string fileName;
    INT32 lineNumber;

    LineInfo(string fn, INT32 ln): 
    fileName(fn), lineNumber(ln) {}

};
typedef set<LineInfo *> LineInfoSet;
static LineInfoSet lineInfoSet;

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


// Print the memory read
VOID RecordMemRead(LineInfo *lineInfo, VOID * addr, UINT32 size)
{
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    string fileName = lineInfo->fileName;
    INT32 lineNumber = lineInfo->lineNumber;

    fprintf(DATATrace, "%s#%d#R#%p#0x", fileName.c_str(),lineNumber, addr);
    byte * buffer = new byte[size];
    PIN_SafeCopy(buffer, addr, size);   
    for(int i = size-1; i > -1; i--){
        fprintf(DATATrace, "%02x", buffer[i]);
    }
    fprintf(DATATrace, "\n");
    delete [] buffer;
}

// Print the memory write
VOID RecordMemWrite(LineInfo *lineInfo, VOID * addr, UINT32 size)
{
    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }
    string fileName = lineInfo->fileName;
    INT32 lineNumber = lineInfo->lineNumber;
    
    fprintf(DATATrace, "%s#%d#W#%p#0x", fileName.c_str(), lineNumber, addr);
    byte *buffer = new byte[size];
    PIN_SafeCopy(buffer, addr, size);
    for(int i = size-1; i > -1; i--){
        fprintf(DATATrace, "%02x", buffer[i]);
    }
    fprintf(DATATrace, "\n");
    delete [] buffer;
}

static VOID Instruction(INS ins, VOID *v)
{    
    string fileName;
    INT32 lineNumber; 

    PIN_GetSourceLocation(INS_Address(ins), NULL, &lineNumber, &fileName);
    if(lineNumber == 0){
		return;
    }
    const char * fileNamePtr = StripPath(fileName.c_str());
    string fileNameStr;
    fileNameStr.assign(fileNamePtr, strlen(fileNamePtr));

    LineInfo *lineInfo = new LineInfo(fileNameStr, lineNumber); 
    lineInfoSet.insert(lineInfo);

    // we skip the lea instruction, although lea may load the address for the point
    // it is not necessary to consider such data depence, we can consider the address as the immediate


    // Instruments memory accesses using a predicated call, i.e.
    // the instrumentation is called iff the instruction will actually be executed.
    // On the IA-32 and Intel(R) 64 architectures conditional moves and REP 
    // prefixed instructions appear as predicated instructions in Pin.
    UINT32 memOperands = INS_MemoryOperandCount(ins);
    // Iterate over each memory operand of the instruction.
    for (UINT32 memOp = 0; memOp < memOperands; memOp++)
    {
        if (INS_MemoryOperandIsRead(ins, memOp))
        {
            //When the instruction has a predicate and the predicate is false, the analysis function is not called
            INS_InsertPredicatedCall(ins, IPOINT_BEFORE, (AFUNPTR)RecordMemRead, IARG_ADDRINT, lineInfo, IARG_MEMORYOP_EA, memOp, IARG_MEMORYREAD_SIZE, IARG_END);
        }
        // Note that in some architectures a single memory operand can be 
        // both read and written (for instance incl (%eax) on IA-32)
        // In that case we instrument it once for read and once for write.
        if (INS_MemoryOperandIsWritten(ins, memOp))
        {
            //If INS_HasFallThrough(INS) is TRUE, then the instruction may execute the "natural" next instruction (i.e. the one which starts immediately after this one), 
            //if it is FALSE, then the instruction following the one tested will not (normally) be executed next. 
            //So HasFallThrough is TRUE for instructions which don't change the control flow (most instructions), 
            //or for conditional branches (which might change the control flow, but might not), 
            //and FALSE for unconditional branches and calls (where the next instruction to be executed is always explicitly specified).
            if(INS_HasFallThrough(ins)){
                //It does not matter because the unconditional branch or call usually has no memory writing
                INS_InsertPredicatedCall(ins, IPOINT_AFTER, (AFUNPTR)RecordMemWrite, IARG_ADDRINT, lineInfo, IARG_MEMORYOP_EA, memOp, IARG_MEMORYWRITE_SIZE, IARG_END);
            }
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
    fclose(DATATrace);	
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr << "This Pintool prints the data flow analysis inforamtion" << endl;
    cerr << endl << KNOB_BASE::StringKnobSummary() << endl;
    return -1;
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char * argv[])
{
    DATATrace = fopen("/home/***/Experiment/Result/srcDATATrace.out", "w");

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
