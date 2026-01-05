"""
APB Scoreboard - pyuvm
======================
Vérifie les transactions APB avec un modèle de référence.
"""

from pyuvm import uvm_subscriber


class ApbScoreboard(uvm_subscriber):
    """
    Scoreboard APB avec modèle de référence.

    Hérite de uvm_subscriber qui fournit automatiquement:
    - Un analysis_export
    - La méthode write() à implémenter
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)

        # Modèle de référence - 4 registres
        self.ref_regs = [0, 0, 0, 0]

        # Compteurs
        self.num_writes = 0
        self.num_reads = 0
        self.num_errors = 0

    def write(self, txn):
        """
        Callback appelée par le monitor via analysis_port.
        Vérifie chaque transaction.
        """
        # Calculer l'index du registre
        reg_idx = (txn.addr >> 2) & 0x3

        if txn.write:
            # -----------------------------------------------------------------
            # Vérification ÉCRITURE
            # -----------------------------------------------------------------
            # Mettre à jour le modèle de référence
            self.ref_regs[reg_idx] = txn.wdata
            self.num_writes += 1

            self.logger.info(f"WRITE: reg[{reg_idx}] = 0x{txn.wdata:08X}")

        else:
            # -----------------------------------------------------------------
            # Vérification LECTURE
            # -----------------------------------------------------------------
            self.num_reads += 1
            expected = self.ref_regs[reg_idx]

            if txn.rdata != expected:
                self.logger.error(
                    f"READ MISMATCH: reg[{reg_idx}] expected=0x{expected:08X}, got=0x{txn.rdata:08X}"
                )
                self.num_errors += 1
            else:
                self.logger.info(f"READ OK: reg[{reg_idx}] = 0x{txn.rdata:08X}")

    def report_phase(self):
        """Affiche le résumé final."""
        self.logger.info("=" * 40)
        self.logger.info("       SCOREBOARD SUMMARY")
        self.logger.info("=" * 40)
        self.logger.info(f"  Writes:  {self.num_writes}")
        self.logger.info(f"  Reads:   {self.num_reads}")
        self.logger.info(f"  Errors:  {self.num_errors}")
        self.logger.info("=" * 40)

        if self.num_errors == 0:
            self.logger.info("*** TEST PASSED ***")
        else:
            self.logger.error("*** TEST FAILED ***")
