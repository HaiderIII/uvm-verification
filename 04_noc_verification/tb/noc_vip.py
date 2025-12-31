"""
NoC VIP (Verification IP)
=========================

Composants:
- NoCPacket       : Représentation d'un paquet NoC
- NoCDriver       : Injecte des paquets dans le routeur
- NoCMonitor      : Observe les paquets sur un port
- NoCScoreboard   : Vérifie le routage correct
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles


# =============================================================================
# Constantes (doivent correspondre au RTL)
# =============================================================================
PACKET_WIDTH = 64

# Positions des champs
TYPE_MSB, TYPE_LSB = 63, 60
SRC_X_MSB, SRC_X_LSB = 59, 56
SRC_Y_MSB, SRC_Y_LSB = 55, 52
DST_X_MSB, DST_X_LSB = 51, 48
DST_Y_MSB, DST_Y_LSB = 47, 44
PAYLOAD_MSB, PAYLOAD_LSB = 43, 0

# Types de paquets
PKT_READ_REQ  = 0b0001
PKT_WRITE_REQ = 0b0010
PKT_RESPONSE  = 0b0100
PKT_ACK       = 0b1000

# Directions
DIR_LOCAL = 0
DIR_NORTH = 1
DIR_SOUTH = 2
DIR_EAST  = 3
DIR_WEST  = 4


# =============================================================================
# Classe NoCPacket
# =============================================================================
class NoCPacket:
    """Représentation d'un paquet NoC."""

    def __init__(self, pkt_type=PKT_WRITE_REQ, src_x=0, src_y=0, dst_x=0, dst_y=0, payload=0):
        self.pkt_type = pkt_type
        self.src_x = src_x
        self.src_y = src_y
        self.dst_x = dst_x
        self.dst_y = dst_y
        self.payload = payload

    def to_bits(self):
        """Convertit le paquet en valeur 64 bits."""
        value = 0
        value |= (self.pkt_type & 0xF) << TYPE_LSB
        value |= (self.src_x & 0xF) << SRC_X_LSB
        value |= (self.src_y & 0xF) << SRC_Y_LSB
        value |= (self.dst_x & 0xF) << DST_X_LSB
        value |= (self.dst_y & 0xF) << DST_Y_LSB
        value |= (self.payload & 0xFFFFFFFFFFF)  # 44 bits
        return value

    @classmethod
    def from_bits(cls, value):
        """Crée un paquet à partir d'une valeur 64 bits."""
        pkt = cls()
        pkt.pkt_type = (value >> TYPE_LSB) & 0xF
        pkt.src_x = (value >> SRC_X_LSB) & 0xF
        pkt.src_y = (value >> SRC_Y_LSB) & 0xF
        pkt.dst_x = (value >> DST_X_LSB) & 0xF
        pkt.dst_y = (value >> DST_Y_LSB) & 0xF
        pkt.payload = value & 0xFFFFFFFFFFF
        return pkt

    def __repr__(self):
        type_names = {PKT_READ_REQ: "READ", PKT_WRITE_REQ: "WRITE",
                      PKT_RESPONSE: "RESP", PKT_ACK: "ACK"}
        type_str = type_names.get(self.pkt_type, f"0x{self.pkt_type:X}")
        return (f"NoCPacket(type={type_str}, src=({self.src_x},{self.src_y}), "
                f"dst=({self.dst_x},{self.dst_y}), payload=0x{self.payload:X})")

    def __eq__(self, other):
        if not isinstance(other, NoCPacket):
            return False
        return (self.pkt_type == other.pkt_type and
                self.src_x == other.src_x and self.src_y == other.src_y and
                self.dst_x == other.dst_x and self.dst_y == other.dst_y and
                self.payload == other.payload)


