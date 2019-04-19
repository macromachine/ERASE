一. install and use intel Pin framework
1. Download and install the pin framework from "https://software.intel.com/en-us/articles/pin-a-binary-instrumentation-tool-downloads"
2. Copy our instrument files (https://github.com/macromachine/ERASE/tree/master/Pin) to "$home/pin/source/tools/MyPinTool"
3. Open a terminal and change work directory to "$home/pin/source/tools/MyPinTool"
4. Execute the command "make all TARGET=ia32"
5. Instrument the execution of target program using: "$home/pin/pin -t $home/pin/source/tools/MyPinTool/obj-ia32/srcTraceTool.so -- $target_program $parameter"

二. install and use ERASE
1. Copy all ERASE files (https://github.com/macromachine/ERASE/tree/master/ERASE) and generate the python projects
2. The entry of project is in "DualSlice.py"
3. First, we set the target program at Line 1872, for example, "appName = "find_b" "
4. Second, we set the failure points at Lines 2474-2609, for example,  "set([5609]), set([-1]) at Line 2497"
5. Lines 2054-2125 are the procedures to install the target program automatically. If we have installed the program, we can comment these codes.
6. Lines 1949-2051 are the procedures to compare the differences between two versions, and align the same codes between two versions.
7. We run the program, and get the results.

三. Explanation of the whole projects:

Given two versions of a program and a test case that passes the old version while fails the new version, we use the passing trace as a “correct reference” to examine how the failing trace produces the failure. In order to use the passing trace, we develop a new trace alignment technique to align the passing and failing traces with regard to source code changes between two versions. We then apply alignment slicing and mending on both traces to isolate the failure-inducing changes and generate a causal path for explaining the failure. The causal path not only eliminates the fault-irrelevant steps of traces as dynamic slicing, but also mends the fault-relevant steps beyond the reach of slicing.

We systematically evaluate our approach with a feasibility experiment on 298 Java regressions in the Defects4J bug repository and a
comparative experiment on 12 real-world C regressions. The results of feasibility experiment shows that, when two ver-
sions contain only failure-inducing changes, our dynamic trace-based approach can:

(1) localize the root cause of 88.9% of the regressions, 

(2) the generated explanation requires minor manual inspection effort (the average/mean of causality graph size is 79.0/11).

The results of comparative experiment shows that our approach is more accurate on isolating the failure-inducing changes than the state-of-the-art techniques.



ERASE tool on C Programs



The Dynamic Binary Analysis Framework Pin.

Pin is a dynamic binary analysis framework and can be used to monitor the execution of the program. We can easily obtain the execution information through Pin, such as the execution trace, memory information of statement instances, and so on.

The source codes of our implementation includes the following files, you can obtain them here:

The files *TraceTool.cpp is used to obtain the execution trace of the program

The files *CFGTool.cpp generates the control flow graph of the program 

The files *DataTool.cpp is used to show the memories written and read by each instance 

The files *CodeDataTool.cpp lists the instructions and the memories at the function calling 




Alignment Slicing and Mending

After obtaining the execution information, this project conducts the trace alignment, and alignment slicing and mending. In a result, we can isolate the failure-inducing changes along with a causal path that explains the failure. 

The source codes of our implementation includes the following files, you can obtain them here:

The file ABAdditionDeleteion.py isolates the statements that are immediately after and before an added or deleted statement 

The file BranchValue.py computes the branch of a conditional instance in the execution

The file CallReturnPoint.py computes the pairs of calling and returning instances in the execution 

The file ChangeAlign.py uses the tool diff to compute the static correspondence of source code between two versions

The file ComplieWork.py automatically compiles and installs the program

The file DeletionExecution.py handles the execution trace

The file DiffUtil.py aligns the source codes of two versions based on the results of ChangeAlign.py

The file DualSlice.py is the main function of this project

The file DynamicCDG.py obtains the dynamic control dependence of the program

The file DynamicDDG.py obtains the dynamic data dependence of the program

The file Exetrace.py computes the execution trace of the program 

The file HandleData.py handles the data trace of the program

The file HandleTrace.py handles the execution trace of the program

The files LineMerge.py and lineSplit.py preprocess the souce codes of the program 

The file LNCalling.py identifies the souce codes that is function calling steps.

The file LoopDet.py identifies the loop statements

The file Memcpy.py adds the memory information for the library function memcpy

The file PinExe.py automatically executes the Pin project

The file PointerCompare.py aligns the memory address

The file PointerDet.py identities the memory address 

The file Realloc.py adds the memory information for the library function realloc

The file Strcpy.py adds the memory information for the library function strcpy

The file SwithchDet.py identifies the switch statement 

The file TraceAlign.py aligns the two traces from two versions




Case Study

In order to verify the effectiveness of ERASE, we conduct a case study on the regression fault between two versions findutils-4.3.5 and findutils-4.3.6. The detailed report can be obtained (https://drive.google.com/file/d/0B3gTTwG7vBRKeWV2bTlrNVBjaDg/view), which shows ERASE is effective in isolating the failure-inducing changes and explaining the failure.




Experimental Results

The experimental objects and results in our evaluation can be downloaded (https://drive.google.com/file/d/0B3gTTwG7vBRKT2tBOXZvVFNkZmM/view).


