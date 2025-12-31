# Makefile for NoC Router cocotb tests

# Simulator
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source files
VERILOG_SOURCES = $(PWD)/rtl/noc_pkg.sv $(PWD)/rtl/noc_router.sv

# Top level module
TOPLEVEL = noc_router

# Python test module
MODULE = tests.test_noc_router

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean target
clean::
	rm -rf sim_build results.xml __pycache__ tests/__pycache__ tb/__pycache__
