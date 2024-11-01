import requests
import logging
import subprocess
from datetime import datetime
import os
from tqdm import tqdm
import sys
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

REPO_PATH = os.path.abspath(script_dir)  

def load_blocklist_urls(urls_file_path):
    try:
        with open(urls_file_path, "r") as file:
            urls = [line.strip() for line in file if line.strip()]
            logging.info(f"{len(urls)} Blocklisten-URLs aus '{urls_file_path}' geladen.")
            return urls
    except FileNotFoundError:
        logging.error(f"Die Datei '{urls_file_path}' wurde nicht gefunden.")
        return []

def download_blocklist(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.RequestException as e:
        logging.warning(f"Fehler beim Laden der Blockliste von {url}: {e}")
        return []

def is_adblock_format(entries):
    for entry in entries:
        if entry.startswith("||") or entry.startswith("@@") or entry.startswith("!"):
            return True
    return False

def clean_abp_entries(entries):
    logging.info("Bereinige ABP-Format...")
    cleaned_entries = set()
    for entry in entries:
        entry = entry.strip()
        if entry.startswith("||") and "^" in entry:
            domain = entry.split("^")[0].lstrip("||")
            if domain:
                cleaned_entries.add(domain)
        elif entry.startswith("!") or entry.startswith("@@") or not entry:
            continue
    logging.info(f"{len(cleaned_entries)} ABP-Einträge bereinigt.")
    return list(cleaned_entries)

def clean_host_entries(entries):
    logging.info("Bereinige Einträge, entferne Kommentare und leere Zeilen...")
    cleaned_entries = []
    for entry in entries:
        entry = entry.strip()
        if entry and not entry.startswith("#"):
            parts = entry.split()
            if len(parts) > 1:
                cleaned_entries.append(parts[1])
            else:
                cleaned_entries.append(parts[0])
    logging.info(f"{len(cleaned_entries)} Einträge bereinigt.")
    return cleaned_entries

def save_blocklist(unique_entries, file_type):
    if file_type == "1" or file_type == "3":
        hosts_format_entries = [f"0.0.0.0 {domain}" for domain in unique_entries]
        output_file_path_hosts = os.path.join(REPO_PATH, "blocklist.hosts")
        with open(output_file_path_hosts, "w") as f:
            f.write("\n".join(hosts_format_entries))
        logging.info(f"Erfolgreich {len(unique_entries)} Einträge in '{output_file_path_hosts}' als Host-Datei gespeichert.")

    if file_type == "2" or file_type == "3":
        output_file_path_domain = os.path.join(REPO_PATH, "blocklist")
        with open(output_file_path_domain, "w") as f:
            f.write("\n".join(unique_entries))
        logging.info(f"Erfolgreich {len(unique_entries)} Einträge in '{output_file_path_domain}' als Domain-Only-Datei gespeichert.")

def main(urls_file_path):
    all_entries = []

    blocklist_urls = load_blocklist_urls(urls_file_path)
    if not blocklist_urls:
        logging.error("Keine Blocklisten zum Herunterladen gefunden. Skript wird beendet.")
        return

    logging.info("Beginne den Download der Blocklisten ...")
    for url in tqdm(blocklist_urls, desc="Herunterladen", unit=" Liste"):
        entries = download_blocklist(url)
        if entries:
            if is_adblock_format(entries):
                entries = clean_abp_entries(entries)
            else:
                entries = clean_host_entries(entries)
            all_entries.extend(entries)

    unique_entries = set(all_entries)
    logging.info(f"{len(unique_entries)} eindeutige Einträge nach Duplikat-Bereinigung.")

    print("\nWelches Format möchtest du generieren?")
    print("1 - Host-Datei (blocklist.hosts)")
    print("2 - Domain-Only-Datei (blocklist)")
    print("3 - Beide Dateien")
    file_type = input("Bitte wähle eine Option (1, 2 oder 3): ")

    save_blocklist(unique_entries, file_type)

    print(f"Die finale Blockliste enthält {len(unique_entries)} Einträge.")
    logging.info(f"Die finale Blockliste enthält {len(unique_entries)} Einträge.")

if __name__ == "__main__":
    urls_file_path = sys.argv[1] if len(sys.argv) > 1 else "blocklist_urls.txt"
    main(urls_file_path)
