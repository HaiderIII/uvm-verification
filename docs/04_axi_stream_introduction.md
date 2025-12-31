# Introduction au Protocole AXI-Stream

## Objectif de ce document

Avant de coder le VIP AXI-Stream, comprenons d'abord ce protocole qui est **fondamentalement différent** d'AXI-Lite.

---

## 1. AXI-Lite vs AXI-Stream : Deux philosophies

### AXI-Lite : Memory-Mapped (ce qu'on a fait)
```
CPU/Master                          Slave/Périphérique
    |                                      |
    |  ----  WRITE addr=0x04, data  ---->  |   (écrit à une adresse)
    |                                      |
    |  ----  READ addr=0x04  ----------->  |   (lit une adresse)
    |  <---  data  ----------------------  |
```
- Accès à des **registres** via des **adresses**
- Bidirectionnel (read + write)
- Utilisé pour : configuration, status, contrôle

### AXI-Stream : Data Flow (ce qu'on va faire)
```
Source                              Sink
    |                                 |
    |  ---- data0 ---- data1 ---->   |   (flux continu de données)
    |  ---- data2 ---- data3 ---->   |
    |  ---- data4 [LAST] -------->   |   (fin du paquet)
```
- **Pas d'adresse** - juste un flux de données
- **Unidirectionnel** (source → sink)
- Utilisé pour : streaming vidéo, audio, paquets réseau, **NoC !**

---

## 2. Les signaux AXI-Stream

### Signaux obligatoires

| Signal   | Direction      | Description |
|----------|----------------|-------------|
| `TVALID` | Source → Sink  | "J'ai une donnée à envoyer" |
| `TREADY` | Sink → Source  | "Je suis prêt à recevoir" |
| `TDATA`  | Source → Sink  | Les données (8, 16, 32, 64... bits) |

### Signaux optionnels (mais très utilisés)

| Signal   | Direction      | Description |
|----------|----------------|-------------|
| `TLAST`  | Source → Sink  | "C'est le dernier mot du paquet" |
| `TKEEP`  | Source → Sink  | Quels bytes sont valides |
| `TSTRB`  | Source → Sink  | Quels bytes sont des données (vs position) |
| `TID`    | Source → Sink  | Identifiant du stream (pour multi-stream) |
| `TDEST`  | Source → Sink  | Destination routing (pour NoC !) |
| `TUSER`  | Source → Sink  | Sideband user-defined |

---

## 3. Le Handshake AXI-Stream

Identique à AXI-Lite ! Le transfert se fait quand `TVALID=1` ET `TREADY=1`.

### Chronogramme d'un transfert simple

```
         Cycle:    1     2     3     4     5     6
                   │     │     │     │     │     │
                   ▼     ▼     ▼     ▼     ▼     ▼
    CLK        ────┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──
                   └──┘  └──┘  └──┘  └──┘  └──┘  └──┘

    TVALID     ─────────┐                    ┌────────
               LOW      └────────────────────┘  LOW

    TREADY     ───────────────┐        ┌─────────────
               LOW            └────────┘  LOW

    TDATA      ═════════╤═══════════════╪════════════
               (X)      │    0xABCD     │   (X)
                        ╧═══════════════╧

                              │     │
                              └──┬──┘
                                 │
                           TRANSFERT!
                        (TVALID=1 ET TREADY=1)
```

**Explication :**
- Cycle 2 : Source met TVALID=1 avec TDATA=0xABCD
- Cycle 2-3 : Sink pas prêt (TREADY=0), source maintient
- Cycle 4 : Sink prêt (TREADY=1) → **TRANSFERT**
- Cycle 5 : Les deux reviennent à 0

---

## 4. Le signal TLAST : Notion de paquet

En AXI-Stream, les données sont groupées en **paquets**. `TLAST=1` indique le dernier mot.

### Exemple : Envoi d'un paquet de 4 mots

```
         Cycle:    1     2     3     4     5
                   │     │     │     │     │
                   ▼     ▼     ▼     ▼     ▼
    CLK        ────┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──
                   └──┘  └──┘  └──┘  └──┘  └──┘

    TVALID     ────┐                       ┌─────
               LOW └───────────────────────┘

    TREADY     ────┐                       ┌─────
               LOW └───────────────────────┘

    TDATA      ════╤═════╤═════╤═════╤═════╪═════
                   │ D0  │ D1  │ D2  │ D3  │
                   ╧═════╧═════╧═════╧═════╧

    TLAST      ────────────────────────┐   ┌─────
               LOW                     └───┘
                                        ▲
                                        │
                                   FIN DE PAQUET
```

