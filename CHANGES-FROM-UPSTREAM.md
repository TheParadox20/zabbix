# CHANGES FROM UPSTREAM

This repository is a **rebranded derivative of Zabbix Agent 2**, produced as
"Netwatch Agent". It exists to ship a white-labeled build of the agent while
complying with the upstream license.

## Upstream project

- **Project:** Zabbix
- **Homepage:** https://www.zabbix.com
- **Source:** https://github.com/zabbix/zabbix
- **Forked from tag:** `7.4.11` (7.4 release line, **non-LTS**, GA)
- **License:** GNU Affero General Public License, version 3 (AGPLv3).
  The full license text is preserved verbatim in [`COPYING`](COPYING) and is
  unchanged from upstream.

> Note: earlier planning notes referred to "GPLv2". That is incorrect for this
> version — Zabbix 7.x is licensed under **AGPLv3**. All packaging and
> compliance artifacts in this repo use AGPLv3.

## Nature of the changes

**Rebrand only. No functional or protocol changes.** Only cosmetic/display
strings and filesystem paths were modified. Item keys, JSON protocol field
names, and configuration directive names (`Server=`, `Hostname=`, …) are
unchanged, so the agent remains wire-compatible with a Zabbix server/proxy.

Naming applied:

| Upstream | Netwatch |
|---|---|
| `Zabbix Agent 2` / `Zabbix agent 2` (display) | `Netwatch Agent` |
| `zabbix_agent2` (binary) | `netwatch_agent` |
| `zabbix-agent2` (service/package) | `netwatch-agent` |
| `zabbix` (user/group) | `netwatch` |
| `/etc/zabbix`, `/var/log/zabbix`, `/run/zabbix` | `/etc/netwatch`, `/var/log/netwatch`, `/run/netwatch` |

### Files changed vs. tag `7.4.11`

- `src/go/cmd/zabbix_agent2/zabbix_agent2.go` — usage/help banner, startup/
  shutdown log lines, error prefixes, `-f` flag description.
- `src/go/cmd/zabbix_agent2/service_nix.go` — example config path in help.
- `src/go/cmd/zabbix_agent2/service_windows.go` — Windows service name and
  command descriptions (Windows is not a packaged target; changed for
  consistency).
- `src/go/pkg/version/version.go` — the `(Zabbix)` token in `-V` output → `(Netwatch)`.
- `src/go/pkg/pidfile/pidfile_nix.go` — default PID path `/tmp/*.pid`.
- `src/go/conf/zabbix_agent2.conf` → **renamed** to `src/go/conf/netwatch_agent.conf`;
  header, default paths, `Hostname`, and `Include` updated.
- `src/go/conf/zabbix_agent2.d/plugins.d/{redis,oracle}.conf` — comment rebrand.
- `src/go/Makefile.am` — `-X main.applicationName=netwatch_agent`, binary output
  renamed to `bin/netwatch_agent`, and install/dist paths.
- `configure.ac` — `AGENT2_CONFIG_FILE`/`AGENT2_CONFIG_DIR` default names.

The Go module path (`golang.zabbix.com/agent2/...`) and internal package/
function names were intentionally **not** renamed (branding is not affected by
them and renaming adds merge risk).

### Intentionally retained upstream strings

- The upstream copyright notice `Copyright (C) 2026 Zabbix SIA` and the AGPLv3
  notice in `-V` output are preserved (required by the license).
- Help-text URLs (`support.zabbix.com`, `www.zabbix.com`,
  `www.zabbix.com/documentation`) are retained for now — they point to the
  genuine upstream resources. **TODO(netwatch):** replace with Netwatch URLs
  when available.
- Protocol-level identifiers that appear as literals (item keys such as
  `zabbix.stats`, the `ZabbixStats`/`ZabbixAsync` plugin names, the
  `SSH-...-zabbix_agent` client banner) are unchanged to preserve compatibility.

## Trademark / artwork

No Zabbix logo or artwork files are included in the packaged output. The RPM
`%files` list installs only the binary, config templates, unit/sysconfig/
tmpfiles/logrotate/firewalld/SELinux files, `COPYING`, and this document —
it does **not** package upstream `man/` pages or `images/` assets, which carry
Zabbix branding/trademark.

## Source availability (AGPLv3 compliance)

The complete corresponding source for this build is the fork:

- https://github.com/TheParadox20/zabbix (branch `netwatch-rebrand-7.4`)

This must remain **publicly accessible** to satisfy AGPLv3's source-provision
requirements. Under AGPLv3 §13, if the agent is ever modified to let remote
users interact with it over a network, those users must also be offered the
corresponding source; the current rebrand introduces no such interaction
beyond the standard monitoring protocol.

_Rebrand date: 2026-07-02. Base: Zabbix 7.4.11._
