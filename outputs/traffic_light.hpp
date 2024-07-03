#ifndef traffic_light_HPP
#define traffic_light_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct traffic_lightState {
	std::string color;
	double sigma;
	std::string currState;

	explicit traffic_lightState(): color("RED"), sigma(5.0), currState("Red"){}
};

std::ostream& operator<<(std::ostream &out, const traffic_lightState& state) {
	out << "[" << state.color << "," << state.sigma << "," << state.currState << "]";
	return out;
}
class traffic_light : public Atomic<traffic_lightState> {
public:
	Port<std::string> LED;
	traffic_light(const std::string id) : Atomic<traffic_lightState>(id, traffic_lightState()) {
		LED = addOutPort<std::string>("LED");
	}

	void internalTransition(traffic_lightState& state) const override {
		if (state.currState == "Red") {
			state.color = "GREEN";
			state.sigma = 5.0;
			state.currState = "Green";
		}
		else if (state.currState == "Green") {
			state.color = "AMBER";
			state.sigma = 2.0;
			state.currState = "Amber";
		}
		else if (state.currState == "Amber") {
			state.color = "RED";
			state.sigma = 5.0;
			state.currState = "Red";
		}
	}

	void externalTransition(traffic_lightState& state, double e) const override {
	}

	void output(const traffic_lightState& state) const override {
		if (state.currState == "Red") {
			LED->addMessage(state.color);
		}
		if (state.currState == "Amber") {
			LED->addMessage(state.color);
		}
		if (state.currState == "Green") {
			LED->addMessage(state.color);
		}
	}

	[[nodiscard]] double timeAdvance(const traffic_lightState& state) const override {
		return state.sigma;
	}
};
#endif