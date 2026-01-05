"""
NoC Router UVM-style Test
=========================
Testbench UVM-style pour NoC Router avec routage XY.

EXERCICE: Complete les TODOs pour faire fonctionner le test.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import random
from enum import IntEnum


# =============================================================================
# Constantes
# =============================================================================
class Port(IntEnum):
    """Ports du routeur NoC."""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    LOCAL = 4


# =============================================================================
# NoC Packet (équivalent de uvm_sequence_item)
# =============================================================================
class NocPacket:
    """
    Représente un paquet NoC.

    Format du paquet (32 bits):
    ┌────────┬────────┬────────┬────────┬─────────────────┐
    │ dst_x  │ dst_y  │ src_x  │ src_y  │    payload      │
    │ [31:28]│ [27:24]│ [23:20]│ [19:16]│    [15:0]       │
    │ 4 bits │ 4 bits │ 4 bits │ 4 bits │   16 bits       │
    └────────┴────────┴────────┴────────┴─────────────────┘
    """

    def __init__(self, dest_x=0, dest_y=0, src_x=0, src_y=0, payload=0):
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.src_x = src_x
        self.src_y = src_y
        self.payload = payload
        self.output_port = None  # Port de sortie (rempli par scoreboard)

    def to_flit(self):
        """
        Convertit le paquet en flit 32 bits.

        TODO 1: Complète cette fonction
        - Décale dest_x de 28 bits vers la gauche
        - Décale dest_y de 24 bits vers la gauche
        - Décale src_x de 20 bits vers la gauche
        - Décale src_y de 16 bits vers la gauche
        - payload reste sur les bits [15:0]
        - Combine tout avec OR (|)
        """
        flit = 0
        # TODO: Complète ici
        flit = ((self.dest_x & 0xF) << 28 |
                (self.dest_y & 0xF) << 24 |
                (self.src_x & 0xF) << 20 |
                (self.src_y & 0xF) << 16 |
                (self.payload & 0xFFFF))
        return flit

    @classmethod
    def from_flit(cls, flit):
        """
        Crée un paquet à partir d'un flit 32 bits.

        TODO 2: Complète cette fonction (inverse de to_flit)
        - Extrais dest_x des bits [31:28]
        - Extrais dest_y des bits [27:24]
        - etc.
        """
        pkt = cls()
        # TODO: Complète ici
        pkt.dest_x = (flit >> 28) & 0xF
        pkt.dest_y = (flit >> 24) & 0xF
        pkt.src_x = (flit >> 20) & 0xF
        pkt.src_y = (flit >> 16) & 0xF
        pkt.payload = flit & 0xFFFF
        return pkt

    def __str__(self):
        port_name = self.output_port.name if self.output_port else "?"
        return (f"PKT src=({self.src_x},{self.src_y}) "
                f"dst=({self.dest_x},{self.dest_y}) "
                f"payload=0x{self.payload:04X} → {port_name}")

    def __eq__(self, other):
        """Pour comparaison dans le scoreboard."""
        if not isinstance(other, NocPacket):
            return False
        return (self.dest_x == other.dest_x and
                self.dest_y == other.dest_y and
                self.payload == other.payload)


# =============================================================================
# XY Routing Model (Modèle de référence pour le scoreboard)
# =============================================================================
class XYRoutingModel:
    """
    Modèle de routage XY.
    C'est le "golden model" - la référence pour vérifier le DUT.
    """

    def __init__(self, router_x, router_y):
        self.router_x = router_x
        self.router_y = router_y

    def route(self, packet):
        """
        Calcule le port de sortie selon l'algorithme XY.

        TODO 3: Complète cette fonction

        Règles (dans cet ordre):
        1. Si dest_x > router_x → EAST
        2. Si dest_x < router_x → WEST
        3. Si dest_y > router_y → SOUTH
        4. Si dest_y < router_y → NORTH
        5. Sinon (dest = router) → LOCAL
        """
        # TODO: Complète ici
        if packet.dest_x > self.router_x:
            return Port.EAST
        elif packet.dest_x < self.router_x:
            return Port.WEST
        elif packet.dest_y > self.router_y:
            return Port.SOUTH
        elif packet.dest_y < self.router_y:
            return Port.NORTH
        else:
            return Port.LOCAL


# =============================================================================
# NoC Driver (équivalent de uvm_driver)
# =============================================================================
class NocDriver:
    """
    Driver NoC - injecte des paquets sur le port LOCAL.
    """

    def __init__(self, dut, log):
        self.dut = dut
        self.log = log

    async def reset(self):
        """Initialise tous les signaux d'entrée."""
        for i in range(5):
            self.dut.data_in[i].value = 0
            self.dut.valid_in[i].value = 0
            self.dut.ready_in[i].value = 1  # Toujours prêt à recevoir

    async def send(self, packet, port=Port.LOCAL):
        """
        Envoie un paquet sur un port d'entrée.

        TODO 4: Complète le handshake valid/ready

        Protocole:
        1. Positionner data_in et valid_in = 1
        2. Attendre que ready_out = 1
        3. Désactiver valid_in
        """
        flit = packet.to_flit()

        # Positionner les données
        self.dut.data_in[port].value = flit
        self.dut.valid_in[port].value = 1

        # TODO: Attendre le handshake (ready_out = 1)
        await RisingEdge(self.dut.clk)
        while self.dut.ready_out[port].value == 0:
            await RisingEdge(self.dut.clk)

        # Désactiver valid
        self.dut.valid_in[port].value = 0

        self.log.info(f"Driver: Sent {packet}")
        return packet


