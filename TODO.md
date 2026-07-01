# TODO: Rebrand Zabbix Agent2 → Netwatch Agent (RHEL)

## Context for the coding agent

This repo is a fork of `zabbix/zabbix` (GPLv2). Goal: produce a fully
white-labeled build of Zabbix Agent2 — binary, config, service, paths,
and all user-facing strings renamed from "Zabbix"/"zabbix_agent2" to
"Netwatch"/"netwatch_agent" — packaged as an RPM for RHEL, while staying
GPLv2-compliant (keep `COPYING`, document changes, no use of the Zabbix
name/trademark/logo in branding).

**Naming convention to apply everywhere:**

| Old | New |
|---|---|
| `Zabbix Agent 2` / `Zabbix agent 2` (display) | `Netwatch Agent` |
| `zabbix_agent2` (binary/identifiers) | `netwatch_agent` |
| `zabbix-agent2` (service/package name) | `netwatch-agent` |
| `zabbix` (user/group) | `netwatch` |
| `/etc/zabbix` | `/etc/netwatch` |
| `/var/log/zabbix` | `/var/log/netwatch` |
| `/run/zabbix` | `/run/netwatch` |

Do **not** rename: item keys, JSON protocol field names, config directive
names (`Server=`, `Hostname=`, etc.) — only cosmetic/display strings and
filesystem paths. Protocol-level names must stay compatible with whatever
server/proxy this agent reports to, unless a later task explicitly says
to change them.

Confirm the target Zabbix version/tag before starting (fill in below),
matching what's currently deployed via RPM (`zabbix_agent2 -V`):

```
TARGET_TAG=7.0.27   # confirmed 2026-07-02: latest 7.0 LTS GA (7.0.28rc1 skipped, not GA).
                    # netwatch-rebrand re-cut onto this tag from upstream github.com/zabbix/zabbix.
                    # Requires Go 1.25.9 (src/go/go.mod) — NOT yet installed on this box.
```

---

## Phase 0 — Repo setup

- [ ] Confirm working branch is a checkout of `TARGET_TAG` off the fork:
      `git checkout -b netwatch-rebrand $TARGET_TAG`
- [ ] Confirm Go toolchain installed matches the minimum version required
      by this Zabbix release (check `src/go/go.mod` for the `go` directive).
- [ ] Install build deps (RHEL): `dnf groupinstall -y "Development Tools"`,
      `dnf install -y golang pcre2-devel openssl-devel autoconf automake libtool git rpm-build`
- [ ] Record baseline: run `./bootstrap.sh && ./configure --enable-agent2` once,
      unmodified, and confirm it builds clean before making any changes
      (sanity check that the environment works before we start editing).

## Phase 1 — Discovery: find every string/path that needs changing

- [ ] Run and save output of a full-repo grep scoped to agent2 and its
      shared deps (do NOT blindly sed the whole repo — agent2 shares
      packages with server/proxy/sender, only touch what agent2 actually
      compiles):
  ```bash
  grep -rniE "zabbix[ _-]?agent[ _-]?2|zabbix agent 2" \
    src/go/cmd/zabbix_agent2/ \
    src/go/pkg/ \
    src/go/plugins/ \
    --include="*.go" -l | sort -u > /tmp/agent2_go_hits.txt
  ```
- [ ] Identify build-time-injected variables (do NOT hardcode-patch these,
      override via ldflags instead — see Phase 3): search
      `src/go/Makefile.am` (or wherever `go build` is invoked) for
      `-ldflags` / `-X main.` patterns, list every `-X` variable found.
- [ ] Identify hardcoded display strings that DO need direct source edits
      (usage banner, help text, `-V`/`-h` output, startup log line,
      "Report bugs to"/homepage URLs). Typical location:
      `src/go/cmd/zabbix_agent2/zabbix_agent2.go` — confirm exact file(s)
      for this tag via the grep above.
- [ ] Check for a version banner / title constants file (name varies by
      version — look for `version.go`, `title.go`, or similar under
      `src/go/pkg/version/`).
- [ ] Check `src/go/pkg/zbxflag/` (or equivalent) for CLI flag descriptions
      that mention "Zabbix agent 2" in help text.
- [ ] Check for references to default paths compiled into fallback logic
      (e.g. `/tmp/zabbix_agent2.log` default LogFile, `/usr/local/etc/...`
      compiled defaults) that aren't already covered by the `-X` ldflags
      vars — list every one found.
- [ ] Check `conf/zabbix_agent2.conf` (the shipped example config template)
      for header comments referencing Zabbix, and default `Include=`,
      `PidFile=`, `LogFile=` paths.
