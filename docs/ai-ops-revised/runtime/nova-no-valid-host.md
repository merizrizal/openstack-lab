# Nova Scheduler: `NoValidHost`

This error means **Nova received the request to create `<server_id>`, but the Nova scheduler could not find any compute host that satisfied all of the requirements for the instance**.

The important part is:

```text
nova.exception.NoValidHost: No valid host was found.
```

The request reached the scheduler successfully:

```text
nova/conductor/manager.py
    schedule_and_build_instances
        ↓
_schedule_instances
        ↓
scheduler_rpcapi.select_destinations
        ↓
nova/scheduler/manager.py
    select_destinations
```

So this is **not primarily an API problem**. The failure occurred during **Nova scheduling**.

Your instance therefore ended up:

```text
status=ERROR
vm_state=error
```

## Placement investigation

The first thing I would investigate is **Placement**.

Modern Nova scheduling normally works roughly like this:

```text
OpenStack API
     │
     ▼
Nova Conductor
     │
     ▼
Nova Scheduler
     │
     ├── Query Placement
     │       │
     │       └── Find resource providers
     │
     ├── Apply scheduler filters
     │
     └── Select compute host
             │
             ▼
        Nova Compute
```

For `<server-id>`, Placement needs to find a compute resource provider with enough resources for the requested flavor.

Check:

```bash
openstack compute service list
```

You want the compute services to be:

```text
Status   = enabled
State    = up
```

For example:

```text
+----+----------------+------+---------+-------+----------------------------+
| ID | Binary         | Host | Zone    | Status| State                      |
+----+----------------+------+---------+-------+----------------------------+
| .. | nova-compute   | compute01 | nova | enabled | up |
+----+----------------+------+---------+-------+----------------------------+
```

Then check Placement resource providers:

```bash
openstack resource provider list
```

You should see your compute host:

```text
+--------------------------------------+----------+
| uuid                                 | name     |
+--------------------------------------+----------+
| ...                                  | compute01|
+--------------------------------------+----------+
```

Then inspect its inventory:

```bash
openstack resource provider inventory show <compute-provider-uuid>
```

You should see resources such as:

```text
VCPU
MEMORY_MB
DISK_GB
```

Also check allocations:

```bash
openstack resource provider show <compute-provider-uuid>
```

and:

```bash
openstack resource provider usage show <compute-provider-uuid>
```

A particularly useful command is:

```bash
openstack resource provider list --resource VCPU=1
```

or, depending on the flavor:

```bash
openstack resource provider list --resource VCPU=<required_vcpus>
```

If Placement has **no provider capable of satisfying the request**, Nova eventually produces:

```text
NoValidHost
```

### Check Placement aggregates/traits too

If your deployment uses aggregates, AZs, traits, or required capabilities, inspect them:

```bash
openstack aggregate list
openstack aggregate show <aggregate>
```

and:

```bash
openstack resource provider trait list <provider-uuid>
```

A provider can have enough CPU/RAM but still be excluded because of a required trait or aggregate relationship.

## Flavor constraints

The next thing to investigate is the flavor:

```text
flavor_id:
<flavor>
```

Get the flavor:

```bash
openstack flavor show <flavor>
```

Check at least:

```text
vcpus
ram
disk
ephemeral
swap
```

For example:

```text
+----------------------------+--------------------------------------+
| Field                      | Value                                |
+----------------------------+--------------------------------------+
| vcpus                      | 4                                    |
| ram                        | 8192                                 |
| disk                       | 50                                   |
| ephemeral                  | 0                                    |
+----------------------------+--------------------------------------+
```

Then compare those requirements with your compute host's available resources.

For example, if the flavor requires:

```text
VCPU      8
RAM       16384 MB
DISK      100 GB
```

but your compute provider only has:

```text
VCPU      4 available
RAM       8192 MB available
```

Placement will eliminate that host.

Also inspect flavor extra specs:

```bash
openstack flavor show <flavor>
```

Look for:

```text
properties
```

or:

```text
extra_specs
```

Extra specs can introduce additional scheduling requirements.

For example:

```text
hw:cpu_policy=dedicated
```

can require specific CPU resources.

Likewise:

```text
hw:mem_page_size=1GB
```

can require huge-page-related resources.

And things such as:

```text
trait:CUSTOM_...
```

can require a specific Placement trait.

So don't only look at `vcpus`, `ram`, and `disk`.

## Host constraints

After Placement and the flavor, investigate **Nova scheduler filters** and host state.

Start with:

```bash
openstack compute service list --service nova-compute
```

Make sure the compute hosts are:

```text
enabled
up
```

Then check the scheduler logs around the exact failure time.

For example:

```bash
grep -i "NoValidHost" /var/log/nova/nova-scheduler.log
```

and:

```bash
grep -i "<server-id>" /var/log/nova/nova-scheduler.log
```

The scheduler log is particularly important because the API error only gives you:

```text
No valid host was found.
```

It does **not tell you which constraint eliminated the candidates**.

Depending on your deployment, you'll often find more useful information around messages involving:

```text
FilterScheduler
HostFilter
Placement
AllocationCandidates
ComputeFilter
NUMATopologyFilter
AggregateInstanceExtraSpecsFilter
RetryFilter
```

For example, a scheduler log might reveal that a compute host was rejected because:

```text
Compute service is down
```

or:

```text
Not enough available VCPU
```

or:

```text
Host does not have required trait
```

or:

```text
Host doesn't match aggregate metadata
```

or:

```text
NUMA topology cannot satisfy request
```

### Check Nova's perception of the hosts

```bash
openstack hypervisor list
```

Then:

```bash
openstack hypervisor show compute01
```

Check:

```text
vcpus
vcpus_used
memory_mb
memory_mb_used
local_gb
local_gb_used
state
status
```

This is useful for comparing:

```text
Nova's view
    ↓
Placement's view
    ↓
Actual compute host
```

A particularly important situation is when **Nova and Placement disagree** about resource availability.

For example:

```text
Nova:
    compute01 = up

Placement:
    compute01 has no valid inventory
```

or:

```text
Nova:
    32 VCPU available

Placement:
    only 4 VCPU available
```

That can produce a `NoValidHost` even though the compute service itself appears healthy.

---

## Most likely investigation path

For this particular error, I'd troubleshoot in this order:

```text
1. nova-compute state
        │
        ▼
2. Placement resource provider exists?
        │
        ▼
3. Placement inventory correct?
        │
        ▼
4. Enough VCPU / RAM / DISK?
        │
        ▼
5. Flavor extra_specs?
        │
        ▼
6. Required traits / aggregates?
        │
        ▼
7. Scheduler filters?
        │
        ▼
8. Nova scheduler log
```

The key point is that **`NoValidHost` is a final scheduling symptom, not the root cause**.

In your case, the most valuable next commands are:

```bash
openstack compute service list
openstack hypervisor list
openstack hypervisor show <compute-host>
openstack flavor show <flavor>
openstack resource provider list
openstack resource provider inventory show <provider-uuid>
openstack resource provider usage show <provider-uuid>
```

and then inspect:

```bash
/var/log/nova/nova-scheduler.log
```

The scheduler log is likely to tell you **why every candidate host was rejected**, which is the information missing from the error returned by your tool.
