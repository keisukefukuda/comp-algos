from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake

class StormRans(ConanFile):
    name = "storm_rans"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"

    # テスト用依存（Catch2 / gtest は test_requires 推奨）
    def build_requirements(self):
        self.test_requires("catch2/3.5.4")

    generators = ("CMakeToolchain", "CMakeDeps")

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