- [ ] Produce a single markdown file `REBRAND_AUDIT.md` at repo root listing
      every file + line found above, categorized as:
      (a) fix via ldflags, (b) fix via direct source edit, (c) fix via
      config template edit. This is a checkpoint — do not proceed to
      Phase 2 until this audit file exists and looks complete.

## Phase 2 — Source edits (category b/c from audit)

- [ ] Patch all display strings identified in Phase 1 from "Zabbix Agent 2"
      / "Zabbix agent 2" → "Netwatch Agent", and `zabbix_agent2` →
      `netwatch_agent` in help/usage/version text.
- [ ] Replace "Report bugs to"/homepage/documentation URLs in the help
      text with placeholders: `<SUPPORT_URL>`, `<HOME_URL>`, `<DOCS_URL>` —
      flag these clearly in a code comment `// TODO(netwatch): set real URL`
      so the human can fill in real values; do not invent URLs.
- [ ] Update `conf/zabbix_agent2.conf` template: rename file itself to
      `conf/netwatch_agent.conf`, update header comments, and set:
      ```
      PidFile=/run/netwatch/netwatch_agent.pid
      LogFile=/var/log/netwatch/netwatch_agent.log
      Include=/etc/netwatch/netwatch_agent.d/*.conf
      ```
- [ ] Do NOT rename Go package names, module paths, or internal function
      names purely for branding — only user-facing strings and the
      shipped config template. (Renaming Go internals adds risk/merge
      pain for no visible benefit; skip unless a later task asks for it.)
- [ ] After edits, re-run the Phase 1 grep commands and confirm zero
      remaining hits in files that were in-scope, except:
      - protocol/wire-level identifiers (leave untouched)
      - anything explicitly marked out-of-scope in REBRAND_AUDIT.md

## Phase 3 — Build with renamed identity

- [ ] Determine the exact `-ldflags "-X ..."` invocation for this tag
      (from Phase 1 findings) and build:
  ```bash
  go build -ldflags "\
    -X main.applicationName=netwatch_agent \
    -X main.confDefault=/etc/netwatch/netwatch_agent.conf" \
    -o build/netwatch_agent \
    ./src/go/cmd/zabbix_agent2/
  ```
  (Adjust variable names to whatever Phase 1 actually found — do not
  assume `main.applicationName`/`main.confDefault` are correct for this
  tag without verifying.)
- [ ] Verify:
  ```bash
  ./build/netwatch_agent -V   # must show Netwatch branding, no "Zabbix" string
  ./build/netwatch_agent -h   # must show Netwatch branding, no "Zabbix" string
  ```
- [ ] Run: `strings build/netwatch_agent | grep -i zabbix` — review every
      hit. Expected remaining hits: none in display/help/version text.
      Acceptable remaining hits (do not remove): none related to
      protocol field names if any exist as literal strings (e.g. JSON
      keys) — list any such hits in `REBRAND_AUDIT.md` under a new
      "accepted residual strings" section with justification.
- [ ] Confirm binary runs standalone against a test config:
      `./build/netwatch_agent -c ./conf/netwatch_agent.conf -t agent.ping`

## Phase 4 — Packaging layout

- [ ] Create packaging tree under `packaging/rpm/` in the repo:
  ```
  packaging/rpm/netwatch-agent.spec
  packaging/systemd/netwatch-agent.service
  packaging/sysconfig/netwatch-agent
  packaging/tmpfiles.d/netwatch-agent.conf
  packaging/logrotate/netwatch-agent
  packaging/firewalld/netwatch-agent.xml
  packaging/selinux/netwatch-agent.te   (see Phase 5)
  ```
- [ ] `packaging/systemd/netwatch-agent.service`:
  ```ini
  [Unit]
  Description=Netwatch Agent
  After=network.target

  [Service]
  Environment="CONFFILE=/etc/netwatch/netwatch_agent.conf"
  EnvironmentFile=-/etc/sysconfig/netwatch-agent
  Type=simple
  Restart=on-failure
  RestartSec=10s
  PIDFile=/run/netwatch/netwatch_agent.pid
  KillMode=control-group
  ExecStart=/usr/sbin/netwatch_agent -c ${CONFFILE} -f
  ExecStop=/bin/kill -SIGTERM $MAINPID
  User=netwatch
  Group=netwatch

  [Install]
  WantedBy=multi-user.target
  ```
- [ ] `packaging/tmpfiles.d/netwatch-agent.conf`:
  ```
  d /run/netwatch 0755 netwatch netwatch -
  ```
- [ ] `packaging/logrotate/netwatch-agent`:
  ```
  /var/log/netwatch/netwatch_agent.log {
      weekly
      rotate 10
      compress
      missingok
      notifempty
      create 640 netwatch netwatch
      postrotate
          systemctl reload netwatch-agent >/dev/null 2>&1 || true
      endscript
  }
  ```
