"""
APB Cocotb Test Entry Point
===========================
Fichier principal pour lancer les tests avec cocotb + pyuvm.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from pyuvm import uvm_root

import sys
sys.path.insert(0, "/home/faiz/projects/uvm-verification/05_apb_uvm/tb_pyuvm")

# Variable globale pour le DUT (simplifié)
DUT = None


async def reset_dut(dut):
    """Reset le DUT."""
    dut.preset_n.value = 0
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0
    dut.paddr.value = 0
    dut.pwdata.value = 0

    await ClockCycles(dut.pclk, 5)
    dut.preset_n.value = 1
    await ClockCycles(dut.pclk, 2)


@cocotb.test()
async def test_apb_uvm(dut):
    """
    Test APB avec pyuvm.

    Ce test utilise l'architecture UVM complète:
    - Environnement avec Agent et Scoreboard
    - Séquences pour générer les transactions
    - Driver pour convertir les transactions en signaux
    - Monitor pour observer le bus
    """
    global DUT
    DUT = dut

    # Démarrer l'horloge (100 MHz)
    cocotb.start_soon(Clock(dut.pclk, 10, unit="ns").start())

    # Reset
    await reset_dut(dut)

    # Importer et lancer le test
    from apb_test import ApbBaseTest
    await uvm_root().run_test(ApbBaseTest)
