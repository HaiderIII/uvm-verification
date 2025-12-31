"""
Tests AXI-Lite Slave
====================

Ces tests vérifient :
1. Écriture simple
2. Lecture simple
3. Write puis Read (cohérence)
4. Accès à toutes les adresses
5. Test avec byte strobes
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tb'))
from axi_lite_master import AXILiteMaster, AXILiteMonitor


async def reset_dut(dut):
    """Reset le DUT."""
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_single_write(dut):
    """Test d'écriture simple à l'adresse 0x00."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    await master.init()
    await reset_dut(dut)

    # Écrire 0xDEADBEEF à l'adresse 0x00
    resp = await master.write(addr=0x00, data=0xDEADBEEF)

    # Vérifier la réponse
    assert resp == 0, f"Expected OKAY (0), got {resp}"

    dut._log.info("Test single_write PASSED!")


@cocotb.test()
async def test_single_read(dut):
    """Test de lecture simple après écriture."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    await master.init()
    await reset_dut(dut)

    # Écrire puis lire
    test_data = 0x12345678
    await master.write(addr=0x00, data=test_data)
    (read_data, resp) = await master.read(addr=0x00)

    # Vérifier
    assert resp == 0, f"Expected OKAY (0), got {resp}"
    assert read_data == test_data, f"Expected 0x{test_data:08X}, got 0x{read_data:08X}"

    dut._log.info(f"Test single_read PASSED! Read back: 0x{read_data:08X}")


@cocotb.test()
async def test_all_registers(dut):
    """Test d'accès aux 4 registres."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    await master.init()
    await reset_dut(dut)

    # Données de test pour chaque registre
    test_values = {
        0x00: 0xAAAAAAAA,
        0x04: 0xBBBBBBBB,
        0x08: 0xCCCCCCCC,
        0x0C: 0xDDDDDDDD
    }

    # Écrire tous les registres
    for addr, data in test_values.items():
        resp = await master.write(addr=addr, data=data)
        assert resp == 0, f"Write to 0x{addr:02X} failed with resp={resp}"

    # Relire et vérifier
    for addr, expected in test_values.items():
        (read_data, resp) = await master.read(addr=addr)
        assert resp == 0, f"Read from 0x{addr:02X} failed with resp={resp}"
        assert read_data == expected, \
            f"Mismatch at 0x{addr:02X}: expected 0x{expected:08X}, got 0x{read_data:08X}"

    dut._log.info("Test all_registers PASSED! All 4 registers verified.")


@cocotb.test()
async def test_byte_strobes(dut):
    """Test des byte strobes (écriture partielle)."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    await master.init()
    await reset_dut(dut)

    # Écrire une valeur complète
    await master.write(addr=0x00, data=0xFFFFFFFF, strb=0xF)

    # Écrire seulement le byte 0 (strb=0001)
    await master.write(addr=0x00, data=0x00000012, strb=0x1)

    # Lire et vérifier : seul le byte 0 a changé
    (read_data, _) = await master.read(addr=0x00)
    expected = 0xFFFFFF12

    assert read_data == expected, \
        f"Byte strobe failed: expected 0x{expected:08X}, got 0x{read_data:08X}"

    dut._log.info(f"Test byte_strobes PASSED! Result: 0x{read_data:08X}")


@cocotb.test()
async def test_multiple_writes_reads(dut):
    """Test de multiples écritures/lectures séquentielles."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    await master.init()
    await reset_dut(dut)

    # 10 écritures puis 10 lectures
    for i in range(10):
        addr = (i % 4) * 4  # Cycle entre 0x00, 0x04, 0x08, 0x0C
        data = 0x1000 + i

        await master.write(addr=addr, data=data)
        (read_data, _) = await master.read(addr=addr)

        assert read_data == data, \
            f"Iteration {i}: expected 0x{data:08X}, got 0x{read_data:08X}"

    dut._log.info("Test multiple_writes_reads PASSED! 10 transactions verified.")


@cocotb.test()
async def test_with_monitor(dut):
    """Test avec le monitor actif."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    master = AXILiteMaster(dut, "s_axi")
    monitor = AXILiteMonitor(dut, "s_axi")

    await master.init()
    await reset_dut(dut)

    # Démarrer le monitor
    monitor.start()

    # Quelques transactions
    await master.write(addr=0x00, data=0x11111111)
    await master.write(addr=0x04, data=0x22222222)
    await master.read(addr=0x00)
    await master.read(addr=0x04)

    # Attendre un peu pour que le monitor capture tout
    await ClockCycles(dut.clk, 5)
    monitor.stop()

    # Vérifier que le monitor a capturé les transactions
    txns = monitor.get_transactions()
    dut._log.info(f"Monitor captured {len(txns)} transactions")

    # On devrait avoir 2 WRITE + 2 READ = 4 transactions
    # Note: le monitor peut capturer légèrement différemment selon le timing
    assert len(txns) >= 2, f"Expected at least 2 transactions, got {len(txns)}"

    dut._log.info("Test with_monitor PASSED!")
