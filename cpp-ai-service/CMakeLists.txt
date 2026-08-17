cmake_minimum_required(VERSION 3.16)
project(warehouse_ai_service LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
find_package(SQLite3 REQUIRED)
find_package(ncnn REQUIRED)

add_executable(warehouse-ai-service src/main.cpp)
target_link_libraries(warehouse-ai-service PRIVATE ${OpenCV_LIBS} SQLite::SQLite3 ncnn)
target_include_directories(warehouse-ai-service PRIVATE ${OpenCV_INCLUDE_DIRS})

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(warehouse-ai-service PRIVATE -O3 -DNDEBUG)
  include(CheckIPOSupported)
  check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)
  if(ipo_supported)
    set_property(TARGET warehouse-ai-service PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
  endif()
endif()

install(TARGETS warehouse-ai-service RUNTIME DESTINATION bin)
