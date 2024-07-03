#ifndef generator_HPP
#define generator_HPP

#include <iostream>
#include "cadmium/modeling/devs/atomic.hpp"

using namespace cadmium;

struct generatorState {
bool active;
int counter;
double sigma;
std::string currState;

 explicit generatorState(): active(true), counter(0), sigma(std::numeric_limits<double>::infinity()), currState("passive"){}
};
std::ostream& operator<<(std::ostream &out, const generatorState& state) {
 out << "[" << state.active << "," << state.counter << "," << state.sigma << "," << state.currState << "]";
 return out;
}
class generator : public Atomic<generatorState> {
public:
Port<int> in;
Port<int> out;
generator(const std::string id) : Atomic<generatorState>(id, generatorState()) {
in = addInPort<int>("in");
out = addOutPort<int>("out");
}

void internalTransition(generatorState& state) const override {
if (state.currState == "increment") {
state.active = true;
state.counter = state.counter + 1;
state.sigma = 1.0;
state.currState = "increment";
}
}

void externalTransition(generatorState& state, double e) const override {
if(!in->empty()) {
 int input;
for(const auto &x : in->getBag()){input = x;}
if (state.currState == "passive") {
state.active = true;
state.counter = 0;
state.sigma = 1.0;
state.currState = "increment";
}
else if (state.currState == "increment") {
state.active = false;
state.counter = 0;
state.sigma = std::numeric_limits<double>::infinity();
state.currState = "passive";
}
}
}

void output(const generatorState& state) const override {
if (state.currState == "increment") {
out->addMessage(state.counter);
}
}

[[nodiscard]] double timeAdvance(const generatorState& state) const override {
return state.sigma;
}
};
#endif