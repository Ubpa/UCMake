#include "../add.h"

#include <iostream>

int main() {
	int result = add(1, 2);
	std::cout << result << std::endl;
	if (result != 3) {
		std::cerr << "FAILED: expected 3, got " << result << std::endl;
		return 1;
	}
	return 0;
}
