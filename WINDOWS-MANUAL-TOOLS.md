# Tools not included in the HexStrike WSL2 image

As of the WSL2 rewrite, HexStrike on Windows runs inside a real Kali
userland (`wsl/Dockerfile`) with most of its CLI tool ecosystem already
installed via `apt` — nmap, sqlmap, hydra, john, gobuster, ffuf, nuclei,
metasploit, radare2, volatility3, and the rest of `essential`/`network`/
`web_security`/`password`/`binary`/`forensics`/`osint`/`additional` in
`/health`'s tool list all come preinstalled. `pwntools` and `angr` — the two
that flatly cannot run on native Windows at all — work fine here too, since
this is genuinely Linux underneath.

What's *not* included, and why: a handful of tools are GUI desktop
applications (Burp Suite, OWASP ZAP, Ghidra, Postman, Insomnia, Maltego,
Autopsy, Wireshark) — running a GUI app inside a headless WSL2 distro adds
real complexity (WSLg, X server, ...) for something that already has a
perfectly good native Windows installer. Install these directly on Windows
instead, outside the WSL2 image:

- **Burp Suite** (Community, free): https://portswigger.net/burp/communitydownload
- **OWASP ZAP**: https://www.zaproxy.org/download/
- **Ghidra** (needs a Java 21+ JDK): https://ghidra-sre.org/
- **Postman**: https://www.postman.com/downloads/
- **Insomnia**: https://insomnia.rest/download
- **Maltego**: https://www.maltego.com/downloads/
- **Autopsy**: https://www.autopsy.com/download/
- **Wireshark** (also gives you `tshark`): https://www.wireshark.org/download.html
- **Metasploit** does ship inside the WSL2 image via `apt`, but if you'd
  rather have the Windows-native GUI/installer version too:
  https://github.com/rapid7/metasploit-framework/wiki/Downloads-by-Version

A few tools genuinely don't work anywhere on Windows-hosted virtualization,
WSL2 included — real wireless monitor-mode attacks (`airmon-ng`,
`aireplay-ng`, `kismet`, ...) need direct hardware access to a wireless
adapter that WSL2's virtualized networking doesn't expose. Those need a
dedicated Linux box or a real (not WSL2) VM with USB passthrough.

If something you expect is still missing from the image itself, it's most
likely because it's not in the Kali meta-packages `wsl/Dockerfile` installs
(`kali-tools-top10`, `-information-gathering`, `-vulnerability`, `-web`,
`-passwords`, `-exploitation`, `-forensics`, `-reverse-engineering`,
`-sniffing-spoofing`) — `apt install <tool>` inside the running distro
(`wsl -d HexStrikeAI`) gets you anything else Kali packages, same as on a
real Kali box.
