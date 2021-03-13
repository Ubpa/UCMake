#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#else
#include <dlfcn.h>
#endif

#include "../MyClass.h"

#include <iostream>

typedef size_t(*F_sizeof_MyClass)();
typedef MyClassHandle(*F_MyClass_Construct)(void*);
typedef void(*F_MyClass_Destruct)(MyClassHandle);
typedef void(*F_MyClass_SayHello)(MyClassConstHandle);

int main() {
	F_sizeof_MyClass fp_sizeof_MyClass;
	F_MyClass_Construct fp_MyClass_Construct;
	F_MyClass_Destruct fp_MyClass_Destruct;
	F_MyClass_SayHello fp_MyClass_SayHello;

#if defined(_WIN32) || defined(_WIN64)
	constexpr char dllname[] = "UCMake_test_05_dll_class_virtual_gen" UCMAKE_CONFIG_POSTFIX ".dll";

	HMODULE dll = LoadLibrary(dllname);
	if (!dll) {
		std::cerr << "load " << dllname << " failed." << std::endl;
		return 1;
	}
	fp_sizeof_MyClass = (F_sizeof_MyClass)GetProcAddress(dll, "sizeof_MyClass");
	fp_MyClass_Construct = (F_MyClass_Construct)GetProcAddress(dll, "MyClass_Construct");
	fp_MyClass_Destruct = (F_MyClass_Destruct)GetProcAddress(dll, "MyClass_Destruct");
	fp_MyClass_SayHello = (F_MyClass_SayHello)GetProcAddress(dll, "MyClass_SayHello");
#else
	constexpr char soname[] = "./" "lib" "UCMake_test_05_dll_class_virtual_gen" UCMAKE_CONFIG_POSTFIX ".so";
	void* so = dlopen(soname, RTLD_LAZY);
	if (!so) {
		std::cerr << "load " << soname << " failed." << std::endl;
		return 1;
	}
	fp_sizeof_MyClass = (F_sizeof_MyClass)dlsym(so, "sizeof_MyClass");
	fp_MyClass_Construct = (F_MyClass_Construct)dlsym(so, "MyClass_Construct");
	fp_MyClass_Destruct = (F_MyClass_Destruct)dlsym(so, "MyClass_Destruct");
	fp_MyClass_SayHello = (F_MyClass_SayHello)dlsym(so, "MyClass_SayHello");
#endif


	size_t s = fp_sizeof_MyClass();
	void* addr = malloc(s);
	MyClassHandle h = fp_MyClass_Construct(addr);
	fp_MyClass_SayHello(h); // c
	h->SayHello(); // virtual
	fp_MyClass_Destruct(h);
	free(addr);

	return 0;
}
