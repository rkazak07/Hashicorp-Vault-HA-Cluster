# Hashicorp Vault HA Cluster Ansible Playbook

## Bu doküman, HashiCorp Vault'un Ansible ile Debian 12 ve Ubuntu sistemlerinde nasıl kurulup yönetileceğini anlatır.

🚀 Desteklenen İşletim Sistemleri
* ✅ Debian 12
* ✅ Ubuntu (22.04, 24.04)

📌 Gereksinimler
Ansible (2.10 veya üstü)
SSH bağlantısı (Root veya sudo yetkili kullanıcı)

🛠 Değişkenlerin Düzenlenmesi
📌 Inventories Dosyası (hosts.ini)
Sunucularınızı ve IP adreslerini aşağıdaki gibi belirtebilirsiniz:

```
[vault]
vault01.domain.com ansible_host=192.168.117.133
vault02.domain.com ansible_host=192.168.117.134
vault03.domain.com ansible_host=192.168.117.135

[all:children]
vault
```

📌 Genel Ayarlar (group_vars/all.yml)
Vault ve sistem genel ayarları buradan yönetilebilir:

```
vault_version: "vault=1.18.5-1"
vault_init_keys: 5
vault_init_threshold: 2
vault_cluster_name: "SAMPLE-CLUSTER"
vault_log_level: "info" # trace,info,debug,error,warning
vault_domain_name: "domain.com"
vault_virtual_ip_address: "192.168.117.200"
self_signed: false
iptables_install: true
```
self_signed: true → Self-signed TLS sertifikaları otomatik oluşturulur.
iptables_install: true → Iptables otomatik yapılandırılır. False yapılırsa iptables devre dışı kalır.

📌 Her Sunucu İçin Ayrı Konfigürasyon (host_vars/)

Örnek: host_vars/vault01.domain.com.yml

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

Örnek: host_vars/vault02.domain.com.yml

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

# Ansible Playbook Çalıştırma

host_vars, group_vars ve inventories düzenlemerini sisteminize göre sağladıktan sonra playbook'u çalıştırınız. Playbook çalıştırılmadan önce sunucularda *curl*, *sshpass*, *wget*, *sudo* yüklü olması gerekmektedir.

```
ansible-playbook -i inventories/hosts.ini site.yml
```

## DEBUG Mode için

```
ansible-playbook -i inventories/hosts.ini site.yml -vvv
```
