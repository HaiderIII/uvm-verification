"""
Test RAL - Démonstration du Register Abstraction Layer
======================================================

Ce test montre les avantages du RAL:
1. Accès par nom de registre au lieu d'adresses
2. Accès aux champs individuels
3. Vérification miroir automatique

EXERCICE: Lis et comprends comment le RAL simplifie les tests.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

from tb.ral_model import ApbRegBlock
from tb.apb_adapter import ApbAdapter


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
async def test_ral_basic(dut):
    """
    Test 1: Utilisation basique du RAL

    Compare l'ancien style (adresses) vs le nouveau style (RAL).
    """
    # Démarrer l'horloge
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())

    # Reset
    await reset_dut(dut)

    # Créer le modèle RAL
    reg_model = ApbRegBlock("apb_regs")

    # Créer et connecter l'adapter
    adapter = ApbAdapter(dut, dut._log)
    reg_model.set_adapter(adapter)

    dut._log.info("=" * 50)
    dut._log.info("  TEST 1: RAL Basic Write/Read")
    dut._log.info("=" * 50)

    # =========================================================================
    # ANCIEN STYLE (sans RAL) - Commenté pour comparaison
    # =========================================================================
    # await adapter.write(0x00, 0xDEADBEEF)  # C'est quoi 0x00 ? Faut chercher...
    # await adapter.write(0x04, 0xCAFEBABE)  # Et 0x04 ?

    # =========================================================================
    # NOUVEAU STYLE (avec RAL) - Lisible !
    # =========================================================================
    dut._log.info("\n--- Écriture via RAL ---")

    # Écrire dans REG0 - Le nom est explicite !
    await reg_model.write_reg(reg_model.REG0, 0xDEADBEEF)

    # Écrire dans REG1
    await reg_model.write_reg(reg_model.REG1, 0xCAFEBABE)

    # Écrire dans REG2
    await reg_model.write_reg(reg_model.REG2, 0x12345678)

    # Écrire dans REG3
    await reg_model.write_reg(reg_model.REG3, 0xAAAABBBB)

    dut._log.info("\n--- Lecture et vérification via RAL ---")

    # Lire et vérifier REG0
    value = await reg_model.read_reg(reg_model.REG0)
    assert value == 0xDEADBEEF, f"REG0 mismatch: got 0x{value:08X}"
    dut._log.info(f"REG0 = 0x{value:08X} ✓")

    # Lire et vérifier REG1
    value = await reg_model.read_reg(reg_model.REG1)
    assert value == 0xCAFEBABE, f"REG1 mismatch: got 0x{value:08X}"
    dut._log.info(f"REG1 = 0x{value:08X} ✓")

    # Lire REG2
    value = await reg_model.read_reg(reg_model.REG2)
    assert value == 0x12345678, f"REG2 mismatch: got 0x{value:08X}"
    dut._log.info(f"REG2 = 0x{value:08X} ✓")

    # Lire REG3
    value = await reg_model.read_reg(reg_model.REG3)
    assert value == 0xAAAABBBB, f"REG3 mismatch: got 0x{value:08X}"
    dut._log.info(f"REG3 = 0x{value:08X} ✓")

    dut._log.info("\n*** TEST 1 PASSED ***")


@cocotb.test()
async def test_ral_fields(dut):
    """
    Test 2: Accès aux champs (fields)

    Montre comment manipuler des bits individuels.
    """
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await reset_dut(dut)

    reg_model = ApbRegBlock("apb_regs")
    adapter = ApbAdapter(dut, dut._log)
    reg_model.set_adapter(adapter)

    dut._log.info("=" * 50)
    dut._log.info("  TEST 2: RAL Field Access")
    dut._log.info("=" * 50)

    # Accéder au champ DATA de REG0
    reg_model.REG0.fields["DATA"].set(0x42)
    dut._log.info(f"Set REG0.DATA = 0x{reg_model.REG0.fields['DATA'].get():08X}")

    # Écrire le registre entier (avec la valeur du champ)
    await reg_model.write_reg(reg_model.REG0, reg_model.REG0.get_value())

    # Vérifier
    value = await reg_model.read_reg(reg_model.REG0)
    assert value == 0x42, f"Expected 0x42, got 0x{value:08X}"

    dut._log.info(f"REG0 = 0x{value:08X} ✓")
    dut._log.info("\n*** TEST 2 PASSED ***")


@cocotb.test()
async def test_ral_mirror(dut):
    """
    Test 3: Vérification miroir

    Le RAL garde une copie de ce que le DUT devrait contenir.
    mirror_check() vérifie que le DUT est synchronisé.
    """
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await reset_dut(dut)

    reg_model = ApbRegBlock("apb_regs")
    adapter = ApbAdapter(dut, dut._log)
    reg_model.set_adapter(adapter)

    dut._log.info("=" * 50)
    dut._log.info("  TEST 3: RAL Mirror Check")
    dut._log.info("=" * 50)

    # Écrire une valeur
    await reg_model.write_reg(reg_model.REG0, 0x11111111)
    await reg_model.write_reg(reg_model.REG1, 0x22222222)

    dut._log.info("\n--- Mirror Check ---")

    # Vérifier que le DUT contient la même valeur que le miroir
    await reg_model.mirror_check(reg_model.REG0)
    dut._log.info("REG0 mirror check: OK ✓")

    await reg_model.mirror_check(reg_model.REG1)
    dut._log.info("REG1 mirror check: OK ✓")

    dut._log.info("\n*** TEST 3 PASSED ***")


@cocotb.test()
async def test_ral_vs_direct(dut):
    """
    Test 4: Comparaison RAL vs accès direct

    Montre la différence de lisibilité.
    """
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await reset_dut(dut)

    reg_model = ApbRegBlock("apb_regs")
    adapter = ApbAdapter(dut, dut._log)
    reg_model.set_adapter(adapter)

    dut._log.info("=" * 50)
    dut._log.info("  TEST 4: RAL vs Direct Access")
    dut._log.info("=" * 50)

    # =========================================================================
    # Style DIRECT (difficile à maintenir)
    # =========================================================================
    dut._log.info("\n--- Style Direct (adresses magiques) ---")
    await adapter.write(0x00, 0xAAAA0000)  # Qu'est-ce que 0x00 ?
    await adapter.write(0x04, 0xBBBB0000)  # Et 0x04 ?

    # =========================================================================
    # Style RAL (auto-documenté)
    # =========================================================================
    dut._log.info("\n--- Style RAL (noms explicites) ---")
    await reg_model.write_reg(reg_model.REG2, 0xCCCC0000)  # Clair !
    await reg_model.write_reg(reg_model.REG3, 0xDDDD0000)  # Évident !

    # Vérification
    v0 = await adapter.read(0x00)
    v1 = await adapter.read(0x04)
    v2 = await reg_model.read_reg(reg_model.REG2)
    v3 = await reg_model.read_reg(reg_model.REG3)

    dut._log.info(f"\nRésultats:")
    dut._log.info(f"  REG0 = 0x{v0:08X}")
    dut._log.info(f"  REG1 = 0x{v1:08X}")
    dut._log.info(f"  REG2 = 0x{v2:08X}")
    dut._log.info(f"  REG3 = 0x{v3:08X}")

    assert v0 == 0xAAAA0000
    assert v1 == 0xBBBB0000
    assert v2 == 0xCCCC0000
    assert v3 == 0xDDDD0000

    dut._log.info("\n*** TEST 4 PASSED ***")
    dut._log.info("\n" + "=" * 50)
    dut._log.info("  ALL RAL TESTS PASSED!")
    dut._log.info("=" * 50)
