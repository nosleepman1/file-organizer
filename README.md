# 📁 Smart File Organizer

> **Un outil intelligent, sécurisé et élégant pour trier et automatiser la gestion de vos fichiers sous Windows/Linux/macOS.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Backend-Flask-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🌟 Fonctionnalités Clés

- 🎨 **Dashboard Web Moderne** : Interface graphique en *Glassmorphism Dark Mode* avec graphiques interactifs (Chart.js) pour visualiser la répartition des types de fichiers.
- ⚡ **Classification Automatique** : Tri par catégories (*Documents*, *Images*, *Vidéos*, *Audio*, *Archives*, *Code & Dev*, *Exécutables*), par **Date (Année-Mois)** ou par **Taille**.
- 🛡️ **Sécurité Anti-Perte de Données** :
  - **Mode Aperçu (Dry-Run)** : Prévisualisez exactement ce qui sera déplacé avant de lancer l'organisation.
  - **Anti-Écrasement des Doublons** : Gestion automatique des doublons avec renommage dynamique (`document (1).pdf`).
  - **Bouton Annuler (Undo 1-Clic)** : Historique complet permettant de restaurer immédiatement des fichiers à leur emplacement d'origine en cas d'erreur.
- 👀 **Surveillance en Temps Réel (Auto-Watcher)** : Service en arrière-plan qui surveille un dossier (ex: *Téléchargements*) et classe automatiquement chaque nouveau fichier téléchargé.
- 💻 **Interface CLI & API REST** : Utilisable aussi bien en ligne de commande que via son API backend.

---

## 📂 Structure du Projet

```text
smart-file-organizer/
├── core/
│   ├── organizer.py       # Moteur de tri principal et scanneur
│   ├── rules.py           # Règles d'extensions et méthodes de sous-dossiers
│   ├── history.py         # Gestionnaire de l'historique et fonction Undo
│   └── watcher.py         # Service de surveillance temps réel (Watchdog)
├── web/
│   ├── index.html         # Application Web Dashboard
│   ├── css/style.css      # Style Glassmorphism Dark Mode
│   └── js/app.js          # Interactions Frontend et communication API
├── tests/
│   └── test_organizer.py  # Suite de tests unitaires automatisés
├── server.py              # Serveur Web Flask & API REST
├── organizer_cli.py       # Utilitaire en Ligne de Commande (CLI)
├── requirements.txt       # Dépendances Python (Flask, Watchdog)
└── README.md              # Documentation du projet
```

---

## 🚀 Installation & Prérequis

### Prérequis
- Python 3.10 ou version ultérieure.

### Installation des dépendances
Ouvrez un terminal dans le dossier du projet et exécutez :

```powershell
py -m pip install -r requirements.txt
```

---

## 💻 Utilisation

### 1. Interface Web Dashboard (Recommandé)

Lancez le serveur Flask :

```powershell
py server.py
```

Ouvrez ensuite votre navigateur sur **[http://localhost:5000](http://localhost:5000)**.

- **Raccourcis Rapides** : Cliquez sur *Téléchargements*, *Bureau* ou *Documents* pour sélectionner votre dossier en 1-clic.
- **Lancer le Tri** : Analysez le dossier, vérifiez l'aperçu puis cliquez sur **Lancer l'Organisation**.
- **Annuler** : Cliquez sur **Annuler Dernier Tri (Undo)** à tout moment.

---

### 2. Interface Ligne de Commande (CLI)

Vous pouvez utiliser le script CLI `organizer_cli.py` :

#### Aperçu sans modifier de fichier (Dry-Run)
```powershell
py organizer_cli.py --dry-run --dir "C:\Users\VotreNom\Downloads"
```

#### Exécuter le tri
```powershell
py organizer_cli.py --dir "C:\Users\VotreNom\Downloads"
```

#### Changer le mode de tri (par Date ou par Taille)
```powershell
py organizer_cli.py --mode date --dir "C:\Users\VotreNom\Downloads"
py organizer_cli.py --mode size --dir "C:\Users\VotreNom\Downloads"
```

#### Annuler le dernier tri
```powershell
py organizer_cli.py --undo --dir "C:\Users\VotreNom\Downloads"
```

#### Activer la surveillance automatique en temps réel
```powershell
py organizer_cli.py --watch --dir "C:\Users\VotreNom\Downloads"
```

---

## 🧪 Tests Unitaires

Pour exécuter la suite de tests automatisés :

```powershell
py -m unittest discover -s tests
```

---

## ⚙️ Personnalisation des Règles

Vous pouvez personnaliser les extensions et catégories associées directement dans le fichier `core/rules.py` :

```python
DEFAULT_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", ...],
    "Images": ["jpg", "png", "webp", ...],
    # Ajoutez vos propres catégories ici !
}
```

---

## 📜 Licence

Ce projet est distribué sous la licence MIT.
