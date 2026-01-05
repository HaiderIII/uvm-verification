"""
RAL Model - Register Abstraction Layer
======================================
Modèle de registres pour notre APB Slave.

EXERCICE: Complete les TODOs pour construire le modèle RAL.
"""


# =============================================================================
# Register Field - Représente un champ dans un registre
# =============================================================================
class RegField:
    """
    Un champ (field) dans un registre.

    Exemple: ENABLE est un champ de 1 bit à la position 31
    """

    def __init__(self, name, width, lsb_pos, reset_value=0, access="RW"):
        """
        Args:
            name: Nom du champ (ex: "ENABLE")
            width: Largeur en bits (ex: 1)
            lsb_pos: Position du bit de poids faible (ex: 31)
            reset_value: Valeur après reset
            access: "RW" (read-write), "RO" (read-only), "WO" (write-only)
        """
        self.name = name
        self.width = width
        self.lsb_pos = lsb_pos
        self.reset_value = reset_value
        self.access = access
        self.value = reset_value

    def set(self, value):
        """Modifie la valeur du champ (dans le miroir RAL)."""
        # Masquer pour garder seulement les bits valides
        mask = (1 << self.width) - 1
        self.value = value & mask

    def get(self):
        """Retourne la valeur actuelle du champ."""
        return self.value

    def reset(self):
        """Remet le champ à sa valeur de reset."""
        self.value = self.reset_value


# =============================================================================
# Register - Représente un registre complet
# =============================================================================
class Register:
    """
    Un registre avec ses champs.

    TODO 1: Comprends comment les champs sont combinés en une valeur 32 bits.
    """

    def __init__(self, name, address, reset_value=0):
        self.name = name
        self.address = address
        self.reset_value = reset_value
        self.fields = {}  # Dict de RegField par nom
        self._value = reset_value  # Valeur miroir complète

    def add_field(self, field):
        """Ajoute un champ au registre."""
        self.fields[field.name] = field
        return field

    def get_value(self):
        """
        Construit la valeur 32 bits à partir des champs.

        TODO 2: Complète cette fonction

        Pour chaque champ:
        - Décale sa valeur vers sa position (lsb_pos)
        - Combine avec OR (|)

        Exemple: Si ENABLE=1 à bit 31, et MODE=3 à bits [1:0]
        Résultat: 0x80000003
        """
        value = 0
        # TODO: Complète ici
        for field in self.fields.values():
            value |= (field.get() << field.lsb_pos)
        return value

    def set_value(self, value):
        """
        Met à jour tous les champs à partir d'une valeur 32 bits.

        TODO 3: Complète cette fonction (inverse de get_value)

        Pour chaque champ:
        - Extrais les bits correspondants
        - Met à jour le champ
        """
        self._value = value
        # TODO: Complète ici
        for field in self.fields.values():
            mask = (1 << field.width) - 1
            field_value = (value >> field.lsb_pos) & mask
            field.set(field_value)

    def reset(self):
        """Remet le registre à sa valeur de reset."""
        for field in self.fields.values():
            field.reset()
        self._value = self.reset_value


# =============================================================================
# Register Block - Contient tous les registres
# =============================================================================
class ApbRegBlock:
    """
    Bloc de registres pour l'APB Slave.

    C'est le "modèle RAL" complet.
    """

    def __init__(self, name="apb_regs"):
        self.name = name
        self.registers = {}
        self.adapter = None  # Sera connecté au driver

        # Créer les registres
        self._build()

    def _build(self):
        """
        Construit la structure des registres.

        TODO 4: Ajoute REG2 et REG3

        Notre APB slave a 4 registres simples de 32 bits:
        - REG0 à 0x00
        - REG1 à 0x04
        - REG2 à 0x08
        - REG3 à 0x0C

        Pour simplifier, chaque registre a un seul champ DATA de 32 bits.
        """
        # REG0 - Registre de données 0
        self.REG0 = Register("REG0", address=0x00, reset_value=0)
        self.REG0.add_field(RegField("DATA", width=32, lsb_pos=0, reset_value=0))
        self.registers["REG0"] = self.REG0

        # REG1 - Registre de données 1
        self.REG1 = Register("REG1", address=0x04, reset_value=0)
        self.REG1.add_field(RegField("DATA", width=32, lsb_pos=0, reset_value=0))
        self.registers["REG1"] = self.REG1

        # TODO: Ajoute REG2 et REG3 ici
        # REG2 - Registre de données 2
        self.REG2 = Register("REG2", address=0x08, reset_value=0)
        self.REG2.add_field(RegField("DATA", width=32, lsb_pos=0, reset_value=0))
        self.registers["REG2"] = self.REG2

        # REG3 - Registre de données 3
        self.REG3 = Register("REG3", address=0x0C, reset_value=0)
        self.REG3.add_field(RegField("DATA", width=32, lsb_pos=0, reset_value=0))
        self.registers["REG3"] = self.REG3

    def set_adapter(self, adapter):
        """Connecte l'adaptateur qui traduit vers le bus."""
        self.adapter = adapter

    async def write_reg(self, reg, value):
        """
        Écrit dans un registre via le bus.

        TODO 5: Comprends le flux
        1. Met à jour la valeur miroir
        2. Utilise l'adapter pour envoyer sur le bus
        """
        # Mettre à jour le miroir
        reg.set_value(value)

        # Envoyer sur le bus via l'adapter
        if self.adapter:
            await self.adapter.write(reg.address, value)

    async def read_reg(self, reg):
        """
        Lit un registre via le bus.

        Retourne la valeur lue du DUT.
        """
        if self.adapter:
            value = await self.adapter.read(reg.address)
            reg.set_value(value)  # Met à jour le miroir
            return value
        return reg.get_value()

    async def mirror_check(self, reg):
        """
        Vérifie que le DUT contient la même valeur que le miroir.

        C'est une fonctionnalité puissante du RAL !
        """
        if self.adapter:
            dut_value = await self.adapter.read(reg.address)
            mirror_value = reg.get_value()

            if dut_value != mirror_value:
                raise ValueError(
                    f"Mirror mismatch for {reg.name}: "
                    f"DUT=0x{dut_value:08X}, Mirror=0x{mirror_value:08X}"
                )
            return True
        return True

    def reset(self):
        """Reset tous les registres."""
        for reg in self.registers.values():
            reg.reset()
