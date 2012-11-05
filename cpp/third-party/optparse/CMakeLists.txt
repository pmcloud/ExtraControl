PROJECT(OptParse)

SET(OP_SRCS optparse.cpp)

ADD_LIBRARY(optparse ${OP_SRCS})
ADD_EXECUTABLE(test test.cpp)
TARGET_LINK_LIBRARIES(test optparse)
