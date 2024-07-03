#ifndef counter_HPP
#define counter_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct counterState {
	bool active;
	int counter;
	double sigma;
	std::string currState;

	explicit counterState(): active(true), counter(0), sigma(std::numeric_limits<double>::infinity()), currState("passive"){}
};

std::ostream& operator<<(std::ostream &out, const counterState& state) {
	out << "[" << state.active << "," << state.counter << "," << state.sigma << "," << state.currState << "]";
	return out;
}
class counter : public Atomic<counterState> {
public:
	Port<bool> in;
	Port<int> out;
	counter(const std::string id) : Atomic<counterState>(id, counterState()) {
		in = addInPort<bool>("in");
		out = addOutPort<int>("out");
	}

	void internalTransition(counterState& state) const override {
		if (state.currState == "increment") {
			state.active = true;
			state.counter = state.counter + 1;
			state.sigma = 1.0;
			state.currState = "increment";
		}
	}

	void externalTransition(counterState& state, double e) const override {
		if(!in->empty()) {
			bool input;
			for(const auto &x : in->getBag()){
				input = x;
			}
			if(input == true){
				if (state.currState == "passive") {
					state.active = input;
					state.counter = 0;
					state.sigma = 1.0;
					state.currState = "increment";
				}
			}
			else if(input == false){
				if (state.currState == "increment") {
					state.active = input;
					state.counter = 0;
					state.sigma = std::numeric_limits<double>::infinity();
					state.currState = "passive";
				}
			}
		}
	}

	void output(const counterState& state) const override {
		if (state.currState == "increment") {
			out->addMessage(state.counter);
		}
	}

	[[nodiscard]] double timeAdvance(const counterState& state) const override {
		return state.sigma;
	}
};
#endif