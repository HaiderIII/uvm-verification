"""
APB UVM-style Test with cocotb
==============================
Version simplifiée qui garde l'architecture UVM mais sans pyuvm.
Plus proche de ce que tu as fait dans les projets précédents.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import random

import sys
sys.path.insert(0, "/home/faiz/projects/uvm-verification/05_apb_uvm/tb_pyuvm")


# =============================================================================
# APB Transaction (équivalent de uvm_sequence_item)
# =============================================================================
class ApbTransaction:
    """Représente une transaction APB."""

    def __init__(self, write=False, addr=0, wdata=0):
        self.write = write
        self.addr = addr
        self.wdata = wdata
        self.rdata = 0
        self.slverr = False

    def randomize(self):
        """Randomise avec contraintes."""
        self.addr = random.choice([0x00, 0x04, 0x08, 0x0C])
        self.write = random.choice([True, False])
        self.wdata = random.randint(0, 0xFFFFFFFF)

    def __str__(self):
        op = "WRITE" if self.write else "READ"
        return f"{op} addr=0x{self.addr:02X} wdata=0x{self.wdata:08X} rdata=0x{self.rdata:08X} err={self.slverr}"


# =============================================================================
# APB Driver (équivalent de uvm_driver)
# =============================================================================
class ApbDriver:
    """Driver APB qui implémente le protocole maître."""

    def __init__(self, dut, log):
        self.dut = dut
        self.log = log

    async def drive(self, txn):
        """
        Exécute une transaction APB.
        Phase SETUP + Phase ACCESS
        """
        # Phase SETUP
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.paddr.value = txn.addr
        self.dut.pwrite.value = 1 if txn.write else 0
        self.dut.pwdata.value = txn.wdata

        await RisingEdge(self.dut.pclk)

        # Phase ACCESS
        self.dut.penable.value = 1

        await RisingEdge(self.dut.pclk)
        while self.dut.pready.value == 0:
            await RisingEdge(self.dut.pclk)

        # Capturer la réponse
        if not txn.write:
            txn.rdata = int(self.dut.prdata.value)
        txn.slverr = bool(self.dut.pslverr.value)

        # Retour à IDLE
        self.dut.psel.value = 0
        self.dut.penable.value = 0

        self.log.info(f"Driver: {txn}")

        return txn


# =============================================================================
# APB Monitor (équivalent de uvm_monitor)
# =============================================================================
class ApbMonitor:
    """Monitor APB qui observe le bus."""

    def __init__(self, dut, log, callback=None):
        self.dut = dut
        self.log = log
        self.callback = callback  # Fonction appelée pour chaque transaction
        self.running = False

    async def start(self):
        """Lance le monitoring en arrière-plan."""
        self.running = True

        while self.running:
            await RisingEdge(self.dut.pclk)

            # Détecter phase SETUP (PSEL=1, PENABLE=0)
            if self.dut.psel.value == 1 and self.dut.penable.value == 0:
                txn = ApbTransaction()
                txn.addr = int(self.dut.paddr.value)
                txn.write = bool(self.dut.pwrite.value)
                txn.wdata = int(self.dut.pwdata.value)

                # Attendre fin de phase ACCESS
                await RisingEdge(self.dut.pclk)
                while not (self.dut.psel.value == 1 and
                           self.dut.penable.value == 1 and
                           self.dut.pready.value == 1):
                    await RisingEdge(self.dut.pclk)

                txn.rdata = int(self.dut.prdata.value)
                txn.slverr = bool(self.dut.pslverr.value)

                self.log.info(f"Monitor: {txn}")

                # Appeler le callback (scoreboard)
                if self.callback:
                    self.callback(txn)

    def stop(self):
        self.running = False


# =============================================================================
# APB Scoreboard (équivalent de uvm_scoreboard)
# =============================================================================
class ApbScoreboard:
    """Scoreboard APB avec modèle de référence."""

    def __init__(self, log):
        self.log = log
        self.ref_regs = [0, 0, 0, 0]  # Modèle de référence
        self.num_writes = 0
        self.num_reads = 0
        self.num_errors = 0

    def check(self, txn):
        """Vérifie une transaction."""
        reg_idx = (txn.addr >> 2) & 0x3

        if txn.write:
            self.ref_regs[reg_idx] = txn.wdata
            self.num_writes += 1
            self.log.info(f"Scoreboard WRITE: reg[{reg_idx}] = 0x{txn.wdata:08X}")
        else:
            self.num_reads += 1
            expected = self.ref_regs[reg_idx]

            if txn.rdata != expected:
                self.log.error(f"READ MISMATCH: reg[{reg_idx}] expected=0x{expected:08X}, got=0x{txn.rdata:08X}")
                self.num_errors += 1
            else:
                self.log.info(f"Scoreboard READ OK: reg[{reg_idx}] = 0x{txn.rdata:08X}")

    def report(self):
        """Affiche le résumé."""
        self.log.info("=" * 40)
        self.log.info("       SCOREBOARD SUMMARY")
        self.log.info("=" * 40)
        self.log.info(f"  Writes:  {self.num_writes}")
        self.log.info(f"  Reads:   {self.num_reads}")
        self.log.info(f"  Errors:  {self.num_errors}")
        self.log.info("=" * 40)

        return self.num_errors == 0


# =============================================================================
# Test
# =============================================================================
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
async def test_apb_uvm_style(dut):
    """
    Test APB avec architecture style-UVM.

    Composants:
    - Driver: envoie les transactions
    - Monitor: observe le bus
    - Scoreboard: vérifie avec modèle de référence
    """
    # Démarrer l'horloge
    cocotb.start_soon(Clock(dut.pclk, 10, unit="ns").start())

    # Reset
    await reset_dut(dut)

    # Créer les composants UVM-style
    driver = ApbDriver(dut, dut._log)
    scoreboard = ApbScoreboard(dut._log)
    monitor = ApbMonitor(dut, dut._log, callback=scoreboard.check)

    # Lancer le monitor en arrière-plan
    cocotb.start_soon(monitor.start())

    # === Séquence de test ===
    dut._log.info("Starting APB test sequence...")

    # 1. Écrire dans tous les registres
    test_data = [0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0xAAAABBBB]
    for i, data in enumerate(test_data):
        txn = ApbTransaction(write=True, addr=i*4, wdata=data)
        await driver.drive(txn)

    # 2. Relire tous les registres
    for i in range(4):
        txn = ApbTransaction(write=False, addr=i*4)
        await driver.drive(txn)

    # 3. Quelques transactions aléatoires
    for _ in range(10):
        txn = ApbTransaction()
        txn.randomize()
        await driver.drive(txn)

    # Attendre un peu
    await ClockCycles(dut.pclk, 5)

    # Arrêter le monitor
    monitor.stop()

    # Afficher le rapport
    passed = scoreboard.report()

    assert passed, "Test FAILED - voir les erreurs ci-dessus"
    dut._log.info("*** TEST PASSED ***")
