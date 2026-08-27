# Manually installing the rest of HexStrike's tools on Windows

HexStrike's "Install Tools" button in the Windows app automatically installs **nmap, hashcat, nuclei, httpx, subfinder, katana, ffuf, gobuster, dalfox** — the tools that ship as a single native `.exe` with no extra runtime. Everything else HexStrike can call needs either a runtime you install yourself (Python, Ruby, Go, Java) or doesn't have a real Windows story at all. This page is the honest list, grouped the same way `/health` reports them, so you can see exactly what you're getting into per tool.

**Legend:** 🟢 official Windows installer/binary exists — straightforward. 🟡 needs a runtime (Python/Ruby/Go/Java) installed first, then a one-line install command. 🔴 no practical native-Windows path — use [WSL](https://learn.microsoft.com/windows/wsl/install) (`wsl --install`, then use Linux `apt`/`pip` as normal inside it) or a Linux VM.

## Essential

- **dirb** 🔴 — no Windows build. Use WSL, or gobuster/ffuf (already auto-installed) instead.
- **nikto** 🟡 — Perl script. Install [Strawberry Perl](https://strawberryperl.com/), then `perl nikto.pl` from https://github.com/sullo/nikto.
- **sqlmap** 🟡 — pure Python. Install [Python](https://www.python.org/downloads/windows/), then `pip install sqlmap` or clone https://github.com/sqlmapproject/sqlmap.
- **hydra** 🔴 — notoriously unreliable on native Windows. Use WSL: `sudo apt install hydra`.
- **john** (John the Ripper) 🟢 — official Windows "Jumbo" build: https://www.openwall.com/john/ (download the `-jumbo-*-win64.zip`).

## Network

- **rustscan** 🟢 — Windows binary in releases: https://github.com/RustScan/RustScan/releases
- **masscan** 🔴 — needs raw sockets/libpcap, no official Windows build. WSL.
- **autorecon** 🟡 — Python. `pip install autorecon` (needs Python).
- **nbtscan**, **arp-scan**, **rpcclient**, **enum4linux** 🔴 — Linux-native, no real Windows build. WSL.
- **responder** 🟡/🔴 — Python, technically runs on Windows with admin rights but designed for Linux; WSL recommended, or use [Inveigh](https://github.com/Kevin-Robertson/Inveigh) (a genuine PowerShell-native equivalent) instead.
- **nxc** (NetExec) 🟡 — Python. `pip install netexec`.
- **enum4linux-ng** 🟡 — Python. `pip install` per https://github.com/cddmp/enum4linux-ng, needs Python.

## Web security

- **feroxbuster** 🟢 — Windows binary: https://github.com/epi052/feroxbuster/releases
- **dirsearch** 🟡 — Python. `pip install dirsearch`.
- **dotdotpwn**, **xsser** 🔴 — Perl/Linux-GUI oriented. WSL.
- **wfuzz** 🔴 — Python but depends on `pycurl`, painful to build on native Windows. WSL, or use ffuf (already installed) instead.
- **gau** 🟢 — Windows binary: https://github.com/lc/gau/releases
- **waybackurls**, **hakrawler**, **anew**, **qsreplace** 🟡 — Go tools with no prebuilt binaries; need the [Go toolchain](https://go.dev/dl/) then e.g. `go install github.com/tomnomnom/waybackurls@latest`.
- **arjun** 🟡 — Python. `pip install arjun`.
- **paramspider** 🟡 — Python. `pip install` per https://github.com/devanshbatham/ParamSpider.
- **x8** 🟢 — Windows binary: https://github.com/Sh1Yo/x8/releases
- **jaeles** 🟢 — Windows binary: https://github.com/jaeles-project/jaeles/releases
- **wafw00f** 🟡 — Python. `pip install wafw00f`.
- **burpsuite** 🟢 — official Windows installer (Community Edition, free): https://portswigger.net/burp/communitydownload
- **zaproxy** (OWASP ZAP) 🟢 — official Windows installer: https://www.zaproxy.org/download/

## Vulnerability scanning

- **wpscan** 🟡 — Ruby gem. Install [RubyInstaller](https://rubyinstaller.org/), then `gem install wpscan`.
- **graphql-scanner**, **jwt-analyzer** — these don't correspond to one single well-known standalone project; treat as best-effort/unsupported on Windows.

## Password

- **medusa**, **patator** 🔴 — Linux-native, unreliable to build on Windows. WSL.
- **hash-identifier** 🟡 — small Python script, just needs Python. Clone and run directly.
- **ophcrack** 🟢 — official Windows installer: https://ophcrack.sourceforge.io/
- **hashcat-utils** 🟢 — Windows binaries in releases: https://github.com/hashcat/hashcat-utils/releases

## Binary / reverse engineering

- **gdb**, **objdump** 🟡 — install via [MSYS2](https://www.msys2.org/) (`pacman -S gdb binutils`), or use WSL.
- **radare2** 🟢 — official Windows build/installer: https://github.com/radareorg/radare2/releases
- **binwalk** 🟡 — Python. `pip install binwalk` (some features need WSL for full parity).
- **ropgadget** 🟡 — Python. `pip install ROPgadget`.
- **checksec** 🟡 — Python. `pip install checksec.py`.
- **ghidra** 🟢 — official cross-platform release (needs a Java 21+ JDK): https://ghidra-sre.org/
- **pwntools** 🔴 — genuinely cannot install on native Windows (needs POSIX `ptrace`/`pty`). WSL only — this is a hard OS limitation, not a missing package.
- **one-gadget** 🟡 — Ruby gem. `gem install one_gadget` (needs Ruby).
- **ropper** 🟡 — Python. `pip install ropper`.
- **angr** 🟡 — Python, mostly works on native Windows via `pip install angr` (unofficial/untested by the angr team, but its dependencies do ship Windows wheels).
- **libc-database** 🟡 — Python + git. Clone https://github.com/niklasb/libc-database.
- **pwninit** 🔴 — targets Linux ELF pwn binaries; not very useful on Windows targets anyway. WSL.

## Forensics

- **volatility3** / **vol** 🟡 — Python. `pip install volatility3`.
- **steghide** 🟡 — old Windows binary on https://steghide.sourceforge.net/ (unmaintained) or WSL.
- **hashpump** 🔴 — needs building from source, no Windows binary. WSL.
- **foremost**, **scalpel**, **outguess** 🔴 — Linux-native, no Windows build. WSL.
- **exiftool** 🟢 — official standalone Windows executable: https://exiftool.org/
- **strings** 🟢 — use Microsoft's own Sysinternals `strings.exe`: https://learn.microsoft.com/sysinternals/downloads/strings
- **xxd**, **file** 🟡 — install via [Git for Windows](https://gitforwindows.org/) (bundles a Unix toolset) or MSYS2.
- **photorec**, **testdisk** 🟢 — official cross-platform build: https://www.cgsecurity.org/wiki/TestDisk_Download
- **bulk-extractor** 🔴 — spotty old Windows builds, unreliable. WSL.
- **stegsolve** 🟢 — Java `.jar`, just needs a JRE installed: `java -jar StegSolve.jar`.
- **zsteg** 🟡 — Ruby gem. `gem install zsteg`.

## Cloud

- **prowler** 🟡 — Python. `pip install prowler-cloud`.
- **scout-suite** 🟡 — Python. `pip install scoutsuite`.
- **trivy** 🟢 — Windows binary: https://github.com/aquasecurity/trivy/releases
- **kube-hunter** 🟡 — Python. `pip install kube-hunter`.
- **kube-bench** 🟢 — Windows binary: https://github.com/aquasecurity/kube-bench/releases
- **checkov** 🟡 — Python. `pip install checkov`.
- **terrascan** 🟢 — Windows binary: https://github.com/tenable/terrascan/releases
- **docker-bench-security** 🔴 — bash script inspecting the Docker daemon; realistically Linux/WSL only.
- **falco** 🔴 — Linux-kernel/eBPF runtime tool. Not applicable to Windows at all.
- **clair** 🔴 — runs as a server, not really a standalone CLI; needs Docker.

## OSINT

- **amass** 🟢 — Windows binary: https://github.com/owasp-amass/amass/releases
- **fierce** 🟡 — Python. `pip install fierce`.
- **dnsenum** 🔴 — Perl + several modules, fragile on Windows. WSL.
- **theharvester** 🟡 — Python. `pip install theHarvester`.
- **sherlock** 🟡 — Python. `pip install sherlock-project`.
- **social-analyzer** 🟡 — Python. `pip install social-analyzer`.
- **recon-ng** 🟡 — Python. `pip install recon-ng`.
- **maltego** 🟢 — official Windows installer: https://www.maltego.com/downloads/
- **spiderfoot** 🟡 — Python, cross-platform. `pip install spiderfoot`.
- **shodan-cli** 🟡 — Python. `pip install shodan` (needs an API key).
- **censys-cli** 🟡 — Python. `pip install censys` (needs an API key).
- **have-i-been-pwned** — not a CLI tool, it's an API; no install, just needs an HIBP API key.

## Exploitation

- **metasploit** 🟢 — official Windows installer: https://github.com/rapid7/metasploit-framework/wiki/Downloads-by-Version (also bundles `msfconsole`/`msfvenom` below).
- **exploit-db** / **searchsploit** 🔴 — the CLI is a bash script; use the web version at https://www.exploit-db.com/ instead, or WSL.

## API

- **postman** 🟢 — official Windows app: https://www.postman.com/downloads/
- **insomnia** 🟢 — official Windows app: https://insomnia.rest/download
- **curl** 🟢 — already built into Windows 10/11, nothing to install.
- **httpie** 🟢/🟡 — has a Windows installer, or `pip install httpie`: https://httpie.io/docs/cli/installation
- **anew**, **qsreplace** 🟡 — Go tools, no prebuilt binaries. Install [Go](https://go.dev/dl/), then `go install github.com/tomnomnom/<tool>@latest`.
- **uro** 🟡 — Python. `pip install uro`.
- **api-schema-analyzer** — no single well-known standalone project; best-effort/unsupported.

## Wireless

- **wireshark** 🟢 — official Windows installer (also gives you `tshark`): https://www.wireshark.org/download.html
- **tcpdump** 🟡 — no real native equivalent; use Wireshark/`tshark` above instead of hunting for a Windows tcpdump port.
- **kismet** 🔴 — needs wireless-adapter monitor-mode support Windows doesn't expose. Not practical here at all, WSL included.

## Additional

- **smbmap** 🟡 — Python. `pip install smbmap`.
- **volatility** (v2, legacy) — superseded by `volatility3` above; use that instead.
- **sleuthkit** 🟢 — official Windows build: https://www.sleuthkit.org/sleuthkit/download.php
- **autopsy** 🟢 — official Windows installer (GUI, built on Sleuth Kit): https://www.autopsy.com/download/
- **evil-winrm** 🟡 — Ruby gem. `gem install evil-winrm`.
- **airmon-ng**, **airodump-ng**, **aireplay-ng**, **aircrack-ng** 🔴 — real wireless monitor-mode attacks aren't practical on Windows due to driver limitations. Needs a dedicated Linux box/WSL with a compatible USB adapter, not just a software install.
- **msfvenom**, **msfconsole** 🟢 — included with the Metasploit installer above.
