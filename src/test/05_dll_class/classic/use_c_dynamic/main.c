#ifdef __cplusplus
#error "use C"
#endif // __cplusplus

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#else
#include <dlfcn.h>
#endif

#include <stdio.h>
#include <stdlib.h>

#include "../MyClass.h"

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
	const char dllname[] = "UCMake_test_05_dll_class_classic_gen" UCMAKE_CONFIG_POSTFIX ".dll";

	HMODULE dll = LoadLibrary(dllname);
	if (!dll) {
		printf("load %s failed.", dllname);
		return 1;
	}
	fp_sizeof_MyClass = (F_sizeof_MyClass)GetProcAddress(dll, "sizeof_MyClass");
	fp_MyClass_Construct = (F_MyClass_Construct)GetProcAddress(dll, "MyClass_Construct");
	fp_MyClass_Destruct = (F_MyClass_Destruct)GetProcAddress(dll, "MyClass_Destruct");
	fp_MyClass_SayHello = (F_MyClass_SayHello)GetProcAddress(dll, "MyClass_SayHello");
#else
	const char soname[] = "./" "lib" "UCMake_test_05_dll_class_classic_gen" UCMAKE_CONFIG_POSTFIX ".so";
	void* so = dlopen(soname, RTLD_LAZY);
	if (!so) {
		printf("load %s failed.", soname);
		return 1;
	}
	fp_sizeof_MyClass = (F_sizeof_MyClass)dlsym(so, "sizeof_MyClass");
	fp_MyClass_Construct = (F_MyClass_Construct)dlsym(so, "MyClass_Construct");
	fp_MyClass_Destruct = (F_MyClass_Destruct)dlsym(so, "MyClass_Destruct");
	fp_MyClass_SayHello = (F_MyClass_SayHello)dlsym(so, "MyClass_SayHello");
#endif

	{ // for non-stdard-layout type
		size_t s = fp_sizeof_MyClass();
		void* addr = malloc(s);
		MyClassHandle h = fp_MyClass_Construct(addr);
		printf("(%d, %d)\n", h->x, h->y);
		fp_MyClass_SayHello(h);
		fp_MyClass_Destruct(h);
		free(addr);
	}
	{ // for stdard-layout type
		MyClass myclass;
		fp_MyClass_Construct(&myclass);
		printf("(%d, %d)\n", myclass.x, myclass.y);
		fp_MyClass_SayHello(&myclass);
		fp_MyClass_Destruct(&myclass);
	}

	return 0;
}
