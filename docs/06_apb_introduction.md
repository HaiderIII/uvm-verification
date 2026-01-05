# Introduction au Protocole APB

## Objectif de ce document

Comprendre le protocole APB (Advanced Peripheral Bus) avant de l'implémenter en UVM.

---

## 1. APB dans l'écosystème AMBA

```
┌─────────────────────────────────────────────────────────────────┐
│                      AMBA Bus Family                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AXI (haute performance)                                       │
│    │                                                            │
│    ├── AXI4 (full)     → DDR, DMA, GPU                         │
│    ├── AXI4-Lite       → Registres de config (ce qu'on a fait) │
│    └── AXI4-Stream     → Streaming (ce qu'on a fait)           │
│                                                                 │
│   AHB (medium performance)                                      │
│    └── AHB-Lite        → Mémoires on-chip, bridges             │
│                                                                 │
│   APB (low power, simple)  ← CE QU'ON VA FAIRE                 │
│    └── APB4            → UART, GPIO, Timers, SPI, I2C          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**APB** est conçu pour les périphériques **lents et simples** où la performance n'est pas critique.

---

## 2. Comparaison APB vs AXI-Lite

| Caractéristique | APB | AXI-Lite |
|-----------------|-----|----------|
| Canaux | 1 seul | 5 (AW, W, B, AR, R) |
| Phases | 2 (Setup + Access) | Handshake par canal |
| Complexité | Simple | Moyenne |
| Pipeline | Non | Oui |
| Usage | Périphériques lents | Registres haute perf |

---

## 3. Les signaux APB

### Signaux du Master vers le Slave

| Signal | Largeur | Description |
|--------|---------|-------------|
| `PSEL` | 1 bit | Slave sélectionné |
| `PENABLE` | 1 bit | Phase Access active |
| `PWRITE` | 1 bit | 1=Write, 0=Read |
| `PADDR` | N bits | Adresse |
| `PWDATA` | 32 bits | Données à écrire |

### Signaux du Slave vers le Master

| Signal | Largeur | Description |
|--------|---------|-------------|
| `PREADY` | 1 bit | Slave prêt (peut insérer wait states) |
| `PRDATA` | 32 bits | Données lues |
| `PSLVERR` | 1 bit | Erreur (optionnel) |

---

## 4. Les 2 phases d'un transfert APB

### Phase 1 : SETUP (1 cycle)
- Master met `PSEL=1`, `PENABLE=0`
- Master positionne `PADDR`, `PWRITE`, `PWDATA`

### Phase 2 : ACCESS (1+ cycles)
- Master met `PENABLE=1`
- Slave répond avec `PREADY=1` quand prêt
- Transfert complété quand `PSEL=1 AND PENABLE=1 AND PREADY=1`

---

## 5. Chronogramme : Écriture sans wait state

```
         Cycle:    1       2       3       4
                   │       │       │       │
    CLK        ────┐   ┌───┐   ┌───┐   ┌───┐   ┌───
                   └───┘   └───┘   └───┘   └───┘

    PSEL       ────────┐               ┌───────────
               LOW     └───────────────┘   LOW

    PENABLE    ────────────────┐       ┌───────────
               LOW             └───────┘   LOW

    PADDR      ════════╤═══════════════╪═══════════
                       │    0x04       │
                       ╧═══════════════╧

    PWRITE     ────────┐               ┌───────────
               LOW     └───────────────┘

    PWDATA     ════════╤═══════════════╪═══════════
                       │  0xDEADBEEF   │
                       ╧═══════════════╧

    PREADY     ─────────────────────────────────────
               HIGH (toujours prêt)

                   │       │       │
                 IDLE   SETUP   ACCESS
                               (transfert!)
```

**Explication :**
- Cycle 1 : IDLE
- Cycle 2 : SETUP - PSEL=1, PENABLE=0, adresse et données positionnées
- Cycle 3 : ACCESS - PENABLE=1, PREADY=1 → **transfert complété**
- Cycle 4 : Retour à IDLE

---

## 6. Chronogramme : Lecture avec 1 wait state

```
         Cycle:    1       2       3       4       5
                   │       │       │       │       │
    CLK        ────┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
                   └───┘   └───┘   └───┘   └───┘   └───┘

    PSEL       ────────┐                       ┌───────
               LOW     └───────────────────────┘

    PENABLE    ────────────────┐               ┌───────
               LOW             └───────────────┘

    PADDR      ════════╤═══════════════════════╪═══════
                       │        0x08           │
                       ╧═══════════════════════╧

    PWRITE     ─────────────────────────────────────────
               LOW (lecture)

    PREADY     ────────────────────────┐       ┌───────
               LOW                     └───────┘ HIGH

    PRDATA     ════════════════════════╤═══════╪═══════
                                       │0x1234 │
                                       ╧═══════╧

                   │       │       │       │
                 IDLE   SETUP   ACCESS  ACCESS
                               (wait)  (done!)
```

**Explication :**
- Cycle 3 : ACCESS mais PREADY=0 → wait state (slave pas prêt)
- Cycle 4 : PREADY=1 → transfert complété, PRDATA valide

---

## 7. Machine à états APB

```
                    ┌──────────┐
         ─────────>│   IDLE   │<─────────────────┐
                   │ PSEL=0   │                  │
                   └────┬─────┘                  │
                        │                        │
                   Transfer                      │
                   requested                     │
                        │                        │
                        ▼                        │
                   ┌──────────┐                  │
                   │  SETUP   │                  │
                   │ PSEL=1   │                  │
                   │PENABLE=0 │                  │
                   └────┬─────┘                  │
                        │                        │
                   Always                        │
                   (1 cycle)                     │
                        │                        │
                        ▼                        │
                   ┌──────────┐                  │
           ┌──────>│  ACCESS  │──────────────────┘
           │       │ PSEL=1   │    PREADY=1
           │       │PENABLE=1 │    (transfer done)
           │       └────┬─────┘
           │            │
           └────────────┘
            PREADY=0
            (wait state)
```

---

## 8. Notre projet : APB Slave avec 4 registres

### Architecture

```
                     ┌─────────────────────────────┐
                     │        APB SLAVE            │
     APB Master      │                             │
    (testbench)      │   ┌─────┐  REG0 (0x00)     │
         │           │   │     │                   │
    PSEL ───────────>│   │     │  REG1 (0x04)     │
    PENABLE ────────>│   │REGS │                   │
    PWRITE ─────────>│   │     │  REG2 (0x08)     │
    PADDR ──────────>│   │     │                   │
    PWDATA ─────────>│   └─────┘  REG3 (0x0C)     │
         │           │                             │
    PREADY <─────────│                             │
    PRDATA <─────────│                             │
    PSLVERR <────────│                             │
                     └─────────────────────────────┘
```

---

## 9. Questions de compréhension

Avant de coder, vérifie que tu as compris :

1. **Combien de cycles minimum faut-il pour un transfert APB ?**
   - A) 1 cycle
   - B) 2 cycles
   - C) 3 cycles

2. **Pendant quelle phase PENABLE est-il à 1 ?**
   - A) IDLE
   - B) SETUP
   - C) ACCESS

3. **Que se passe-t-il si PREADY reste à 0 pendant ACCESS ?**

4. **Quelle est la condition pour qu'un transfert soit complété ?**

5. **Pourquoi APB est-il plus simple qu'AXI-Lite ?**