# =============================================================================
# NoC Monitor (équivalent de uvm_monitor)
# =============================================================================
class NocMonitor:
    """
    Monitor NoC - observe tous les ports de sortie.
    """

    def __init__(self, dut, log, callback=None):
        self.dut = dut
        self.log = log
        self.callback = callback
        self.running = False

    async def start(self):
        """Lance le monitoring sur tous les ports."""
        self.running = True
        for port in Port:
            cocotb.start_soon(self._monitor_port(port))

    async def _monitor_port(self, port):
        """
        Observe un port de sortie spécifique.

        TODO 5: Détecte quand un paquet sort sur ce port

        Condition: valid_out = 1 ET ready_in = 1
        """
        while self.running:
            await RisingEdge(self.dut.clk)

            # TODO: Détecter un paquet valide
            if (self.dut.valid_out[port].value == 1 and
                self.dut.ready_in[port].value == 1):

                flit = int(self.dut.data_out[port].value)
                packet = NocPacket.from_flit(flit)
                packet.output_port = port

                self.log.info(f"Monitor: Received on {port.name}: {packet}")

                if self.callback:
                    self.callback(packet)

    def stop(self):
        self.running = False


# =============================================================================
# NoC Scoreboard (équivalent de uvm_scoreboard)
# =============================================================================
class NocScoreboard:
    """
    Scoreboard NoC - vérifie que les paquets sortent sur le bon port.
    """

    def __init__(self, log, router_x=0, router_y=0):
        self.log = log
        self.routing_model = XYRoutingModel(router_x, router_y)

        # File d'attente des paquets attendus par port
        self.expected = {port: [] for port in Port}

        # Compteurs
        self.num_sent = 0
        self.num_received = 0
        self.num_errors = 0

    def expect(self, packet):
        """
        Enregistre un paquet envoyé et prédit son port de sortie.

        TODO 6: Utilise le routing_model pour prédire le port
        """
        # TODO: Calculer le port de sortie attendu
        expected_port = self.routing_model.route(packet)
        packet.output_port = expected_port

        # Ajouter à la file d'attente du port
        self.expected[expected_port].append(packet)
        self.num_sent += 1

        self.log.info(f"Scoreboard: Expecting {packet}")

    def check(self, received_packet):
        """
        Vérifie un paquet reçu contre les attentes.

        TODO 7: Compare le paquet reçu avec celui attendu
        """
        port = received_packet.output_port
        self.num_received += 1

        # Vérifier qu'on attendait un paquet sur ce port
        if not self.expected[port]:
            self.log.error(f"UNEXPECTED packet on {port.name}")
            self.num_errors += 1
            return

        # TODO: Comparer avec le premier paquet attendu
        expected = self.expected[port].pop(0)

        if received_packet == expected:
            self.log.info(f"Scoreboard: MATCH on {port.name}")
        else:
            self.log.error(f"MISMATCH on {port.name}!")
            self.log.error(f"  Expected: {expected}")
            self.log.error(f"  Got:      {received_packet}")
            self.num_errors += 1

    def report(self):
        """Affiche le résumé final."""
        # Vérifier les paquets non reçus
        for port in Port:
            if self.expected[port]:
                self.log.error(f"{len(self.expected[port])} packets NOT received on {port.name}")
                self.num_errors += len(self.expected[port])

        self.log.info("=" * 50)
        self.log.info("           NOC SCOREBOARD SUMMARY")
        self.log.info("=" * 50)
        self.log.info(f"  Packets sent:     {self.num_sent}")
        self.log.info(f"  Packets received: {self.num_received}")
        self.log.info(f"  Errors:           {self.num_errors}")
        self.log.info("=" * 50)

        return self.num_errors == 0


