import json
import sys

if len(sys.argv) < 2:
        print("Usage: python3 factory.py <top DEVS JSON>")
        sys.exit(1)

jsonFile = open(sys.argv[1], 'r')
jsonFile = json.load(jsonFile)

kw = ['state0', 'ports', 'del_int', 'del_ext', 'lambda']

atomicName_list = [x for x in jsonFile.keys() if x not in kw]
if (len(atomicName_list) > 1) :
    print("Unknown keywords present. Not considered.")

atomicName = atomicName_list[0]

for key in kw:
    if key not in jsonFile.keys():
        print("Error in DEVS JSON: ", key, " not defined")

print("Atomic model: ", atomicName)

hpp_content = f"""#ifndef {atomicName}_HPP
#define {atomicName}_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct {atomicName}State {{
"""
#Get the state variables from the JSON
stateVariables = list(jsonFile[atomicName].keys())

#List out the state variables in the struct
for sv in stateVariables:
    hpp_content += f"{jsonFile[atomicName][sv]} {sv};\n"

hpp_content += "std::string currState;\n"

hpp_content += f"\n explicit {atomicName}State(): "

#Get the initial state
initSV = jsonFile['state0']['init']


for i in range(0, len(stateVariables)):

    #False in JSON is false in cpp
    if(jsonFile[atomicName][stateVariables[i]] == 'bool'):
        if(stateVariables[i] == False):
            hpp_content += f"{stateVariables[i]}(false), "
        else:
            hpp_content += f"{stateVariables[i]}(true), "

    #inf is converted to cpp infinity
    elif(jsonFile['state0'][initSV][i] == 'inf'):
        hpp_content += f"{stateVariables[i]}(std::numeric_limits<double>::infinity()), "

    #No conditions otherwise
    else:
        hpp_content += f"{stateVariables[i]}({jsonFile['state0'][initSV][i]}), "

    #Ending the state constructor
    if(i == len(stateVariables) - 1):
        hpp_content += f"currState(\"{initSV}\"){{}}\n}};\n"

#internal transition state logger
hpp_content += f"std::ostream& operator<<(std::ostream &out, const {atomicName}State& state) {{\n out << \"[\""
for sv in stateVariables:
    hpp_content += f" << state.{sv} << \",\""
hpp_content += " << state.currState << \"]\";\n return out;\n}"

#Building the class
hpp_content += f"\nclass {atomicName} : public Atomic<{atomicName}State> {{\npublic:\n"

#Collecting Ports
inputPorts  = jsonFile['ports']['input']
outputPorts = jsonFile['ports']['output']

#Listing Ports
for port in inputPorts:
    hpp_content += f"Port<{port[list(port.keys())[0]]}> {list(port.keys())[0]};\n"
for port in outputPorts:
    hpp_content += f"Port<{port[list(port.keys())[0]]}> {list(port.keys())[0]};\n"

#Creating the constructor
hpp_content += f"{atomicName}(const std::string id) : Atomic<{atomicName}State>(id, {atomicName}State()) {{\n"

#Init ports
for port in inputPorts:
    hpp_content += f"{list(port.keys())[0]} = addInPort<{port[list(port.keys())[0]]}>(\"{list(port.keys())[0]}\");\n"
for port in outputPorts:
    hpp_content += f"{list(port.keys())[0]} = addOutPort<{port[list(port.keys())[0]]}>(\"{list(port.keys())[0]}\");\n"
#Ending Constructer
hpp_content += "}\n"

#Beinning del_int
hpp_content += f"\nvoid internalTransition({atomicName}State& state) const override {{\n"

delIntCases = list(jsonFile['del_int'].keys())

#List out the transition (Please be careful when editing)
for i in range(0, len(delIntCases)):
    case = delIntCases[i]
    hpp_content += f"if (state.currState == \"{case}\") {{\n"
    nextState = list(jsonFile['del_int'][case].keys())[0]
    j = 0
    for sv in stateVariables:
        svValue = jsonFile['del_int'][case][nextState][j]
        #Cases because of stupid False, false difference
        if(type(svValue) is bool):
            if(svValue == False):
                hpp_content += f"state.{sv} = false;\n"
            elif(svValue == True):
                hpp_content += f"state.{sv} = true;\n"
        elif(svValue == 'inf'):
            hpp_content += f"state.{sv} = std::numeric_limits<double>::infinity();\n"
        else:
            hpp_content += f"state.{sv} = {svValue};\n"
        j += 1
    hpp_content += f"state.currState = \"{nextState}\";\n}}\n"
    if(i != len(delIntCases) - 1):
        hpp_content += "else "
hpp_content += "}\n"

#Beinning del_ext
hpp_content += f"\nvoid externalTransition({atomicName}State& state, double e) const override {{\n"

#Case per port
for port in inputPorts:

    portName = list(port.keys())[0]
    hpp_content += f"if(!{portName}->empty()) {{"

    #Case per state, per port
    delExtCases = list(jsonFile['del_ext'][portName].keys())

    #Create Variable to store input
    hpp_content += f"\n {port[portName]} input;"

    hpp_content += f"\nfor(const auto &x : {portName}->getBag()){{input = x;}}\n"

    #List out the transition (Please be careful when editing)
    for i in range(0, len(delExtCases)):
        case = delExtCases[i]

        hpp_content += f"if (state.currState == \"{case}\") {{\n"
        nextState = list(jsonFile['del_ext'][portName][case].keys())[0]
        j = 0
        for sv in stateVariables:
            svValue = jsonFile['del_ext'][portName][case][nextState][j]
            #Cases because of stupid False, false difference
            if(type(svValue) is bool):
                if(svValue == False):
                    hpp_content += f"state.{sv} = false;\n"
                elif(svValue == True):
                    hpp_content += f"state.{sv} = true;\n"
            elif(svValue == 'inf'):
                hpp_content += f"state.{sv} = std::numeric_limits<double>::infinity();\n"
            elif(svValue == 'x'):
                hpp_content += f"state.{sv} = input;\n"
            else:
                hpp_content += f"state.{sv} = {svValue};\n"
            j += 1
        hpp_content += f"state.currState = \"{nextState}\";\n}}\n"
        if(i != len(delExtCases) - 1):
            hpp_content += "else "

    hpp_content += "}\n"
hpp_content += "}\n"

#Begining Lambda
hpp_content += f"\nvoid output(const {atomicName}State& state) const override {{\n"
lambdaCases = list(jsonFile['lambda'].keys())

#List out the states (Please be careful when editing)
for i in range(0, len(lambdaCases)):
    case = lambdaCases[i]
    hpp_content += f"if (state.currState == \"{case}\") {{\n"
    ports = list(jsonFile['lambda'][case].keys())

    for port in ports:
        sv = jsonFile['lambda'][case][port]
        hpp_content += f"{port}->addMessage(state.{sv});\n"
    hpp_content += "}\n"
hpp_content += "}\n"


hpp_content += f"""\n[[nodiscard]] double timeAdvance(const {atomicName}State& state) const override {{
return state.sigma;
}}
}};
#endif"""

hpp_file = open(f"outputs/{atomicName}.hpp", "w")
hpp_file.write(hpp_content)