# Builds the rootfs for the HexStrike WSL2 appliance — a real Kali userland
# with hexstrike_server.py and its tool ecosystem already installed via apt,
# exported (docker export) into a tarball that `wsl --import` turns into a
# distro. This is the whole point of the WSL2 approach over the old
# standalone-Windows-exe one: apt-installed tools are genuinely the same
# Linux binaries HexStrike already knows how to drive on Kali — no picking
# through which ones happen to have a native Windows build.
#
# Deliberately an explicit tool list rather than Kali's broad meta-packages
# (kali-tools-web, etc.) — those pull in GUI desktop apps (zaproxy alone is
# 220+MB) that don't belong in a "lightweight" headless image and already
# have perfectly good native Windows installers (see WINDOWS-MANUAL-TOOLS.md).
#
# Runs as root by default (no default-user/sudo-password prompt to script
# around) — several of these tools (nmap SYN scans, tcpdump) need raw-socket
# capabilities that are simplest to just have unconditionally inside a
# single-purpose appliance image.

FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        # essential / network
        nmap gobuster dirb nikto sqlmap hydra john hashcat \
        masscan nbtscan arp-scan enum4linux smbclient \
        # web
        ffuf feroxbuster wfuzz wafw00f \
        # password
        medusa hashcat-utils \
        # binary / reverse engineering
        gdb radare2 binwalk checksec binutils \
        # forensics
        steghide foremost exiftool testdisk scalpel bulk-extractor file \
        # osint
        amass dnsenum theharvester recon-ng \
        # exploitation
        metasploit-framework exploitdb \
        # wireless / network capture
        tshark tcpdump \
        # runtimes for the pip/gem-only tools below, plus build deps so
        # packages with C extensions (cffi, zstandard, ...) actually compile
        python3 python3-pip python3-venv python3-dev \
        ruby ruby-dev \
        build-essential libffi-dev libssl-dev cmake pkg-config rustc cargo \
        curl git ca-certificates unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hexstrike-ai

COPY hexstrike_server.py requirements.txt dashboard.html ./
COPY assets ./assets

# One single pip invocation for everything Python — hexstrike_server.py's own
# deps (from requirements.txt: flask, pwntools, angr, ...) together with the
# extra tool-CLIs below, resolved once. Splitting these into separate RUN
# steps (as an earlier version of this file did) makes pip's resolver
# backtrack through dozens of angr/claripy/cle versions trying to reconcile
# two independently-pinned installs of the same packages — merged like this,
# it resolves in well under a minute instead of getting stuck for 20+.
#
# ropper is omitted: its filebytes dependency uses the removed ast.Str API
# and fails to build on this image's Python 3.14 — ropgadget covers similar
# ground and installs cleanly. Cloud-security scanners (prowler-cloud,
# scoutsuite, checkov, kube-hunter) are omitted too: they pull in pandas,
# which has no prebuilt wheel yet for Python 3.14 and takes 20+ minutes to
# compile from source for tools fairly tangential to HexStrike's core
# recon/exploitation/OSINT use anyway.
#
# Various tools' transitive deps want newer versions of common libraries
# (requests, pyparsing, ...) than Kali's apt packages ship, and pip can't
# upgrade over an apt-installed package (no RECORD file to track it) without
# --ignore-installed — which, applied blanket, makes pip re-resolve
# everything from scratch instead of reusing already-sane apt packages, and
# blows up into a multi-hour angr/claripy/cle version search. Purging every
# apt-provided python3-* library (except the interpreter/pip/venv/dev
# packages actually needed to run pip itself) hands the whole Python library
# stack to pip instead of fighting it package-by-package as each conflict
# surfaces.
RUN dpkg -l | awk '/^ii  python3-/{print $2}' \
        | grep -vE '^python3-(pip|venv|dev|setuptools|wheel|minimal)$' \
        | xargs -r apt-get remove -y 2>/dev/null || true
