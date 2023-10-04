cmake_minimum_required(VERSION 3.13)
project(tdce)

find_package(LLVM REQUIRED CONFIG)
include(AddLLVM)

add_llvm_pass_plugin(tdce tdce.cpp)

target_compile_definitions(tdce PRIVATE ${LLVM_DEFINITIONS})
target_include_directories(tdce PRIVATE ${LLVM_INCLUDE_DIRS})
target_link_directories(tdce PRIVATE ${LLVM_LIBRARY_DIRS})

target_compile_features(tdce PRIVATE cxx_std_17)
target_compile_options(tdce PRIVATE -Wall)
