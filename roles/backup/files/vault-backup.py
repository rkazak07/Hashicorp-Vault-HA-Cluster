# !/usr/bin/env python3

import os
import subprocess
import datetime
import requests
import json
import socket

SNAPSHOT_DIR = "{{backup_path}}"
MAX_SNAPSHOTS = {{backup_retention_days}}
VAULT_ADDR = "{{vault_virtual_domain_address}}"
CA_PATH = "{{vault_tls_path}}/ca.crt"
WEBHOOK_URL = "{{backup_webhook_url}}"
PLATFORM = "{{backup_platform}}"


def send_webhook_message(message, success=True):
    """ Send a message to the webhook URL """
    if WEBHOOK_URL:
        payload = create_payload(message, success)
        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending webhook message: {e}\nResponse: {response.text if response else 'No response'}")


def create_payload(message, success):
    """ Create a payload based on the platform """
    if PLATFORM == "teams":
        return {
            "text": message
        }
    elif PLATFORM == "discord":
        return {
            "content": message
        }
    elif PLATFORM == "slack":
        return {
            "text": message
        }
    else:
        # Generic JSON payload
        return {
            "message": message,
            "status": "success" if success else "failure"
        }


def read_credentials():
    """ Read credentials from a secure location """
    with open('/etc/vault.d/vaultbackup-approle.json', 'r') as file:
        credentials = json.load(file)
    return credentials['ROLE_ID'], credentials['SECRET_ID']


def get_vault_token(role_id, secret_id):
    """ Authenticate using AppRole and return the client token. """
    url = f"{VAULT_ADDR}/v1/auth/approle/login"
    data = {"role_id": role_id, "secret_id": secret_id}
    try:
        response = requests.post(url, json=data, verify=CA_PATH)
        response.raise_for_status()
        return response.json()['auth']['client_token']
    except requests.RequestException as e:
        print(f"Error obtaining Vault token: {e}")
        return None


def is_leader(token):
    """ Check if the current Vault node is the leader. """
    api_url = f"{VAULT_ADDR}/v1/sys/leader"
    headers = {'X-Vault-Token': token}
    try:
        response = requests.get(api_url, headers=headers, verify=CA_PATH)
        response.raise_for_status()
        return response.json()['is_self']
    except requests.RequestException as e:
        print(f"Error checking leader status: {e}")
        return False


def get_ip_hostname():
    """ Get the IP address and hostname of the current machine """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address, hostname


def take_snapshot():
    """ Take a snapshot if the current node is the leader. """
    role_id, secret_id = read_credentials()
    token = get_vault_token(role_id, secret_id)
    if token is None or not is_leader(token):
        print("Not authorized or this node is not the leader. Exiting...")
        send_webhook_message("Backup failed: Not authorized or this node is not the leader.", success=False)
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_file = f"{SNAPSHOT_DIR}/snapshot_{timestamp}.snap"

    environment = os.environ.copy()
    environment["VAULT_TOKEN"] = token

    result = subprocess.run(
        ["vault", "operator", "raft", "snapshot", "save", "--tls-skip-verify", snapshot_file],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ip_address, hostname = get_ip_hostname()
    if result.returncode == 0:
        message = f"Backup completed successfully on {hostname} ({ip_address}). Snapshot saved as {snapshot_file}."
        print(message)
        send_webhook_message(message)
    else:
        message = f"Backup failed on {hostname} ({ip_address}) with errors: {result.stderr.decode()}"
        print(message)
        send_webhook_message(message, success=False)

    clean_old_snapshots()


def clean_old_snapshots():
    """ Clean up old snapshots beyond the max allowed. """
    snapshots = sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".snap")],
                       key=lambda x: os.path.getmtime(os.path.join(SNAPSHOT_DIR, x)))
    if len(snapshots) > MAX_SNAPSHOTS:
        for old_snap in snapshots[:-MAX_SNAPSHOTS]:
            os.remove(os.path.join(SNAPSHOT_DIR, old_snap))
            print(f"Deleted old snapshot: {old_snap}")
            send_webhook_message(f"Deleted old snapshot: {old_snap}")


if __name__ == "__main__":
    role_id, secret_id = read_credentials()
    token = get_vault_token(role_id, secret_id)
    if token is not None and is_leader(token):
        take_snapshot()
    else:
        print("This node is not the leader or could not authenticate.")