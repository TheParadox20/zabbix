#!/bin/sh
# Build and install the Netwatch Agent SELinux policy module.
#
# Requires: selinux-policy-devel (provides the refpolicy Makefile and
# interfaces used by netwatch-agent.te), checkpolicy, policycoreutils.
#   dnf install -y selinux-policy-devel checkpolicy policycoreutils
#
# Usage:
#   ./build.sh build     # compile netwatch-agent.pp (default)
#   ./build.sh install   # compile + semodule -i + restorecon
#   ./build.sh remove    # semodule -r netwatch-agent
set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
MODNAME=netwatch-agent
DEVEL_MK=/usr/share/selinux/devel/Makefile

cmd="${1:-build}"

build_pp() {
    if [ -f "$DEVEL_MK" ]; then
        make -C "$DIR" -f "$DEVEL_MK" "${MODNAME}.pp"
    else
        # Fallback without refpolicy devel Makefile (interfaces won't resolve;
        # prefer installing selinux-policy-devel).
        checkmodule -M -m -o "$DIR/${MODNAME}.mod" "$DIR/${MODNAME}.te"
        semodule_package -o "$DIR/${MODNAME}.pp" -m "$DIR/${MODNAME}.mod" -f "$DIR/${MODNAME}.fc"
    fi
}

case "$cmd" in
    build)   build_pp ;;
    install) build_pp
             semodule -i "$DIR/${MODNAME}.pp"
             restorecon -R -v /usr/sbin/netwatch_agent /etc/netwatch /var/log/netwatch /run/netwatch 2>/dev/null || true ;;
    remove)  semodule -r "${MODNAME}" || true ;;
    *) echo "usage: $0 {build|install|remove}" >&2; exit 2 ;;
esac
