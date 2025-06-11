import subprocess
import psutil


def is_streamlit_running():
    """Vérifie si une instance de Streamlit est en cours d'exécution."""
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'streamlit':
            return process
    return None


def kill_streamlit_instance(process):
    """Ferme une instance de Streamlit."""
    print(f"Fermeture de l'instance de Streamlit (PID: {process.pid})...")
    process.terminate()  # Terminer le processus
    process.wait()  # Attendre que le processus se termine
    print("Instance de Streamlit fermée.")


def launch_streamlit(streamlit_path):
    """Lance l'application Streamlit et affiche les logs dans le terminal de VSCode."""
    existing_process = is_streamlit_running()
    if existing_process:
        kill_streamlit_instance(existing_process)
    # Lancer Streamlit et afficher les logs dans le terminal
    try:
        subprocess.run(['streamlit', 'run', streamlit_path], check=True)
        #subprocess.run(['streamlit', streamlit_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de Streamlit : {e}")