- [ ] `packaging/firewalld/netwatch-agent.xml`:
  ```xml
  <?xml version="1.0" encoding="utf-8"?>
  <service>
    <short>Netwatch Agent</short>
    <description>Netwatch monitoring agent (passive checks)</description>
    <port protocol="tcp" port="10050"/>
  </service>
  ```

## Phase 5 — SELinux policy module

- [ ] Write `packaging/selinux/netwatch-agent.te` as a standalone module
      (do not assume the Zabbix SELinux policy package is installed —
      this build should not depend on it):
      - executable domain transition for `/usr/sbin/netwatch_agent`
      - file contexts for `/etc/netwatch(/.*)?`, `/var/log/netwatch(/.*)?`,
        `/run/netwatch(/.*)?`
      - network port type for tcp/10050 if not already covered by an
        existing port type
- [ ] Include build commands in the spec's `%post`/`%postun` (or a
      separate `packaging/selinux/build.sh`) using `checkmodule`/
      `semodule_package`/`semodule -i`.
- [ ] Note in `REBRAND_AUDIT.md` that this policy needs testing in
      enforcing mode on a real RHEL host — flag as a manual QA step,
      do not mark this task fully "done" without that test.

## Phase 6 — RPM spec

- [ ] `packaging/rpm/netwatch-agent.spec` should:
  - `Name: netwatch-agent`, `License: GPLv2`, `Summary:` describing it
    as a Netwatch-branded monitoring agent
  - `%description` includes a clear statement: "This package is a
    rebranded derivative of Zabbix Agent2 (https://www.zabbix.com/),
    licensed under GPLv2. See CHANGES-FROM-UPSTREAM.md for modifications."
  - `%files` list: binary, config template, systemd unit, sysconfig,
    tmpfiles.d, logrotate, firewalld service def, SELinux module
  - `%pre`: create `netwatch` user/group (system account, nologin)
  - `%post`: `systemctl daemon-reload`; install SELinux module;
    `firewall-cmd --reload` if firewalld present (guard with existence
    check, don't hard-fail if firewalld isn't installed)
  - `%preun`/`%postun`: stop/disable service on removal, clean up
    SELinux module and firewalld service def on full uninstall (not on
    upgrade — use the standard `$1` argument check)
  - Include `COPYING` (GPLv2 text) in `%doc`
- [ ] Build and validate: `rpmbuild -bb packaging/rpm/netwatch-agent.spec`
      then `rpmlint` the resulting package and fix any warnings that
      aren't false positives.

## Phase 7 — License / compliance artifacts

- [ ] Ensure `COPYING` (GPLv2) is present at repo root, unmodified.
- [ ] Create `CHANGES-FROM-UPSTREAM.md` documenting: upstream project name
      and URL, version/tag forked from, summary of changes made (rename
      only — no functional changes), and date.
- [ ] Confirm no Zabbix logo/artwork files are included in the packaged
      output (check `%files` in the spec doesn't pull in `man/`, `images/`,
      or doc assets that carry Zabbix branding/trademark — list anything
      excluded for this reason in `CHANGES-FROM-UPSTREAM.md`).
- [ ] Confirm source of this fork remains publicly accessible (satisfies
      GPLv2 source-availability requirement) — note the fork URL in
      `CHANGES-FROM-UPSTREAM.md`.

## Phase 8 — Install test (manual/CI, on an actual RHEL box or container)

- [ ] `rpm -i` the built package on a clean RHEL test host.
- [ ] Confirm: user/group created, directories present with correct
      ownership, SELinux contexts correct (`ls -Z`), service starts
      under `systemctl start netwatch-agent`, log file is written to
      `/var/log/netwatch/netwatch_agent.log`, `netwatch_agent -V`/`-h`
      show no Zabbix branding.
- [ ] Confirm passive check works: `zabbix_get -s <host> -k agent.ping`
      (or equivalent) returns a value from a real Zabbix server pointed
      at this agent, proving protocol compatibility wasn't broken.
- [ ] Confirm SELinux enforcing mode: `getenforce` returns `Enforcing`
      during this whole test, and `journalctl -t setroubleshoot` /
      `ausearch -m avc` show no denials for the service.
- [ ] `rpm -e` and confirm clean removal (no orphaned files, service
      unregistered, SELinux module removed, firewalld service removed).

## Open items requiring a human decision (do not guess)

- [ ] Real support URL / homepage URL / docs URL to replace placeholders
      from Phase 2.
- [ ] Final package version/release numbering scheme (tied to upstream
      Zabbix version, or independent?).
- [ ] Whether TLS PSK / cert-based agent-server auth defaults need any
      Netwatch-specific documentation changes (functionality unchanged,
      docs/wording only).
