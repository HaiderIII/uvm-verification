"""
APB Sequence Item (Transaction) - pyuvm
========================================
Équivalent de uvm_sequence_item en SystemVerilog
"""

from pyuvm import uvm_sequence_item
import random


class ApbSeqItem(uvm_sequence_item):
    """
    Représente une transaction APB (lecture ou écriture).

    Attributs:
        write: bool - True=Write, False=Read
        addr: int - Adresse (0x00, 0x04, 0x08, 0x0C)
        wdata: int - Données à écrire
        rdata: int - Données lues (rempli après lecture)
        slverr: bool - Erreur slave
    """

    def __init__(self, name="apb_seq_item"):
        super().__init__(name)
        self.write = False
        self.addr = 0
        self.wdata = 0
        self.rdata = 0
        self.slverr = False

    def randomize(self):
        """
        Randomise les champs avec contraintes.
        Équivalent des constraints SystemVerilog.
        """
        # Contrainte: adresse alignée sur 4 octets et dans la plage valide
        valid_addrs = [0x00, 0x04, 0x08, 0x0C]
        self.addr = random.choice(valid_addrs)

        # Direction aléatoire
        self.write = random.choice([True, False])

        # Données aléatoires
        self.wdata = random.randint(0, 0xFFFFFFFF)

        return True

    def __str__(self):
        """Équivalent de convert2string() en SystemVerilog."""
        op = "WRITE" if self.write else "READ"
        return f"{op} addr=0x{self.addr:02X} wdata=0x{self.wdata:08X} rdata=0x{self.rdata:08X} err={self.slverr}"

    def __eq__(self, other):
        """Pour comparaison dans le scoreboard."""
        if not isinstance(other, ApbSeqItem):
            return False
        return (self.write == other.write and
                self.addr == other.addr and
                self.wdata == other.wdata)

    def copy(self):
        """Crée une copie de la transaction."""
        item = ApbSeqItem(self.get_name())
        item.write = self.write
        item.addr = self.addr
        item.wdata = self.wdata
        item.rdata = self.rdata
        item.slverr = self.slverr
        return item
