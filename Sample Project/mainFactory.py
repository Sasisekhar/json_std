import json
import sys
import coupledFactory
import os
import git
import shutil

if len(sys.argv) < 3:
    print("Usage: python3 mainFactory.py <path/to/DEVS_JSON> <output directory>")
    sys.exit(1)
DEVSpath = sys.argv[1]
destination = sys.argv[2]

if(destination[-1] == '/'):
    destination = destination[:-1]

if os.path.exists(f"{destination}/main/include") and os.path.isdir(f"{destination}/main/include"):
    shutil.rmtree(f"{destination}/main/include")

os.makedirs(f"{destination}/main/include", exist_ok=True)

git.Git(f"{destination}/main/include").clone("https://github.com/Sasisekhar/cadmium.git")

coupledFactory.coupledFactory(DEVSpath, f"{os.getcwd()}/main/include")

topName = DEVSpath.split('/')[-1].split('.')[0]
cpp_content = f"""#include <cadmium/simulation/rt_root_coordinator.hpp>
#include <limits>
#include "{topName}.hpp"
#include "cadmium/simulation/logger/stdout.hpp"
#include "cadmium/simulation/rt_clock/chrono.hpp"

using namespace cadmium;

int main() {{
    std::shared_ptr<{topName}> model = std::make_shared<{topName}> ("{topName}");
    cadmium::ChronoClock clock;
	auto rootCoordinator = cadmium::RealTimeRootCoordinator<cadmium::ChronoClock<std::chrono::steady_clock>>(model, clock);
    rootCoordinator.setLogger<cadmium::STDOUTLogger>(";");
    rootCoordinator.start();
	rootCoordinator.simulate(std::numeric_limits<double>::infinity());
    rootCoordinator.stop();
    return 0;
}}
"""

cpp_file = open(f"{destination}/main/main.cpp", "w")
cpp_file.write(cpp_content)

makefile = "sim:\n\tg++ -std=gnu++20 -I include/ main.cpp -o run"
makefile_file = open(f"{destination}/main/makefile", "w")
makefile_file.write(makefile)
