"""
APB Adapter - Traduit les opérations RAL en transactions APB
============================================================

L'adapter est le pont entre le RAL et le bus physique.
"""

from cocotb.triggers import RisingEdge


class ApbAdapter:
    """
    Adaptateur RAL → APB.

    Traduit les write/read du RAL en transactions sur le bus APB.

    TODO 6: Comprends comment l'adapter utilise le driver existant
    """

    def __init__(self, dut, log):
        self.dut = dut
        self.log = log

    async def write(self, address, data):
        """
        Effectue une écriture APB.

        Protocol APB:
        1. SETUP phase: psel=1, pwrite=1, paddr, pwdata
        2. ACCESS phase: penable=1, attendre pready

        TODO 7: Complète le protocole APB write
        """
        self.log.info(f"APB Adapter: WRITE addr=0x{address:02X} data=0x{data:08X}")

        # Phase SETUP
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.pwrite.value = 1
        self.dut.paddr.value = address
        self.dut.pwdata.value = data

        await RisingEdge(self.dut.pclk)

        # Phase ACCESS
        self.dut.penable.value = 1

        # TODO: Attendre pready
        await RisingEdge(self.dut.pclk)
        while self.dut.pready.value == 0:
            await RisingEdge(self.dut.pclk)

        # Fin de transaction
        self.dut.psel.value = 0
        self.dut.penable.value = 0

    async def read(self, address):
        """
        Effectue une lecture APB.

        TODO 8: Complète le protocole APB read
        (similaire à write, mais pwrite=0 et on lit prdata)
        """
        self.log.info(f"APB Adapter: READ addr=0x{address:02X}")

        # Phase SETUP
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.pwrite.value = 0  # Lecture !
        self.dut.paddr.value = address

        await RisingEdge(self.dut.pclk)

        # Phase ACCESS
        self.dut.penable.value = 1

        # TODO: Attendre pready
        await RisingEdge(self.dut.pclk)
        while self.dut.pready.value == 0:
            await RisingEdge(self.dut.pclk)

        # Lire les données
        data = int(self.dut.prdata.value)

        # Fin de transaction
        self.dut.psel.value = 0
        self.dut.penable.value = 0

        self.log.info(f"APB Adapter: READ returned 0x{data:08X}")
        return data
