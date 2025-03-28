# HashiCorp Vault HA Cluster Ansible Playbook

This document explains how to install and manage the HashiCorp Vault HA Cluster using Ansible on CentOS/RHEL/OEL, Debian 12, and Ubuntu systems.

### 🚀 Supported Operating Systems

* ✅ Debian 12
* ✅ Ubuntu (22.04, 24.04)
* ✅ Oracle Linux
* ✅ RHEL

## 🛠 Editing Variables

### 📌 Inventories File (inventories/hosts.ini)
You can define your servers and IP addresses as shown below:

```
[vault]
vault01.domain.com ansible_host=192.168.117.133
vault02.domain.com ansible_host=192.168.117.134
vault03.domain.com ansible_host=192.168.117.135

[all:children]
vault
```

### 📌 General Settings (group_vars/all.yml)
 Vault and system-wide settings can be managed here:

```
vault_deb_version: "vault=1.18.5-1" # debian/ubuntu
vault_rhel_version: "vault-1.18.5-1" # rhel/oel
vault_init_keys: 5
vault_init_threshold: 2
vault_cluster_name: "SAMPLE-CLUSTER"
vault_log_level: "info" # Options: trace, info, debug, error, warning
vault_domain_name: "domain.com"
vault_virtual_ip_address: "192.168.117.200"
self_signed: false
iptables_install: true
```

* self_signed: true → Automatically creates self-signed TLS certificates.
* iptables_install: true → Automatically configures iptables. Set to false if you have your own firewall. Works for Debian/Ubuntu systems.
* firewalld_install: false → Set to true if you want to configure firewalld for RHEL/OEL.

### 📌 Per-Host Configuration (host_vars/)

 Example: host_vars/vault01.domain.com.yml.
 The "vault_domain_name" variable here is read from group_vars/all.yml. When editing, take your /etc/hosts or dns records into consideration.

```
keepalived_state: MASTER
keepalived_priority: 101
vault_retry_join:
  - leader_api_addr: "https://vault02.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
  - leader_api_addr: "https://vault03.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
```

 Example: host_vars/vault02.domain.com.yml.
 The "vault_domain_name" variable here is read from group_vars/all.yml. When editing, take your /etc/hosts or dns records into consideration.

```
keepalived_state: BACKUP
keepalived_priority: 100
vault_retry_join:
  - leader_api_addr: "https://vault01.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
  - leader_api_addr: "https://vault03.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
```

## 🚀 Running the Ansible Playbook

 After configuring host_vars, group_vars, and inventories for your system, run the playbook.
 Before executing, make sure curl, sshpass, and sudo are installed on the servers.

```
ansible-playbook -i inventories/hosts.ini site.yml
```

For DEBUG mode

```
ansible-playbook -i inventories/hosts.ini site.yml -vvv
```

# 🛠 Editing Disaster Recovery Configuration

 Note: The main site must be installed using this playbook, otherwise the DR site will not function properly.
 Additionally, while defining host_vars/, DNS addresses from the /etc/hosts file that belong to the cluster should be used.
 If misconfigured, the DR cluster will not operate correctly.

### 📌 Inventories File (hosts.ini)
 You can define your servers and IP addresses as shown below:

```
[vault]
vault01.domain.com ansible_host=192.168.117.133
vault02.domain.com ansible_host=192.168.117.134
vault03.domain.com ansible_host=192.168.117.135

[vault_dr]
dr-vault01.domain.com ansible_host=192.168.118.133
dr-vault02.domain.com ansible_host=192.168.118.134
dr-vault03.domain.com ansible_host=192.168.118.135

[all:children]
vault
```

### 📌 General Settings (group_vars/all-dr.yml)

* dr_enabled: true → Enables disaster recovery synchronization.
* iptables_install: true → Automatically configures iptables. Set to false to disable. Works for Debian/Ubuntu systems.
* firewalld_install: false → Set to true to configure firewalld for RHEL/OEL systems.

### 📌 Per-Host Configuration for DR (host_vars/)

 You must create the necessary YAML files under host_vars for the DR side.
 Below is an example file. The DR site should be configured based on the main site.

 Example: host_vars/dr-vault01.domain.com.yml.
 The "vault_domain_name" variable here is read from group_vars/all.yml. When editing, take your /etc/hosts or dns records into consideration.

```
keepalived_state: MASTER
keepalived_priority: 101
vault_retry_join:
  - leader_api_addr: "https://dr-vault02.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
  - leader_api_addr: "https://dr-vault03.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"

```

 Example: host_vars/dr-vault02.domain.com.yml.
 The "vault_domain_name" variable here is read from group_vars/all.yml. When editing, take your /etc/hosts or dns records into consideration.

```
keepalived_state: BACKUP
keepalived_priority: 100
vault_retry_join:
  - leader_api_addr: "https://dr-vault01.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
  - leader_api_addr: "https://dr-vault03.{{ vault_domain_name }}:8200"
    leader_ca_cert_file: "{{ vault_tls_path }}/ca.crt"
    leader_client_cert_file: "{{ vault_tls_path }}/tls.crt"
    leader_client_key_file: "{{ vault_tls_path }}/tls.key"
```

## 🚀 Running the DR Ansible Playbook

 After configuring host_vars, group_vars, and inventories for your DR environment, run the playbook.
 Make sure curl, sshpass, and sudo are installed on the servers before executing.

```
ansible-playbook -i inventories/hosts.ini disaster.yml
```

For DEBUG mode

```
ansible-playbook -i inventories/hosts.ini disaster.yml -vvv
```

## 🚀 To uninstall all configurations

```
ansible-playbook -i inventories/hosts.ini uninstall.yml
```