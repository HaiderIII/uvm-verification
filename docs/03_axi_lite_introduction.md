# Projet 2 : Introduction à AXI-Lite

## Pourquoi apprendre les protocoles AMBA ?

Le poste NoC demande :
> "Knowledge of communication protocols such as ARM AMBA protocols would be a plus"

**AMBA** (Advanced Microcontroller Bus Architecture) est le standard de ARM pour connecter les composants dans un SoC (System on Chip).

```
┌─────────────────────────────────────────────────────────────┐
│                         SoC                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │   CPU   │    │   GPU   │    │   DMA   │    │  UART   │  │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
│       │              │              │              │        │
│  ═════╪══════════════╪══════════════╪══════════════╪═════  │
│       │         AXI Interconnect (NoC)             │        │
│  ═════╪══════════════╪══════════════╪══════════════╪═════  │
│       │              │              │              │        │
│  ┌────┴────┐    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐  │
│  │  DRAM   │    │  Flash  │    │  Timer  │    │  GPIO   │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## La famille AMBA

| Protocole | Complexité | Usage |
|-----------|------------|-------|
| **APB** | Simple | Périphériques lents (GPIO, UART) |
| **AHB** | Moyen | Legacy, bus partagé |
| **AXI4** | Complexe | Haute performance (mémoire, DMA) |
| **AXI4-Lite** | Simple | Registres de configuration |
| **AXI4-Stream** | Moyen | Streaming de données (vidéo, audio) |

**On commence par AXI4-Lite** car c'est le plus simple, mais il contient les concepts clés d'AXI.

---

## Qu'est-ce que AXI-Lite ?

AXI-Lite est un protocole pour **lire et écrire des registres** à des adresses mémoire.

### Exemple d'utilisation

```
CPU veut configurer un timer :
1. Écrire la valeur 1000 à l'adresse 0x4000_0000 (registre de période)
2. Écrire 1 à l'adresse 0x4000_0004 (registre enable)
3. Lire l'adresse 0x4000_0008 (registre status)

→ Tout ça passe par AXI-Lite !
```

---

## Architecture Master / Slave

```
┌──────────────────┐                    ┌──────────────────┐
│                  │                    │                  │
│     MASTER       │                    │      SLAVE       │
│   (ex: CPU)      │◄──────────────────▶│  (ex: Timer)     │
│                  │    AXI-Lite Bus    │                  │
│  - Initie les    │                    │  - Répond aux    │
│    transactions  │                    │    transactions  │
│                  │                    │                  │
└──────────────────┘                    └──────────────────┘
```

| Rôle | Qui ? | Action |
|------|-------|--------|
| **Master** | CPU, DMA | Initie les lectures/écritures |
| **Slave** | Timer, GPIO, mémoire | Répond aux requêtes |

---

## Les 5 canaux AXI-Lite

AXI-Lite utilise **5 canaux** séparés :

```
          MASTER                              SLAVE
      ┌──────────┐                        ┌──────────┐
      │          │──── Write Address ────▶│          │
      │          │──── Write Data ───────▶│          │
      │          │◀─── Write Response ────│          │
      │          │                        │          │
      │          │──── Read Address ─────▶│          │
      │          │◀─── Read Data ─────────│          │
      └──────────┘                        └──────────┘
```

| Canal | Direction | Rôle |
|-------|-----------|------|
| **AW** (Write Address) | Master → Slave | Adresse où écrire |
| **W** (Write Data) | Master → Slave | Données à écrire |
| **B** (Write Response) | Slave → Master | Confirmation d'écriture |
| **AR** (Read Address) | Master → Slave | Adresse où lire |
| **R** (Read Data) | Slave → Master | Données lues |

---

## Le Handshake VALID/READY

C'est **LE concept clé** d'AXI. Chaque canal utilise un handshake :

```
**Convention de lecture :**
- Ligne en HAUT = signal à 1 (HIGH)
- Ligne en BAS = signal à 0 (LOW)

                         ┌───────────────
