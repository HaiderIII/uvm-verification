# ============================================================================
# Makefile for APB UVM Testbench
# ============================================================================

# Simulator selection (questa, vcs, or xcelium)
SIM ?= questa

# UVM version
UVM_VERSION ?= 1.2

# Source files
RTL_SRC = rtl/apb_if.sv \
          rtl/apb_slave.sv

TB_SRC = tb/apb_pkg.sv \
         tb/tb_top.sv

# Include paths
INC_DIRS = +incdir+tb

# Common compile flags
COMPILE_FLAGS = -sv $(INC_DIRS)

# ============================================================================
# Questa/Modelsim
# ============================================================================
ifeq ($(SIM),questa)
    VLOG = vlog
    VSIM = vsim
    VLIB = vlib
    WORK = work

    VLOG_FLAGS = -sv +acc $(INC_DIRS)
    VSIM_FLAGS = -c -do "run -all; quit" +UVM_TESTNAME=apb_base_test

    compile:
		$(VLIB) $(WORK)
		$(VLOG) $(VLOG_FLAGS) $(RTL_SRC) $(TB_SRC)

    run: compile
		$(VSIM) $(VSIM_FLAGS) tb_top

    gui: compile
		$(VSIM) +UVM_TESTNAME=apb_base_test tb_top

endif

# ============================================================================
# Icarus Verilog (avec UVM open-source)
# ============================================================================
ifeq ($(SIM),icarus)
    IVERILOG = iverilog
    VVP = vvp

    # UVM for Icarus (requires uvm-python or similar)
    # Note: Icarus doesn't fully support UVM, use Verilator or commercial sim

    compile:
		@echo "Note: Icarus Verilog has limited UVM support"
		$(IVERILOG) -g2012 -o sim.vvp $(RTL_SRC) $(TB_SRC)

    run: compile
		$(VVP) sim.vvp

endif

# ============================================================================
# Verilator + UVM (experimental)
# ============================================================================
ifeq ($(SIM),verilator)
    VERILATOR = verilator

    compile:
		$(VERILATOR) --sv --cc $(RTL_SRC) --exe $(TB_SRC)
		make -C obj_dir -f Vtb_top.mk

    run: compile
		./obj_dir/Vtb_top

endif

# ============================================================================
# Clean
# ============================================================================
clean:
	rm -rf work transcript vsim.wlf *.vcd sim.vvp obj_dir

.PHONY: compile run gui clean
