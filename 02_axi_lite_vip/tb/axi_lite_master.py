"""
AXI-Lite Master VIP
===================

Ce module implémente un Master AXI-Lite en Cocotb.
Il peut :
- Écrire à une adresse (write)
- Lire une adresse (read)
- Gérer le handshake VALID/READY

C'est l'équivalent d'un "Driver" en terminologie UVM.
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer


class AXILiteMaster:
    """
    AXI-Lite Master Driver.

    Usage:
        master = AXILiteMaster(dut, "s_axi")
        await master.write(addr=0x00, data=0x12345678)
        value = await master.read(addr=0x00)
    """

    def __init__(self, dut, prefix="s_axi"):
        """
        Args:
            dut: Le DUT Cocotb
            prefix: Préfixe des signaux AXI (ex: "s_axi" pour s_axi_awaddr)
        """
        self.dut = dut
        self.prefix = prefix
        self.log = dut._log

        # Récupérer les signaux via le préfixe
        # Write Address Channel
        self.awaddr = getattr(dut, f"{prefix}_awaddr")
        self.awvalid = getattr(dut, f"{prefix}_awvalid")
        self.awready = getattr(dut, f"{prefix}_awready")

        # Write Data Channel
        self.wdata = getattr(dut, f"{prefix}_wdata")
        self.wstrb = getattr(dut, f"{prefix}_wstrb")
        self.wvalid = getattr(dut, f"{prefix}_wvalid")
        self.wready = getattr(dut, f"{prefix}_wready")

        # Write Response Channel
        self.bresp = getattr(dut, f"{prefix}_bresp")
        self.bvalid = getattr(dut, f"{prefix}_bvalid")
        self.bready = getattr(dut, f"{prefix}_bready")

        # Read Address Channel
        self.araddr = getattr(dut, f"{prefix}_araddr")
        self.arvalid = getattr(dut, f"{prefix}_arvalid")
        self.arready = getattr(dut, f"{prefix}_arready")

        # Read Data Channel
        self.rdata = getattr(dut, f"{prefix}_rdata")
        self.rresp = getattr(dut, f"{prefix}_rresp")
        self.rvalid = getattr(dut, f"{prefix}_rvalid")
        self.rready = getattr(dut, f"{prefix}_rready")

    async def init(self):
        """Initialise tous les signaux du Master."""
        # Write Address Channel
        self.awaddr.value = 0
        self.awvalid.value = 0

        # Write Data Channel
        self.wdata.value = 0
        self.wstrb.value = 0xF  # Tous les bytes actifs par défaut
        self.wvalid.value = 0

        # Write Response Channel
        self.bready.value = 1  # Toujours prêt à recevoir la réponse

        # Read Address Channel
        self.araddr.value = 0
        self.arvalid.value = 0

        # Read Data Channel
        self.rready.value = 1  # Toujours prêt à recevoir les données

    async def write(self, addr: int, data: int, strb: int = 0xF) -> int:
        """
        Effectue une transaction d'écriture AXI-Lite.

        Args:
            addr: Adresse d'écriture
            data: Données à écrire (32 bits)
            strb: Byte strobes (défaut: 0xF = tous les bytes)

        Returns:
            Code de réponse (0 = OKAY, 2 = SLVERR)
        """
        clk = self.dut.clk

        # Attendre un front montant pour synchroniser
        await RisingEdge(clk)

        # Envoyer adresse et données en parallèle
        self.awaddr.value = addr
        self.awvalid.value = 1
        self.wdata.value = data
        self.wstrb.value = strb
        self.wvalid.value = 1

        # Attendre que l'adresse ET les données soient acceptées
        aw_done = False
        w_done = False

        while not (aw_done and w_done):
            await RisingEdge(clk)

            # Check AW handshake
            if not aw_done and int(self.awready.value) == 1:
                aw_done = True

            # Check W handshake
            if not w_done and int(self.wready.value) == 1:
                w_done = True

        # Désactiver les signaux valid
        self.awvalid.value = 0
        self.wvalid.value = 0

        # Attendre la réponse (B channel)
        while True:
            await RisingEdge(clk)
            if int(self.bvalid.value) == 1:
                break

        response = int(self.bresp.value)

        self.log.debug(f"WRITE addr=0x{addr:02X} data=0x{data:08X} resp={response}")

        return response

    async def read(self, addr: int) -> tuple:
        """
        Effectue une transaction de lecture AXI-Lite.

        Args:
            addr: Adresse de lecture

        Returns:
            tuple (data, response) où:
                - data: Données lues (32 bits)
                - response: Code de réponse (0 = OKAY)
        """
        clk = self.dut.clk

        # Attendre un front montant pour synchroniser
        await RisingEdge(clk)

        # Envoyer l'adresse (AR channel)
        self.araddr.value = addr
        self.arvalid.value = 1

        # Attendre que l'adresse soit acceptée
        while True:
            await RisingEdge(clk)
            if int(self.arready.value) == 1:
                break

        self.arvalid.value = 0

        # Attendre les données (R channel)
        while True:
            await RisingEdge(clk)
            if int(self.rvalid.value) == 1:
                break

        data = int(self.rdata.value)
        response = int(self.rresp.value)

        self.log.debug(f"READ addr=0x{addr:02X} data=0x{data:08X} resp={response}")

        return (data, response)


class AXILiteMonitor:
    """
    AXI-Lite Monitor - Observe les transactions sans interférer.

    Usage:
        monitor = AXILiteMonitor(dut, "s_axi")
        monitor.start()
        # ... run tests ...
        transactions = monitor.get_transactions()
    """

    def __init__(self, dut, prefix="s_axi"):
        self.dut = dut
        self.prefix = prefix
        self.log = dut._log
        self.transactions = []
        self._running = False

        # Signaux à observer
        self.awaddr = getattr(dut, f"{prefix}_awaddr")
        self.awvalid = getattr(dut, f"{prefix}_awvalid")
        self.awready = getattr(dut, f"{prefix}_awready")
        self.wdata = getattr(dut, f"{prefix}_wdata")
        self.wvalid = getattr(dut, f"{prefix}_wvalid")
        self.wready = getattr(dut, f"{prefix}_wready")
        self.bresp = getattr(dut, f"{prefix}_bresp")
        self.bvalid = getattr(dut, f"{prefix}_bvalid")
        self.bready = getattr(dut, f"{prefix}_bready")
        self.araddr = getattr(dut, f"{prefix}_araddr")
        self.arvalid = getattr(dut, f"{prefix}_arvalid")
        self.arready = getattr(dut, f"{prefix}_arready")
        self.rdata = getattr(dut, f"{prefix}_rdata")
        self.rresp = getattr(dut, f"{prefix}_rresp")
        self.rvalid = getattr(dut, f"{prefix}_rvalid")
        self.rready = getattr(dut, f"{prefix}_rready")

    def start(self):
        """Démarre le monitoring en background."""
        self._running = True
        cocotb.start_soon(self._monitor_writes())
        cocotb.start_soon(self._monitor_reads())

    def stop(self):
        """Arrête le monitoring."""
        self._running = False

    async def _monitor_writes(self):
        """Observe les transactions d'écriture."""
        while self._running:
            await RisingEdge(self.dut.clk)
            if self.bvalid.value == 1 and self.bready.value == 1:
                txn = {
                    "type": "WRITE",
                    "addr": int(self.awaddr.value),
                    "data": int(self.wdata.value),
                    "resp": int(self.bresp.value)
                }
                self.transactions.append(txn)
                self.log.info(f"Monitor: WRITE addr=0x{txn['addr']:02X} data=0x{txn['data']:08X}")

    async def _monitor_reads(self):
        """Observe les transactions de lecture."""
        while self._running:
            await RisingEdge(self.dut.clk)
            if self.rvalid.value == 1 and self.rready.value == 1:
                txn = {
                    "type": "READ",
                    "addr": int(self.araddr.value),
                    "data": int(self.rdata.value),
                    "resp": int(self.rresp.value)
                }
                self.transactions.append(txn)
                self.log.info(f"Monitor: READ addr=0x{txn['addr']:02X} data=0x{txn['data']:08X}")

    def get_transactions(self):
        """Retourne la liste des transactions observées."""
        return self.transactions

    def clear(self):
        """Efface l'historique des transactions."""
        self.transactions = []
