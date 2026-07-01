# REBRAND_AUDIT.md — Netwatch Agent rebrand discovery (Phase 1)

Base: **Zabbix 7.0.27** LTS GA. Scope: Agent2 only (`src/go/cmd/zabbix_agent2/`,
its compiled `src/go/pkg/`, `src/go/plugins/`, `src/go/conf/`, and the two
build files that inject identity). Protocol/wire names, config directive names,
and GPL license headers are **out of scope** (see section D).

Naming: `Zabbix Agent 2`/`Zabbix agent 2` → **Netwatch Agent**;
`zabbix_agent2` → **netwatch_agent**; `/etc/zabbix`→`/etc/netwatch`,
`/var/log/zabbix`→`/var/log/netwatch`, `/run/zabbix`→`/run/netwatch`.

---

## A. Fix via ldflags (build-time injection — do NOT hardcode)

| File:line | Current | Change to |
|---|---|---|
| [src/go/Makefile.am:19](src/go/Makefile.am#L19) | `-X main.applicationName=zabbix_agent2` | `netwatch_agent` |
| [configure.ac:1890](configure.ac#L1890) | `AGENT2_CONFIG_FILE="${sysconfdir}/zabbix_agent2.conf"` | `.../netwatch_agent.conf` (feeds `-X main.confDefault`) |

> `applicationName` becomes the `-V`/`-h` title token (via `version.Init`,
> [zabbix_agent2.go:156](src/go/cmd/zabbix_agent2/zabbix_agent2.go#L156)).
> For a one-off manual build we can override with `go build -ldflags` instead of
> editing these files (Phase 3). Editing the files makes the `make` build carry
> the brand permanently — decision noted for Phase 2/3.

## B. Fix via direct source edit (user-facing display strings)

### B1 — version print, the `(Zabbix)` literal in `-V`
| File:line | Current | Change to |
|---|---|---|
| [version.go:148](src/go/pkg/version/version.go#L148) | `"%s (Zabbix) %s\n"` | `"%s (Netwatch) %s\n"` |

This is why `-V` prints `... (Zabbix) 7.0.27`; the token is hardcoded, not from ldflags.

### B2 — startup/shutdown/log lines & error prefixes ([zabbix_agent2.go](src/go/cmd/zabbix_agent2/zabbix_agent2.go))
| Line | Current | Change to |
|---|---|---|
| 65 | `Usage of Zabbix agent 2:` | `Usage of Netwatch Agent:` |
| 81 | `Example: zabbix_agent2 -c %[2]s` | `netwatch_agent` |
| 135, 144 | `"zabbix_agent2 [%d]: ERROR: %s\n"` | `netwatch_agent` |
| 351 | `Starting Zabbix Agent 2 (%s)` | `Starting Netwatch Agent (%s)` |
| 443 | `Zabbix Agent2 hostname: [%s]` | `Netwatch Agent hostname: [%s]` |
| 527 | `Zabbix Agent 2 stopped. (%s)` | `Netwatch Agent stopped. (%s)` |

### B3 — help-text URLs → placeholders ([zabbix_agent2.go](src/go/cmd/zabbix_agent2/zabbix_agent2.go), NEEDS HUMAN INPUT)
| Line | Current | Change to |
|---|---|---|
| 83 | `Report bugs to: <https://support.zabbix.com>` | `<SUPPORT_URL>` + `// TODO(netwatch): set real URL` |
| 84 | `Zabbix home page: <https://www.zabbix.com>` | `<HOME_URL>` |
| 85 | `Documentation: <https://www.zabbix.com/documentation>` | `<DOCS_URL>` |

### B4 — compiled-in default path
| File:line | Current | Change to |
|---|---|---|
| [pidfile_nix.go:28](src/go/pkg/pidfile/pidfile_nix.go#L28) | `path = "/tmp/zabbix_agent2.pid"` | `/tmp/netwatch_agent.pid` |

### B5 — Windows service strings (LOW priority; target is RHEL)
[service_windows.go](src/go/cmd/zabbix_agent2/service_windows.go): L37 example path,
L47 `serviceName = "Zabbix Agent 2"`, L85/94/103/112 service-command descriptions,
L359 error prefix, L417 error message. Cosmetic; edit for consistency but not
required for the RHEL deliverable.

## C. Fix via config template edit
Rename [src/go/conf/zabbix_agent2.conf](src/go/conf/zabbix_agent2.conf) →
`src/go/conf/netwatch_agent.conf`, then:

| Line | Current | Change to |
|---|---|---|
| 1 | `# ...configuration file for Zabbix agent 2 (Unix)` | `Netwatch Agent (Unix)` |
| 2 | `# To get more information about Zabbix, visit https://www.zabbix.com` | Netwatch + `<HOME_URL>` placeholder |
| 11 | `# PidFile=/tmp/zabbix_agent2.pid` | `PidFile=/run/netwatch/netwatch_agent.pid` |
| 28 | `# LogFile=/tmp/zabbix_agent2.log` | `LogFile=/var/log/netwatch/netwatch_agent.log` |
| 482 | `Include=./zabbix_agent2.d/plugins.d/*.conf` | `Include=/etc/netwatch/netwatch_agent.d/*.conf` |
| 554-556 | commented `Include=/usr/local/etc/zabbix_agent2*` examples | netwatch example paths |
| 142 | `Hostname=Zabbix server` (active default) | **DECISION** — leave, or set `Hostname=Netwatch server`? |

## D. Leave untouched (out of scope) — do NOT edit
- **GPL license headers** `Copyright (C) 2001-2026 Zabbix SIA` at top of every
  `.go` file (e.g. [version.go:2](src/go/pkg/version/version.go#L2)): GPLv2
  **requires preserving** upstream copyright notices. Keep verbatim.
- **`-V` copyright block** [version.go:33](src/go/pkg/version/version.go#L33)
  `Copyright (C) 2026 Zabbix SIA`: keep Zabbix's notice (may *add* a Netwatch
  line, but must not remove theirs). Flag for CHANGES-FROM-UPSTREAM.md.
- **Third-party license notices** [copyright_extra.go](src/go/cmd/zabbix_agent2/copyright_extra.go)
  (Eclipse/MQTT, goburrow/Modbus): required attributions, not Zabbix branding.
- **Protocol/functional references** in conf comments describing "Zabbix
  server/proxy" it connects to (L63,88,105-125, etc.) and `Server=`/`Hostname=`
  directive names: these describe real protocol behavior — the agent genuinely
  talks to a Zabbix server. Renaming would be inaccurate. Leave.
- **Source-comment mentions** (not compiled into output):
  zbxcmd_nix.go:71/77, zbxcmd_windows.go:111, systemrun.go:85, hw_linux.go:274,
  service_windows.go:634/655/667, version.go:15/145.
- **MQTT client-id prefix** [mqtt.go:537](src/go/plugins/mqtt/mqtt.go#L537)
  `"ZabbixAgent2"+...`: sent on the wire to MQTT brokers = protocol-ish
  identifier. **Accepted residual** — leave unless a later task says otherwise.
- **cgo compile-time `#error`** [tls.go:812](src/go/pkg/tls/tls.go#L812): build
  error text, never shown at runtime. Leave.

## Accepted residual strings (will still appear in `strings <binary> | grep -i zabbix`)
- Go import paths `golang.zabbix.com/agent2/...` (module path — renaming Go
  internals is explicitly out of scope per TODO).
- GPL/copyright notices (section D) — required.
- MQTT client-id prefix, tls.go compile-error text.

## Phase 2/3 completion status (2026-07-02)
- All A/B/C items applied. Binary builds as `src/go/bin/netwatch_agent`.
- `-V` → `netwatch_agent (Netwatch) 7.0.27`; `-h` fully Netwatch-branded
  (default conf path `.../etc/netwatch_agent.conf`).
- Functional: `agent.ping` → `[s|1]`, `agent.version` → `[s|7.0.27]`.
- Extra hits found during verification and fixed (not in original audit):
  zabbix_agent2.go:144 (2nd error prefix, different indent), :564 `-f`
  flag desc; service_windows.go:619 panic msg; netwatch_agent.conf agent
  self-refs (L70/231/241); shipped plugins.d redis.conf/oracle.conf comments.
- Binary output renamed via src/go/Makefile.am (target + `-o` + install/clean);
  Go package path `cmd/zabbix_agent2` intentionally NOT renamed.

### Accepted residual `strings <binary> | grep -i zabbix` (verified, all non-display)
- GPL `Copyright (C) 2026 Zabbix SIA`; help URLs (support/home/docs.zabbix.com — kept by decision).
- Protocol/item-keys: `zabbix.stats`, `net.dns.perf[,zabbix.com]`, `ZabbixStats/Async`,
  `SSH-...-zabbix_agent`, zabbix.stats item description.
- Internal: `golang.zabbix.com/*` module paths, cgo symbols (`handleZabbixLog`),
  shared C-lib msgs (`zbx_malloc ... Zabbix developers`), absolute build paths.

### Release-build follow-up (Phase 3/6, not a branding blocker)
- Add `-trimpath` to the Go build (and consider stripping) so the binary does
  not embed the developer's absolute path `/home/.../netwatch/zabbix/...`.

## Out-of-scope residual (Windows packaging — not targeted)
- `src/go/conf/zabbix_agent2.win.conf` (Windows config template) left unbranded;
  not installed by the Unix Makefile, so absent from the RHEL deliverable.

## Open decisions for the human
1. **B3 URLs** — real support/home/docs URLs.
2. **A (ldflags)** — edit Makefile.am/configure.ac permanently, or override per-build?
3. **C L142** — default `Hostname` value: leave `Zabbix server` or rebrand?
4. **version.go:33** — add a Netwatch copyright line alongside Zabbix's?
