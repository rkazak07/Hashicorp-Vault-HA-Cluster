# Hashicorp Vault HA Cluster Ansible Playbook

 Bu doküman, HashiCorp Vault Ha Cluster yapısının Ansible ile Centos/Rhel/Oel, Debian 12 ve Ubuntu sistemlerinde nasıl kurulup yönetileceğini anlatır.

### 🚀 Desteklenen İşletim Sistemleri
* ✅ Debian 12
* ✅ Ubuntu (22.04, 24.04)
* ✅ Oracle Linux
* ✅ Rhel


## 🛠 Değişkenlerin Düzenlenmesi

### 📌 Inventories Dosyası (hosts.ini)
Sunucularınızı ve IP adreslerini aşağıdaki gibi belirtebilirsiniz:

```
[vault]
vault01.domain.com ansible_host=192.168.117.133
vault02.domain.com ansible_host=192.168.117.134
vault03.domain.com ansible_host=192.168.117.135

[all:children]
vault
```

### 📌 Genel Ayarlar (group_vars/all.yml)
Vault ve sistem genel ayarları buradan yönetilebilir:

```
vault_version: "vault=1.18.5-1" # Rhel/Oel için "vault-1.18.5-1" olarak duzenleyiniz.
vault_init_keys: 5
vault_init_threshold: 2
vault_cluster_name: "SAMPLE-CLUSTER"
vault_log_level: "info" # trace,info,debug,error,warning
vault_domain_name: "domain.com"
vault_virtual_ip_address: "192.168.117.200"
self_signed: false
iptables_install: true
```
* self_signed: true → Self-signed TLS sertifikaları otomatik oluşturulur.
* iptables_install: true → Iptables otomatik yapılandırılır. False yapılırsa iptables devre dışı kalır. Debian/Ubuntu için çalışmakradır.
* firewalld_install: false → True yapılırsa Rhel/Oel için firewalld ayarlarını yapılandırır

### 📌 Her Sunucu İçin Ayrı Konfigürasyon (host_vars/)

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

## 🚀 Ansible Playbook Çalıştırma

host_vars, group_vars ve inventories düzenlemerini sisteminize göre sağladıktan sonra playbook'u çalıştırınız. Playbook çalıştırılmadan önce sunucularda *curl*, *sshpass*, *sudo* yüklü olması gerekmektedir.

```
ansible-playbook -i inventories/hosts.ini site.yml
```

DEBUG Modu için

```
ansible-playbook -i inventories/hosts.ini site.yml -vvv
```

# 🛠 Disaster Konfigurasyonlarının Düzenlenmesi

 Not: Main Site tarafındaki kurulumların bu playbook ile yapılması gerekmektedir, aksi takdirde DR Site tarafı düzgün çalışmayacaktır. Ayrıca host_vars/ tanımlarını yaparken etc/hosts dosyasına dahil edilen ve cluster'da bulunan hostların DNS adreslerini kullanmaktadır. Düzgün yapılandırılmazsa sağlıklı çalışmayacaktır.

### 📌 Inventories Dosyası (hosts.ini)
Sunucularınızı ve IP adreslerini aşağıdaki gibi belirtebilirsiniz:

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
### 📌 Genel Ayarlar (group_vars/all-dr.yml)
Vault ve sistem genel ayarları buradan yönetilebilir:

* dr_enabled: true  → Disaster ayarlarının senkronizasyonunu sağlamaktadır.
* iptables_install: true → Iptables otomatik yapılandırılır. False yapılırsa iptables devre dışı kalır. Debian/Ubuntu için çalışmakradır.
* firewalld_install: false → True yapılırsa Rhel/Oel için firewalld ayarlarını yapılandırır.

### 📌 Her DR Sunucusu İçin Ayrı Konfigürasyon (host_vars/)

host_vars altında dr tarafı için kullanacağımız yml dosyalarını oluşturmalıyız. aşağıda örnek bir yaml dosyası paylaştım. Main Site'a göre DR Site'ı yapılandırmalıyız.

Örnek: host_vars/dr-vault01.domain.com.yml

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

Örnek: host_vars/dr-vault02.domain.com.yml

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

## 🚀 DR Ansible Playbook Çalıştırma

host_vars, group_vars ve inventories düzenlemerini sisteminize göre sağladıktan sonra playbook'u çalıştırınız. Playbook çalıştırılmadan önce sunucularda *curl*, *sshpass*, *sudo* yüklü olması gerekmektedir.

```
ansible-playbook -i inventories/hosts.ini disaster.yml
```

DEBUG Modu için

```
ansible-playbook -i inventories/hosts.ini disaster.yml -vvv
```

## 🚀 Tüm yapılandırmaları silmek için

```
ansible-playbook -i inventories/hosts.ini uninstall.yml
```