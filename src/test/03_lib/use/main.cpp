#include "../add.h"

#include <cassert>
#include <iostream>

int main() {
	int result = add(1, 2);
	std::cout << result << std::endl;
	assert(result == 3);
	return 0;
}
