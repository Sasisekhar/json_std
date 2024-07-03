import json
import sys
import atomicFactory
import os
import pathlib

#!TODO: Support for EIC, EOC ports

def coupledFactory(filename, destination):    

    jsonFile = open(filename, 'r')
    jsonFile = json.load(jsonFile)

    if(destination[-1] == '/'):
        destination = destination[:-1]

    coupledName = list(jsonFile.keys())[0]

    coupledComponentsDir = f"{destination}/{coupledName}Components"
    os.makedirs(coupledComponentsDir, exist_ok=True)

    listComponents = list(jsonFile[coupledName]["components"].keys())

    for component in listComponents:
        atomicFactory.atomicFactory(f"{pathlib.Path(filename).parent}/{coupledName}Components/{component}.json", coupledComponentsDir)

    hpp_content = f"""#ifndef {coupledName}_HPP
#define {coupledName}_HPP

#include "cadmium/modeling/devs/coupled.hpp"\n"""

    for component in listComponents:
        hpp_content += f"#include \"{coupledName}Components/{component}.hpp\"\n"

    hpp_content += f"using namespace cadmium;\nstruct {coupledName} : public Coupled{{\n"

    hpp_content += f"\t{coupledName}(const std::string& id) : Coupled(id) {{\n"

    for component in listComponents:
        instance = jsonFile[coupledName]["components"][component]["component_id"]
        hpp_content += f"\t\tauto {instance} = addComponent<{component}>(\"{instance}\");\n"

    listCouplings = jsonFile[coupledName]["couplings"]
    for coupling in listCouplings:
        hpp_content += f"\t\taddCoupling({coupling['componentFrom']}->{coupling['portFrom']}, {coupling['componentTo']}->{coupling['portTo']});\n"

    hpp_content += "\t}\n};\n#endif"

    hpp_file = open(f"{destination}/{coupledName}.hpp", "w")
    hpp_file.write(hpp_content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 coupledFactory.py <coupledModel.json> <output directory>")
        sys.exit(1)
    filename = sys.argv[1]
    destination = sys.argv[2]
    coupledFactory(filename, destination)