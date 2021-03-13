#include "../MyClass.h"

#include <iostream>

MyClass::MyClass() :
	x{ 1 },
	y{ 2 }
{
	std::cout << "call MyClass::MyClass()" << std::endl;
}

MyClass::~MyClass() {
	std::cout << "call MyClass::~MyClass()" << std::endl;
}

void MyClass::SayHello() const {
	std::cout << "MyClass@" << this << ": hello!" << std::endl;
}

UCMake_test_05_dll_class_classic_gen_API size_t sizeof_MyClass() {
	return sizeof(MyClass);
}

UCMake_test_05_dll_class_classic_gen_API MyClassHandle MyClass_Construct(void* addr) {
	return new(addr)MyClass;
}

UCMake_test_05_dll_class_classic_gen_API void MyClass_Destruct(MyClassHandle h) {
	h->~MyClass();
}

UCMake_test_05_dll_class_classic_gen_API void MyClass_SayHello(MyClassConstHandle h) {
	h->SayHello();
}