# apt's dependency resolution cascade-removed python3-pip itself along with
# the above despite being excluded by name (and this image's python3 lacks
# the separate ensurepip package Debian splits out) — just reinstall it.
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/*

# angr is dropped: pinning it just traded one problem for another (pip's
# resolver backtracking through 100+ versions searching for one whose
# archinfo/claripy/cle trio doesn't conflict with the rest of this package
# set) for another (the version that resolution settled on, 9.2.120, crashes
# on import — "property 'filename' of 'CLexer' object has no setter" —
# against the newer pycparser this environment otherwise needs). angr is
# never imported by hexstrike_server.py itself either way — only inside a
# generated-script template for the /api/tools/angr endpoint, run as a
# separate subprocess — so without it that one endpoint reports a normal
# error instead of working, the same graceful-degradation shape as the
# pwntools-on-native-Windows tradeoff, not a crash anywhere else. pwntools
# itself is kept — genuinely works here, unlike on native Windows.
RUN grep -v '^angr' requirements.txt > /tmp/requirements-wsl.txt \
    && pip3 install --break-system-packages --no-cache-dir \
        -r /tmp/requirements-wsl.txt \
        dirsearch arjun uro \
        ropgadget \
        volatility3 \
        fierce sherlock-project shodan censys \
        smbmap \
        git+https://github.com/Pennyw0rth/NetExec \
    && rm -f /tmp/requirements-wsl.txt

# sqlmap and wfuzz are apt packages that depend on the python3-* libraries
# purged above — reinstalling just these two after pip has already resolved
# everything avoids reintroducing the apt-vs-pip conflicts that caused the
# purge in the first place.
RUN apt-get update && apt-get install -y --no-install-recommends sqlmap wfuzz \
    && rm -rf /var/lib/apt/lists/*

RUN gem install --no-document wpscan one_gadget zsteg evil-winrm

# dalfox names its release assets "linux-x86_64", not "linux_amd64" like the
# ProjectDiscovery tools below. Extracting the .deb's contents directly
# (dpkg-deb -x) rather than installing it (dpkg -i) — it's a single Go
# binary with no real runtime deps to resolve, and dpkg -i fails without
# apt's package lists (already dropped earlier) to satisfy declared deps.
RUN dalfox_deb_url=$(curl -s "https://api.github.com/repos/hahwul/dalfox/releases/latest" \
        | grep -oP '"browser_download_url":\s*"\K[^"]*linux-x86_64\.deb' | grep -v sha256 | head -1) \
    && curl -sL "$dalfox_deb_url" -o /tmp/dalfox.deb \
    && dpkg-deb -x /tmp/dalfox.deb /tmp/dalfox.extract \
    && find /tmp/dalfox.extract -type f -name dalfox -exec install -m 755 {} /usr/local/bin/dalfox \; \
    && rm -rf /tmp/dalfox.deb /tmp/dalfox.extract

# ProjectDiscovery's Go tools aren't in Kali's apt repos — installed from
# their GitHub release binaries instead, same technique as everything else
# here: resolve the current release via the API, download, extract to PATH.
RUN for repo in projectdiscovery/nuclei projectdiscovery/httpx projectdiscovery/subfinder projectdiscovery/katana; do \
        name=$(basename "$repo"); \
        url=$(curl -s "https://api.github.com/repos/$repo/releases/latest" \
            | grep -oP '"browser_download_url":\s*"\K[^"]*linux_amd64\.(zip|tar\.gz)' | head -1); \
        echo "Installing $name from $url"; \
        curl -sL "$url" -o "/tmp/$name.archive"; \
        mkdir -p "/tmp/$name.extract"; \
        case "$url" in \
            *.zip) unzip -q -o "/tmp/$name.archive" -d "/tmp/$name.extract" ;; \
            *) tar -xzf "/tmp/$name.archive" -C "/tmp/$name.extract" ;; \
        esac; \
        find "/tmp/$name.extract" -maxdepth 1 -type f -name "$name" -exec install -m 755 {} "/usr/local/bin/$name" \; ; \
        rm -rf "/tmp/$name.archive" "/tmp/$name.extract"; \
    done

# systemd=false: WSL boots faster without it, and this image has exactly one
# job (run hexstrike_server.py on request from the Windows launcher), not a
# general-purpose init system to manage.
RUN mkdir -p /etc && printf '[boot]\nsystemd=false\n' > /etc/wsl.conf

EXPOSE 8888

CMD ["python3", "hexstrike_server.py"]
