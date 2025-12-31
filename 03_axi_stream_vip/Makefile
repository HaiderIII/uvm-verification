# Makefile for AXI-Stream FIFO cocotb tests

# Simulator
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source files
VERILOG_SOURCES = $(PWD)/rtl/axi_stream_fifo.sv

# Top level module
TOPLEVEL = axi_stream_fifo

# Python test module
MODULE = tests.test_axi_stream

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean target
clean::
	rm -rf sim_build results.xml __pycache__ tests/__pycache__ tb/__pycache__
