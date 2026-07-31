# Smart File Organizer Pro (Open-Source & DeepSeek IA)

> **Un outil open-source ultra-complet, intelligent, sécurisé et chirurgical pour trier et automatiser la gestion de vos fichiers sous Windows, Linux et macOS.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![DeepSeek](https://img.shields.io/badge/AI-DeepSeek_API-cyan)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🌟 Fonctionnalités Clés

- 🤖 **Intelligence Artificielle DeepSeek à Bas Coût** :
  - **Saisie de votre propre clé API DeepSeek** pour une autonomie totale et des coûts minimes (quelques centimes pour des milliers de fichiers).
  - **Classification sémantique intelligente** : Création dynamique de sous-dossiers pertinents (ex: `Projets/Python`, `Administratif/Factures/2026`).
  - **Nettoyage et renommage propre** des fichiers tout en conservant l'extension d'origine.
  - **Prompt système personnalisé** configurable pour des règles métier sur-mesure.

- 🛡️ **Réorganisation Chirurgicale & Sécurité Maximale** :
  - **Dry-Run avec aperçu diff** : Inspectez chaque action avant d'appliquer le moindre changement sur votre disque.
  - **Détection des Conflits & Anti-Écrasement** : Stratégie anti-collision automatique (`nom (1).ext`).
  - **Filtres Chirurgicaux Avancés** : Filtrage par Expression Régulière (Regex), Taille min/max en Mo, et Plage de dates de modification.
  - **Annulation Atomique (Undo)** : Restaurez n'importe quel lot passé en 1 clic/commande sans risque.

- 🤖 **CLI Daemon & Démarrage Automatique au Boot OS** :
  - **Démon d'arrière-plan autonome** : Surveille en continu vos dossiers sans nécessiter de serveur lourd.
  - **Installation au boot OS en 1 commande** (`python organizer_cli.py service install`) pour Windows (Startup/Registre), Linux (`systemd`), et macOS (`launchd`).
  - **Rapport Digest 24 Heures** (`python organizer_cli.py history --last-24h`) : Résumé quotidien automatique de tous les fichiers réorganisés.

- 🎨 **Dashboard Web Dashboard Pro (Local)** :
  - 4 thèmes personnalisables (*Sombre Glass*, *Clair*, *Cyberpunk*, *Émeraude*).
  - Graphiques interactifs Chart.js de la répartition par catégorie.
  - Interface interactive de détection de doublons réels par hash **SHA256**.

---

## Structure du Projet

```text
smart-file-organizer/
├── core/
│   ├── ai_organizer.py    # Moteur d'IA sémantique DeepSeek (OpenAI REST compatible)
│   ├── autostart.py       # Gestionnaire multi-plateformes du démarrage au boot de l'OS
│   ├── config.py          # Configuration centralisée et sécurisée (organizer_config.json)
│   ├── history.py         # Historique des transactions et Rapport Digest sur 24h
│   ├── organizer.py       # Moteur de tri principal et filtres chirurgicaux
│   ├── rules.py           # Règles d'extensions par défaut et personnalisées
│   └── watcher.py         # Service de surveillance temps réel (Watchdog)
├── web/
│   ├── index.html         # Application Web Dashboard Pro
│   ├── css/style.css      # Design Glassmorphism Dark Mode & thèmes
│   └── js/app.js          # Logique frontend et intégration DeepSeek API
├── tests/
│   └── test_organizer.py  # Tests automatisés
├── server.py              # Serveur local Flask & API REST
├── organizer_cli.py       # Utilitaire CLI complet, Daemon & Service
├── requirements.txt       # Dépendances légères (Flask, Watchdog)
└── README.md              # Documentation Open-Source
```

---

## Installation & Prise en Main

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

---

## Utilisation CLI & Service Daemon

### 1. Configurer la clé API DeepSeek (Optionnel)

```bash
python organizer_cli.py config --key "sk-votre-cle-deepseek" --model "deepseek-chat"
```

### 2. Scanner un dossier en mode aperçu (Dry-Run)

```bash
# Scan classique
python organizer_cli.py scan -d ~/Downloads

# Scan intelligent via l'IA DeepSeek
python organizer_cli.py scan -d ~/Downloads --ai

# Scan chirurgical avec filtre Regex (ex: uniquement les fichiers PDF)
python organizer_cli.py scan -d ~/Downloads --regex ".*\.pdf$" --min-size 1
```

### 3. Exécuter la réorganisation

```bash
python organizer_cli.py organize -d ~/Downloads --ai -y
```

### 4. Activer le Service d'Arrière-Plan au Démarrage de la Machine (Boot OS)

Activer le démon qui tourne en permanence et démarre automatiquement à l'allumage de votre ordinateur :

```bash
python organizer_cli.py service install
```

Pour désactiver ou vérifier le statut :

```bash
python organizer_cli.py service status
python organizer_cli.py service uninstall
```

### 5. Consulter le Rapport Digest des 24 Dernières Heures

```bash
python organizer_cli.py history -d ~/Downloads --last-24h
```

### 6. Annuler le dernier tri (Undo)

```bash
python organizer_cli.py undo -d ~/Downloads
```

---

## Interface Web Dashboard Local

Pour lancer l'interface graphique web locale :

```bash
python server.py
```

Rendez-vous ensuite sur **[http://localhost:5000](http://localhost:5000)**.

- **Modal Clé API DeepSeek** : Cliquez sur le bouton *Clé API DeepSeek* en haut à droite pour renseigner et tester votre clé en direct.
- **Service Boot OS** : Cliquez sur le badge *Boot OS* pour activer/désactiver le démarrage automatique.
- **Rapport 24H** : Consultez l'onglet *Rapport 24H* pour voir la synthèse quotidienne.

---

## 🧪 Tests Unitaires

Pour exécuter la suite de tests unitaires :

```bash
python -m unittest discover -s tests
```

---

## 📜 Licence

Ce projet est sous licence **MIT** - Libre et Open-Source.
