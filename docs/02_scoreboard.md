# Projet 1 : Le Scoreboard

## Le problème avec nos tests actuels

Dans `test_counter.py`, on fait des vérifications "en dur" :

```python
expected = 10
actual = int(dut.count.value)
assert actual == expected
```

**Problèmes :**
- On calcule manuellement la valeur attendue
- Si le design change, on doit recalculer à la main
- Pas de vérification continue (on vérifie à un instant T)
- Difficile de tester des séquences complexes

---

## La solution : Le Scoreboard

Un **Scoreboard** est un **modèle de référence** qui :
1. Reçoit les mêmes entrées que le DUT
2. Calcule la sortie attendue (en Python)
3. Compare automatiquement avec la sortie réelle du DUT

```
                    ┌─────────────────┐
    Entrées ───────▶│   DUT (RTL)     │───────▶ Sortie réelle
        │           └─────────────────┘              │
        │                                            │
        │           ┌─────────────────┐              ▼
        └──────────▶│ Scoreboard      │         ┌────────┐
                    │ (modèle Python) │────────▶│ Compare│──▶ OK/ERREUR
                    └─────────────────┘         └────────┘
                           │
                           ▼
                    Sortie attendue
```

---

## Pourquoi c'est puissant ?

### Sans Scoreboard (ce qu'on a fait)
```python
# On doit prédire manuellement
dut.enable.value = 1
await ClockCycles(dut.clk, 10)
assert dut.count.value == 10  # Calcul mental
```

### Avec Scoreboard
```python
# Le scoreboard calcule pour nous
dut.enable.value = 1
await ClockCycles(dut.clk, 10)
# Le scoreboard a suivi les 10 cycles et vérifie automatiquement
```

---

## Architecture complète d'un testbench

```
┌──────────────────────────────────────────────────────────────────────┐
│                           TESTBENCH                                  │
│                                                                      │
│  ┌──────────┐                              ┌──────────┐              │
│  │  Driver  │                              │ Monitor  │              │
│  │ (génère  │                              │(observe) │              │
│  │ stimuli) │                              │          │              │
│  └────┬─────┘                              └────┬─────┘              │
│       │                                         │                    │
│       │         ┌─────────────────┐             │                    │
│       └────────▶│      DUT        │─────────────┘                    │
│       │         │   (counter)     │             │                    │
│       │         └─────────────────┘             │                    │
│       │                                         │                    │
│       │         ┌─────────────────┐             │                    │
│       │         │   Scoreboard    │             │                    │
│       └────────▶│ (modèle Python) │◀────────────┘                    │
│                 │                 │                                  │
│                 │  expected = ?   │                                  │
│                 │  actual = ?     │                                  │
│                 │  COMPARE!       │                                  │
│                 └─────────────────┘                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

| Composant | Rôle | Notre implémentation |
|-----------|------|---------------------|
| **Driver** | Envoie les signaux au DUT | Code dans le test |
| **Monitor** | Observe les sorties du DUT | Lecture de `dut.count` |
| **Scoreboard** | Modèle + comparaison | Classe `CounterScoreboard` |

---

## Le modèle de référence

C'est une version **simplifiée** du comportement attendu, écrite en Python :

```python
class CounterModel:
    """Modèle de référence du compteur"""

    def __init__(self, width=8):
        self.width = width
        self.max_val = (1 << width) - 1  # 255 pour 8 bits
        self.count = 0

    def reset(self):
        """Comportement du reset"""
        self.count = 0

    def tick(self, enable):
        """Comportement à chaque cycle d'horloge"""
        if enable:
            if self.count == self.max_val:
                self.count = 0  # Wrap
            else:
                self.count += 1

    def get_expected(self):
        """Retourne la valeur attendue"""
        return self.count
```

**C'est le même comportement que le RTL, mais en Python !**

---

## Le Scoreboard complet

```python
class CounterScoreboard:
    """Compare le DUT avec le modèle"""

    def __init__(self):
        self.model = CounterModel()
        self.errors = 0
        self.checks = 0

    def reset(self):
        """Signal de reset reçu"""
        self.model.reset()

    def tick(self, enable):
        """Un cycle d'horloge s'est passé"""
        self.model.tick(enable)

    def check(self, actual_value):
        """Compare la valeur réelle avec l'attendue"""
        expected = self.model.get_expected()
        self.checks += 1

        if actual_value != expected:
            self.errors += 1
            raise AssertionError(
                f"Mismatch! Expected={expected}, Actual={actual_value}"
            )

    def report(self):
        """Rapport final"""
        print(f"Checks: {self.checks}, Errors: {self.errors}")
```

---

## Avantages du Scoreboard

| Aspect | Sans Scoreboard | Avec Scoreboard |
|--------|-----------------|-----------------|
| Calcul des attendus | Manuel | Automatique |
| Vérification | Ponctuelle | Continue |
| Maintenabilité | Difficile | Facile |
| Réutilisabilité | Faible | Haute |
| Détection de bugs | Limitée | Complète |

---

## Lien avec UVM

En UVM, le Scoreboard est un composant standard :

```
┌─────────────────────────────────────────────────────────────────┐
│                      UVM Testbench                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     UVM Agent                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Sequencer│  │  Driver  │  │ Monitor  │              │   │
│  │  └──────────┘  └──────────┘  └────┬─────┘              │   │
│  └───────────────────────────────────┼─────────────────────┘   │
│                                      │                          │
│                                      ▼                          │
│                            ┌──────────────────┐                 │
│                            │   Scoreboard     │                 │
│                            │ (uvm_scoreboard) │                 │
│                            └──────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

**Ce qu'on apprend avec Cocotb s'applique directement en UVM !**

---

## Ce qu'on va coder

1. **`CounterModel`** : Le modèle de référence en Python
2. **`CounterScoreboard`** : Compare DUT vs modèle
3. **Tests mis à jour** : Utilisent le scoreboard au lieu de valeurs en dur

---

## Exercice de réflexion

Avant de coder, réponds à cette question :

> Si le compteur a un bug où il saute de 5 à 7 (sans passer par 6),
> comment le scoreboard le détecterait-il ?

<details>
<summary>Réponse</summary>

Le scoreboard suit chaque cycle :
- Cycle 5 : modèle = 5, DUT = 5 ✓
- Cycle 6 : modèle = 6, DUT = 7 ✗ **ERREUR DÉTECTÉE !**

Sans scoreboard, si on vérifiait seulement à la fin (cycle 10),
on verrait : modèle = 10, DUT = 11... on saurait qu'il y a un bug,
mais pas **quand** il s'est produit.

</details>
