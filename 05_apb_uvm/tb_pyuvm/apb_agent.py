"""
APB Agent - pyuvm
=================
Conteneur qui regroupe: Driver + Monitor + Sequencer
"""

from pyuvm import uvm_agent, uvm_sequencer, ConfigDB
from apb_driver import ApbDriver
from apb_monitor import ApbMonitor
from apb_seq_item import ApbSeqItem


class ApbAgent(uvm_agent):
    """
    Agent APB contenant driver, monitor et sequencer.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.driver = None
        self.monitor = None
        self.sequencer = None

    def build_phase(self):
        super().build_phase()

        # Le monitor est TOUJOURS créé
        self.monitor = ApbMonitor("monitor", self)

        # Le driver et sequencer sont créés seulement en mode ACTIVE
        if self.get_is_active():
            self.driver = ApbDriver("driver", self)
            self.sequencer = uvm_sequencer("sequencer", self)

    def connect_phase(self):
        super().connect_phase()

        # Connecter le driver au sequencer
        if self.get_is_active():
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
