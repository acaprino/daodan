cmake_minimum_required(VERSION 3.13)
project(cfixture C)
# platform_win.c is left out on purpose: a file no compile command covers. util.c is compiled twice, by both
# libraries, so the index holds it twice. Libraries only: nothing links.
add_library(app STATIC main.c util.c decoy.c split.c)
add_library(app_shared SHARED util.c)
