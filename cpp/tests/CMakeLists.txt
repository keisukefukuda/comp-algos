add_executable(test_cpu test_cpu.cpp)

find_package(Catch2 CONFIG REQUIRED)

# Catch2が提供するターゲット（Main同梱の方が楽）
target_link_libraries(test_cpu PRIVATE storm_rans_cpu Catch2::Catch2WithMain)

add_test(NAME unit_tests COMMAND unit_tests)

if (CUDAToolkit_FOUND)
    add_executable(test_cuda test_main.cpp)
    target_compile_definitions(test_cuda PRIVATE USE_CUDA)
    target_link_libraries(test_cuda PRIVATE storm_rans_cuda CUDA::cudart)
endif()

