import json
import sys

def atomicFactory(filename, dest):
    jsonFile = open(filename, 'r')
    jsonFile = json.load(jsonFile)


    kw = ['state0', 'ports', 'del_int', 'del_ext', 'lambda']

    atomicName_list = [x for x in jsonFile.keys() if x not in kw]
    if (len(atomicName_list) > 1) :
        print("Unknown keywords present. Not considered.")

    atomicName = atomicName_list[0]

    if("components" in list(jsonFile[atomicName].keys())):
        print(f"Coupled model \"{atomicName}\" given, skipping")
        return

    for key in kw:
        if key not in jsonFile.keys():
            print("Error in DEVS JSON: ", key, " not defined")

    print("Atomic model: ", atomicName)

    hpp_content = f"""#ifndef {atomicName}_HPP
#define {atomicName}_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct {atomicName}State {{\n"""
    #Get the state variables from the JSON
    stateVariables = list(jsonFile[atomicName].keys())

    #List out the state variables in the struct
    for sv in stateVariables:
        hpp_content += f"\t{jsonFile[atomicName][sv]} {sv};\n"

    hpp_content += "\tstd::string currState;\n"

    hpp_content += f"\n\texplicit {atomicName}State(): "

    #Get the initial state
    initSV = list(jsonFile['state0'].keys())[0]


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
            hpp_content += f"currState(\"{initSV}\"){{}}\n}};\n\n"

    #internal transition state logger
    hpp_content += f"std::ostream& operator<<(std::ostream &out, const {atomicName}State& state) {{\n\tout << \"[\""
    for sv in stateVariables:
        hpp_content += f" << state.{sv} << \",\""
    hpp_content += " << state.currState << \"]\";\n\treturn out;\n}"

    #Building the class
    hpp_content += f"\nclass {atomicName} : public Atomic<{atomicName}State> {{\npublic:\n"

    #Collecting Ports
    inputPorts  = jsonFile['ports']['input']
    outputPorts = jsonFile['ports']['output']

    #Listing Ports
    for port in inputPorts:
        hpp_content += f"\tPort<{port[list(port.keys())[0]]}> {list(port.keys())[0]};\n"
    for port in outputPorts:
        hpp_content += f"\tPort<{port[list(port.keys())[0]]}> {list(port.keys())[0]};\n"

    #Creating the constructor
    hpp_content += f"\t{atomicName}(const std::string id) : Atomic<{atomicName}State>(id, {atomicName}State()) {{\n"

    #Init ports
    for port in inputPorts:
        hpp_content += f"\t\t{list(port.keys())[0]} = addInPort<{port[list(port.keys())[0]]}>(\"{list(port.keys())[0]}\");\n"
    for port in outputPorts:
        hpp_content += f"\t\t{list(port.keys())[0]} = addOutPort<{port[list(port.keys())[0]]}>(\"{list(port.keys())[0]}\");\n"
    #Ending Constructer
    hpp_content += "\t}\n"

    #Beinning del_int
    hpp_content += f"\n\tvoid internalTransition({atomicName}State& state) const override {{\n"

    delIntCases = list(jsonFile['del_int'].keys())

    #List out the transition (Please be careful when editing)
    for i in range(0, len(delIntCases)):
        case = delIntCases[i]

        if i == 0:
            hpp_content += "\t\t"
        hpp_content += f"if (state.currState == \"{case}\") {{\n"
        nextState = list(jsonFile['del_int'][case].keys())[0]
        j = 0
        for sv in stateVariables:
            svValue = jsonFile['del_int'][case][nextState][j]
            #Cases because of stupid False, false difference
            if(type(svValue) is bool):
                if(svValue == False):
                    hpp_content += f"\t\t\tstate.{sv} = false;\n"
                elif(svValue == True):
                    hpp_content += f"\t\t\tstate.{sv} = true;\n"
            elif(svValue == 'inf'):
                hpp_content += f"\t\t\tstate.{sv} = std::numeric_limits<double>::infinity();\n"
            else:
                hpp_content += f"\t\t\tstate.{sv} = {svValue};\n"
            j += 1
        hpp_content += f"\t\t\tstate.currState = \"{nextState}\";\n\t\t}}\n"
        if(i != len(delIntCases) - 1):
            hpp_content += "\t\telse "
    hpp_content += "\t}\n"

    #Beinning del_ext
    hpp_content += f"\n\tvoid externalTransition({atomicName}State& state, double e) const override {{\n"

    #Case per port
    for port in inputPorts:

        portName = list(port.keys())[0]
        hpp_content += f"\t\tif(!{portName}->empty()) {{"

        #Create Variable to store input
        hpp_content += f"\n\t\t\t{port[portName]} x;"

        hpp_content += f"\n\t\t\tfor(const auto &input : {portName}->getBag()){{\n\t\t\t\tx = input;\n\t\t\t}}\n"

        #Conditions on input, per port
        inputConds = list(jsonFile['del_ext'][portName].keys())

        for condition_itr in range(0, len(inputConds)):
            conds = inputConds[condition_itr]

            if(condition_itr == 0):
                hpp_content += "\t\t\t"

            hpp_content += f"if({conds}){{\n"

            #Case per state, per port
            delExtCases = list(jsonFile['del_ext'][portName][conds].keys())

            #List out the transition (Please be careful when editing)
            for i in range(0, len(delExtCases)):
                case = delExtCases[i]

                if(i == 0):
                    hpp_content += "\t\t\t\t"

                hpp_content += f"if (state.currState == \"{case}\") {{\n"
                nextState = list(jsonFile['del_ext'][portName][conds][case].keys())[0]
                j = 0
                for sv in stateVariables:
                    svValue = jsonFile['del_ext'][portName][conds][case][nextState][j]
                    #Cases because of stupid False, false difference
                    if(type(svValue) is bool):
                        if(svValue == False):
                            hpp_content += f"\t\t\t\t\tstate.{sv} = false;\n"
                        elif(svValue == True):
                            hpp_content += f"\t\t\t\t\tstate.{sv} = true;\n"
                    elif(svValue == 'inf'):
                        hpp_content += f"\t\t\t\t\tstate.{sv} = std::numeric_limits<double>::infinity();\n"
                    # elif(svValue == 'x'):
                    #     hpp_content += f"\t\t\t\t\tstate.{sv} = input;\n"
                    else:
                        hpp_content += f"\t\t\t\t\tstate.{sv} = {svValue};\n"
                    j += 1
                hpp_content += f"\t\t\t\t\tstate.currState = \"{nextState}\";\n\t\t\t\t}}\n"
                if(i != len(delExtCases) - 1):
                    hpp_content += "\t\t\t\telse "

            hpp_content += "\t\t\t}\n"    
            if(condition_itr != len(inputConds) - 1):
                hpp_content += "\t\t\telse "

        hpp_content += "\t\t}\n"
    hpp_content += "\t}\n"

    #Begining Lambda
    hpp_content += f"\n\tvoid output(const {atomicName}State& state) const override {{\n"
    lambdaCases = list(jsonFile['lambda'].keys())

    #List out the states (Please be careful when editing)
    for i in range(0, len(lambdaCases)):
        case = lambdaCases[i]
        hpp_content += f"\t\tif (state.currState == \"{case}\") {{\n"
        ports = list(jsonFile['lambda'][case].keys())

        for port in ports:
            sv = jsonFile['lambda'][case][port]
            hpp_content += f"\t\t\t{port}->addMessage(state.{sv});\n"
        hpp_content += "\t\t}\n"
    hpp_content += "\t}\n"


    hpp_content += f"""\n\t[[nodiscard]] double timeAdvance(const {atomicName}State& state) const override {{
\t\treturn state.sigma;
\t}}
}};
#endif"""

    destination = dest

    if(destination[-1] != '/'):
        destination += '/'

    hpp_file = open(f"{destination}{atomicName}.hpp", "w")
    hpp_file.write(hpp_content)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 atomicFactory.py <atomicModel.json> <output directory>")
        sys.exit(1)
    atomicFactory(sys.argv[1], sys.argv[2])