%global debug_package %{nil}
%global agentuser netwatch
%global agentgroup netwatch

Name:           netwatch-agent
Version:        7.0.27
Release:        1%{?dist}
Summary:        Netwatch-branded monitoring agent (rebranded Zabbix Agent 2)

# Upstream (Zabbix 7.0) is licensed under the GNU Affero GPL v3.
License:        AGPLv3
URL:            https://www.zabbix.com
# NOTE(netwatch): replace URL/Source0 with the Netwatch fork location once public.
# The source tarball is expected to be the (rebranded) repository tree.
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  pkgconfig
BuildRequires:  pcre2-devel
BuildRequires:  openssl-devel
# Go >= 1.25.9 (src/go/go.mod) must be on PATH at build time. Not a hard
# BuildRequires because sites commonly install the upstream Go tarball in
# /usr/local/go, which is not RPM-managed. If your dnf go-toolset provides
# >= 1.25.9, you may uncomment the next line and drop the tarball.
# BuildRequires:  golang >= 1.25.9
BuildRequires:  systemd-rpm-macros
# For building the bundled SELinux policy module:
BuildRequires:  selinux-policy-devel

Requires(pre):  shadow-utils
Requires:       (libpcre2-8 or pcre2)
%{?systemd_requires}
# SELinux policy is loaded in scriptlets; require the tooling.
Requires(post):   policycoreutils
Requires(postun): policycoreutils

%description
Netwatch Agent is a monitoring agent for collecting system metrics and
serving passive checks and active checks to a monitoring server/proxy.