VALID                    │ =1 (prêt)
       ──────────────────┘ =0 (pas prêt)

                               ┌─────────
READY                          │ =1 (prêt)
       ────────────────────────┘ =0 (pas prêt)
                               ↑
                               └── Transfert quand VALID=1 ET READY=1
```

### Règles du handshake

1. **VALID** : "J'ai des données prêtes"
2. **READY** : "Je suis prêt à recevoir"
3. **Transfert** : Se produit quand `VALID=1 AND READY=1`

### Les 3 scénarios possibles

```
Scénario 1 : VALID passe à 1 avant READY
────────────────────────────────────────
        clk  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
             │  │  │  │  │  │  │  │  │  │
          ───┘  └──┘  └──┘  └──┘  └──┘  └──

                    ┌───────────────────────
      VALID         │ =1 (Master prêt)
          ──────────┘

                          ┌─────────────────
      READY               │ =1 (Slave prêt)
          ────────────────┘
                          ↑
                          Transfert ! (les deux à 1)

Scénario 2 : READY passe à 1 avant VALID
────────────────────────────────────────
        clk  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
             │  │  │  │  │  │  │  │  │  │
          ───┘  └──┘  └──┘  └──┘  └──┘  └──

                          ┌─────────────────
      VALID               │ =1 (Master prêt)
          ────────────────┘

                    ┌───────────────────────
      READY         │ =1 (Slave prêt)
          ──────────┘
                          ↑
                          Transfert ! (les deux à 1)

Scénario 3 : VALID et READY passent à 1 en même temps
─────────────────────────────────────────────────────
        clk  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
             │  │  │  │  │  │  │  │  │  │
          ───┘  └──┘  └──┘  └──┘  └──┘  └──

                    ┌───────────────────────
      VALID         │ =1
          ──────────┘
                    ┌───────────────────────
      READY         │ =1
          ──────────┘
                    ↑
                    Transfert immédiat !
```

---

## Signaux AXI-Lite complets

### Canal Write Address (AW)

| Signal | Largeur | Direction | Description |
|--------|---------|-----------|-------------|
| `AWADDR` | 32 bits | M→S | Adresse d'écriture |
| `AWPROT` | 3 bits | M→S | Protection (ignoré souvent) |
| `AWVALID` | 1 bit | M→S | Adresse valide |
| `AWREADY` | 1 bit | S→M | Slave prêt |

### Canal Write Data (W)

| Signal | Largeur | Direction | Description |
|--------|---------|-----------|-------------|
| `WDATA` | 32 bits | M→S | Données à écrire |
| `WSTRB` | 4 bits | M→S | Byte enables (quels octets écrire) |
| `WVALID` | 1 bit | M→S | Données valides |
| `WREADY` | 1 bit | S→M | Slave prêt |

### Canal Write Response (B)

| Signal | Largeur | Direction | Description |
|--------|---------|-----------|-------------|
| `BRESP` | 2 bits | S→M | Réponse (00=OK, 10=SLVERR) |
| `BVALID` | 1 bit | S→M | Réponse valide |
| `BREADY` | 1 bit | M→S | Master prêt à recevoir |

### Canal Read Address (AR)

| Signal | Largeur | Direction | Description |
|--------|---------|-----------|-------------|
| `ARADDR` | 32 bits | M→S | Adresse de lecture |
| `ARPROT` | 3 bits | M→S | Protection (ignoré souvent) |
| `ARVALID` | 1 bit | M→S | Adresse valide |
| `ARREADY` | 1 bit | S→M | Slave prêt |

### Canal Read Data (R)

| Signal | Largeur | Direction | Description |
|--------|---------|-----------|-------------|
| `RDATA` | 32 bits | S→M | Données lues |
| `RRESP` | 2 bits | S→M | Réponse (00=OK, 10=SLVERR) |
| `RVALID` | 1 bit | S→M | Données valides |
| `RREADY` | 1 bit | M→S | Master prêt à recevoir |

---

## Transaction d'écriture

```
        clk   ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
           ───┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └───

                  ┌─────────┐
     AWVALID      │ =1      │
           ───────┘         └───────────────────
     AWADDR  ─────< 0x100   >───────────────────
                        ┌───┐
     AWREADY            │=1 │
           ─────────────┘   └───────────────────
                        ↑
                        Adresse acceptée (AWVALID=1 & AWREADY=1)

                  ┌─────────┐
      WVALID      │ =1      │
           ───────┘         └───────────────────
      WDATA  ─────< 0xAB    >───────────────────
                        ┌───┐
      WREADY            │=1 │
           ─────────────┘   └───────────────────
                        ↑
                        Données acceptées

                              ┌───┐
      BVALID                  │=1 │
           ───────────────────┘   └─────────────
      BRESP  ─────────────────< OK >────────────
                    ┌─────────────────────────
      BREADY        │ =1 (Master toujours prêt)
           ─────────┘
                              ↑
                              Écriture confirmée !
