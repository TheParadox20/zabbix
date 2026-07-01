# Netwatch Agent — RHEL build & install test (Phases 6 & 8)

These steps **must run on a real RHEL / Rocky / Alma 9 host or container** —
they cannot be performed on the Kali dev box (no `rpmbuild` toolchain deps, no
SELinux, no systemd session). `rpmbuild` and `rpm` exist on Kali but the
`BuildRequires` (golang, pcre2-devel, openssl-devel, systemd-rpm-macros,
selinux-policy-devel) and the SELinux refpolicy Makefile do not.

## 1. Build the RPM (Phase 6)

On a RHEL 9 host/container:

```bash
dnf install -y rpm-build rpmlint golang gcc make autoconf automake libtool \
    pcre2-devel openssl-devel systemd-rpm-macros selinux-policy-devel

# Prepare the source tarball (name must match Source0: netwatch-agent-<ver>.tar.gz)
VER=7.0.27
git -C /path/to/repo archive --format=tar.gz \
    --prefix=netwatch-agent-${VER}/ -o ~/rpmbuild/SOURCES/netwatch-agent-${VER}.tar.gz HEAD

# Network-isolated builders (mock/koji): vendor Go deps first and include vendor/
#   (cd src/go && go mod vendor) then re-create the tarball.

rpmbuild -bb packaging/rpm/netwatch-agent.spec
rpmlint ~/rpmbuild/RPMS/x86_64/netwatch-agent-*.rpm   # fix non-false-positive warnings
```

## 2. Install test (Phase 8)

On a **clean** RHEL host with `getenforce` == `Enforcing` throughout:

```bash
rpm -i netwatch-agent-7.0.27-1.el9.x86_64.rpm
```

Confirm each:

- [ ] **User/group:** `getent passwd netwatch && getent group netwatch`
      (system account, `/sbin/nologin`).
- [ ] **Directories + ownership:**
      `ls -ld /etc/netwatch /etc/netwatch/netwatch_agent.d /var/log/netwatch`
      and `ls -ld /run/netwatch` (created by tmpfiles, owned netwatch:netwatch).
- [ ] **SELinux contexts:** `ls -Z /usr/sbin/netwatch_agent /etc/netwatch \
      /var/log/netwatch /run/netwatch` show the `netwatch_agent_*` types.
- [ ] **Service:** `systemctl start netwatch-agent && systemctl status netwatch-agent`
      starts cleanly; enable with `systemctl enable netwatch-agent`.
- [ ] **Logging:** `/var/log/netwatch/netwatch_agent.log` is written.
- [ ] **Branding:** `netwatch_agent -V` and `-h` show no "Zabbix" in
      display/help text (upstream copyright notice + retained URLs excepted).
- [ ] **Protocol compatibility:** from a Zabbix server/proxy pointed at this
      host, `zabbix_get -s <host> -k agent.ping` returns `1`.
- [ ] **SELinux denials:** during the whole test,
      `ausearch -m avc -ts recent` / `journalctl -t setroubleshoot` show no
      denials for `netwatch_agent_t`.
      NOTE: the shipped policy declares the domain **permissive** initially
      (see netwatch-agent.te) so denials are logged, not enforced. Review any
      denials, fold the needed `allow` rules into the `.te`, then remove the
      `permissive netwatch_agent_t;` line and rebuild to enforce.
- [ ] **firewalld:** if firewalld is running, `firewall-cmd --add-service=netwatch-agent`
      opens tcp/10050.

## 3. Removal test

```bash
rpm -e netwatch-agent
```

- [ ] Service stopped and disabled; unit removed.
- [ ] SELinux module removed: `semodule -l | grep netwatch-agent` → empty.
- [ ] firewalld service def removed / reload clean.
- [ ] No orphaned files under `/usr/sbin`, `/etc/netwatch`
      (note: `%config(noreplace)` files and logs may remain by design; verify
      this matches your uninstall policy).
```