**Interprétation :**
- Paquet = [D0, D1, D2, D3]
- D3 est marqué avec TLAST=1
- Le récepteur sait que le paquet est complet

---

## 5. Back-pressure : Quand le Sink est lent

### Scénario : Sink occupe tous les 2 cycles

```
         Cycle:    1     2     3     4     5     6     7
                   │     │     │     │     │     │     │
                   ▼     ▼     ▼     ▼     ▼     ▼     ▼
    CLK        ────┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
                   └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘

    TVALID     ────┐                             ┌───────
               LOW └─────────────────────────────┘

    TREADY     ────┐     ┌─────┐     ┌─────┐     ┌───────
               LOW └─────┘     └─────┘     └─────┘

    TDATA      ════╤═══════════╤═══════════╤═════╪═══════
                   │    D0     │    D1     │ D2  │
                   ╧═══════════╧═══════════╧═════╧

                   │     │     │     │     │
                   └──┬──┘     └──┬──┘     └──┬──┘
                      │           │           │
                   XFER D0     XFER D1     XFER D2
```

**Points clés :**
- La source garde TVALID=1 et TDATA stable tant que TREADY=0
- Quand TREADY passe à 1, le transfert se fait
- La source peut alors changer TDATA pour la donnée suivante
- C'est le mécanisme de **back-pressure** (le sink "freine" la source)

---

## 6. Pourquoi AXI-Stream pour les NoC ?

Dans un Network-on-Chip, les données circulent en **paquets** entre les routeurs :

```
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │  Core 0 │ ──AXI-S─→│ Router  │──AXI-S─→│  Core 1 │
    └─────────┘         └─────────┘         └─────────┘
                             │
                           AXI-S
                             │
                             ▼
                        ┌─────────┐
                        │ Router  │
                        └─────────┘
```

**Pourquoi c'est parfait :**
1. **Pas d'adresse** - le routage est fait par `TDEST` ou dans le header du paquet
2. **TLAST** - délimite clairement les paquets
3. **Back-pressure** - gère la congestion naturellement
4. **Simple** - peu de signaux, facile à router

---

## 7. Notre projet : AXI-Stream FIFO avec VIP

### Architecture

```
                    ┌─────────────────────────────────────┐
                    │         AXI-Stream FIFO             │
    ┌──────────┐    │    ┌────────────────────┐          │    ┌──────────┐
    │  Master  │────│───→│                    │          │────│  Slave   │
    │   VIP    │ S  │    │   FIFO (depth=8)   │          │ M  │   VIP    │
    │ (Source) │    │    │                    │          │    │  (Sink)  │
    └──────────┘    │    └────────────────────┘          │    └──────────┘
                    │                                     │
                    │  s_axis_*            m_axis_*       │
                    └─────────────────────────────────────┘
```

### Composants à créer

1. **RTL : `axi_stream_fifo.sv`**
   - FIFO asynchrone ou synchrone
   - Entrée : interface slave (s_axis_*)
   - Sortie : interface master (m_axis_*)

2. **VIP Master : `AXIStreamMaster`**
   - Envoie des paquets de données
   - Gère TVALID, TDATA, TLAST

3. **VIP Slave : `AXIStreamSlave`**
   - Reçoit des paquets de données
   - Gère TREADY
   - Peut simuler un sink lent (back-pressure)

4. **Monitor : `AXIStreamMonitor`**
   - Observe les deux côtés
   - Vérifie que données entrantes = données sortantes

---

## 8. Questions de compréhension

Avant de coder, vérifiez que vous avez compris :

1. **Quelle est la différence fondamentale entre AXI-Lite et AXI-Stream ?**

2. **Dans AXI-Stream, comment le récepteur sait-il qu'un paquet est terminé ?**

3. **Que se passe-t-il si TVALID=1 mais TREADY=0 ?**

4. **Pourquoi AXI-Stream est-il adapté aux NoC ?**

---

## 9. Prochaines étapes

Une fois les questions validées :
1. Créer le RTL de la FIFO AXI-Stream
2. Créer le VIP Master (source)
3. Créer le VIP Slave (sink) avec back-pressure configurable
4. Créer le Monitor
5. Écrire les tests

