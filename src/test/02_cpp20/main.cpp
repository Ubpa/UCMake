#include <iostream>

template<typename T>
concept HaveHelloCpp20 = requires(const T& x) {
	{x.HelloCpp20()};
};

class Cpp20 {
public:
	void HelloCpp20() const {
		std::cout << "hello cpp20" << std::endl;
	}
};

template<HaveHelloCpp20 T>
void CallHelloCpp20(const T& obj) {
	obj.HelloCpp20();
}

int main() {
	CallHelloCpp20(Cpp20{});
}
