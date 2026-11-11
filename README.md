# 🛡️ Sentinelle — Watchdog Système & Conteneurs Docker avec Diagnostic IA Local

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Engine%20%2F%20Compose-2496ED.svg)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/LLM-Llama_3.2_(Ollama)-black.svg)](https://ollama.com/)
[![TTS](https://img.shields.io/badge/TTS-Piper_Local-orange.svg)](https://github.com/rhasspy/piper)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Sentinelle** est un agent d'observabilité et de monitoring local conçu pour les environnements Linux et homelabs. 

Contrairement aux outils de supervision traditionnels qui inondent l'administrateur de stack-traces brutes et illisibles, Sentinelle **intercepte les anomalies système et les crashs de conteneurs Docker, les transmet à un LLM local qui en extrait la cause racine, et émet un rapport vocal clinique instantané**.

Le projet fonctionne **à 100 % hors ligne**, garantissant une souveraineté et une confidentialité absolues des données d'infrastructure.

---

## 🏗️ Architecture & Flux

```text
[ Métriques CPU/RAM/Disque ]
            +                ---> [ Détection Anomalie ] ---> [ LLM Local : Ollama ]
[ Crashs Conteneurs Docker ]          (sentinelle.py)          (Llama 3.2 3B - Cause racine)
                                                                            |
                                                +---------------------------+
                                                v                           v
                                       [ Audio : Piper TTS ]      [ Webhook : Discord ]
                                       (Rapport vocal local)       (Notification texte)
```

✨ Fonctionnalités clés

  - Surveillance des ressources hôte : Détection en temps réel des surcharges
    CPU, des saturations de RAM (prévention de l'OOM Killer) et du remplissage
    de la partition racine.
  - Supervision Docker : Écoute de l'état des conteneurs via l'API Docker
    (docker-py), détection des boucles de redémarrage (restarting) et des pannes
    (dead).
  - Filtrage cognitif par LLM local : Extraction automatique des 10 dernières
    lignes de logs pour diagnostic immédiat de la cause racine (ports fermés,
    échecs BDD, droits d'accès).
  - Rapport vocal ultra-rapide : Synthèse vocale générée hors-ligne en moins
    de 100 ms grâce au moteur C++ Piper TTS.
  - Mécanisme d'anti-spam : Système de cooldown configurable évitant la
    redondance des alertes récurrentes.
  - Persistance : Prêt pour un déploiement en démon d'arrière-plan via systemd.

🛠️ Stack Technique

  - Système d'exploitation : Linux (testé et validé sur Ubuntu 22.04 / 24.04
    LTS)
  - Langage & Bibliothèques : Python 3 (psutil, docker, requests)
  - Moteur d'IA : Ollama exécutant llama3.2:3b
  - Moteur Vocal : Piper TTS (modèle français fr_FR-siwis-medium)
  - Lecteur Audio : aplay (ALSA) / paplay (PulseAudio/PipeWire)

🚀 Guide d'installation pas à pas

1. Prérequis système

sudo apt update && sudo apt install -y alsa-utils pulseaudio-utils curl python3-pip python3-venv git

Assurez-vous que votre utilisateur a accès au socket Docker :

sudo usermod -aG docker $USER
sudo chmod 666 /var/run/docker.sock

2. Déployer Ollama & le modèle LLM

# Installation d'Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Téléchargement du modèle de diagnostic rapide
ollama pull llama3.2:3b

3. Installer Piper TTS & la voix française

# Télécharger le binaire Piper
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz
tar -xvf piper_linux_x86_64.tar.gz && rm piper_linux_x86_64.tar.gz

# Télécharger le modèle de voix ONNX
mkdir -p models
curl -L -o models/fr_FR-siwis-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx"
curl -L -o models/fr_FR-siwis-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json"

4. Configurer l'environnement Python

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

🎮 Utilisation

Lancement manuel

source venv/bin/activate
python sentinelle.py

Lancement permanent en tant que service systemd

Pour que Sentinelle tourne 24h/24 et démarre avec le système :

sudo nano /etc/systemd/system/sentinelle.service

Insérez le contenu suivant (en adaptant avec votre nom d'utilisateur) :

[Unit]
Description=Watchdog Sentinelle Homelab
After=network.target docker.service sound.target

[Service]
Type=simple
User=VOTRE_USER
WorkingDirectory=/home/VOTRE_USER/sentinelle
ExecStart=/home/VOTRE_USER/sentinelle/venv/bin/python /home/VOTRE_USER/sentinelle/sentinelle.py
Restart=always
RestartSec=10
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=multi-user.target

Activez et démarrez le service :

sudo systemctl daemon-reload
sudo systemctl enable --now sentinelle

🧪 Simulation d'incident (Test de bon fonctionnement)

Pour valider l'interception et le diagnostic d'un crash Docker :

docker run --name test-crash --restart=always -d alpine sh -c "echo 'FATAL: database connection timeout on port 5432'; exit 1"

Résultat attendu : Sentinelle détecte l'état du conteneur, soumet les logs à
Ollama et énonce à voix haute :

« Le conteneur test-crash a échoué en raison d'un problème de connexion à la
base de données sur le port 5432. Risque de perturbation des services
dépendants. »

Nettoyez le conteneur de test après validation :

docker rm -f test-crash

📄 Licence

Distribué sous licence MIT. Projet conçu pour l'apprentissage et l'observabilité
homelab. EOF


