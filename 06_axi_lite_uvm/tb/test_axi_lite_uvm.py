"""
AXI-Lite UVM-style Test
=======================
Testbench UVM-style pour AXI-Lite Slave.
Réutilise l'architecture apprise avec APB.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer
import random


# =============================================================================
# AXI-Lite Transaction (équivalent de uvm_sequence_item)
# =============================================================================
class AxiLiteTransaction:
    """
    Représente une transaction AXI-Lite.

    Différence avec APB:
    - APB: 1 phase SETUP + 1 phase ACCESS
    - AXI-Lite: Handshakes indépendants sur 5 canaux
    """

    # Réponses AXI
    RESP_OKAY = 0b00
    RESP_SLVERR = 0b10

    def __init__(self, write=False, addr=0, data=0, strb=0xF):
        self.write = write      # True=Write, False=Read
        self.addr = addr        # Adresse
        self.data = data        # Données (wdata ou rdata selon write)
        self.strb = strb        # Byte strobes (écriture seulement)
        self.resp = 0           # Réponse (OKAY, SLVERR)

    def randomize(self):
        """Randomise avec contraintes."""
        valid_addrs = [0x00, 0x04, 0x08, 0x0C]
        self.addr = random.choice(valid_addrs)
        self.write = random.choice([True, False])
        self.data = random.randint(0, 0xFFFFFFFF)
        self.strb = 0xF  # Tous les octets

    def __str__(self):
        op = "WRITE" if self.write else "READ"
        resp_str = "OKAY" if self.resp == self.RESP_OKAY else "SLVERR"
        return f"{op} addr=0x{self.addr:02X} data=0x{self.data:08X} resp={resp_str}"


# =============================================================================
# AXI-Lite Driver (équivalent de uvm_driver)
# =============================================================================
class AxiLiteDriver:
    """
    Driver AXI-Lite Master.

    Implémente les 5 canaux:
    - Write: AW + W → B
    - Read: AR → R
    """

    def __init__(self, dut, log):
        self.dut = dut
        self.log = log

    async def reset(self):
        """Initialise tous les signaux master."""
        # Write Address Channel
        self.dut.s_axi_awvalid.value = 0
        self.dut.s_axi_awaddr.value = 0
        # Write Data Channel
        self.dut.s_axi_wvalid.value = 0
        self.dut.s_axi_wdata.value = 0
        self.dut.s_axi_wstrb.value = 0
        # Write Response Channel
        self.dut.s_axi_bready.value = 1
        # Read Address Channel
        self.dut.s_axi_arvalid.value = 0
        self.dut.s_axi_araddr.value = 0
        # Read Data Channel
        self.dut.s_axi_rready.value = 1

    async def drive(self, txn):
        """Exécute une transaction AXI-Lite."""
        if txn.write:
            await self._write(txn)
        else:
            await self._read(txn)

        self.log.info(f"Driver: {txn}")
        return txn

    async def _write(self, txn):
        """
        Écriture AXI-Lite:
        1. Envoyer adresse sur AW (awvalid/awready)
        2. Envoyer données sur W (wvalid/wready)
        3. Recevoir réponse sur B (bvalid/bready)
        """
        # === Canal AW (Write Address) ===
        self.dut.s_axi_awaddr.value = txn.addr
        self.dut.s_axi_awvalid.value = 1

        # === Canal W (Write Data) ===
        self.dut.s_axi_wdata.value = txn.data
        self.dut.s_axi_wstrb.value = txn.strb
        self.dut.s_axi_wvalid.value = 1

        # Attendre les handshakes
        aw_done = False
        w_done = False

        while not (aw_done and w_done):
            await RisingEdge(self.dut.clk)

            if self.dut.s_axi_awready.value == 1 and not aw_done:
                aw_done = True
                self.dut.s_axi_awvalid.value = 0

            if self.dut.s_axi_wready.value == 1 and not w_done:
                w_done = True
                self.dut.s_axi_wvalid.value = 0

        # === Canal B (Write Response) ===
        while self.dut.s_axi_bvalid.value == 0:
            await RisingEdge(self.dut.clk)

        txn.resp = int(self.dut.s_axi_bresp.value)
        await RisingEdge(self.dut.clk)

    async def _read(self, txn):
        """
        Lecture AXI-Lite:
        1. Envoyer adresse sur AR (arvalid/arready)
        2. Recevoir données sur R (rvalid/rready)
        """
        # === Canal AR (Read Address) ===
        self.dut.s_axi_araddr.value = txn.addr
        self.dut.s_axi_arvalid.value = 1

        # Attendre handshake
        while self.dut.s_axi_arready.value == 0:
            await RisingEdge(self.dut.clk)

        await RisingEdge(self.dut.clk)
        self.dut.s_axi_arvalid.value = 0

        # === Canal R (Read Data) ===
        while self.dut.s_axi_rvalid.value == 0:
            await RisingEdge(self.dut.clk)

        txn.data = int(self.dut.s_axi_rdata.value)
        txn.resp = int(self.dut.s_axi_rresp.value)
        await RisingEdge(self.dut.clk)


# =============================================================================
# AXI-Lite Monitor (équivalent de uvm_monitor)
# =============================================================================
class AxiLiteMonitor:
    """
    Monitor AXI-Lite qui observe les 5 canaux.
    """

    def __init__(self, dut, log, callback=None):
        self.dut = dut
        self.log = log
        self.callback = callback
        self.running = False

    async def start(self):
        """Lance le monitoring en arrière-plan."""
        self.running = True

        # Lancer les monitors pour Write et Read en parallèle
        cocotb.start_soon(self._monitor_writes())
        cocotb.start_soon(self._monitor_reads())

    async def _monitor_writes(self):
        """Observe les écritures (AW + W + B)."""
        while self.running:
            await RisingEdge(self.dut.clk)

            # Détecter une écriture complète (bvalid & bready)
            if self.dut.s_axi_bvalid.value == 1 and self.dut.s_axi_bready.value == 1:
                txn = AxiLiteTransaction(write=True)
                txn.addr = int(self.dut.s_axi_awaddr.value)
                txn.data = int(self.dut.s_axi_wdata.value)
                txn.resp = int(self.dut.s_axi_bresp.value)

                self.log.info(f"Monitor: {txn}")
                if self.callback:
                    self.callback(txn)

    async def _monitor_reads(self):
        """Observe les lectures (AR + R)."""
        pending_addr = 0

        while self.running:
            await RisingEdge(self.dut.clk)

            # Capturer l'adresse de lecture
            if self.dut.s_axi_arvalid.value == 1 and self.dut.s_axi_arready.value == 1:
                pending_addr = int(self.dut.s_axi_araddr.value)

            # Détecter une lecture complète (rvalid & rready)
            if self.dut.s_axi_rvalid.value == 1 and self.dut.s_axi_rready.value == 1:
                txn = AxiLiteTransaction(write=False)
                txn.addr = pending_addr
                txn.data = int(self.dut.s_axi_rdata.value)
                txn.resp = int(self.dut.s_axi_rresp.value)

                self.log.info(f"Monitor: {txn}")
                if self.callback:
                    self.callback(txn)

    def stop(self):
        self.running = False


# =============================================================================
# AXI-Lite Scoreboard (équivalent de uvm_scoreboard)
# =============================================================================
class AxiLiteScoreboard:
    """Scoreboard AXI-Lite avec modèle de référence."""

    def __init__(self, log):
        self.log = log
        self.ref_regs = [0, 0, 0, 0]  # 4 registres
        self.num_writes = 0
        self.num_reads = 0
        self.num_errors = 0

    def check(self, txn):
        """Vérifie une transaction."""
        reg_idx = (txn.addr >> 2) & 0x3

        if txn.write:
            self.ref_regs[reg_idx] = txn.data
            self.num_writes += 1
            self.log.info(f"Scoreboard WRITE: reg[{reg_idx}] = 0x{txn.data:08X}")
        else:
            self.num_reads += 1
            expected = self.ref_regs[reg_idx]

            if txn.data != expected:
                self.log.error(f"READ MISMATCH: reg[{reg_idx}] expected=0x{expected:08X}, got=0x{txn.data:08X}")
                self.num_errors += 1
            else:
                self.log.info(f"Scoreboard READ OK: reg[{reg_idx}] = 0x{txn.data:08X}")

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
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_axi_lite_uvm_style(dut):
    """
    Test AXI-Lite avec architecture UVM-style.

    Même structure que le projet APB:
    - Driver
    - Monitor
    - Scoreboard
    """
    # Démarrer l'horloge
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Créer les composants
    driver = AxiLiteDriver(dut, dut._log)
    scoreboard = AxiLiteScoreboard(dut._log)
    monitor = AxiLiteMonitor(dut, dut._log, callback=scoreboard.check)

    # Reset
    await driver.reset()
    await reset_dut(dut)

    # Lancer le monitor
    await monitor.start()

    dut._log.info("Starting AXI-Lite UVM test...")

    # === Séquence de test ===

    # 1. Écrire dans tous les registres
    test_data = [0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0xAAAABBBB]
    for i, data in enumerate(test_data):
        txn = AxiLiteTransaction(write=True, addr=i*4, data=data)
        await driver.drive(txn)

    # 2. Relire tous les registres
    for i in range(4):
        txn = AxiLiteTransaction(write=False, addr=i*4)
        await driver.drive(txn)

    # 3. Transactions aléatoires
    for _ in range(10):
        txn = AxiLiteTransaction()
        txn.randomize()
        await driver.drive(txn)

    # Attendre
    await ClockCycles(dut.clk, 10)
    monitor.stop()

    # Rapport
    passed = scoreboard.report()
    assert passed, "Test FAILED"
    dut._log.info("*** TEST PASSED ***")
