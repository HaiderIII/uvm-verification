# Makefile for RAL Testbench

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source files (réutilise le RTL du projet APB)
VERILOG_SOURCES = $(PWD)/rtl/apb_slave.sv

# Top level module
TOPLEVEL = apb_slave

# Python test module
MODULE = tb.test_ral

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean
clean::
	rm -rf sim_build results.xml __pycache__ tb/__pycache__ *.vcd
