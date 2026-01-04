cmake_minimum_required(VERSION 3.23)

# 最初はC++のみでプロジェクトを定義
project(StormRANS LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# =========================================
# CUDA Toolkit の検出（任意）
# =========================================
find_package(CUDAToolkit QUIET)

if(CUDAToolkit_FOUND)
    message(STATUS "CUDA Toolkit found: ${CUDAToolkit_VERSION}")
    message(STATUS "Building with CUDA support")
    
    # CUDA言語を有効化
    enable_language(CUDA)
    
    set(CMAKE_CUDA_STANDARD 17)
    set(CMAKE_CUDA_STANDARD_REQUIRED ON)
    
    # CUDAアーキテクチャの指定
    # 例: Ampere(80), Ada(89), Hopper(90) など。複数指定も可。
    set(CMAKE_CUDA_ARCHITECTURES "70;75;80;86;89;90" CACHE STRING "")
else()
    message(STATUS "CUDA Toolkit not found: Building CPU-only version")
endif()

# =========================================
# CPU版ライブラリ（常にビルド）
# =========================================
add_library(storm_rans_cpu STATIC
    src/cpu/storm_rans.cpp
)

target_include_directories(storm_rans_cpu PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

set_target_properties(storm_rans_cpu PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)


# =========================================
# CUDA版ライブラリ（CUDA検出時のみ）
# =========================================
if(CUDAToolkit_FOUND)
    add_library(storm_rans_cuda STATIC
        src/cuda/storm_rans.cu
    )
    
    target_include_directories(storm_rans_cuda PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
    
    target_link_libraries(storm_rans_cuda PRIVATE
        CUDA::cudart
    )
    
    set_target_properties(storm_rans_cuda PROPERTIES
        CUDA_STANDARD 17
        CUDA_STANDARD_REQUIRED ON
    )

    # =========================================
    # 実行ファイル(CPU)
    # =========================================
    add_executable(app
        src/cuda/storm_rans.cu
    )
    
    # CUDA使用可能フラグを定義
    target_compile_definitions(app_cuda PRIVATE USE_CUDA)
endif()

option(BUILD_TESTING "Build tests" ON)
if(BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests)
endif()

