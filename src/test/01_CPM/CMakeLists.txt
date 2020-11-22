#if(Ubpa_BuildTest_UCMake)
#  CPMAddPackage(
#    NAME nameof
#    GITHUB_REPOSITORY Neargye/nameof
#    GIT_TAG v0.9.4
#  )
#endif()
#
#Ubpa_AddTarget(
#  TEST
#  MODE EXE
#  LIB nameof::nameof
#)