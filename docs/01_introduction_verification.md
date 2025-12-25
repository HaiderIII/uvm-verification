# Introduction à la Vérification Hardware

## Pourquoi la vérification ?

En conception de puces (ASIC/FPGA), **60-70% du temps** est passé en vérification, pas en design.

**Pourquoi ?** Une erreur dans le silicium coûte des **millions de dollars** à corriger (re-fabrication). Contrairement au logiciel, on ne peut pas "patcher" une puce après fabrication.

```
Coût d'un bug détecté en :
┌─────────────────────────────────────────────────────────┐
│ Simulation      → $0         (on corrige le code)       │
│ FPGA prototype  → $10K       (temps perdu)              │
│ Après fabrication → $1M-$10M (nouveau masque)           │
│ Chez le client  → $100M+     (rappel produit)           │
└─────────────────────────────────────────────────────────┘
```

---

## Le problème fondamental

Tu as conçu un module RTL (Verilog/SystemVerilog). **Comment prouver qu'il fonctionne ?**

### Approche naïve : simulation manuelle

```verilog
// Testbench "à la main"
initial begin
    reset = 1;
    #10 reset = 0;
    #10 enable = 1;
    #100;
    if (count != 10) $display("ERREUR!");
end
```

**Problèmes :**
- Tu ne testes que les cas auxquels tu as pensé
- Pas de vérification automatique
- Difficile à maintenir
- Pas réutilisable

---

## La solution : Vérification méthodique

### Les 3 questions clés

1. **Qu'est-ce qu'on vérifie ?** → Le DUT (Design Under Test)
2. **Comment on stimule ?** → Le Driver (envoie des signaux)
3. **Comment on vérifie ?** → Le Monitor + Scoreboard (observe et compare)

### Architecture d'un testbench moderne

```
┌─────────────────────────────────────────────────────────────┐
│                      TESTBENCH                              │
│  ┌─────────┐     ┌─────────┐     ┌──────────────┐          │
│  │ Driver  │────▶│   DUT   │────▶│   Monitor    │          │
│  │(stimuli)│     │(ta puce)│     │(observation) │          │
│  └─────────┘     └─────────┘     └──────┬───────┘          │
│       │                                  │                  │
│       │         ┌──────────────┐         │                  │
│       └────────▶│  Scoreboard  │◀────────┘                  │
│                 │  (compare)   │                            │
│                 └──────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

| Composant | Rôle | Analogie |
|-----------|------|----------|
| **Driver** | Génère les stimuli (entrées) | Le testeur qui appuie sur les boutons |
| **DUT** | Le design à vérifier | La machine qu'on teste |
| **Monitor** | Observe les sorties | La caméra qui enregistre |
| **Scoreboard** | Compare résultat vs attendu | Le juge qui dit "OK" ou "ERREUR" |

---

## UVM vs Cocotb : Deux approches

### UVM (Universal Verification Methodology)

- **Langage :** SystemVerilog
- **Utilisé par :** Industrie (Intel, AMD, Qualcomm, etc.)
- **Avantages :** Standard industriel, très puissant
- **Inconvénients :** Complexe, verbeux, courbe d'apprentissage raide

```systemverilog
// Exemple UVM (verbeux !)
class my_driver extends uvm_driver #(my_transaction);
    `uvm_component_utils(my_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            // ... drive signals ...
            seq_item_port.item_done();
        end
    endtask
endclass
```

### Cocotb (Coroutine-based Co-simulation Testbench)

- **Langage :** Python
- **Utilisé par :** Startups, projets open-source, prototypage rapide
- **Avantages :** Simple, rapide à écrire, Pythonic
- **Inconvénients :** Moins standardisé, moins d'outils

```python
# Même chose en Cocotb (simple !)
@cocotb.test()
async def test_something(dut):
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    assert dut.count.value == expected
```

### Pourquoi apprendre Cocotb d'abord ?

