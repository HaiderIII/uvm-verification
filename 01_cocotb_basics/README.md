# Projet 1 : Cocotb Basics + Scoreboard

## Objectif

Apprendre les bases de la vérification hardware avec Cocotb :
- Créer un testbench pour un compteur 8-bit
- Comprendre le timing (RisingEdge, FallingEdge)
- Implémenter un **Scoreboard** (modèle de référence)

---

## Structure du projet

```
01_cocotb_basics/
├── rtl/
│   └── counter.sv          # DUT : compteur 8-bit
├── tb/
│   ├── __init__.py
│   └── scoreboard.py       # Modèle de référence + Scoreboard
├── tests/
│   ├── __init__.py
│   ├── test_counter.py                 # Tests basiques (valeurs en dur)
│   └── test_counter_with_scoreboard.py # Tests avec scoreboard
└── Makefile
```

---

## Le DUT : Counter

```systemverilog
module counter (
    input  logic       clk,      // Horloge
    input  logic       rst_n,    // Reset actif bas
    input  logic       enable,   // Active le comptage
    output logic [7:0] count     // Valeur 0-255
);
```

**Comportement :**
- `rst_n = 0` → count = 0
- `enable = 1` → count++ à chaque cycle
- Wrap-around : 255 → 0

---

## Concepts appris

### 1. Génération d'horloge

```python
clock = Clock(dut.clk, 10, unit="ns")  # 100 MHz
cocotb.start_soon(clock.start())
```

### 2. Triggers (synchronisation)

| Trigger | Usage |
|---------|-------|
| `await RisingEdge(dut.clk)` | Attendre front montant |
| `await FallingEdge(dut.clk)` | Attendre front descendant (lecture stable) |
| `await ClockCycles(dut.clk, N)` | Attendre N cycles |

### 3. Driver les signaux

```python
dut.enable.value = 1      # Écrire
dut.rst_n.value = 0       # Reset actif
```

### 4. Lire les signaux

```python
actual = int(dut.count.value)  # Lire et convertir en int
```

### 5. Le bug de timing

**Problème :** Lire immédiatement après `RisingEdge` donne l'ancienne valeur.

**Solution :** Lire sur `FallingEdge` pour laisser le DUT se stabiliser.

```
    ┌───┐   ┌───┐   ┌───┐
clk─┘   └───┘   └───┘   └───
        ↑       ↓
        │       └── Lire ici (FallingEdge) ✓
        └── DUT met à jour ici (RisingEdge)
```

---

## Le Scoreboard

### Pourquoi ?

| Sans Scoreboard | Avec Scoreboard |
|-----------------|-----------------|
| `assert count == 10` (en dur) | Le modèle calcule automatiquement |
| Vérification ponctuelle | Vérification continue |
| Difficile à maintenir | Réutilisable |

### Architecture

```
          ┌─────────────┐
Entrées──▶│    DUT      │──▶ Sortie réelle
    │     └─────────────┘         │
    │                             ▼
    │     ┌─────────────┐    ┌─────────┐
    └────▶│ Scoreboard  │───▶│ Compare │──▶ OK/ERREUR
          │  (Python)   │    └─────────┘
          └─────────────┘
```

### Implémentation

```python
class CounterModel:
    def tick(self, enable):
        if enable:
            self.count = (self.count + 1) % 256

class CounterScoreboard:
    def check(self, actual_value):
        expected = self.model.get_expected()
        assert actual_value == expected
```

---

## Tests

### Tests basiques (`test_counter.py`)

| Test | Description |
|------|-------------|
| `test_counter_reset` | Reset met count à 0 |
| `test_counter_count` | Count incrémente avec enable |
| `test_counter_enable_control` | Count stop quand enable = 0 |
| `test_counter_wrap` | Wrap-around 255 → 0 |

### Tests avec scoreboard (`test_counter_with_scoreboard.py`)

| Test | Description |
|------|-------------|
| `test_scoreboard_basic` | Vérifie à chaque cycle |
| `test_scoreboard_enable_toggle` | Enable ON/OFF/ON |
| `test_scoreboard_wrap` | Wrap avec vérification continue |
| `test_scoreboard_random_enable` | Enable aléatoire (reproductible via seed) |

---

## Commandes

```bash
# Activer l'environnement
source .venv/bin/activate

# Tests basiques
make

# Tests avec scoreboard
make MODULE=tests.test_counter_with_scoreboard

# Nettoyer
make clean
```

---

## Points clés à retenir

1. **Timing** : Toujours lire sur `FallingEdge` pour éviter les race conditions
2. **Scoreboard** : Modèle Python qui calcule la valeur attendue automatiquement
3. **Seed** : Tests aléatoires mais reproductibles grâce au seeding
4. **Architecture** : Driver → DUT → Monitor → Scoreboard (même pattern qu'UVM)

---

## Prochaine étape

**Projet 2 : AXI-Lite VIP** - Apprendre les protocoles AMBA
