# UVM Verification Projects

Learning and practicing hardware verification with **Cocotb** (Python-based) and **UVM** (SystemVerilog).

## 🎯 Learning Objectives

Based on NoC verification engineer requirements:
- Verify NoC-level features
- Develop UVM testbenches and Python test generators
- Create VIPs for AMBA protocols (AXI-Lite, AXI-Stream, AXI4)
- Build automated verification regressions

## 📁 Project Structure

```
uvm-verification/
├── 01_cocotb_basics/       # Start here - Learn Cocotb fundamentals
├── 02_axi_lite_vip/        # AXI-Lite protocol VIP
├── 03_axi_stream_vip/      # AXI-Stream protocol VIP
├── 04_noc_verification/    # Network-on-Chip verification
├── common/                 # Shared utilities
│   ├── python_utils/       # Python test generators
│   └── constraints/        # Timing constraints
└── docs/                   # Documentation
```

## 🚀 Getting Started

### Prerequisites

```bash
# Install Cocotb
pip install cocotb cocotb-bus cocotb-coverage

# Verify installation
python -c "import cocotb; print(cocotb.__version__)"
```

### Simulators Supported

- **Icarus Verilog** (free, open-source) - recommended for learning
- **Verilator** (free, fast)
- VCS, Questa, Xcelium (commercial)

```bash
# Install Icarus Verilog (Ubuntu/Debian)
sudo apt install iverilog
```

## 📚 Learning Roadmap

### Phase 1: Cocotb Basics (Week 1-2)
- [ ] Simple combinational logic testbench
- [ ] Sequential logic with clock/reset
- [ ] Coroutines and triggers
- [ ] Scoreboards and monitors

### Phase 2: Bus Protocols (Week 3-4)
- [ ] AXI-Lite master/slave VIP
- [ ] AXI-Stream VIP
- [ ] Protocol assertions

### Phase 3: Advanced (Week 5-6)
- [ ] Functional coverage with cocotb-coverage
- [ ] Constrained random verification
- [ ] Regression automation with pytest

### Phase 4: NoC Verification (Week 7-8)
- [ ] Simple router design
- [ ] Multi-port arbitration
- [ ] End-to-end transaction verification

## 🔧 Tools & Technologies

| Category | Tool |
|----------|------|
| Testbench | Cocotb (Python) |
| RTL | SystemVerilog |
| Simulator | Icarus Verilog / Verilator |
| Coverage | cocotb-coverage |
| CI/CD | GitHub Actions |
| Version Control | Git |

## 📖 Resources

### Cocotb
- [Cocotb Documentation](https://docs.cocotb.org/)
- [cocotb-bus](https://github.com/cocotb/cocotb-bus) - Bus interfaces
- [cocotb-coverage](https://github.com/mcijeters/cocotb-coverage) - Functional coverage

### AMBA Protocols
- [ARM AMBA Specifications](https://developer.arm.com/architectures/system-architectures/amba)
- AXI4-Lite: Simple memory-mapped interface
- AXI4-Stream: Streaming data interface

## 🏃 Running Tests

```bash
cd 01_cocotb_basics
make
```

## License

MIT
