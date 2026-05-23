# OpenStack Instance Metadata 503 After Gazpacho Upgrade

## Symptom

After upgrading the OpenStack lab to Gazpacho / 2026.1, newly created tenant VMs
booted but cloud-init repeatedly failed in the VM console.

Observed console messages included:

```text
cloud-init
url_helper.py
Endpoint returned a 503 error
http://169.254.169.254/openstack
```

From inside the guest, `169.254.169.254` is the OpenStack metadata endpoint.
Cloud-init uses it to fetch instance metadata, network data, SSH keys, and
user-data.

## Metadata Request Path

The request path in this lab is:

```text
guest cloud-init
  -> 169.254.169.254
  -> Neutron metadata proxy / metadata agent
  -> Nova metadata API
  -> instance metadata response
```

Because the guest saw a `503`, the first suspicion was Neutron metadata routing.
The investigation started with Neutron, then followed the proxy path upstream to
Nova.

## Investigation Steps

### 1. Confirm running Vagrant lab nodes

The base OpenStack nodes were running:

```bash
vagrant global-status
```

Expected nodes for this case:

```text
controller01
compute01
compute02
storage01
```

### 2. Check branch changes related to the upgrade

When investigating an upgrade branch, compare it against its base branch. During
the original Gazpacho troubleshooting this was done against `main` before the
upgrade branch was merged:

```bash
git diff main...HEAD --stat
git diff main...HEAD -- \
  ansible/deploy_openstack/roles/neutron \
  ansible/deploy_openstack/roles/neutron_controller \
  ansible/deploy_openstack/roles/neutron_compute \
  ansible/deploy_openstack/roles/nova \
  ansible/deploy_openstack/roles/nova_controller \
  ansible/deploy_openstack/inventories/local/group_vars/all/common.yml
```

Important branch changes found:

- `openstack_repo` changed from `cloud-archive:epoxy` to `cloud-archive:gazpacho`.
- Nova API startup changed from `nova-api` service to Apache.
- Neutron API startup changed from `neutron-server` service to Apache plus
  `neutron-rpc-server`.

Those changes are relevant because the metadata request path depends on both
Neutron metadata agent and Nova metadata API.

### 3. Check controller services and listening ports

On `controller01`:

```bash
sudo systemctl --no-pager --plain --type=service --state=running,failed \
  | egrep 'apache2|nova|neutron|httpd'

sudo ss -ltnp
```

Key findings:

- `apache2` was running.
- `neutron-dhcp-agent`, `neutron-l3-agent`, `neutron-metadata-agent`,
  `neutron-openvswitch-agent`, and `neutron-rpc-server` were running.
- `nova-conductor`, `nova-scheduler`, and `nova-novncproxy` were running.
- Apache was listening on:
  - `5000` for Keystone
  - `8774` for Nova API
  - `8776` for Cinder API
  - `8778` for Placement API
  - `9696` for Neutron API
- Nothing was listening on `8775`, the Nova metadata API port.

Direct confirmation:

```bash
curl -sv --max-time 3 http://127.0.0.1:8775/openstack
```

Failed result:

```text
connect to 127.0.0.1 port 8775 failed: Connection refused
```

### 4. Check OpenStack service health

On `controller01`:

```bash
. /etc/environment
openstack network agent list
openstack compute service list
openstack endpoint list --service compute
openstack endpoint list --service network
```

Important findings:

- Neutron DHCP, L3, metadata, and OVS agents were `UP`.
- Nova scheduler, conductor, and compute services were `up`.
- Compute endpoint was correctly registered on `8774`.
- Network endpoint was correctly registered on `9696`.

This showed that the main Neutron and Nova control-plane services were healthy.
The failure was narrower than general Neutron API or Nova API availability.

### 5. Inspect Neutron metadata-agent configuration

On `controller01`:

```bash
sudo sed -n '1,80p' /etc/neutron/metadata_agent.ini
```

Relevant configuration:

