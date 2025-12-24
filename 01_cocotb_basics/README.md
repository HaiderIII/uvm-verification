# 01 - Cocotb Basics

First project to learn Cocotb fundamentals with a simple counter.

## Design Under Test (DUT)

**8-bit Counter** with:
- `clk` - Clock input
- `rst_n` - Active-low reset
- `enable` - Count enable
- `count[7:0]` - Counter output

## Tests

| Test | Description |
|------|-------------|
| `test_counter_reset` | Verify reset sets counter to 0 |
| `test_counter_count` | Verify counter increments when enabled |
| `test_counter_enable_control` | Verify counter holds when disabled |
| `test_counter_wrap` | Verify wrap-around at 255 |

## Running

```bash
# Install dependencies first
pip install cocotb

# Run all tests
make

# Run with waveform dump
make WAVES=1

# Clean
make clean
```

## Key Cocotb Concepts

### 1. Clock Generation
```python
clock = Clock(dut.clk, 10, units="ns")  # 100 MHz
cocotb.start_soon(clock.start())
```

### 2. Driving Signals
```python
dut.enable.value = 1
dut.rst_n.value = 0
```

### 3. Waiting for Events
```python
await RisingEdge(dut.clk)      # Wait for rising edge
await ClockCycles(dut.clk, 5)  # Wait 5 clock cycles
```

### 4. Reading Signals
```python
count_value = int(dut.count.value)
```

### 5. Assertions
```python
assert dut.count.value == 0, "Error message"
```

## Next Steps

After this project, move to:
- Adding a scoreboard (model-based checking)
- Using `cocotb.fork()` for parallel operations
- Adding functional coverage
