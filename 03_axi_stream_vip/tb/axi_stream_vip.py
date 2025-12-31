"""
AXI-Stream VIP (Verification IP)
================================

Composants:
- AXIStreamMaster : Envoie des paquets (source)
- AXIStreamSlave  : Reçoit des paquets (sink) avec back-pressure configurable
- AXIStreamMonitor: Observe et enregistre les transactions
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from collections import deque


class AXIStreamTransaction:
    """Représente une transaction AXI-Stream (un transfert)."""

    def __init__(self, data, last=False):
        self.data = data
        self.last = last

    def __repr__(self):
        return f"AXIStreamTransaction(data=0x{self.data:08X}, last={self.last})"


class AXIStreamPacket:
    """Représente un paquet AXI-Stream (plusieurs transactions terminées par TLAST)."""

    def __init__(self, data_list=None):
        self.data = data_list if data_list else []

    def append(self, data):
        self.data.append(data)

    def __repr__(self):
        hex_data = [f"0x{d:08X}" for d in self.data]
        return f"AXIStreamPacket({hex_data})"

    def __eq__(self, other):
        if isinstance(other, AXIStreamPacket):
            return self.data == other.data
        return False

    def __len__(self):
        return len(self.data)


# =============================================================================
# AXI-Stream Master (Source) - Envoie des données
# =============================================================================
class AXIStreamMaster:
    """
    AXI-Stream Master VIP.

    Envoie des paquets de données sur une interface AXI-Stream.
    """

    def __init__(self, dut, prefix, clk):
        """
        Args:
            dut: Le DUT
            prefix: Préfixe des signaux (ex: "s_axis")
            clk: Signal d'horloge
        """
        self.dut = dut
        self.clk = clk
        self.log = dut._log

        # Signaux AXI-Stream
        self.tdata = getattr(dut, f"{prefix}_tdata")
        self.tvalid = getattr(dut, f"{prefix}_tvalid")
        self.tready = getattr(dut, f"{prefix}_tready")
        self.tlast = getattr(dut, f"{prefix}_tlast")

    async def reset(self):
        """Remet les signaux à leur état initial."""
        self.tvalid.value = 0
        self.tdata.value = 0
        self.tlast.value = 0

    async def send_packet(self, packet):
        """
        Envoie un paquet complet.

        Args:
            packet: AXIStreamPacket ou liste de données
        """
        if isinstance(packet, list):
            packet = AXIStreamPacket(packet)

        for i, data in enumerate(packet.data):
            is_last = (i == len(packet.data) - 1)
            await self._send_beat(data, is_last)

    async def _send_beat(self, data, last=False):
        """
        Envoie un seul beat (mot) de données.

        Args:
            data: Donnée à envoyer
            last: True si c'est le dernier mot du paquet
        """
        # Positionner les signaux
        self.tdata.value = data
        self.tlast.value = 1 if last else 0
        self.tvalid.value = 1

        # Attendre le handshake
        while True:
            await RisingEdge(self.clk)
            if int(self.tready.value) == 1:
                break

        # Transaction complète, remettre à zéro
        self.tvalid.value = 0
        self.tlast.value = 0


# =============================================================================
# AXI-Stream Slave (Sink) - Reçoit des données
# =============================================================================
class AXIStreamSlave:
    """
    AXI-Stream Slave VIP.

    Reçoit des paquets de données. Peut simuler un sink lent (back-pressure).
    """

    def __init__(self, dut, prefix, clk, ready_latency=0):
        """
        Args:
            dut: Le DUT
            prefix: Préfixe des signaux (ex: "m_axis")
            clk: Signal d'horloge
            ready_latency: Nombre de cycles avant de mettre TREADY=1 (simule back-pressure)
        """
        self.dut = dut
        self.clk = clk
        self.log = dut._log
        self.ready_latency = ready_latency

        # Signaux AXI-Stream
        self.tdata = getattr(dut, f"{prefix}_tdata")
        self.tvalid = getattr(dut, f"{prefix}_tvalid")
        self.tready = getattr(dut, f"{prefix}_tready")
        self.tlast = getattr(dut, f"{prefix}_tlast")

        # Stockage des paquets reçus
        self.received_packets = []
        self._current_packet = AXIStreamPacket()

        # Contrôle
        self._running = False

    async def reset(self):
        """Remet les signaux à leur état initial."""
        self.tready.value = 0
        self.received_packets = []
        self._current_packet = AXIStreamPacket()

    def start(self):
        """Démarre la réception en background."""
        self._running = True
        cocotb.start_soon(self._receive_loop())

    def stop(self):
        """Arrête la réception."""
        self._running = False

    async def _receive_loop(self):
        """Boucle de réception des données."""
        while self._running:
            # Simuler la latence (back-pressure)
            for _ in range(self.ready_latency):
                self.tready.value = 0
                await RisingEdge(self.clk)

            # Prêt à recevoir
            self.tready.value = 1
            await RisingEdge(self.clk)

            # Vérifier s'il y a un transfert
            if int(self.tvalid.value) == 1:
                data = int(self.tdata.value)
                last = int(self.tlast.value)

                self._current_packet.append(data)

                if last:
                    self.received_packets.append(self._current_packet)
                    self.log.info(f"Slave received packet: {self._current_packet}")
                    self._current_packet = AXIStreamPacket()

    async def receive_packet(self, timeout_cycles=100):
        """
        Attend et reçoit un paquet complet.

        Args:
            timeout_cycles: Nombre max de cycles à attendre

        Returns:
            AXIStreamPacket reçu ou None si timeout
        """
        packet = AXIStreamPacket()

        for _ in range(timeout_cycles):
            # Prêt à recevoir
            self.tready.value = 1
            await RisingEdge(self.clk)

            if int(self.tvalid.value) == 1:
                data = int(self.tdata.value)
                last = int(self.tlast.value)

                packet.append(data)

                if last:
                    self.tready.value = 0
                    return packet

        self.tready.value = 0
        return None


# =============================================================================
# AXI-Stream Monitor - Observe les transactions
# =============================================================================
class AXIStreamMonitor:
    """
    AXI-Stream Monitor.

    Observe passivement une interface AXI-Stream et enregistre les transactions.
    """

    def __init__(self, dut, prefix, clk, name="Monitor"):
        """
        Args:
            dut: Le DUT
            prefix: Préfixe des signaux (ex: "s_axis" ou "m_axis")
            clk: Signal d'horloge
            name: Nom du monitor (pour les logs)
        """
        self.dut = dut
        self.clk = clk
        self.log = dut._log
        self.name = name

        # Signaux AXI-Stream
        self.tdata = getattr(dut, f"{prefix}_tdata")
        self.tvalid = getattr(dut, f"{prefix}_tvalid")
        self.tready = getattr(dut, f"{prefix}_tready")
        self.tlast = getattr(dut, f"{prefix}_tlast")

        # Stockage
        self.transactions = []
        self.packets = []
        self._current_packet = AXIStreamPacket()
        

        # Contrôle
        self._running = False

        #count des transactions
        self.transaction_count = 0


    def start(self):
        """Démarre le monitoring."""
        self._running = True
        cocotb.start_soon(self._monitor_loop())

    def stop(self):
        """Arrête le monitoring."""
        self._running = False
        self.log.info(f"{self.name}: Stopped monitoring. Total transactions: {self.transaction_count}")


    async def _monitor_loop(self):
        """Boucle de monitoring."""
        while self._running:
            await RisingEdge(self.clk)

            # Vérifier s'il y a un transfert (handshake complet)
            if int(self.tvalid.value) == 1 and int(self.tready.value) == 1:
                data = int(self.tdata.value)
                last = int(self.tlast.value)
                self.transaction_count += 1

                # Enregistrer la transaction
                txn = AXIStreamTransaction(data, last)
                self.transactions.append(txn)

                # Construire le paquet
                self._current_packet.append(data)

                if last:
                    self.packets.append(self._current_packet)
                    self.log.info(f"{self.name}: Captured packet {self._current_packet}")
                    self._current_packet = AXIStreamPacket()


# =============================================================================
# Scoreboard - Compare entrée et sortie
# =============================================================================
class AXIStreamScoreboard:
    """
    Scoreboard pour vérifier que la FIFO transmet correctement les données.
    """

    def __init__(self, log):
        self.log = log
        self.expected_packets = deque()
        self.errors = 0
        self.matches = 0

    def add_expected(self, packet):
        """Ajoute un paquet attendu."""
        if isinstance(packet, list):
            packet = AXIStreamPacket(packet)
        self.expected_packets.append(packet)

    def check_received(self, packet):
        """Vérifie un paquet reçu contre les attendus."""
        if not self.expected_packets:
            self.log.error(f"Scoreboard: Unexpected packet received: {packet}")
            self.errors += 1
            return False

        expected = self.expected_packets.popleft()
        if packet == expected:
            self.log.info(f"Scoreboard: MATCH - {packet}")
            self.matches += 1
            return True
        else:
            self.log.error(f"Scoreboard: MISMATCH!")
            self.log.error(f"  Expected: {expected}")
            self.log.error(f"  Received: {packet}")
            self.errors += 1
            return False

    def report(self):
        """Affiche le rapport final."""
        self.log.info(f"Scoreboard Report: {self.matches} matches, {self.errors} errors")
        if self.expected_packets:
            self.log.warning(f"  {len(self.expected_packets)} packets never received!")
        return self.errors == 0 and len(self.expected_packets) == 0