```ini
[DEFAULT]
nova_metadata_host = 192.168.121.5
metadata_proxy_shared_secret = platformpass
```

The default `nova_metadata_port` is documented in the same file as `8775`.
Therefore Neutron metadata agent was expected to proxy requests to:

```text
http://192.168.121.5:8775
```

### 6. Inspect Neutron metadata-agent logs

On `controller01`:

```bash
sudo tail -n 100 /var/log/neutron/neutron-metadata-agent.log
```

The log showed repeated failures reaching Nova metadata:

```text
The remote metadata server is temporarily unavailable. Please try again later.
HTTPConnectionPool(host='192.168.121.5', port=8775): Max retries exceeded
with url: /openstack
Failed to establish a new connection: [Errno 111] Connection refused
```

This is the direct server-side explanation for the guest-side `503`.

### 7. Inspect Apache site configuration

On `controller01`:

```bash
ls -l /etc/apache2/sites-enabled /etc/apache2/sites-available
cat /etc/apache2/sites-available/nova-api.conf
cat /etc/apache2/sites-available/neutron-api.conf
```

Findings:

- `nova-api.conf` existed and exposed `/usr/bin/nova-api-wsgi` on `8774`.
- `neutron-api.conf` existed and exposed `/usr/bin/neutron-api` on `9696`.
- No Apache virtual host existed for Nova metadata on `8775`.

The Gazpacho package includes the metadata WSGI entrypoint:

```bash
ls -l /usr/bin/nova-metadata-wsgi
```

But the role did not create an Apache site for it.

## Root Cause

The Gazpacho upgrade moved Nova API serving to Apache WSGI, but the deployment
role only exposed the Nova compute API on port `8774`.

It did not expose Nova metadata WSGI on port `8775`.

As a result:

1. Guest cloud-init requested metadata from `169.254.169.254/openstack`.
2. Neutron metadata agent accepted the request.
3. Neutron metadata agent tried to proxy it to Nova metadata at
   `192.168.121.5:8775`.
4. Nothing was listening on `8775`.
5. Neutron returned `503` to the guest.

## Fix

Add an Apache virtual host for Nova metadata API and enable it from the Nova
controller role.

Files changed:

- `ansible/deploy_openstack/roles/nova_controller/files/metadata_api.conf`
- `ansible/deploy_openstack/roles/nova_controller/tasks/main.yml`

The new Apache site listens on `8775` and serves:

```text
/usr/bin/nova-metadata-wsgi
```

The Nova controller role now creates:

```text
/etc/apache2/sites-available/nova-metadata.conf
/etc/apache2/sites-enabled/nova-metadata.conf
```

Then the existing Apache restart in the role applies the new listener.

## Validation

After rerunning the Nova controller playbook or otherwise applying the Apache
site, validate on `controller01`.

Check that Apache listens on `8775`:

```bash
sudo ss -ltnp | grep 8775
```

Check the metadata endpoint locally:

```bash
curl -sS -i --max-time 3 http://127.0.0.1:8775/openstack
```

Check Neutron metadata-agent logs:

```bash
sudo tail -n 100 /var/log/neutron/neutron-metadata-agent.log
```

The previous connection refused errors should stop after cloud-init retries or
after booting a new instance.

Check from a tenant VM:

```bash
curl -sS -i --max-time 3 http://169.254.169.254/openstack
```

Expected result is an HTTP response from metadata service instead of a `503`.

## Notes

- Neutron was a reasonable first suspect because `169.254.169.254` traffic is
  handled through Neutron metadata plumbing.
- In this case, Neutron was not the broken component. It was correctly proxying
  requests to the configured Nova metadata endpoint.
- The decisive evidence was the combination of:
  - Neutron metadata agents `UP`
  - repeated Neutron metadata log failures to `192.168.121.5:8775`
  - no listener on `8775`
  - `nova-metadata-wsgi` present but not wired into Apache
- Existing instances may need cloud-init retry, reboot, or rebuild depending on
  how long they had already been failing metadata discovery.
