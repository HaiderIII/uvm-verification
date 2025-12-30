"""
Counter Testbench avec Scoreboard
=================================

Ce fichier démontre l'utilisation d'un scoreboard pour :
- Vérification automatique (pas de valeurs en dur)
- Vérification continue (à chaque cycle)
- Détection précise des erreurs
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles

# Import du scoreboard (depuis le dossier tb/)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tb'))
from scoreboard import CounterScoreboard


async def reset_dut(dut, scoreboard):
    """
    Séquence de reset réutilisable.

    Args:
        dut: Le design under test
        scoreboard: Le scoreboard à synchroniser
    """
    dut.enable.value = 0
    dut.rst_n.value = 0  # Assert reset (active low)
    await ClockCycles(dut.clk, 5)

    # Informer le scoreboard du reset
    scoreboard.reset()

    dut.rst_n.value = 1  # Release reset
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_scoreboard_basic(dut):
    """Test basique avec scoreboard : compte 10 cycles."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    scoreboard = CounterScoreboard(width=8)

    # Reset
    await reset_dut(dut, scoreboard)

    # Enable et compte
    dut.enable.value = 1

    # Vérifie à chaque cycle !
    for cycle in range(10):
        await RisingEdge(dut.clk)
        scoreboard.tick(enable=True)  # Le modèle avance
        await FallingEdge(dut.clk)    # Attendre stabilité
        scoreboard.check(int(dut.count.value), log=dut._log)

    # Rapport final
    scoreboard.report(log=dut._log)


@cocotb.test()
async def test_scoreboard_enable_toggle(dut):
    """Test avec enable qui change : le scoreboard suit."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    scoreboard = CounterScoreboard(width=8)

    # Reset
    await reset_dut(dut, scoreboard)

    # Séquence : ON 5 cycles, OFF 3 cycles, ON 5 cycles
    sequence = [True] * 5 + [False] * 3 + [True] * 5

    for enable in sequence:
        dut.enable.value = int(enable)
        await RisingEdge(dut.clk)
        scoreboard.tick(enable=enable)
        await FallingEdge(dut.clk)
        scoreboard.check(int(dut.count.value), log=dut._log)

    # Rapport final
    result = scoreboard.report(log=dut._log)

    # Vérification : 5 + 5 = 10 incréments
    expected_final = 10
    assert int(dut.count.value) == expected_final, \
        f"Expected {expected_final}, got {dut.count.value}"


@cocotb.test()
async def test_scoreboard_wrap(dut):
    """Test du wrap-around avec scoreboard."""

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    scoreboard = CounterScoreboard(width=8)

    # Reset
    await reset_dut(dut, scoreboard)

    # Compte jusqu'au wrap (260 cycles)
    dut.enable.value = 1

    for cycle in range(260):
        await RisingEdge(dut.clk)
        scoreboard.tick(enable=True)

        # Vérifie seulement tous les 50 cycles (pour la vitesse)
        if cycle % 50 == 0 or cycle >= 254:
            await FallingEdge(dut.clk)
            scoreboard.check(int(dut.count.value), log=dut._log)
            dut._log.info(f"Cycle {cycle}: count = {dut.count.value}")

    # Rapport final (pas de vérification supplémentaire, déjà fait dans la boucle)
    scoreboard.report(log=dut._log)


@cocotb.test()
async def test_scoreboard_random_enable(dut):
    """Test avec enable aléatoire : le scoreboard gère tout."""

    import random

    # Setup
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    scoreboard = CounterScoreboard(width=8)

    # Reset
    await reset_dut(dut, scoreboard)

    # 50 cycles avec enable aléatoire
    for cycle in range(50):
        enable = random.choice([True, False])
        dut.enable.value = int(enable)
        await RisingEdge(dut.clk)
        scoreboard.tick(enable=enable)
        await FallingEdge(dut.clk)
        scoreboard.check(int(dut.count.value), log=dut._log)

    # Rapport
    result = scoreboard.report(log=dut._log)
    dut._log.info(f"Final count: {dut.count.value}")
