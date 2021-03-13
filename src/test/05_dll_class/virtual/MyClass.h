#if (defined(WIN32) || defined(_WIN32)) && !defined(UCMake_test_05_dll_class_virtual_gen_STATIC)
  #ifdef UCMake_test_05_dll_class_virtual_gen_EXPORTS
    #define UCMake_test_05_dll_class_virtual_gen_API __declspec(dllexport)
  #else
    #define UCMake_test_05_dll_class_virtual_gen_API __declspec(dllimport)
  #endif
#else
  #define UCMake_test_05_dll_class_virtual_gen_API extern
#endif // (defined(WIN32) || defined(_WIN32)) && !defined(UCMake_test_05_dll_class_virtual_gen_STATIC)

#include <stddef.h>

#ifdef __cplusplus

class MyClass {
public:
	virtual ~MyClass() = default;
	virtual void SayHello() const = 0;
};
static_assert(sizeof(MyClass) == sizeof(void*));
using MyClassHandle = MyClass*;
using MyClassConstHandle = const MyClass*;
#else
typedef struct{
	void* vtable;
} MyClass;
typedef MyClass* MyClassHandle;
typedef const MyClass* MyClassConstHandle;
#endif

#ifdef __cplusplus
extern "C" {
#endif

UCMake_test_05_dll_class_virtual_gen_API size_t sizeof_MyClass();
UCMake_test_05_dll_class_virtual_gen_API MyClassHandle MyClass_Construct(void* addr);
UCMake_test_05_dll_class_virtual_gen_API void MyClass_Destruct(MyClassHandle h);
UCMake_test_05_dll_class_virtual_gen_API void MyClass_SayHello(MyClassConstHandle h);

#ifdef __cplusplus
}
#endif
