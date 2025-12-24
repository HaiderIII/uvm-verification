#!/bin/bash
# Setup script for UVM Verification environment

set -e

echo "=== UVM Verification Environment Setup ==="

# Check Python version
echo ""
echo "[1/3] Checking Python..."
python3 --version

# Install Python packages
echo ""
echo "[2/3] Installing Python packages..."
pip install --upgrade pip
pip install cocotb cocotb-bus cocotb-coverage pytest

# Check for simulator
echo ""
echo "[3/3] Checking simulator..."
if command -v iverilog &> /dev/null; then
    echo "✓ Icarus Verilog found: $(iverilog -V 2>&1 | head -1)"
elif command -v verilator &> /dev/null; then
    echo "✓ Verilator found: $(verilator --version)"
else
    echo "⚠ No simulator found!"
    echo ""
    echo "Install Icarus Verilog:"
    echo "  Ubuntu/Debian: sudo apt install iverilog"
    echo "  macOS:         brew install icarus-verilog"
    echo ""
    echo "Or install Verilator:"
    echo "  Ubuntu/Debian: sudo apt install verilator"
    echo "  macOS:         brew install verilator"
fi

# Verify Cocotb installation
echo ""
echo "=== Verification ==="
python3 -c "import cocotb; print(f'✓ Cocotb {cocotb.__version__} installed')"

echo ""
echo "=== Setup Complete ==="
echo "Run your first test:"
echo "  cd 01_cocotb_basics && make"
