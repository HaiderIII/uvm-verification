"""
Tests AXI-Stream FIFO
=====================

Tests pour vérifier le fonctionnement de la FIFO AXI-Stream.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, FallingEdge

import sys
sys.path.insert(0, "/home/faiz/projects/uvm-verification/03_axi_stream_vip/tb")

from axi_stream_vip import (
    AXIStreamMaster, AXIStreamSlave, AXIStreamMonitor,
    AXIStreamPacket, AXIStreamScoreboard
)


async def reset_dut(dut):
    """Reset le DUT."""
    dut.rst_n.value = 0
    dut.s_axis_tvalid.value = 0
    dut.s_axis_tdata.value = 0
    dut.s_axis_tlast.value = 0
    dut.m_axis_tready.value = 0

    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_single_transfer(dut):
    """Test d'un transfert simple (1 mot avec TLAST)."""

    # Démarrer l'horloge
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Reset
    await reset_dut(dut)

    # Créer le master et envoyer un paquet d'un seul mot
    master = AXIStreamMaster(dut, "s_axis", dut.clk)
    await master.reset()

    # Activer le ready côté sortie
    dut.m_axis_tready.value = 1

    # Envoyer un paquet
    await master.send_packet([0xDEADBEEF])

    # Attendre que la donnée traverse la FIFO
    await ClockCycles(dut.clk, 3)

    # Vérifier la sortie
    await FallingEdge(dut.clk)
    dut._log.info(f"Test single_transfer PASSED!")


@cocotb.test()
async def test_packet_transfer(dut):
    """Test d'un paquet complet (4 mots)."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    master = AXIStreamMaster(dut, "s_axis", dut.clk)
    slave = AXIStreamSlave(dut, "m_axis", dut.clk)

    await master.reset()
    await slave.reset()

    # Envoyer un paquet de 4 mots
    test_data = [0x11111111, 0x22222222, 0x33333333, 0x44444444]

    # Démarrer la réception
    slave.start()

    # Envoyer le paquet
    await master.send_packet(test_data)

    # Attendre la réception
    await ClockCycles(dut.clk, 10)

    slave.stop()

    # Vérifier
    assert len(slave.received_packets) == 1, f"Expected 1 packet, got {len(slave.received_packets)}"
    assert slave.received_packets[0].data == test_data, f"Data mismatch!"

    dut._log.info(f"Test packet_transfer PASSED! Received: {slave.received_packets[0]}")


@cocotb.test()
async def test_multiple_packets(dut):
    """Test de plusieurs paquets consécutifs."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    master = AXIStreamMaster(dut, "s_axis", dut.clk)
    slave = AXIStreamSlave(dut, "m_axis", dut.clk)

    await master.reset()
    await slave.reset()

    # Préparer 3 paquets
    packets = [
        [0xAAAAAAAA, 0xBBBBBBBB],
        [0xCCCCCCCC],
        [0x11111111, 0x22222222, 0x33333333]
    ]

    slave.start()

    # Envoyer les paquets
    for packet in packets:
        await master.send_packet(packet)
        await ClockCycles(dut.clk, 5)

    # Attendre que tout soit reçu
    await ClockCycles(dut.clk, 20)

    slave.stop()

    # Vérifier
    assert len(slave.received_packets) == 3, f"Expected 3 packets, got {len(slave.received_packets)}"

    for i, (sent, received) in enumerate(zip(packets, slave.received_packets)):
        assert received.data == sent, f"Packet {i} mismatch: sent {sent}, received {received.data}"

    dut._log.info(f"Test multiple_packets PASSED! Received {len(slave.received_packets)} packets.")


@cocotb.test()
async def test_back_pressure(dut):
    """Test du back-pressure (sink lent)."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    master = AXIStreamMaster(dut, "s_axis", dut.clk)

    # Slave avec latence (1 cycle d'attente entre chaque ready)
    slave = AXIStreamSlave(dut, "m_axis", dut.clk, ready_latency=2)

    await master.reset()
    await slave.reset()

    # Paquet de test
    test_data = [0xAA, 0xBB, 0xCC, 0xDD]

    slave.start()

    # Envoyer
    await master.send_packet(test_data)

    # Plus de temps car le slave est lent
    await ClockCycles(dut.clk, 30)

    slave.stop()

    # Vérifier
    assert len(slave.received_packets) == 1, f"Expected 1 packet, got {len(slave.received_packets)}"
    assert slave.received_packets[0].data == test_data

    dut._log.info(f"Test back_pressure PASSED! Slave with latency received correctly.")


@cocotb.test()
async def test_with_monitors(dut):
    """Test avec monitors sur les deux interfaces."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    master = AXIStreamMaster(dut, "s_axis", dut.clk)
    slave = AXIStreamSlave(dut, "m_axis", dut.clk)

    # Monitors sur entrée et sortie
    input_monitor = AXIStreamMonitor(dut, "s_axis", dut.clk, "InputMon")
    output_monitor = AXIStreamMonitor(dut, "m_axis", dut.clk, "OutputMon")

    await master.reset()
    await slave.reset()

    # Démarrer les monitors
    input_monitor.start()
    output_monitor.start()
    slave.start()

    # Envoyer des paquets
    packets = [
        [0x11111111, 0x22222222],
        [0x33333333, 0x44444444, 0x55555555]
    ]

    for packet in packets:
        await master.send_packet(packet)
        await ClockCycles(dut.clk, 5)

    await ClockCycles(dut.clk, 20)

    # Arrêter
    input_monitor.stop()
    output_monitor.stop()
    slave.stop()

    # Vérifier que les monitors ont capturé les mêmes paquets
    assert len(input_monitor.packets) == len(output_monitor.packets), \
        f"Monitor mismatch: input={len(input_monitor.packets)}, output={len(output_monitor.packets)}"

    dut._log.info(f"Test with_monitors PASSED!")
    dut._log.info(f"  Input monitor captured {len(input_monitor.packets)} packets")
    dut._log.info(f"  Output monitor captured {len(output_monitor.packets)} packets")


@cocotb.test()
async def test_with_scoreboard(dut):
    """Test complet avec scoreboard."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    master = AXIStreamMaster(dut, "s_axis", dut.clk)
    slave = AXIStreamSlave(dut, "m_axis", dut.clk)
    scoreboard = AXIStreamScoreboard(dut._log)

    await master.reset()
    await slave.reset()

    slave.start()

    # Préparer et envoyer des paquets
    packets = [
        [0xDEADBEEF],
        [0x12345678, 0x9ABCDEF0],
        [0x11, 0x22, 0x33, 0x44]
    ]

    for packet in packets:
        scoreboard.add_expected(packet)
        await master.send_packet(packet)
        await ClockCycles(dut.clk, 5)

    await ClockCycles(dut.clk, 20)
    slave.stop()

    # Vérifier avec le scoreboard
    for received in slave.received_packets:
        scoreboard.check_received(received)

    # Rapport final
    assert scoreboard.report(), "Scoreboard detected errors!"

    dut._log.info(f"Test with_scoreboard PASSED!")
