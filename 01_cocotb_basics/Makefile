# Cocotb Makefile for Counter Testbench

# Simulator selection (use Icarus Verilog by default)
SIM ?= icarus

# Top-level module name
TOPLEVEL = counter

# Language of the design
TOPLEVEL_LANG = verilog

# RTL source files
VERILOG_SOURCES = $(PWD)/rtl/counter.sv

# Python test module (without .py extension)
MODULE = tests.test_counter

# Include Cocotb's Makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean simulation artifacts
clean::
	rm -rf sim_build results.xml __pycache__ tests/__pycache__
