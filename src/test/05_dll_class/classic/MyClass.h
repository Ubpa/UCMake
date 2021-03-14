#if (defined(WIN32) || defined(_WIN32)) && !defined(UCMAKE_STATIC_UCMake_test_05_dll_class_classic_gen)
  #ifdef UCMAKE_EXPORT_UCMake_test_05_dll_class_classic_gen
    #define UCMake_test_05_dll_class_classic_gen_API __declspec(dllexport)
    #define UCMake_test_05_dll_class_classic_gen_CLASS_API __declspec(dllexport)
  #else
    #define UCMake_test_05_dll_class_classic_gen_API __declspec(dllimport)
    #define UCMake_test_05_dll_class_classic_gen_CLASS_API __declspec(dllimport)
  #endif
#else
  #define UCMake_test_05_dll_class_classic_gen_API extern
  #define UCMake_test_05_dll_class_classic_gen_CLASS_API
#endif // (defined(WIN32) || defined(_WIN32)) && !defined(UCMAKE_STATIC_UCMake_test_05_dll_class_classic_gen)

#include <stddef.h>

#ifdef __cplusplus
#include <type_traits>

class UCMake_test_05_dll_class_classic_gen_CLASS_API MyClass {
public:
	int x;
	int y;

	MyClass();
	~MyClass();
	void SayHello() const;
};
static_assert(std::is_standard_layout_v<MyClass>);
using MyClassHandle = MyClass*;
using MyClassConstHandle = const MyClass*;
#else
typedef struct{
	int x;
	int y;
} MyClass;
typedef MyClass* MyClassHandle;
typedef const MyClass* MyClassConstHandle;
#endif

#ifdef __cplusplus
extern "C" {
#endif

UCMake_test_05_dll_class_classic_gen_API size_t sizeof_MyClass();
UCMake_test_05_dll_class_classic_gen_API MyClassHandle MyClass_Construct(void* addr);
UCMake_test_05_dll_class_classic_gen_API void MyClass_Destruct(MyClassHandle h);
UCMake_test_05_dll_class_classic_gen_API void MyClass_SayHello(MyClassConstHandle h);

#ifdef __cplusplus
}
#endif
