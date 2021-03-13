#if (defined(WIN32) || defined(_WIN32)) && !defined(UCMake_test_04_dll_STATIC)
  #ifdef UCMake_test_04_dll_gen_EXPORTS
    #define UCMake_test_04_dll_gen_API __declspec(dllexport)
  #else
    #define UCMake_test_04_dll_gen_API __declspec(dllimport)
  #endif
#else
  #define UCMake_test_04_dll_gen_API extern
#endif // (defined(WIN32) || defined(_WIN32)) && !defined(UCMake_test_04_dll_STATIC)

#ifdef __cplusplus
extern "C" {
#endif

UCMake_test_04_dll_gen_API int mul(int a, int b);

#ifdef __cplusplus
}
#endif
