# Makefile for NoC Router UVM-style Testbench

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source files
VERILOG_SOURCES = $(PWD)/rtl/noc_router.sv

# Top level module
TOPLEVEL = noc_router

# Python test module
MODULE = tb.test_noc_uvm

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean
clean::
	rm -rf sim_build results.xml __pycache__ tb/__pycache__ *.vcd
