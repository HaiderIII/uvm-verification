# Introduction aux Network-on-Chip (NoC)

## Objectif de ce document

Comprendre les concepts fondamentaux des NoC avant de créer un environnement de vérification.

---

## 1. Pourquoi un NoC ?

### Le problème : trop d'IP à connecter

Dans un SoC moderne, on a des dizaines de composants :

```
┌─────────────────────────────────────────────────────────────┐
│                          SoC                                │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐      │
│  │CPU 0│  │CPU 1│  │ GPU │  │ DSP │  │ DMA │  │Crypto│     │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘      │
│                                                             │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                        │
│  │ DDR │  │SRAM │  │ PCIe│  │ USB │   ... et 20 autres     │
│  └─────┘  └─────┘  └─────┘  └─────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Solution 1 : Bus partagé (ancien)

```
    CPU0    CPU1    GPU     DSP     DDR     SRAM
      │       │       │       │       │       │
      └───────┴───────┴───────┴───────┴───────┘
                      │
              ┌───────────────┐
              │  BUS PARTAGÉ  │
              └───────────────┘
```

**Problèmes :**
- Un seul transfert à la fois
- Goulot d'étranglement
- Ne scale pas (>10 IP = catastrophe)

### Solution 2 : NoC (moderne)

```
    ┌─────┐     ┌─────┐     ┌─────┐
    │ CPU │     │ GPU │     │ DSP │
    └──┬──┘     └──┬──┘     └──┬──┘
       │           │           │
    ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
    │ R00 │─────│ R01 │─────│ R02 │    R = Router
    └──┬──┘     └──┬──┘     └──┬──┘
       │           │           │
    ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
    │ R10 │─────│ R11 │─────│ R12 │
    └──┬──┘     └──┬──┘     └──┬──┘
       │           │           │
    ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
    │ DDR │     │SRAM │     │ DMA │
    └─────┘     └─────┘     └─────┘
```

**Avantages :**
- Transferts parallèles (CPU→DDR en même temps que GPU→SRAM)
- Scalable (ajouter des routeurs)
- Bande passante élevée

---

## 2. Anatomie d'un NoC

### Les composants

| Composant | Rôle |
|-----------|------|
| **Router** | Reçoit les paquets et les forward vers la bonne direction |
| **Link** | Connexion physique entre deux routeurs |
| **Network Interface (NI)** | Adapte le protocole IP (AXI) vers le protocole NoC |
| **Packet** | Unité de données qui traverse le réseau |

### Structure d'un paquet NoC

```
┌─────────────────────────────────────────────────────┐
│                    PAQUET NoC                       │
├──────────┬──────────┬──────────┬───────────────────┤
│  HEADER  │  SOURCE  │   DEST   │      PAYLOAD      │
│  (type)  │  (x,y)   │  (x,y)   │     (données)     │
├──────────┼──────────┼──────────┼───────────────────┤
│  4 bits  │  8 bits  │  8 bits  │    32+ bits       │
└──────────┴──────────┴──────────┴───────────────────┘
```

- **Header** : Type de paquet (READ_REQ, WRITE_REQ, RESPONSE, etc.)
- **Source** : Coordonnées (x,y) de l'émetteur
- **Dest** : Coordonnées (x,y) du destinataire
- **Payload** : Les données (adresse, data, etc.)

---

## 3. Le Routage

### Algorithme XY (le plus simple)

Le paquet va d'abord horizontalement (X), puis verticalement (Y).

**Exemple : (0,0) → (2,1)**

```
    (0,0)───────(1,0)───────(2,0)
      │           │           │
      │           │           │
    (0,1)       (1,1)       (2,1)  ← Destination
      │           │           │

    Chemin: (0,0) → (1,0) → (2,0) → (2,1)
            ────X────────────────→ puis ↓Y
```

### Pourquoi XY ?
- Simple à implémenter
- Pas de deadlock (si tous utilisent le même algorithme)
- Déterministe (même chemin à chaque fois)

---

## 4. Les défis de vérification NoC

### Ce qu'il faut vérifier

| Test | Description |
|------|-------------|
| **Routage correct** | Le paquet arrive à la bonne destination |
| **Intégrité des données** | Les données ne sont pas corrompues |
| **Pas de deadlock** | Le réseau ne se bloque pas |
| **Pas de livelock** | Les paquets ne tournent pas en boucle |
| **Latence** | Le temps de traversée est acceptable |
| **Bande passante** | Le débit sous charge est correct |
| **Congestion** | Le réseau gère les pics de trafic |

### Scénarios de test typiques

1. **Single packet** : Un paquet de A vers B
2. **Multi-source** : Plusieurs sources vers une destination
3. **Multi-dest** : Une source vers plusieurs destinations
4. **All-to-all** : Tous les nœuds communiquent
5. **Hot-spot** : Trafic concentré sur un nœud (stress test)

---

## 5. Notre projet : Router 5-ports

### Architecture

Nous allons créer un routeur simple avec 5 ports :

```
                    NORTH
                      │
                      ▼
              ┌───────────────┐
     WEST ───►│               │◄─── EAST
              │    ROUTER     │
     WEST ◄───│               │───► EAST
              └───────────────┘
                      │
                      ▼
                    SOUTH
                      │
                      ▼
                    LOCAL
               (IP connectée)
```

### Les 5 ports

| Port | Direction | Usage |
|------|-----------|-------|
| **North** | Vers routeur (x, y-1) | Connexion mesh |
| **South** | Vers routeur (x, y+1) | Connexion mesh |
| **East** | Vers routeur (x+1, y) | Connexion mesh |
| **West** | Vers routeur (x-1, y) | Connexion mesh |
| **Local** | Vers l'IP connectée | Injection/éjection |

### Interface : AXI-Stream !

Chaque port utilise AXI-Stream (ce qu'on a appris au Projet 3) :

```
    Port North IN:   north_in_tdata, north_in_tvalid, north_in_tready, north_in_tlast
    Port North OUT:  north_out_tdata, north_out_tvalid, north_out_tready, north_out_tlast
    ... (même chose pour South, East, West, Local)
```

---

## 6. Ce qu'on va construire

### RTL

- `noc_packet.sv` : Définition du format de paquet
- `noc_router.sv` : Router 5-ports avec routage XY

### VIP (Verification IP)

- `NoCPacketGenerator` : Génère des paquets avec source/dest aléatoires
- `NoCDriver` : Injecte les paquets dans le port Local
- `NoCMonitor` : Capture les paquets sur tous les ports
- `NoCScoreboard` : Vérifie que chaque paquet arrive à destination

### Tests

1. **test_local_to_north** : Paquet local vers le nord
2. **test_routing_xy** : Vérifier le routage XY
3. **test_multiple_packets** : Plusieurs paquets simultanés
4. **test_back_pressure** : Router sous congestion

---

## 7. Questions de compréhension

1. **Quelle est la différence principale entre un bus partagé et un NoC ?**

2. **Dans l'algorithme de routage XY, si je suis en (1,1) et je veux aller en (3,2), quelle est la prochaine direction ?**
   - A) North
   - B) South
   - C) East
   - D) West

3. **Pourquoi utilise-t-on AXI-Stream pour les liens du NoC ?**

4. **Quel champ du paquet permet au routeur de décider où envoyer le paquet ?**