```
Complexité
    │
    │   ┌─────────────────┐
    │   │      UVM        │  ← Destination finale
    │   │  (industrie)    │
    │   └────────▲────────┘
    │            │
    │   ┌────────┴────────┐
    │   │     Cocotb      │  ← On commence ici
    │   │ (mêmes concepts)│
    │   └─────────────────┘
    │
    └─────────────────────────▶ Temps d'apprentissage
```

**Les concepts sont identiques** (Driver, Monitor, Scoreboard, Coverage).
Cocotb te permet de les comprendre sans la complexité de SystemVerilog.

---

## Ce qu'on a fait dans le projet counter

### Le DUT : `counter.sv`

```systemverilog
module counter (
    input  logic       clk,      // Horloge
    input  logic       rst_n,    // Reset actif bas
    input  logic       enable,   // Active le comptage
    output logic [7:0] count     // Valeur du compteur
);
```

Un compteur 8-bit simple :
- Reset → count = 0
- Enable = 1 → count++ à chaque cycle
- Wrap à 255 → 0

### Le Testbench : `test_counter.py`

```python
@cocotb.test()
async def test_counter_count(dut):
    # 1. SETUP : Créer l'horloge
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # 2. STIMULUS : Driver les entrées
    dut.rst_n.value = 0          # Reset
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1          # Libère reset
    dut.enable.value = 1         # Active comptage

    # 3. ATTENTE : Laisser le DUT travailler
    await ClockCycles(dut.clk, 10)
    await FallingEdge(dut.clk)   # Attendre stabilité

    # 4. VÉRIFICATION : Scoreboard simple
    expected = 10
    actual = int(dut.count.value)
    assert actual == expected    # Compare !
```

---

## Le bug de timing qu'on a corrigé

### Le problème

```
        Cycle 9          Cycle 10
           │                │
    ───────┼────────────────┼───────
           │                │
     clk ──┘    ┌───────────┘    ┌──
               │                │
    count ─────┤ 9 ─────────────┤ 10
               │                │
               ▲                ▲
               │                └── Valeur mise à jour ICI
               │
               └── On lisait ICI (trop tôt !)
```

### La solution : `await FallingEdge(dut.clk)`

```
        Cycle 10
           │
    ───────┼─────────┬───────────
           │         │
     clk ──┘    ┌────┘    (falling edge)
               │    │
    count ─────┤ 10 │
               │    │
               ▲    ▲
               │    └── On lit ICI (après stabilisation)
               │
               └── Valeur mise à jour
```

**Règle d'or :** En vérification, on lit les signaux sur le **front descendant** (falling edge) pour éviter les race conditions.

---

## Concepts clés à retenir

| Concept | Explication |
|---------|-------------|
| **DUT** | Design Under Test - le module qu'on vérifie |
| **Testbench** | L'environnement qui teste le DUT |
| **Driver** | Génère les stimuli (entrées) |
| **Monitor** | Observe les sorties |
| **Scoreboard** | Compare résultat vs attendu |
| **Coverage** | Mesure ce qu'on a testé |
| **Assertion** | Vérifie une condition (assert) |
| **Trigger** | Événement pour synchroniser (RisingEdge, FallingEdge) |

---

## Prochaines étapes

1. **Ajouter un Scoreboard** → Modèle de référence en Python
2. **Ajouter de la Coverage** → Mesurer ce qu'on teste
3. **Protocole AXI-Lite** → Interface de communication standard
4. **Créer un VIP** → Verification IP réutilisable

---

## Lien avec le poste NoC

Le poste demande :
- ✅ **Verify NoC-level features** → On apprend à vérifier
- ✅ **UVM benches** → Cocotb enseigne les mêmes concepts
- ✅ **Python generators** → Cocotb = Python natif
- ✅ **AMBA protocols** → Prochaine étape (AXI)
- ✅ **Automated regressions** → pytest + Cocotb

Tu construis les fondations pour comprendre UVM plus tard.
