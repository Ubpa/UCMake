#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#else
#include <dlfcn.h>
#endif


#include <iostream>

using Func = int(int, int);

int main() {
	Func* mul;
#if defined(_WIN32) || defined(_WIN64)
	constexpr char dllname[] = "UCMake_test_04_dll_gen" UCMAKE_CONFIG_POSTFIX ".dll";

	auto dll = LoadLibrary(dllname);
	if (!dll) {
		std::cerr << "load " << dllname << " faild." << std::endl;
		return 1;
	}
	mul = (Func*)GetProcAddress(dll, "mul");
#else
	constexpr char soname[] = "./" "lib" "UCMake_test_04_dll_gen" UCMAKE_CONFIG_POSTFIX ".so";
	auto so = dlopen(soname, RTLD_LAZY);
	if (!so) {
		std::cerr << dlerror() << std::endl;
		std::cerr << "load " << soname << " faild." << std::endl;
		return 1;
	}
	mul = (Func*)dlsym(so, "mul");
#endif

	std::cout << mul(2, 3) << std::endl;
	return 0;
}
