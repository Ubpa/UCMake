#include "../MyClass.h"

#include <iostream>

int main() {
	{
		MyClass myclass;
		myclass.SayHello();
		std::cout << "(" << myclass.x << ", " << myclass.y << ")" << std::endl;
		if (myclass.x != 1 || myclass.y != 2) {
			std::cerr << "FAILED: expected (1, 2), got (" << myclass.x << ", " << myclass.y << ")" << std::endl;
			return 1;
		}
	}
	return 0;
}
