# SDL enables CMake's runtime-library policy. Match Rust's +crt-static for
# every native dependency; /MT in CMAKE_C_FLAGS alone can be overridden by /MD.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>" CACHE STRING "MSVC runtime" FORCE)
