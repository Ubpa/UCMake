#include "../MyClass.h"

#include <iostream>

int main() {
	{
		MyClass myclass;
		myclass.SayHello();
		std::cout << "(" << myclass.x << ", " << myclass.y << ")" << std::endl;
	}
	return 0;
}