This package is a rebranded derivative of Zabbix Agent 2
(https://www.zabbix.com/), licensed under the GNU Affero General Public
License v3. Only cosmetic/display strings and filesystem paths have been
changed; no functional or protocol changes were made. See
CHANGES-FROM-UPSTREAM.md for the full list of modifications.

%prep
%setup -q

%build
# NOTE(netwatch): the Go build resolves modules from the network by default.
# In a network-isolated build (mock/koji), vendor dependencies first
# (`cd src/go && go mod vendor`) and ship the vendor/ tree in Source0, or
# provide a populated module cache. GOFLAGS below prefers vendor if present.
export GOFLAGS="-mod=mod"
./bootstrap.sh
# sysconfdir=/etc/netwatch makes the compiled default config path
# /etc/netwatch/netwatch_agent.conf (via -X main.confDefault).
%configure \
    --enable-agent2 \
    --with-libpcre2 \
    --with-openssl \
    --sbindir=%{_sbindir} \
    --sysconfdir=%{_sysconfdir}/netwatch
make %{?_smp_mflags}

# Build the SELinux policy module (netwatch-agent.pp).
make -C packaging/selinux -f %{_datadir}/selinux/devel/Makefile netwatch-agent.pp

%install
# --- binary ---
install -D -m 0755 src/go/bin/netwatch_agent %{buildroot}%{_sbindir}/netwatch_agent

# --- main config + include dirs ---
install -D -m 0640 src/go/conf/netwatch_agent.conf \
        %{buildroot}%{_sysconfdir}/netwatch/netwatch_agent.conf
install -d -m 0755 %{buildroot}%{_sysconfdir}/netwatch/netwatch_agent.d/plugins.d
for f in src/go/conf/zabbix_agent2.d/plugins.d/*.conf; do
    [ -e "$f" ] || continue
    install -m 0644 "$f" %{buildroot}%{_sysconfdir}/netwatch/netwatch_agent.d/plugins.d/
done

# --- log dir (owned, empty) ---
install -d -m 0750 %{buildroot}%{_localstatedir}/log/netwatch

# --- systemd / sysconfig / tmpfiles / logrotate / firewalld ---
install -D -m 0644 packaging/systemd/netwatch-agent.service \
        %{buildroot}%{_unitdir}/netwatch-agent.service
install -D -m 0640 packaging/sysconfig/netwatch-agent \
        %{buildroot}%{_sysconfdir}/sysconfig/netwatch-agent
install -D -m 0644 packaging/tmpfiles.d/netwatch-agent.conf \
        %{buildroot}%{_tmpfilesdir}/netwatch-agent.conf
install -D -m 0644 packaging/logrotate/netwatch-agent \
        %{buildroot}%{_sysconfdir}/logrotate.d/netwatch-agent
install -D -m 0644 packaging/firewalld/netwatch-agent.xml \
        %{buildroot}%{_prefix}/lib/firewalld/services/netwatch-agent.xml

# --- SELinux policy module ---
install -D -m 0644 packaging/selinux/netwatch-agent.pp \
        %{buildroot}%{_datadir}/selinux/packages/%{name}/netwatch-agent.pp

%pre
getent group %{agentgroup} >/dev/null || groupadd -r %{agentgroup}
getent passwd %{agentuser} >/dev/null || \
    useradd -r -g %{agentgroup} -d /run/netwatch -s /sbin/nologin \
            -c "Netwatch Agent" %{agentuser}
exit 0

%post
%systemd_post netwatch-agent.service
systemd-tmpfiles --create %{_tmpfilesdir}/netwatch-agent.conf >/dev/null 2>&1 || true

# Load SELinux policy module (only if SELinux tooling is present).
if [ -x /usr/sbin/semodule ]; then
    semodule -i %{_datadir}/selinux/packages/%{name}/netwatch-agent.pp >/dev/null 2>&1 || :
    restorecon -R %{_sbindir}/netwatch_agent %{_sysconfdir}/netwatch \
        %{_localstatedir}/log/netwatch /run/netwatch >/dev/null 2>&1 || :
fi

# Register the firewalld service definition (do not hard-fail if absent).
if [ -x /usr/bin/firewall-cmd ] && /usr/bin/firewall-cmd --state >/dev/null 2>&1; then
    /usr/bin/firewall-cmd --reload >/dev/null 2>&1 || :
fi

%preun
%systemd_preun netwatch-agent.service

%postun
%systemd_postun_with_restart netwatch-agent.service
# On full uninstall ($1 == 0), not on upgrade: clean up SELinux + firewalld.
if [ "$1" -eq 0 ]; then
    if [ -x /usr/sbin/semodule ]; then
        semodule -r netwatch-agent >/dev/null 2>&1 || :
    fi
    if [ -x /usr/bin/firewall-cmd ] && /usr/bin/firewall-cmd --state >/dev/null 2>&1; then
        /usr/bin/firewall-cmd --reload >/dev/null 2>&1 || :
    fi
fi

%files
%license COPYING
%doc CHANGES-FROM-UPSTREAM.md
%attr(0755,root,root) %{_sbindir}/netwatch_agent
%dir %attr(0755,root,root) %{_sysconfdir}/netwatch
%dir %attr(0755,root,root) %{_sysconfdir}/netwatch/netwatch_agent.d
%dir %attr(0755,root,root) %{_sysconfdir}/netwatch/netwatch_agent.d/plugins.d
%config(noreplace) %attr(0640,root,%{agentgroup}) %{_sysconfdir}/netwatch/netwatch_agent.conf
%config(noreplace) %{_sysconfdir}/netwatch/netwatch_agent.d/plugins.d/*.conf
%config(noreplace) %attr(0640,root,root) %{_sysconfdir}/sysconfig/netwatch-agent
%config(noreplace) %{_sysconfdir}/logrotate.d/netwatch-agent
%{_unitdir}/netwatch-agent.service
%{_tmpfilesdir}/netwatch-agent.conf
%{_prefix}/lib/firewalld/services/netwatch-agent.xml
%{_datadir}/selinux/packages/%{name}/netwatch-agent.pp
%dir %attr(0750,%{agentuser},%{agentgroup}) %{_localstatedir}/log/netwatch

%changelog
* Thu Jul 02 2026 Netwatch <noreply@example.com> - 7.0.27-1
- Initial Netwatch Agent package: rebranded build of Zabbix Agent 2 7.0.27 (AGPLv3).
