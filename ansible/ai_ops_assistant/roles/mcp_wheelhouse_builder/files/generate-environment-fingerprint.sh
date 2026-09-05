#!/usr/bin/env bash

set -euo pipefail

OUTPUT="${1:-environment-fingerprint.txt}"

{
    echo "=== OS ==="
    cat /etc/os-release
    echo

    echo "=== Kernel / Architecture ==="
    uname -srmo
    dpkg --print-architecture
    echo

    echo "=== Python ==="
    echo "python3_path=$(command -v python3)"
    echo "python3_realpath=$(readlink -f "$(command -v python3)")"
    python3 --version
    echo

    echo "=== Python binary checksum ==="
    sha256sum "$(readlink -f "$(command -v python3)")"
    echo

    echo "=== Python runtime details ==="
    python3 - <<'PY'
import platform
import sys
import sysconfig

print(f"sys.version={sys.version}")
print(f"sys.executable={sys.executable}")
print(f"implementation={platform.python_implementation()}")
print(f"machine={platform.machine()}")
print(f"platform={platform.platform()}")
print(f"python_build={platform.python_build()}")
print(f"python_compiler={platform.python_compiler()}")
print(f"SOABI={sysconfig.get_config_var('SOABI')}")
print(f"MULTIARCH={sysconfig.get_config_var('MULTIARCH')}")
PY
    echo

    echo "=== glibc ==="
    getconf GNU_LIBC_VERSION
    ldd --version | head -n 1
    dpkg-query -W -f='libc6=${Version}\n' libc6 2>/dev/null || true
    echo

    echo "=== pip / Python packaging ==="
    python3 -m pip --version 2>/dev/null || echo "pip=not-installed"

    python3 -m pip show \
        pip \
        setuptools \
        wheel \
        pip-tools \
        2>/dev/null \
        | grep -E '^(Name|Version):' || true
    echo

    echo "=== Build tools ==="

    for cmd in \
        gcc \
        g++ \
        make \
        cmake \
        pkg-config \
        ld \
        ar \
        git \
        curl \
        openssl
    do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "--- $cmd ---"
            echo "path=$(command -v "$cmd")"

            case "$cmd" in
                make)
                    "$cmd" --version | head -n 1
                    ;;
                *)
                    "$cmd" --version 2>&1 | head -n 1
                    ;;
            esac
        else
            echo "--- $cmd ---"
            echo "not-installed"
        fi
    done

    echo

    echo "=== Relevant Debian packages ==="

    dpkg-query -W \
        -f='${Package}=${Version}\n' \
        python3 \
        python3-pip \
        python3-dev \
        libc6 \
        libc6-dev \
        build-essential \
        gcc \
        g++ \
        make \
        cmake \
        pkg-config \
        binutils \
        git \
        curl \
        libssl-dev \
        2>/dev/null \
        | sort

} > "$OUTPUT"

sha256sum "$OUTPUT" > "${OUTPUT}.sha256"

echo "Created:"
echo "  $OUTPUT"
echo "  ${OUTPUT}.sha256"