cmake_minimum_required(VERSION 3.13)
project(cfixture C)
# platform_win.c is left out on purpose: a file no compile command covers. A library, so nothing links.
add_library(app STATIC main.c util.c)
