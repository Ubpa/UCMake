#if (defined(WIN32) || defined(_WIN32)) && !defined(UCMAKE_STATIC_UCMake_test_06_static_shared_gen)
  #ifdef UCMAKE_EXPORT_UCMake_test_06_static_shared_gen
    #define UCMake_test_06_static_shared_gen_API __declspec(dllexport)
  #else
    #define UCMake_test_06_static_shared_gen_API __declspec(dllimport)
  #endif
#else
  #define UCMake_test_06_static_shared_gen_API extern
#endif // (defined(WIN32) || defined(_WIN32)) && !defined(UCMAKE_STATIC_UCMake_test_06_static_shared_gen)

#ifdef __cplusplus
extern "C" {
#endif

UCMake_test_06_static_shared_gen_API int mul(int a, int b);

#ifdef __cplusplus
}
#endif
