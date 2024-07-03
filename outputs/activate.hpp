#ifndef activate_HPP
#define activate_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct activateState {
	bool active;
	double sigma;
	std::string currState;

	explicit activateState(): active(true), sigma(5.0), currState("active"){}
};

std::ostream& operator<<(std::ostream &out, const activateState& state) {
	out << "[" << state.active << "," << state.sigma << "," << state.currState << "]";
	return out;
}
class activate : public Atomic<activateState> {
public:
	Port<bool> out;
	activate(const std::string id) : Atomic<activateState>(id, activateState()) {
		out = addOutPort<bool>("out");
	}

	void internalTransition(activateState& state) const override {
		if (state.currState == "active") {
			state.active = false;
			state.sigma = 10.0;
			state.currState = "passive";
		}
		else if (state.currState == "passive") {
			state.active = true;
			state.sigma = 5.0;
			state.currState = "active";
		}
	}

	void externalTransition(activateState& state, double e) const override {
	}

	void output(const activateState& state) const override {
		if (state.currState == "active") {
			out->addMessage(state.active);
		}
		if (state.currState == "passive") {
			out->addMessage(state.active);
		}
	}

	[[nodiscard]] double timeAdvance(const activateState& state) const override {
		return state.sigma;
	}
};
#endif