```

---

## Transaction de lecture

```
        clk   ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
           ───┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └───

                  ┌─────────┐
     ARVALID      │ =1      │
           ───────┘         └───────────────────
     ARADDR  ─────< 0x100   >───────────────────
                        ┌───┐
     ARREADY            │=1 │
           ─────────────┘   └───────────────────
                        ↑
                        Adresse acceptée

                              ┌───┐
      RVALID                  │=1 │
           ───────────────────┘   └─────────────
      RDATA  ─────────────────< 0xAB >──────────
      RRESP  ─────────────────< OK   >──────────
                    ┌─────────────────────────
      RREADY        │ =1 (Master toujours prêt)
           ─────────┘
                              ↑
                              Données reçues !
```

---

## Ce qu'on va coder

### 1. AXI-Lite Slave (RTL)

Un bloc mémoire simple avec 4 registres :
- Adresse 0x00 : Registre 0
- Adresse 0x04 : Registre 1
- Adresse 0x08 : Registre 2
- Adresse 0x0C : Registre 3

### 2. AXI-Lite Master (VIP en Python)

Un **driver** Cocotb qui :
- Peut écrire à une adresse
- Peut lire une adresse
- Gère le handshake VALID/READY

### 3. Tests

- Écrire puis relire → vérifier cohérence
- Écrire à plusieurs adresses
- Accès à adresse invalide → vérifier SLVERR

---

## Questions de compréhension

Avant de coder, réponds à ces questions :

### Question 1
Dans un handshake, qui décide quand le transfert a lieu ?
- A) Le Master seul (avec VALID)
- B) Le Slave seul (avec READY)
- C) Les deux ensemble (VALID AND READY)

### Question 2
Pour écrire la valeur 0x1234 à l'adresse 0x100, combien de canaux sont utilisés ?

### Question 3
Quelle est la différence entre AXI4 complet et AXI4-Lite ?

<details>
<summary>Réponses</summary>

**Q1 : C)** Les deux ensemble. Le transfert se produit quand VALID=1 ET READY=1.

**Q2 : 3 canaux**
- AW : Envoie l'adresse 0x100
- W : Envoie les données 0x1234
- B : Reçoit la confirmation

**Q3 :** AXI4 complet supporte :
- Bursts (transferts multiples)
- Transactions out-of-order
- IDs de transaction
- Plusieurs tailles de données

AXI4-Lite est simplifié :
- Pas de bursts (1 transfert à la fois)
- Toujours 32 bits
- Pas d'IDs
- Plus simple à implémenter

</details>

---

## Ressources

- [ARM AMBA AXI Protocol Specification](https://developer.arm.com/documentation/ihi0022/latest)
- [AXI4-Lite Tutorial (ZipCPU)](https://zipcpu.com/blog/2020/03/08/easyaxil.html)
