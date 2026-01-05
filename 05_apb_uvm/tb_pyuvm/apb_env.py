"""
APB Environment - pyuvm
=======================
Conteneur principal: Agent + Scoreboard
"""

from pyuvm import uvm_env
from apb_agent import ApbAgent
from apb_scoreboard import ApbScoreboard


class ApbEnv(uvm_env):
    """
    Environnement APB contenant l'agent et le scoreboard.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None

    def build_phase(self):
        super().build_phase()

        # Créer l'agent
        self.agent = ApbAgent("agent", self)

        # Créer le scoreboard
        self.scoreboard = ApbScoreboard("scoreboard", self)

    def connect_phase(self):
        super().connect_phase()

        # Connecter monitor -> scoreboard
        # uvm_subscriber a un analysis_export intégré
        self.agent.monitor.ap.connect(self.scoreboard.analysis_export)
