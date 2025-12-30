"""
Counter Scoreboard
==================

Ce fichier contient :
1. CounterModel : Le modèle de référence (comportement attendu)
2. CounterScoreboard : Compare le DUT avec le modèle
"""


class CounterModel:
    """
    Modèle de référence du compteur.

    C'est une version Python du comportement RTL.
    On l'utilise pour calculer la valeur attendue.
    """

    def __init__(self, width: int = 8):
        """
        Args:
            width: Nombre de bits du compteur (défaut: 8)
        """
        self.width = width
        self.max_val = (1 << width) - 1  # 2^width - 1 = 255 pour 8 bits
        self.count = 0

    def reset(self):
        """Simule le reset : remet le compteur à 0."""
        self.count = 0

    def tick(self, enable: bool):
        """
        Simule un cycle d'horloge.

        Args:
            enable: État du signal enable
        """
        if enable:
            if self.count == self.max_val:
                self.count = 0  # Wrap-around
            else:
                self.count += 1

    def get_expected(self) -> int:
        """Retourne la valeur attendue du compteur."""
        return self.count


class CounterScoreboard:
    """
    Scoreboard : Compare le DUT avec le modèle de référence.

    Usage:
        sb = CounterScoreboard()
        sb.reset()                    # Quand reset est actif
        sb.tick(enable=True)          # À chaque cycle d'horloge
        sb.check(dut.count.value)     # Vérifie la valeur
        sb.report()                   # Affiche le résumé
    """

    def __init__(self, width: int = 8):
        self.model = CounterModel(width)
        self.errors = 0
        self.checks = 0

    def reset(self):
        """Appelé quand le DUT reçoit un reset."""
        self.model.reset()

    def tick(self, enable: bool):
        """Appelé à chaque cycle d'horloge."""
        self.model.tick(enable)

    def check(self, actual_value: int, log=None) -> bool:
        """
        Compare la valeur réelle avec l'attendue.

        Args:
            actual_value: Valeur lue depuis le DUT
            log: Logger cocotb (optionnel)

        Returns:
            True si OK, False si erreur

        Raises:
            AssertionError si mismatch
        """
        expected = self.model.get_expected()
        self.checks += 1

        if actual_value != expected:
            self.errors += 1
            msg = f"MISMATCH! Expected={expected}, Actual={actual_value}"
            if log:
                log.error(msg)
            raise AssertionError(msg)

        if log:
            log.debug(f"Check OK: {actual_value} == {expected}")

        return True

    def report(self, log=None) -> dict:
        """
        Affiche le rapport final.

        Returns:
            dict avec les statistiques
        """
        status = "PASS" if self.errors == 0 else "FAIL"
        msg = f"Scoreboard: {self.checks} checks, {self.errors} errors - {status}"

        if log:
            if self.errors == 0:
                log.info(f"✓ {msg}")
            else:
                log.error(f"✗ {msg}")

        return {
            "checks": self.checks,
            "errors": self.errors,
            "status": status
        }
