import os
import subprocess
import time
import requests
import psutil
import docker

# ================= Configuration =================
BASE_DIR = os.path.expanduser("~/sentinelle")
PIPER_BIN = os.path.join(BASE_DIR, "piper", "piper")
MODEL_PATH = os.path.join(BASE_DIR, "models", "fr_FR-siwis-medium.onnx")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# Seuils d'alerte
CPU_THRESHOLD = 90.0      # % d'usage
RAM_THRESHOLD = 90.0      # % d'usage
DISK_THRESHOLD = 90.0     # % d'usage partition principale
CHECK_INTERVAL = 10       # Vérification toutes les 10 secondes
COOLDOWN_PERIOD = 300     # 5 minutes de silence entre 2 alertes similaires

DISCORD_WEBHOOK_URL = ""  # Collez votre webhook si souhaité, sinon laissez vide

last_alerts = {}

# ================= Fonctions Alertes =================
def is_on_cooldown(key: str) -> bool:
    now = time.time()
    if key in last_alerts and (now - last_alerts[key]) < COOLDOWN_PERIOD:
        return True
    last_alerts[key] = now
    return False

def ask_sentinelle(incident_raw: str) -> str:
    system_prompt = (
        "Tu es Sentinelle, l'IA de surveillance clinique et posée d'un serveur homelab. "
        "Analyse l'anomalie suivante. Explique la cause et l'impact en DEUX phrases très concises maximum. "
        "Le texte sera lu à voix haute par un module TTS. N'utilise pas d'emojis, de markdown, ni de salutations."
    )
    
    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": f"Incident détecté :\n{incident_raw}",
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 70}
    }
    
    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=8)
        return res.json().get("response", "").strip()
    except Exception as e:
        return f"Alerte système : {incident_raw}. Moteur d'analyse indisponible."

def play_audio(text: str):
    try:
        p1 = subprocess.Popen(['echo', text], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(
            [PIPER_BIN, '--model', MODEL_PATH, '--output-raw'],
            stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        subprocess.run(['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw'], stdin=p2.stdout, check=True)
    except Exception as e:
        print(f"[Erreur Audio] : {e}")

def notify_discord(text: str):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🛡️ **[Sentinelle]** : {text}"}, timeout=5)
    except Exception as e:
        print(f"[Erreur Discord] : {e}")

def process_alert(alert_key: str, context: str):
    if is_on_cooldown(alert_key):
        return

    print(f"\n[!] Anomalie : {alert_key}")
    analysis = ask_sentinelle(context)
    print(f"[Sentinelle parle] : {analysis}")
    
    notify_discord(analysis)
    play_audio(analysis)

# ================= Surveillance Système =================
def check_system():
    # CPU
    cpu = psutil.cpu_percent(interval=1)
    if cpu >= CPU_THRESHOLD:
        process_alert("cpu_high", f"Le processeur est surchargé à {cpu}%.")

    # RAM
    ram = psutil.virtual_memory().percent
    if ram >= RAM_THRESHOLD:
        process_alert("ram_high", f"Saturation mémoire vive à {ram}%.")

    # Disque
    disk = psutil.disk_usage('/').percent
    if disk >= DISK_THRESHOLD:
        process_alert("disk_full", f"L'espace disque racine est occupé à {disk}%.")

def check_docker(client):
    if not client:
        return
    try:
        for c in client.containers.list(all=True):
            if c.status in ["restarting", "dead"]:
                logs = c.logs(tail=10).decode('utf-8', errors='ignore')
                process_alert(
                    f"docker_{c.name}",
                    f"Le conteneur '{c.name}' a échoué (statut : {c.status}). Derniers logs :\n{logs}"
                )
    except Exception as e:
        print(f"[Erreur Docker API] : {e}")

# ================= Boucle Principale =================
def main():
    print("🛡️ Sentinelle en ligne. Surveillance initialisée.")
    
    try:
        docker_client = docker.from_env()
    except Exception:
        docker_client = None
        print("[Note] Docker non démarré ou non installé. Surveillance métriques uniquement.")

    while True:
        check_system()
        check_docker(docker_client)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
