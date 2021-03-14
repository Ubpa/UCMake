#if (defined(WIN32) || defined(_WIN32)) && !defined(UCMAKE_STATIC_UCMake_test_04_dll)
  #ifdef UCMAKE_EXPORT_UCMake_test_04_dll_gen
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
