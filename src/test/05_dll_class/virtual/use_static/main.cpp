#include "../MyClass.h"

#include <cstdlib>

int main() {
	size_t s = sizeof_MyClass();
	void* addr = malloc(s);
	MyClass* myclass = MyClass_Construct(addr);
	myclass->SayHello();
	MyClass_Destruct(myclass);
	free(addr);
	return 0;
}
