# Installing Netwatch Agent (RHEL / Rocky / AlmaLinux)

This guide builds **Netwatch Agent** from source into an RPM and installs it on
Enterprise Linux 8, 9, or 10. Netwatch Agent is a rebranded build of Zabbix
Agent 2 (AGPLv3) — it stays wire-compatible with a Zabbix server/proxy.

> **Build once per EL major version.** The agent links `pcre2`/`openssl`/`glibc`
> from the release it is built on, so build the `.el8` RPM on EL8, `.el9` on EL9,
> and `.el10` on EL10. Don't build once and deploy everywhere.

**Assumptions:** commands are run as **root** (hence `~` = `/root`). The build
host needs **internet access** (Go modules are fetched during the build).

---

## 1. Install build dependencies

`selinux-policy-devel` and some others live in the CRB repo (PowerTools on EL8):

```bash
. /etc/os-release && echo "$VERSION_ID"          # 8 -> powertools, 9/10 -> crb
dnf install -y dnf-plugins-core
dnf config-manager --set-enabled crb             # EL8: use  powertools  instead
dnf groupinstall -y "Development Tools"
dnf install -y rpm-build rpmlint gcc make autoconf automake libtool pkgconfig \
               pcre2-devel openssl-devel systemd-rpm-macros \
               selinux-policy-devel checkpolicy policycoreutils createrepo_c git
```

## 2. Install the Go toolchain

The build needs **Go >= 1.25.9**. The distro `golang` package may be older, so
install the official tarball. Run these one line at a time:

```bash
curl -LO https://go.dev/dl/go1.25.11.linux-amd64.tar.gz
ls -lh go1.25.11.linux-amd64.tar.gz              # sanity: ~64 MB
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.25.11.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
go version                                       # go1.25.11 (must be >= 1.25.9)
```

## 3. Clone the source

```bash
git clone -b netwatch-rebrand-7.4 https://github.com/TheParadox20/zabbix.git netwatch-agent
cd netwatch-agent
```

## 4. Build the RPM

```bash
VER=7.4.11
mkdir -p ~/rpmbuild/SOURCES
git archive --format=tar.gz --prefix=netwatch-agent-${VER}/ \
    -o ~/rpmbuild/SOURCES/netwatch-agent-${VER}.tar.gz HEAD
rpmbuild -bb packaging/rpm/netwatch-agent.spec
```

`rpmbuild` runs `bootstrap → configure → make` (compiling the C libraries and
the Go agent) and builds the SELinux policy module. It takes a few minutes and
finishes with:

```
Wrote: /root/rpmbuild/RPMS/x86_64/netwatch-agent-7.4.11-1.el9.x86_64.rpm
```

## 5. Verify the build

```bash
rpmlint ~/rpmbuild/RPMS/x86_64/netwatch-agent-*.rpm    # only intentional warnings remain
rpm -qlp ~/rpmbuild/RPMS/x86_64/netwatch-agent-*.rpm   # files it will install
rpm -qp  --requires ~/rpmbuild/RPMS/x86_64/netwatch-agent-*.rpm   # auto-detected lib deps
```

The remaining `rpmlint` findings are intentional: the config is mode `0640` and
`/var/log/netwatch` is `0750` (hardening), the `netwatch` uid/gid is
non-standard (dedicated service account), and there is no man page.

## 6. Install

```bash
dnf install -y ~/rpmbuild/RPMS/x86_64/netwatch-agent-7.4.11-1.el9.x86_64.rpm
```

Installing creates the `netwatch` system user/group, the directories under
`/etc/netwatch` and `/var/log/netwatch`, the systemd unit, and loads the
SELinux policy module.

## 7. Configure it to reach your server

Edit `/etc/netwatch/netwatch_agent.conf`. The shipped defaults are placeholders
(`Server=127.0.0.1`, `Hostname=Netwatch server`) — the agent will **not** talk
to your server until you set these three directives:

```ini
# IP of the monitoring server allowed to poll this agent (passive checks)
Server=<SERVER_IP>

# IP of the server this agent reports to (active checks)
ServerActive=<SERVER_IP>

# MUST exactly match the host name configured on the server
Hostname=<THIS_HOST_NAME>
```

Open the agent port so the server can reach it (passive checks, TCP 10050):

```bash
firewall-cmd --permanent --add-service=netwatch-agent
firewall-cmd --reload
```

## 8. Start the service

```bash
systemctl enable netwatch-agent
systemctl start netwatch-agent
systemctl status netwatch-agent --no-pager
```

> If you edit the config later, apply it with `systemctl restart netwatch-agent`.

## 9. Confirm it works

```bash
netwatch_agent -V                                # shows "netwatch_agent (Netwatch) 7.4.11"
tail /var/log/netwatch/netwatch_agent.log        # startup + hostname line
```

On the monitoring server, add a host whose name matches `Hostname`, link the
`Linux by Netwatch agent active` template, and within a minute or two the items
begin collecting data.

---

## Notes

### SELinux
The agent runs in its own confined domain (`netwatch_agent_t`). The shipped
policy currently ships **permissive** (denials are logged, not enforced) while
the policy is being validated. To review denials:

```bash
ausearch -m avc -ts recent | grep netwatch_agent
```

### Removing

```bash
dnf remove -y netwatch-agent
```

Service is stopped/disabled and the SELinux module removed on uninstall.
`%config(noreplace)` files under `/etc/netwatch` and existing logs are left in
place by design; delete them manually for a full purge.

### Shipping to many hosts
Instead of copying the RPM to each host, publish an internal dnf repo:

```bash
dnf install -y createrepo_c httpd
mkdir -p /var/www/html/netwatch/{8,9,10}/x86_64
cp *el8*.rpm /var/www/html/netwatch/8/x86_64/    # per major version
cp *el9*.rpm /var/www/html/netwatch/9/x86_64/
cp *el10*.rpm /var/www/html/netwatch/10/x86_64/
for v in 8 9 10; do createrepo_c /var/www/html/netwatch/$v/x86_64/; done
systemctl enable --now httpd
firewall-cmd --permanent --add-service=http && firewall-cmd --reload
```

Clients add `/etc/yum.repos.d/netwatch.repo` (`$releasever` auto-selects 8/9/10):

```ini
[netwatch]
name=Netwatch Agent
baseurl=http://<REPO_SERVER>/netwatch/$releasever/$basearch/
enabled=1
gpgcheck=0
```

Then `dnf install netwatch-agent`.
