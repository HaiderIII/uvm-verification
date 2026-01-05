"""
APB Test - pyuvm
================
Point d'entrée du testbench UVM.
"""

from pyuvm import uvm_test, ConfigDB
from apb_env import ApbEnv
from apb_sequences import ApbFullTestSeq


class ApbBaseTest(uvm_test):
    """
    Test de base APB.

    Crée l'environnement et lance la séquence.
    """

    def __init__(self, name="apb_base_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        # Créer l'environnement
        self.env = ApbEnv("env", self)

    async def run_phase(self):
        self.raise_objection()

        # Créer et lancer la séquence
        seq = ApbFullTestSeq("seq")
        await seq.start(self.env.agent.sequencer)

        self.drop_objection()