# =============================================================================
# NoCDriver - Injecte des paquets
# =============================================================================
class NoCDriver:
    """
    Driver pour injecter des paquets dans un port du routeur.
    Utilise l'interface AXI-Stream.
    """

    def __init__(self, dut, prefix, clk, name="Driver"):
        """
        Args:
            dut: Le DUT
            prefix: Préfixe des signaux (ex: "local_in")
            clk: Signal d'horloge
            name: Nom pour les logs
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

    async def reset(self):
        """Initialise les signaux."""
        self.tvalid.value = 0
        self.tdata.value = 0
        self.tlast.value = 0

    async def send(self, packet):
        """
        Envoie un paquet NoC.

        Args:
            packet: NoCPacket à envoyer
        """
        # Positionner les signaux
        self.tdata.value = packet.to_bits()
        self.tlast.value = 1  # Un paquet NoC = 1 flit pour simplifier
        self.tvalid.value = 1

        # Attendre le handshake
        while True:
            await RisingEdge(self.clk)
            if int(self.tready.value) == 1:
                break

        self.log.info(f"{self.name}: Sent {packet}")

        # Remettre à zéro
        self.tvalid.value = 0
        self.tlast.value = 0


# =============================================================================
# NoCMonitor - Observe les paquets
# =============================================================================
class NoCMonitor:
    """
    Monitor pour observer les paquets sur un port de sortie.
    """

    def __init__(self, dut, prefix, clk, name="Monitor"):
        """
        Args:
            dut: Le DUT
            prefix: Préfixe des signaux (ex: "local_out")
            clk: Signal d'horloge
            name: Nom pour les logs
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
        self.received_packets = []
        self.transaction_count = 0

        # Contrôle
        self._running = False

    def start(self):
        """Démarre le monitoring."""
        self._running = True
        cocotb.start_soon(self._monitor_loop())

    def stop(self):
        """Arrête le monitoring."""
        self._running = False
        self.log.info(f"{self.name}: Stopped. {self.transaction_count} packets captured.")

    async def _monitor_loop(self):
        """Boucle de monitoring."""
        while self._running:
            await RisingEdge(self.clk)

            # Vérifier le handshake
            if int(self.tvalid.value) == 1 and int(self.tready.value) == 1:
                data = int(self.tdata.value)
                packet = NoCPacket.from_bits(data)

                self.received_packets.append(packet)
                self.transaction_count += 1

                self.log.info(f"{self.name}: Received {packet}")


# =============================================================================
# NoCReceiver - Reçoit les paquets (met TREADY à 1)
# =============================================================================
class NoCReceiver:
    """
    Receiver simple qui accepte tous les paquets (TREADY = 1).
    """

    def __init__(self, dut, prefix, clk, name="Receiver"):
        self.dut = dut
        self.clk = clk
        self.name = name

        self.tready = getattr(dut, f"{prefix}_tready")

    async def start(self):
        """Active la réception."""
        self.tready.value = 1

    async def stop(self):
        """Désactive la réception."""
        self.tready.value = 0


# =============================================================================
# NoCScoreboard - Vérifie le routage
# =============================================================================
class NoCScoreboard:
    """
    Scoreboard pour vérifier que les paquets arrivent au bon port.
    """

    def __init__(self, log, router_x, router_y):
        """
        Args:
            log: Logger
            router_x: Position X du routeur
            router_y: Position Y du routeur
        """
        self.log = log
        self.router_x = router_x
        self.router_y = router_y
        self.errors = 0
        self.matches = 0

    def compute_expected_direction(self, packet):
        """Calcule la direction attendue selon l'algorithme XY."""
        if packet.dst_x > self.router_x:
            return DIR_EAST
        elif packet.dst_x < self.router_x:
            return DIR_WEST
        elif packet.dst_y > self.router_y:
            return DIR_SOUTH
        elif packet.dst_y < self.router_y:
            return DIR_NORTH
        else:
            return DIR_LOCAL

    def direction_name(self, direction):
        """Retourne le nom de la direction."""
        names = {DIR_LOCAL: "LOCAL", DIR_NORTH: "NORTH", DIR_SOUTH: "SOUTH",
                 DIR_EAST: "EAST", DIR_WEST: "WEST"}
        return names.get(direction, "UNKNOWN")

    def check_packet(self, packet, actual_port):
        """
        Vérifie qu'un paquet a été routé vers le bon port.

        Args:
            packet: Le paquet reçu
            actual_port: Le port sur lequel il a été reçu (DIR_*)
        """
        expected_port = self.compute_expected_direction(packet)

        if actual_port == expected_port:
            self.log.info(f"Scoreboard: MATCH - {packet} → {self.direction_name(actual_port)}")
            self.matches += 1
            return True
        else:
            self.log.error(f"Scoreboard: MISMATCH!")
            self.log.error(f"  Packet: {packet}")
            self.log.error(f"  Expected: {self.direction_name(expected_port)}")
            self.log.error(f"  Actual: {self.direction_name(actual_port)}")
            self.errors += 1
            return False

    def report(self):
        """Affiche le rapport final."""
        self.log.info(f"Scoreboard Report: {self.matches} matches, {self.errors} errors")
        return self.errors == 0