# =============================================================================
# Test
# =============================================================================
async def reset_dut(dut):
    """Reset le DUT."""
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def test_noc_xy_routing(dut):
    """
    Test du routage XY.

    Le routeur est à la position (0,0).

    TODO 8: Comprends les tests et prédis les résultats

    Questions:
    1. Un paquet vers (1,0) sort sur quel port?
    2. Un paquet vers (0,1) sort sur quel port?
    3. Un paquet vers (0,0) sort sur quel port?
    4. Un paquet vers (2,3) sort sur quel port? (XY = d'abord X)
    """
    ROUTER_X = 0
    ROUTER_Y = 0

    # Démarrer l'horloge
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Créer les composants UVM-style
    driver = NocDriver(dut, dut._log)
    scoreboard = NocScoreboard(dut._log, ROUTER_X, ROUTER_Y)
    monitor = NocMonitor(dut, dut._log, callback=scoreboard.check)

    # Reset
    await driver.reset()
    await reset_dut(dut)

    # Lancer le monitor
    await monitor.start()

    dut._log.info("=" * 50)
    dut._log.info(f"  NoC Router Test - Router at ({ROUTER_X},{ROUTER_Y})")
    dut._log.info("=" * 50)

    # === Test 1: Destination (1,0) ===
    # Réponse attendue: EAST (car dest_x=1 > router_x=0)
    dut._log.info("\n--- Test 1: dest=(1,0) ---")
    pkt = NocPacket(dest_x=1, dest_y=0, src_x=0, src_y=0, payload=0x1111)
    scoreboard.expect(pkt)
    await driver.send(pkt)
    await ClockCycles(dut.clk, 5)

    # === Test 2: Destination (0,1) ===
    # Réponse attendue: SOUTH (car dest_y=1 > router_y=0)
    dut._log.info("\n--- Test 2: dest=(0,1) ---")
    pkt = NocPacket(dest_x=0, dest_y=1, src_x=0, src_y=0, payload=0x2222)
    scoreboard.expect(pkt)
    await driver.send(pkt)
    await ClockCycles(dut.clk, 5)

    # === Test 3: Destination (0,0) = LOCAL ===
    # Réponse attendue: LOCAL (car dest = router)
    dut._log.info("\n--- Test 3: dest=(0,0) ---")
    pkt = NocPacket(dest_x=0, dest_y=0, src_x=0, src_y=0, payload=0x3333)
    scoreboard.expect(pkt)
    await driver.send(pkt)
    await ClockCycles(dut.clk, 5)

    # === Test 4: Destination (2,3) - XY routing ===
    # Réponse attendue: EAST (car on route d'abord X, et dest_x=2 > 0)
    dut._log.info("\n--- Test 4: dest=(2,3) - XY routing ---")
    pkt = NocPacket(dest_x=2, dest_y=3, src_x=0, src_y=0, payload=0x4444)
    scoreboard.expect(pkt)
    await driver.send(pkt)
    await ClockCycles(dut.clk, 5)

    # Attendre et terminer
    await ClockCycles(dut.clk, 20)
    monitor.stop()

    # Rapport
    passed = scoreboard.report()
    assert passed, "Test FAILED"
    dut._log.info("*** TEST PASSED ***")
