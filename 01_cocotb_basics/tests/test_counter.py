"""
Cocotb Testbench for Counter Module
===================================

This is your first Cocotb testbench. It demonstrates:
- Clock generation
- Reset sequence
- Driving inputs
- Checking outputs
- Using coroutines (async/await)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles


@cocotb.test()
async def test_counter_reset(dut):
    """Test that reset sets counter to 0."""

    # Start clock (10ns period = 100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Initialize inputs
    dut.enable.value = 0
    dut.rst_n.value = 0  # Assert reset (active low)

    # Wait a few clock cycles
    await ClockCycles(dut.clk, 5)

    # Check counter is 0 during reset
    assert dut.count.value == 0, f"Counter should be 0 during reset, got {dut.count.value}"

    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Counter should still be 0 (enable is off)
    assert dut.count.value == 0, f"Counter should be 0 after reset, got {dut.count.value}"

    dut._log.info("✓ Reset test passed!")


@cocotb.test()
async def test_counter_count(dut):
    """Test that counter increments when enabled."""

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut.enable.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Enable counting
    dut.enable.value = 1

    # Count for 10 cycles
    await ClockCycles(dut.clk, 10)

    # Check counter value
    expected = 10
    actual = int(dut.count.value)
    assert actual == expected, f"Expected count={expected}, got {actual}"

    dut._log.info(f"✓ Counter reached {actual} as expected!")


@cocotb.test()
async def test_counter_enable_control(dut):
    """Test that counter stops when enable is deasserted."""

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut.enable.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Enable and count for 5 cycles
    dut.enable.value = 1
    await ClockCycles(dut.clk, 5)

    # Disable and wait
    dut.enable.value = 0
    count_when_disabled = int(dut.count.value)
    await ClockCycles(dut.clk, 10)

    # Counter should not have changed
    count_after_wait = int(dut.count.value)
    assert count_after_wait == count_when_disabled, \
        f"Counter should stay at {count_when_disabled}, but got {count_after_wait}"

    dut._log.info(f"✓ Counter correctly held at {count_after_wait} when disabled!")


@cocotb.test()
async def test_counter_wrap(dut):
    """Test counter wrap-around at 255 (8-bit)."""

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.enable.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Count for 260 cycles (should wrap at 256)
    dut.enable.value = 1
    await ClockCycles(dut.clk, 260)

    # Should have wrapped: 260 % 256 = 4
    expected = 260 % 256
    actual = int(dut.count.value)
    assert actual == expected, f"Expected wrap to {expected}, got {actual}"

    dut._log.info(f"✓ Counter correctly wrapped to {actual}!")
