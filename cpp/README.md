```
# First time
conan profile detect

rm -rf build/

# 依存解決＆toolchain/deps生成
conan install . -of build -s build_type=Debug --build=missing

cmake --preset conan-debug 

# build
cmake --build build/build/Debug

# test
ctest --test-dir build

```

