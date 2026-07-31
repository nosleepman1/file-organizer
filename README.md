# Smart File Organizer Pro

Smart File Organizer Pro est une solution logicielle open-source de tri, de réorganisation et d'automatisation de fichiers pour systèmes Windows, Linux et macOS. L'application intègre une architecture découplée associant un backend Python Flask performant et une interface utilisateur réactive développée en React 18, TypeScript et Vite.

L'outil propose des modes de classement déterministes (par type, date, taille), un mode d'analyse sémantique propulsé par des modèles d'intelligence artificielle multi-fournisseurs (Ollama 100% local et hors-ligne, DeepSeek, OpenAI, endpoints REST personnalisés), une recherche de doublons par empreinte SHA256 avec mise en cache disque, ainsi qu'un service d'arrière-plan autonome et de démarrage au boot système.

---

## Sommaire

1. [Architecture du Projet](#architecture-du-projet)
2. [Prérequis](#prérequis)
3. [Installation](#installation)
4. [Guide d'Utilisation](#guide-dutilisation)
   - [Interface Web (Dashboard React)](#1-interface-web-dashboard-react)
   - [Interface en Ligne de Commande (CLI)](#2-interface-en-ligne-de-commande-cli)
   - [Service Daemon et Démarrage au Boot](#3-service-daemon-et-démarrage-au-boot)
5. [Spécifications Techniques et Sécurité](#spécifications-techniques-et-sécurité)
   - [Configuration Multi-Fournisseurs IA](#configuration-multi-fournisseurs-ia)
   - [Mise en Cache SHA256 et Exécution Parallèle](#mise-en-cache-sha256-et-exécution-parallèle)
   - [Sécurité et Chiffrement des Clés API](#sécurité-et-chiffrement-des-clés-api)
   - [Suppression Sécurisée (Corbeille OS)](#suppression-sécurisée-corbeille-os)
6. [Suite de Tests](#suite-de-tests)
7. [Licence](#licence)

---

## Architecture du Projet

Le projet est structuré selon un modèle monorepo strict séparant la logique applicative backend, l'interface frontend React et le code de production :

```text
file-organizer/
├── backend/
│   ├── core/                           # Engine métier Python
│   │   ├── ai_organizer.py             # Adaptateur LLM Multi-Fournisseurs (Ollama, DeepSeek, OpenAI)
│   │   ├── autostart.py                # Gestionnaire du service boot (Windows, Linux, macOS)
│   │   ├── config.py                   # Gestionnaire de configuration & chiffrement des clés
│   │   ├── hash_cache.py               # Cache disque thread-safe des empreintes SHA256
│   │   ├── history.py                  # Transaction log et rapport digest 24 heures
│   │   ├── organizer.py                # Moteur d'organisation, filtres et suppression sécurisée
│   │   ├── rules.py                    # Définition et persistance des règles d'extension
│   │   └── watcher.py                  # Surveillance système de fichiers temps réel (Watchdog)
│   ├── tests/                          # Suite de tests automatisés (unittest)
│   │   ├── test_deepseek_and_surgical.py
│   │   ├── test_organizer.py
│   │   ├── test_performance_and_ui.py
│   │   └── test_security_and_ai.py
│   ├── web/                            # Bundle de production du frontend généré par Vite
│   ├── organizer_cli.py                # Point d'entrée pour la CLI et le mode Daemon
│   ├── server.py                       # Serveur Web Flask & API REST
│   └── requirements.txt                # Dépendances Python backend
├── frontend/                           # Application Single Page React + TypeScript + Vite
│   ├── src/
│   │   ├── components/                 # Composants UI modulaires par domaine
│   │   │   ├── ai/                     # Configuration et tests des modèles IA
│   │   │   ├── digest/                 # Visualisation du rapport des dernières 24 heures
│   │   │   ├── duplicates/             # Gestion et nettoyage des doublons SHA256
│   │   │   ├── layout/                 # En-tête, barre latérale et sélecteur de thèmes
│   │   │   ├── preview/                # Tableau réactif des actions de tri
│   │   │   ├── rename/                 # Outil de renommage en masse
│   │   │   ├── rules/                  # Gestionnaire dynamique de règles et catégories
│   │   │   ├── surgical/               # Formulaire des filtres avancés (Regex, Taille, Date)
│   │   │   └── ui/                     # Primitives d'interface Shadcn UI (button, card, input, switch, badge)
│   │   ├── lib/                        # Utilitaires d'interface (cn utility)
│   │   ├── services/                   # Client d'API REST typé pour communication avec Flask
│   │   ├── types/                      # Interfaces et types TypeScript stricts
│   │   ├── App.tsx                     # Composant racine
│   │   ├── index.css                   # Design system et thèmes de couleurs
│   │   └── main.tsx                    # Point d'entrée de l'application React
│   ├── package.json                    # Dépendances Node (inclut @nosleepman/react-starter)
│   ├── tsconfig.json                   # Configuration du compilateur TypeScript
│   └── vite.config.ts                  # Configuration du bundler Vite
├── .gitignore
└── README.md
```

---

## Prérequis

### Environnement Backend
- Python 3.10 ou version supérieure
- Gestionnaire de paquets `pip`

### Environnement Frontend (Développement / Build)
- Node.js version 18.0 ou supérieure
- Gestionnaire de paquets `npm` ou `yarn`

---

## Installation

### 1. Clonage du Dépôt

```bash
git clone https://github.com/nosleepman1/file-organizer.git
cd file-organizer
```

### 2. Installation du Backend Python

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Installation et Compilations du Frontend React (Optionnel en cas de modification source)

```bash
cd frontend
npm install
npm run build
cd ..
```

Le script de build Vite compile automatiquement les assets optimisés directement dans le dossier `backend/web/`.

---

## Guide d'Utilisation

### 1. Interface Web (Dashboard React)

Pour démarrer le serveur Web Flask local et accéder à l'interface graphique :

```bash
python backend/server.py
```

Ouvrez ensuite votre navigateur à l'adresse suivante :
`http://localhost:5000`

L'interface web permet de :
- Sélectionner le dossier cible à réorganiser (avec raccourcis vers `DOWNLOADS`, `DESKTOP`, `DOCUMENTS`).
- Choisir le mode d'organisation (par Type, par Date, par Taille, ou par IA Sémantique).
- Définir des filtres chirurgicaux (expressions régulières, seuils de taille en Mo, fenêtres de date).
- Configurer les paramètres d'IA (Ollama local offline, DeepSeek, OpenAI).
- Consulter le tableau d'aperçu des déplacements avec détection automatique des collisions de nom.
- Exécuter la réorganisation ou annuler l'opération précédente (Undo).
- Analyser et nettoyer les fichiers doublons exacts par hash SHA256 avec mise en Corbeille sécurisée.
- Suivre les statistiques du disque et le rapport digest d'activité sur 24 heures.

### 2. Interface en Ligne de Commande (CLI)

L'interface CLI permet d'exécuter des opérations de tri rapidement ou d'intégrer l'outil dans des scripts d'automatisation.

#### Scanner un dossier sans modifier les fichiers (Mode Aperçu / Dry-Run)
```bash
python backend/organizer_cli.py scan -d DOWNLOADS --mode type
```

#### Scanner en appliquant le classement par IA DeepSeek
```bash
python backend/organizer_cli.py scan -d DOWNLOADS --ai
```

#### Scanner avec des filtres chirurgicaux
```bash
python backend/organizer_cli.py scan -d DOWNLOADS --regex ".*\.pdf$" --min-size 5.0 --days 30
```

#### Exécuter la réorganisation avec confirmation automatique
```bash
python backend/organizer_cli.py organize -d DOWNLOADS --mode type -y
```

#### Annuler la dernière opération de réorganisation (Undo)
```bash
python backend/organizer_cli.py undo -d DOWNLOADS
```

#### Consulter le rapport d'activité des dernières 24 heures
```bash
python backend/organizer_cli.py history -d DOWNLOADS --last-24h
```

#### Configurer le fournisseur IA via la CLI
```bash
# Configuration d'Ollama local (Offline)
python backend/organizer_cli.py config --provider ollama --model llama3:latest

# Configuration de la clé API DeepSeek
python backend/organizer_cli.py config --provider deepseek --key "sk-votre-cle-api" --model "deepseek-chat"
```

### 3. Service Daemon et Démarrage au Boot

Le système permet de démarrer une surveillance continue d'un dossier ou de configurer un service d'arrière-plan démarrant automatiquement au boot du système d'exploitation.

#### Lancer le daemon de surveillance continue
```bash
python backend/organizer_cli.py daemon -d DOWNLOADS --mode type
```

#### Gérer le service au boot du système (Windows Startup, Linux systemd, macOS launchd)
```bash
# Activer le service au démarrage de la machine
python backend/organizer_cli.py service install

# Vérifier le statut du service
python backend/organizer_cli.py service status

# Désactiver le service
python backend/organizer_cli.py service uninstall
```

---

## Spécifications Techniques et Sécurité

### Configuration Multi-Fournisseurs IA

Le moteur `DeepSeekEngine` (`backend/core/ai_organizer.py`) prend en charge plusieurs fournisseurs de modèles de langage :
- **Ollama Local (100% Offline)** : Fonctionne sur le port local `http://localhost:11434` sans envoi de données à des tiers et sans clé API.
- **DeepSeek API** : Modèles `deepseek-chat` et `deepseek-coder` via protocole REST.
- **OpenAI API** : Modèles `gpt-4o-mini` et `gpt-4o`.
- **Custom REST Endpoint** : Compatibilité avec les serveurs locaux compatibles OpenAI (LM Studio, LocalAI, vLLM).
- **Analyse du Contenu (Content-Aware Parsing)** : Extraction automatique des 500 premiers caractères des fichiers texte et code (`.txt`, `.md`, `.json`, `.py`, `.sql`, etc.) pour affiner la classification sémantique basée sur le contenu réel des documents.

### Mise en Cache SHA256 et Exécution Parallèle

- La classe `HashCacheManager` (`backend/core/hash_cache.py`) conserve un index persistant au format JSON enregistrant les métadonnées des fichiers (`mtime`, `size`, `sha256`). Si la date de modification et la taille d'un fichier n'ont pas changé, le calcul coûteux du hash est évité.
- La recherche de doublons dans `FileOrganizer.scan_duplicates` exploite un pool de threads d'exécution (`concurrent.futures.ThreadPoolExecutor`) pour calculer en parallèle les empreintes SHA256 des fichiers suspects de même taille.

### Sécurité et Chiffrement des Clés API

- Les clés API enregistrées dans la configuration (`organizer_config.json`) sont automatiquement chiffrees au repos.
- Le chiffrement repose sur un algorithme XOR-Base64 utilisant une clé dérivée de l'identifiant matériel de la machine cliente (`uuid.getnode()` et `platform.node()`). Une configuration copiée sur un autre ordinateur ne permettra pas d'exposer la clé API en clair.

### Suppression Sécurisée (Corbeille OS)

- La fonction `safe_delete_file` (`backend/core/organizer.py`) utilise la bibliothèque `send2trash` pour envoyer les fichiers doublons supprimés dans la Corbeille du système d'exploitation au lieu d'effectuer une suppression définitive.
- En cas d'indisponibilité du sous-système de la corbeille, un mécanisme de repli déplace automatiquement le fichier vers un répertoire sécurisé `.organizer_trash/` situé dans le dossier cible.

---

## Suite de Tests

Le projet inclut une suite complète de tests automatisés basée sur le framework standard `unittest`.

Pour exécuter l'ensemble de la suite de tests :

```bash
py -m unittest discover -s backend/tests
```

Couverture des tests :
- `test_organizer.py` : Scans, déplacements, renommage en masse, annulation et gestion des règles.
- `test_deepseek_and_surgical.py` : Filtres chirurgicaux, rapports 24h et statut d'autostart.
- `test_security_and_ai.py` : Chiffrement des clés API, suppression sécurisée, extraction de contenu et moteurs IA.
- `test_performance_and_ui.py` : Cache d'empreinte SHA256 et détection parallèle des doublons.

---

## Licence

Ce projet est distribué sous la licence MIT. Voir le fichier `LICENSE` pour plus de détails.
