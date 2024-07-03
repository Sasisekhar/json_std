#ifndef top_HPP
#define top_HPP

#include "cadmium/modeling/devs/coupled.hpp"
#include "topComponents/counter.hpp"
#include "topComponents/activate.hpp"
#include "topComponents/traffic_light.hpp"
using namespace cadmium;
struct top : public Coupled{
	top(const std::string& id) : Coupled(id) {
		auto increment = addComponent<counter>("increment");
		auto button = addComponent<activate>("button");
		auto toy = addComponent<traffic_light>("toy");
		addCoupling(button->out, increment->in);
		addCoupling(button->out, toy->in);
	}
};
#endif