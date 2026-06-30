import argparse
import ipaddress
import locale
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import webbrowser


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = REPO_ROOT / "Runtime" / ".venv" / "Scripts" / "python.exe"
RUNTIME_PYTHON = REPO_ROOT / "Runtime" / "Python"
RUNTIME_VENV_SCRIPTS = REPO_ROOT / "Runtime" / ".venv" / "Scripts"
SITE_PACKAGES = REPO_ROOT / "Runtime" / ".venv" / "Lib" / "site-packages"
IPV4_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
VIRTUAL_ADAPTER_MARKERS = (
    "loopback",
    "vethernet",
    "virtual",
    "vmware",
    "virtualbox",
    "bluetooth",
    "tunnel",
    "tap",
    "wsl",
    "hyper-v",
    "meta",
)


def configure_package_environment() -> None:
    os.environ["PYTHONNOUSERSITE"] = "1"
    os.environ["PYTHONPATH"] = str(REPO_ROOT)
    os.environ["GENIE_DATA_DIR"] = str(REPO_ROOT / "GenieData")

    path_parts = [
        str(RUNTIME_VENV_SCRIPTS),
        str(RUNTIME_PYTHON),
        str(RUNTIME_PYTHON / "Scripts"),
        str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"),
        os.environ.get("SystemRoot", r"C:\Windows"),
    ]

    nvidia_root = SITE_PACKAGES / "nvidia"
    if nvidia_root.exists():
        for child in sorted(nvidia_root.iterdir()):
            bin_dir = child / "bin"
            if bin_dir.is_dir():
                path_parts.insert(0, str(bin_dir))

    os.environ["PATH"] = os.pathsep.join(path_parts)

    for candidate in (REPO_ROOT / "src", REPO_ROOT):
        candidate_text = str(candidate)
        if candidate_text not in sys.path:
            sys.path.insert(0, candidate_text)


def is_ipv4_lan_address(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return ip.version == 4 and any(ip in network for network in RFC1918_NETWORKS)


def adapter_looks_virtual(adapter_name: str) -> bool:
    lowered = adapter_name.lower()
    return any(marker in lowered for marker in VIRTUAL_ADAPTER_MARKERS)


def add_lan_address(addresses: list[str], value: str) -> None:
    if is_ipv4_lan_address(value) and value not in addresses:
        addresses.append(value)


def ipv4_candidates(text: str) -> list[str]:
    return IPV4_RE.findall(text)


def ipconfig_lan_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    try:
        completed = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return addresses

    blocks = completed.stdout.replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].rstrip().endswith(":"):
            continue
        adapter_name = lines[0].rstrip(":")
        if adapter_looks_virtual(adapter_name):
            continue

        gateway_lines: list[str] = []
        for index, line in enumerate(lines):
            if "Gateway" in line or "网关" in line:
                gateway_lines.append(line)
                if index + 1 < len(lines) and lines[index + 1].startswith(" "):
                    gateway_lines.append(lines[index + 1])
        has_lan_gateway = any(
            is_ipv4_lan_address(part)
            for line in gateway_lines
            for part in ipv4_candidates(line)
        )
        if not has_lan_gateway:
            continue

        for line in lines:
            if "IPv4" not in line:
                continue
            for part in ipv4_candidates(line):
                add_lan_address(addresses, part)
    return addresses


def socket_lan_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM):
            add_lan_address(addresses, item[4][0])
    except OSError:
        pass
    return addresses


def get_lan_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    for address in ipconfig_lan_ipv4_addresses() or socket_lan_ipv4_addresses():
        add_lan_address(addresses, address)

    return addresses


def port_is_available(host: str, port: int) -> bool:
    bind_host = "" if host in {"0.0.0.0", "::"} else host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((bind_host, port))
        return True
    except OSError:
        return False


def find_free_port(host: str) -> int:
    bind_host = "" if host in {"0.0.0.0", "::"} else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((bind_host, 0))
        return int(sock.getsockname()[1])


def resolve_port(host: str, requested_port: int, strict_port: bool) -> tuple[int, bool]:
    if requested_port <= 0:
        return find_free_port(host), True
    if port_is_available(host, requested_port):
        return requested_port, False
    if strict_port:
        raise SystemExit(f"Port {requested_port} is already in use on host {host}.")
    return find_free_port(host), True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the Genie-TTS API and local WebUI.")
    parser.add_argument("--host", default=os.environ.get("GENIE_WEBUI_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("GENIE_WEBUI_PORT", "8000")))
    parser.add_argument(
        "--runtime",
        default=os.environ.get("GENIE_WEBUI_RUNTIME", "cuda"),
        choices=("cpu", "cuda", "directml", "auto"),
    )
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    parser.add_argument("--strict-port", action="store_true", help="Fail instead of selecting a free port.")
    return parser.parse_args()


def main() -> None:
    if not PYTHON_EXE.exists():
        raise SystemExit(f"Internal Python was not found: {PYTHON_EXE}")

    configure_package_environment()
    args = parse_args()
    port, changed_port = resolve_port(args.host, args.port, args.strict_port)
    os.environ["GENIE_WEBUI_HOST"] = args.host
    os.environ["GENIE_WEBUI_PORT"] = str(port)
    os.environ["GENIE_WEBUI_RUNTIME"] = args.runtime
    local_url = f"http://127.0.0.1:{port}/ui"
    lan_addresses = get_lan_ipv4_addresses()
    lan_urls = [f"http://{address}:{port}/ui" for address in lan_addresses]

    import genie_tts as genie

    runtime = genie.configure_runtime(args.runtime)

    print("Genie-TTS WebUI launcher", flush=True)
    print(f"Package root: {REPO_ROOT}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    print(f"Runtime request: {args.runtime}", flush=True)
    print(f"Runtime effective providers: {runtime['providers']}", flush=True)
    if changed_port and args.port > 0:
        print(f"Port {args.port} was unavailable; using free port {port}.", flush=True)
    print(f"Backend listen: http://{args.host}:{port}", flush=True)
    print(f"Local WebUI: {local_url}", flush=True)
    if lan_urls:
        print("LAN IPv4 addresses: " + ", ".join(lan_addresses), flush=True)
        for url in lan_urls:
            print(f"LAN WebUI: {url}", flush=True)
    else:
        print("LAN IPv4 addresses: none detected", flush=True)
    print("Press Ctrl+C to stop the server.", flush=True)

    if not args.no_open:
        threading.Timer(1.0, lambda: webbrowser.open(local_url)).start()

    genie.start_server(host=args.host, port=port, workers=1)


if __name__ == "__main__":
    main()
