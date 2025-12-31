"""
Tests NoC Router
================

Tests pour vérifier le routage XY du routeur NoC.
Le routeur est configuré en position (1, 1).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

import sys
sys.path.insert(0, "/home/faiz/projects/uvm-verification/04_noc_verification/tb")

from noc_vip import (
    NoCPacket, NoCDriver, NoCMonitor, NoCReceiver, NoCScoreboard,
    PKT_WRITE_REQ, DIR_LOCAL, DIR_NORTH, DIR_SOUTH, DIR_EAST, DIR_WEST
)

# Position du routeur (doit correspondre aux paramètres RTL)
# Par défaut dans le RTL: ROUTER_X=0, ROUTER_Y=0
ROUTER_X = 0
ROUTER_Y = 0


async def reset_dut(dut):
    """Reset le DUT et initialise tous les signaux."""
    dut.rst_n.value = 0

    # Initialiser tous les ports d'entrée
    for port in ["local_in", "north_in", "south_in", "east_in", "west_in"]:
        getattr(dut, f"{port}_tdata").value = 0
        getattr(dut, f"{port}_tvalid").value = 0
        getattr(dut, f"{port}_tlast").value = 0

    # Initialiser tous les ready de sortie
    for port in ["local_out", "north_out", "south_out", "east_out", "west_out"]:
        getattr(dut, f"{port}_tready").value = 1

    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_route_to_east(dut):
    """
    Test: Paquet de LOCAL vers EAST.
    Routeur en (0,0), destination (2,0) → doit aller vers EAST.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    # Créer driver et monitor
    driver = NoCDriver(dut, "local_in", dut.clk, "LocalDriver")
    monitor = NoCMonitor(dut, "east_out", dut.clk, "EastMonitor")

    await driver.reset()
    monitor.start()

    # Créer un paquet: src=(0,0), dst=(2,0) → EAST (car dst_x > router_x)
    packet = NoCPacket(
        pkt_type=PKT_WRITE_REQ,
        src_x=0, src_y=0,
        dst_x=2, dst_y=0,
        payload=0xDEADBEEF
    )

    await driver.send(packet)
    await ClockCycles(dut.clk, 5)

    monitor.stop()

    # Vérifier
    assert len(monitor.received_packets) == 1, f"Expected 1 packet on EAST, got {len(monitor.received_packets)}"
    assert monitor.received_packets[0] == packet, "Packet mismatch!"

    dut._log.info("Test route_to_east PASSED!")


@cocotb.test()
async def test_route_to_south(dut):
    """
    Test: Paquet de LOCAL vers SOUTH.
    Routeur en (0,0), destination (0,2) → doit aller vers SOUTH.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    driver = NoCDriver(dut, "local_in", dut.clk, "LocalDriver")
    monitor = NoCMonitor(dut, "south_out", dut.clk, "SouthMonitor")

    await driver.reset()
    monitor.start()

    # dst=(0,2) → SOUTH (car dst_x == router_x et dst_y > router_y)
    packet = NoCPacket(
        pkt_type=PKT_WRITE_REQ,
        src_x=0, src_y=0,
        dst_x=0, dst_y=2,
        payload=0xCAFEBABE
    )

    await driver.send(packet)
    await ClockCycles(dut.clk, 5)

    monitor.stop()

    assert len(monitor.received_packets) == 1, f"Expected 1 packet on SOUTH, got {len(monitor.received_packets)}"
    dut._log.info("Test route_to_south PASSED!")


@cocotb.test()
async def test_route_diagonal(dut):
    """
    Test: Paquet de LOCAL vers destination diagonale.
    Routeur en (0,0), destination (2,2) → XY routing: d'abord EAST.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    driver = NoCDriver(dut, "local_in", dut.clk, "LocalDriver")
    monitor = NoCMonitor(dut, "east_out", dut.clk, "EastMonitor")

    await driver.reset()
    monitor.start()

    # dst=(2,2) → EAST d'abord (algorithme XY: X avant Y)
    packet = NoCPacket(
        pkt_type=PKT_WRITE_REQ,
        src_x=0, src_y=0,
        dst_x=2, dst_y=2,
        payload=0x12345678
    )

    await driver.send(packet)
    await ClockCycles(dut.clk, 5)

    monitor.stop()

    assert len(monitor.received_packets) == 1, f"Expected 1 packet on EAST, got {len(monitor.received_packets)}"
    dut._log.info("Test route_diagonal PASSED!")


@cocotb.test()
async def test_route_to_local(dut):
    """
    Test: Paquet de SOUTH vers LOCAL.
    Paquet venant du sud avec destination (0,0) → LOCAL.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    driver = NoCDriver(dut, "south_in", dut.clk, "SouthDriver")
    monitor = NoCMonitor(dut, "local_out", dut.clk, "LocalMonitor")

    await driver.reset()
    monitor.start()

    # dst=(0,0) == router position → LOCAL
    packet = NoCPacket(
        pkt_type=PKT_WRITE_REQ,
        src_x=0, src_y=1,  # Vient du sud
        dst_x=0, dst_y=0,  # Destination = ce routeur
        payload=0xAAAABBBB
    )

    await driver.send(packet)
    await ClockCycles(dut.clk, 5)

    monitor.stop()

    assert len(monitor.received_packets) == 1, f"Expected 1 packet on LOCAL, got {len(monitor.received_packets)}"
    dut._log.info("Test route_to_local PASSED!")


@cocotb.test()
async def test_with_scoreboard(dut):
    """
    Test complet avec scoreboard vérifiant plusieurs destinations.
    Routeur en (0,0) - on ne peut tester que EAST et SOUTH depuis LOCAL.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    driver = NoCDriver(dut, "local_in", dut.clk, "LocalDriver")
    scoreboard = NoCScoreboard(dut._log, ROUTER_X, ROUTER_Y)

    # Monitors sur les ports de sortie possibles
    monitors = {
        DIR_SOUTH: NoCMonitor(dut, "south_out", dut.clk, "SouthMon"),
        DIR_EAST:  NoCMonitor(dut, "east_out",  dut.clk, "EastMon"),
    }

    await driver.reset()
    for mon in monitors.values():
        mon.start()

    # Envoyer des paquets vers différentes destinations (depuis routeur 0,0)
    test_packets = [
        NoCPacket(PKT_WRITE_REQ, 0, 0, 2, 0, 0x1111),  # → EAST (dst_x > 0)
        NoCPacket(PKT_WRITE_REQ, 0, 0, 3, 0, 0x2222),  # → EAST
        NoCPacket(PKT_WRITE_REQ, 0, 0, 0, 1, 0x3333),  # → SOUTH (dst_y > 0)
        NoCPacket(PKT_WRITE_REQ, 0, 0, 0, 2, 0x4444),  # → SOUTH
    ]

    for pkt in test_packets:
        await driver.send(pkt)
        await ClockCycles(dut.clk, 3)

    await ClockCycles(dut.clk, 10)

    for mon in monitors.values():
        mon.stop()

    # Vérifier avec le scoreboard
    for direction, mon in monitors.items():
        for pkt in mon.received_packets:
            scoreboard.check_packet(pkt, direction)

    assert scoreboard.report(), "Scoreboard detected routing errors!"
    dut._log.info("Test with_scoreboard PASSED!")
