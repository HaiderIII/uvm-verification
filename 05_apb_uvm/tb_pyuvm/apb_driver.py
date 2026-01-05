"""
APB Driver - pyuvm
==================
Convertit les transactions en signaux sur le bus APB.
Implémente le protocole APB (SETUP + ACCESS phases).
"""

from pyuvm import uvm_driver
from cocotb.triggers import RisingEdge


class ApbDriver(uvm_driver):
    """
    Driver APB qui implémente le protocole maître.

    Reçoit les transactions du sequencer et les convertit en signaux.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None

    def build_phase(self):
        super().build_phase()

    async def run_phase(self):
        """
        Boucle principale du driver.
        Équivalent de run_phase en SystemVerilog UVM.
        """
        # Récupérer le DUT au début de run_phase (après qu'il soit initialisé)
        import test_apb
        self.dut = test_apb.DUT

        # Attendre la fin du reset
        while self.dut.preset_n.value == 0:
            await RisingEdge(self.dut.pclk)

        await RisingEdge(self.dut.pclk)

        while True:
            # Récupérer la prochaine transaction du sequencer
            # Équivalent de: seq_item_port.get_next_item(req)
            txn = await self.seq_item_port.get_next_item()

            # Exécuter la transaction
            await self.drive_transaction(txn)

            # Signaler que la transaction est terminée
            # Équivalent de: seq_item_port.item_done()
            self.seq_item_port.item_done()

    async def drive_transaction(self, txn):
        """
        Implémente le protocole APB.

        Phase SETUP (1 cycle): PSEL=1, PENABLE=0
        Phase ACCESS (1+ cycles): PSEL=1, PENABLE=1, attente PREADY
        """
        # -----------------------------------------------------------------
        # Phase SETUP (1 cycle)
        # -----------------------------------------------------------------
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.paddr.value = txn.addr
        self.dut.pwrite.value = 1 if txn.write else 0
        self.dut.pwdata.value = txn.wdata

        await RisingEdge(self.dut.pclk)

        # -----------------------------------------------------------------
        # Phase ACCESS
        # -----------------------------------------------------------------
        self.dut.penable.value = 1

        # Attendre PREADY=1
        await RisingEdge(self.dut.pclk)
        while self.dut.pready.value == 0:
            await RisingEdge(self.dut.pclk)

        # Capturer les données de lecture et l'erreur
        if not txn.write:
            txn.rdata = int(self.dut.prdata.value)
        txn.slverr = bool(self.dut.pslverr.value)

        # -----------------------------------------------------------------
        # Retour à IDLE
        # -----------------------------------------------------------------
        self.dut.psel.value = 0
        self.dut.penable.value = 0

        self.logger.info(f"Drove: {txn}")
