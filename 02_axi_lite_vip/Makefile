# Cocotb Makefile for AXI-Lite VIP

# Simulator
SIM ?= icarus

# Top-level module
TOPLEVEL = axi_lite_slave

# Language
TOPLEVEL_LANG = verilog

# RTL sources
VERILOG_SOURCES = $(PWD)/rtl/axi_lite_slave.sv

# Python test module
MODULE = tests.test_axi_lite

# Include Cocotb Makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean
clean::
	rm -rf sim_build results.xml __pycache__ tests/__pycache__ tb/__pycache__
