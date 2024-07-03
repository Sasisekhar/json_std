#include <cadmium/simulation/rt_root_coordinator.hpp>
#include <limits>
#include "top.hpp"
#include "cadmium/simulation/logger/stdout.hpp"
#include "cadmium/simulation/rt_clock/chrono.hpp"

using namespace cadmium;

int main() {
    std::shared_ptr<top> model = std::make_shared<top> ("top");
    cadmium::ChronoClock clock;
	auto rootCoordinator = cadmium::RealTimeRootCoordinator<cadmium::ChronoClock<std::chrono::steady_clock>>(model, clock);
    rootCoordinator.setLogger<cadmium::STDOUTLogger>(";");
    rootCoordinator.start();
	rootCoordinator.simulate(std::numeric_limits<double>::infinity());
    rootCoordinator.stop();
    return 0;
}
