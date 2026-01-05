# Makefile for AXI-Lite UVM-style Testbench

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source files
VERILOG_SOURCES = $(PWD)/rtl/axi_lite_slave.sv

# Top level module
TOPLEVEL = axi_lite_slave

# Python test module
MODULE = tb.test_axi_lite_uvm

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean
clean::
	rm -rf sim_build results.xml __pycache__ tb/__pycache__ *.vcd
