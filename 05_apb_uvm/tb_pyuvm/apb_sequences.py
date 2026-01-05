"""
APB Sequences - pyuvm
=====================
Les séquences génèrent les transactions pour le driver.
"""

from pyuvm import uvm_sequence
from apb_seq_item import ApbSeqItem


class ApbBaseSeq(uvm_sequence):
    """Séquence de base - Une seule transaction aléatoire."""

    async def body(self):
        txn = ApbSeqItem("txn")
        txn.randomize()

        await self.start_item(txn)
        await self.finish_item(txn)


class ApbWriteReadSeq(uvm_sequence):
    """Séquence Write-Read - Écrit puis relit la même adresse."""

    def __init__(self, name="apb_write_read_seq"):
        super().__init__(name)
        self.addr = 0x00
        self.data = 0xDEADBEEF

    async def body(self):
        # Écriture
        write_txn = ApbSeqItem("write_txn")
        write_txn.write = True
        write_txn.addr = self.addr
        write_txn.wdata = self.data

        await self.start_item(write_txn)
        await self.finish_item(write_txn)

        # Lecture
        read_txn = ApbSeqItem("read_txn")
        read_txn.write = False
        read_txn.addr = self.addr

        await self.start_item(read_txn)
        await self.finish_item(read_txn)


class ApbFullTestSeq(uvm_sequence):
    """Séquence complète - Test tous les registres."""

    async def body(self):
        addrs = [0x00, 0x04, 0x08, 0x0C]
        test_data = [0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0xAAAABBBB]

        # Écrire tous les registres
        for i, addr in enumerate(addrs):
            txn = ApbSeqItem(f"write_{i}")
            txn.write = True
            txn.addr = addr
            txn.wdata = test_data[i]

            await self.start_item(txn)
            await self.finish_item(txn)

        # Relire tous les registres
        for i, addr in enumerate(addrs):
            txn = ApbSeqItem(f"read_{i}")
            txn.write = False
            txn.addr = addr

            await self.start_item(txn)
            await self.finish_item(txn)

        # Quelques transactions aléatoires
        for i in range(10):
            txn = ApbSeqItem(f"random_{i}")
            txn.randomize()

            await self.start_item(txn)
            await self.finish_item(txn)
