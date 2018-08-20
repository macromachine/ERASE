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
// This tool prints the CFG information
//
#include <fstream>
#include <iostream>
#include <cassert>
#include <string.h>
#include "pin.H"
#include <set>

FILE * CFGTrace;
static INT processId = -1;
static UINT threadId = UINT_MAX;

typedef set<string> RTN_SET;
static RTN_SET rtnSet;

bool LookUp(string fileAndRtnName){
    //Searches the container for an element equivalent to val and returns an iterator to it if found,
    //otherwise it returns an iterator to set::end.
    set<string>::iterator it = rtnSet.find(fileAndRtnName);
    if(it != rtnSet.end()){
        return true;
    }
    else{
	   rtnSet.insert(fileAndRtnName);
	   return false;
    }
}

//Obtain the fileName from the path
const char * StripPath(const char * path)
{
    const char * file = strrchr(path,'/');
    if (file){
        return file + 1;
    }
    else{
        return path;
    }
}

// This is the instrumentation component, which is only called onece
// *** think it is enough to obtain the CFG information through instrumentation component
// This tool does not include the analysis component
static VOID Trace(TRACE trace, VOID *v)
{    
    INT32 lineNumber; 
    string fileName;

    if (processId != -1 || threadId != UINT_MAX){
        if (processId != PIN_GetPid() || threadId != PIN_ThreadId()){
            return;
        }
    }
    else{
        processId = PIN_GetPid();
        threadId = PIN_ThreadId();
    }

    INS ins = BBL_InsHead(TRACE_BblHead(trace));
    RTN rtn = INS_Rtn(ins);  
    if (!RTN_Valid(rtn)){
        return;
    } 
    
    if (INS_Address(ins) == RTN_Address(rtn)){
        /* The first ins of an RTN that will be executed - it is possible at this point to examine all the INSs 
           of the RTN that Pin can statically identify (using whatever standard symbol information is available).
           A tool may wish to parse each such RTN only once, if so it will need to record and identify which RTNs 
           have already been parsed(such comment is displayed in parse_executed_rtns.cpp, but *** thinks that 
           it is not necessary to record because the instrumentation only happens once for each trace, in the 
           implementation, we still store the rtnname) 
        */
        // Get the static information of the line number of the instruction
        // It is often placed in the instrumentation component
        PIN_GetSourceLocation(INS_Address(ins), NULL, &lineNumber, &fileName);
        if(lineNumber == 0){
            return;
        }
        string fileAndRtnName = StripPath(fileName.c_str()) + RTN_Name(rtn);
        bool found = LookUp(fileAndRtnName);
        if(!found){
            // Output the file name
	        fprintf(CFGTrace, "***%s***\n", StripPath(fileName.c_str()));
            //Open the given rtn. This must be called before RTN_InsHead() or RTN_InsertCall() or RTN_InsHeadOnly()
            RTN_Open(rtn);
            for(INS ins = RTN_InsHead(rtn); INS_Valid(ins); ins = INS_Next(ins)){
                // Get the static information of the line number of the instruction
                // It is often placed in the instrumentation component
    	        PIN_GetSourceLocation(INS_Address(ins), NULL, &lineNumber, &fileName);
                if(lineNumber == 0){
                    continue;
                }
                if(INS_IsDirectBranch(ins)){
                    // format: <src#dst#sym#src-lineNumber>
                    //string::npos presents that it does not find the specified string
                    if((INS_Disassemble(ins).find("jmp") == string::npos) && (INS_Disassemble(ins).find("JMP") == string::npos)){
                        // Conditional branch
                        fprintf(CFGTrace,"%p#%p#B#%d\n", reinterpret_cast<void *>(INS_Address(ins)), reinterpret_cast<void *>(INS_DirectBranchOrCallTargetAddress(ins)), lineNumber);
                    }		      
		            else{
                        // Unconditionally jump branch
		                fprintf(CFGTrace,"%p#%p#U#%d\n", reinterpret_cast<void *>(INS_Address(ins)), reinterpret_cast<void *>(INS_DirectBranchOrCallTargetAddress(ins)), lineNumber);
		            }			    	
		        }
                else if(INS_IsBranch(ins)){
                    // The destination of the branch is dependent on the practical situation
                    // The switch case in the function get_expr in tree.c in the project find-4.2.18 has the indirectbranch 
                    // At present, we take such instruction as the general instruction
                    fprintf(CFGTrace,"%p#S#%d\n", reinterpret_cast<void *>(INS_Address(ins)), lineNumber);
                }
	   	        else{
		            // Does not consider the indirect branch or call, because we cannot obtain the target address. Otherwise, *** thinks there is no conditional indirect branch or call	
		            fprintf(CFGTrace,"%p#%d\n", reinterpret_cast<void *>(INS_Address(ins)), lineNumber);
	  	        }        
            }
            RTN_Close(rtn);
	    }
    }  
}

// This function is called when the application exits
// It closes the files
VOID Fini(INT32 code, VOID *v)
{
    fclose(CFGTrace);
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr << "This Pintool prints the CFG inforamtion" << endl;
    cerr << endl << KNOB_BASE::StringKnobSummary() << endl;
    return -1;
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char * argv[])
{
    CFGTrace = fopen("/home/***/Experiment/Result/dstCFGTrace.out", "w");

    // Initialize symbol table code, needed for rtn instrumentation
    PIN_InitSymbols();
    // Initialize pin
    if (PIN_Init(argc, argv)){
		return Usage();
    }

    // Register Routine to be called to instrument instruction
    TRACE_AddInstrumentFunction(Trace, 0);

    // Register Fini to be called when the application exits
    PIN_AddFiniFunction(Fini, 0);
    
    // Start the program, never returns
    PIN_StartProgram();
    
    return 0;
}
