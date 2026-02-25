#include "../mul.h"

#include <iostream>

int main() {
	int result = mul(2, 3);
	std::cout << result << std::endl;
	if (result != 6) {
		std::cerr << "FAILED: expected 6, got " << result << std::endl;
		return 1;
	}
	return 0;
}
