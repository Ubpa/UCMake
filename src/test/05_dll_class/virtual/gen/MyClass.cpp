#include "../MyClass.h"

#include <iostream>

class MyClassImpl final : public MyClass {
public:
	MyClassImpl();
	~MyClassImpl() override final;
	void SayHello() const override final;
};

MyClassImpl::MyClassImpl() {
	std::cout << "call MyClass::MyClass()" << std::endl;
}

MyClassImpl::~MyClassImpl() {
	std::cout << "call MyClass::~MyClass()" << std::endl;
}

void MyClassImpl::SayHello() const {
	std::cout << "MyClass@" << this << ": hello!" << std::endl;
}

UCMake_test_05_dll_class_virtual_gen_API size_t sizeof_MyClass() {
	return sizeof(MyClassImpl);
}

UCMake_test_05_dll_class_virtual_gen_API MyClassHandle MyClass_Construct(void* addr) {
	return new(addr)MyClassImpl;
}

UCMake_test_05_dll_class_virtual_gen_API void MyClass_Destruct(MyClassHandle h) {
	static_cast<MyClassImpl*>(h)->~MyClassImpl();
}

UCMake_test_05_dll_class_virtual_gen_API void MyClass_SayHello(MyClassConstHandle h) {
	h->SayHello();
}
