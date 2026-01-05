"""
APB Monitor - pyuvm
===================
Observe le bus APB et capture les transactions.
Envoie les transactions au scoreboard via analysis_port.
"""

from pyuvm import uvm_monitor, uvm_analysis_port
from cocotb.triggers import RisingEdge
from apb_seq_item import ApbSeqItem


class ApbMonitor(uvm_monitor):
    """
    Monitor APB qui observe le bus.

    Détecte les transactions et les envoie au scoreboard.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None
        self.ap = None  # Analysis port

    def build_phase(self):
        super().build_phase()
        # Créer l'analysis port
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """
        Boucle principale du monitor.
        Observe le bus et capture les transactions.
        """
        # Récupérer le DUT au début de run_phase (après qu'il soit initialisé)
        import test_apb
        self.dut = test_apb.DUT

        # Attendre la fin du reset
        while self.dut.preset_n.value == 0:
            await RisingEdge(self.dut.pclk)

        while True:
            await RisingEdge(self.dut.pclk)

            # Détecter le début d'une transaction (phase SETUP)
            # PSEL=1 et PENABLE=0
            if self.dut.psel.value == 1 and self.dut.penable.value == 0:
                # Créer une nouvelle transaction
                txn = ApbSeqItem("mon_txn")

                # Capturer les informations de la phase SETUP
                txn.addr = int(self.dut.paddr.value)
                txn.write = bool(self.dut.pwrite.value)
                txn.wdata = int(self.dut.pwdata.value)

                # Attendre la fin de la phase ACCESS
                # Le transfert est complété quand PSEL=1, PENABLE=1, PREADY=1
                await RisingEdge(self.dut.pclk)  # Passage en ACCESS

                while not (self.dut.psel.value == 1 and
                           self.dut.penable.value == 1 and
                           self.dut.pready.value == 1):
                    await RisingEdge(self.dut.pclk)

                # Capturer les données de lecture et l'erreur
                txn.rdata = int(self.dut.prdata.value)
                txn.slverr = bool(self.dut.pslverr.value)

                # Envoyer la transaction au scoreboard
                self.ap.write(txn)

                self.logger.info(f"Observed: {txn}")
