#ifdef __cplusplus
#error "use C"
#endif // __cplusplus

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#else
#include <dlfcn.h>
#endif

#include <stdio.h>

typedef int(*Func)(int, int);

int main() {
	Func mul;
#if defined(_WIN32) || defined(_WIN64)
	const char dllname[] = "UCMake_test_04_dll_gen" UCMAKE_CONFIG_POSTFIX ".dll";

	HMODULE dll = LoadLibrary(dllname);
	if (!dll) {
		printf("load %s failed.", dllname);
		return 1;
	}
	mul = (Func)GetProcAddress(dll, "mul");
#else
	const char soname[] = "./" "lib" "UCMake_test_04_dll_gen" UCMAKE_CONFIG_POSTFIX ".so";
	void* so = dlopen(soname, RTLD_LAZY);
	if (!so) {
		printf("load %s failed.", soname);
		return 1;
	}
	mul = (Func)dlsym(so, "mul");
#endif

	printf("mul(2, 3): %d\n", mul(2, 3));
	return 0;
}
