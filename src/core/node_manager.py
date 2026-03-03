#!/usr/bin/env python3
"""
Gestor del node Dogecoin Core: instal·lació, inici, aturada i comunicació RPC.
"""

import subprocess
import platform
import shutil
import zipfile
import tarfile
import time
import secrets
import logging
from pathlib import Path
from typing import Optional, Callable

import requests
from packaging import version
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from src.utils.downloader import download_file
from src.core.system_check import check_disk_space

logger = logging.getLogger("DogeSolo")

DOGECOIN_VERSION = "1.14.7"


class NodeManager:
    def __init__(self, config=None):
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._rpc: Optional[AuthServiceProxy] = None

        self.rpc_user = "dogesolo_user"
        self.rpc_password = "dogesolo_" + secrets.token_hex(16)
        self.rpc_port = 22555
        self.data_dir = Path.home() / ".dogecoin"
        self.bin_dir = Path.home() / ".dogesolo" / "bin"
        self.config_file = self.data_dir / "dogecoin.conf"

        self._load_config()
        self._load_rpc_config()

    def _load_config(self):
        if self.config:
            data_dir_str = self.config.get("data_dir", str(self.data_dir))
            self.data_dir = Path(data_dir_str).expanduser().resolve()
            self.rpc_user = self.config.get("rpc_user", self.rpc_user)
            self.rpc_password = self.config.get("rpc_password", self.rpc_password)
            self.rpc_port = self.config.get("rpc_port", self.rpc_port)
            self.config_file = self.data_dir / "dogecoin.conf"

    @property
    def rpc_connection(self) -> Optional[AuthServiceProxy]:
        if self._rpc is None:
            self._connect_rpc()
        return self._rpc

    def is_installed(self) -> bool:
        return self._daemon_path().exists()

    def is_running(self) -> bool:
        if self._process is not None:
            if self._process.poll() is None:
                return True
            self._process = None
        try:
            rpc = self._make_rpc()
            rpc.getblockcount()
            self._rpc = rpc
            return True
        except Exception:
            self._rpc = None
            return False

    def get_block_count(self) -> Optional[int]:
        try:
            return self.rpc_connection.getblockcount()
        except Exception:
            return None

    def get_blockchain_info(self) -> Optional[dict]:
        try:
            return self.rpc_connection.getblockchaininfo()
        except Exception:
            return None

    def get_network_info(self) -> Optional[dict]:
        try:
            return self.rpc_connection.getnetworkinfo()
        except Exception:
            return None

    def get_mining_info(self) -> Optional[dict]:
        try:
            return self.rpc_connection.getmininginfo()
        except Exception:
            return None

    def start_node(self) -> bool:
        if self.is_running():
            return True

        daemon = self._daemon_path()
        if not daemon.exists():
            logger.error("Binari dogecoind no trobat.")
            return False

        self._ensure_config()

        try:
            args = [
                str(daemon),
                f"-datadir={self.data_dir}",
                "-daemon=0",
                "-server=1",
                f"-rpcuser={self.rpc_user}",
                f"-rpcpassword={self.rpc_password}",
                f"-rpcport={self.rpc_port}",
                "-rpcallowip=127.0.0.1",
                "-listenonion=0",
                "-upnp=0",
            ]
            kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
            if platform.system() == "Windows":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            self._process = subprocess.Popen(args, **kwargs)

            for _ in range(60):
                time.sleep(1)
                if self.is_running():
                    logger.info("Node iniciat correctament.")
                    return True

            logger.error("El node no ha respost en 60 s.")
            return False
        except Exception as e:
            logger.error(f"Error iniciant node: {e}")
            return False

    def stop_node(self) -> bool:
        try:
            if self._rpc:
                self._rpc.stop()
                time.sleep(3)
        except Exception:
            pass

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        self._rpc = None
        return True

    def install_node(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        try:
            if not check_disk_space(self.data_dir, required_gb=50):
                msg = "⚠️  Espai insuficient al disc. Necessites almenys 50 GB lliures."
                if callback:
                    callback(msg)
                logger.error(msg)
                return False

            self.bin_dir.mkdir(parents=True, exist_ok=True)
            system = platform.system().lower()
            machine = platform.machine().lower()
            arch_tag = "aarch64" if ("arm" in machine or "aarch64" in machine) else "x86_64"
            v = DOGECOIN_VERSION
            base = f"https://github.com/dogecoin/dogecoin/releases/download/v{v}"

            if system == "windows":
                fname = f"dogecoin-{v}-win64.zip"
            elif system == "darwin":
                fname = f"dogecoin-{v}-osx64.tar.gz"
            else:
                fname = f"dogecoin-{v}-{arch_tag}-linux-gnu.tar.gz"

            url = f"{base}/{fname}"
            temp_file = self.bin_dir / fname

            if callback:
                callback(f"📥 Descarregant {fname}...")

            def progress_callback(downloaded, total):
                if total > 0 and callback:
                    pct = int(downloaded * 100 / total)
                    callback(f"📥 Descarregant... {pct}%")

            if not download_file(url, temp_file, callback=progress_callback):
                raise Exception("Error en la descàrrega")

            if callback:
                callback("📦 Extraient fitxers...")

            if fname.endswith(".zip"):
                with zipfile.ZipFile(temp_file, "r") as z:
                    z.extractall(self.bin_dir)
            elif fname.endswith(".tar.gz"):
                with tarfile.open(temp_file, "r:gz") as t:
                    t.extractall(self.bin_dir)

            temp_file.unlink(missing_ok=True)

            for item in list(self.bin_dir.iterdir()):
                if item.is_dir() and item.name.startswith("dogecoin-"):
                    bin_subdir = item / "bin"
                    src_dir = bin_subdir if bin_subdir.exists() else item
                    for f in src_dir.iterdir():
                        dest = self.bin_dir / f.name
                        if not dest.exists():
                            shutil.move(str(f), str(dest))
                    shutil.rmtree(item, ignore_errors=True)

            if system != "windows":
                for bn in ["dogecoind", "dogecoin-cli"]:
                    p = self.bin_dir / bn
                    if p.exists():
                        p.chmod(0o755)

            self._ensure_config()
            if callback:
                callback("✅ Node instal·lat correctament!")
            return True

        except Exception as e:
            msg = f"❌ Error instal·lant node: {e}"
            if callback:
                callback(msg)
            logger.exception("Error en instal·lació")
            return False

    def _daemon_path(self) -> Path:
        name = "dogecoind.exe" if platform.system() == "Windows" else "dogecoind"
        return self.bin_dir / name

    def _make_rpc(self) -> AuthServiceProxy:
        url = f"http://{self.rpc_user}:{self.rpc_password}@127.0.0.1:{self.rpc_port}"
        return AuthServiceProxy(url, timeout=10)

    def _connect_rpc(self):
        try:
            rpc = self._make_rpc()
            rpc.getblockcount()
            self._rpc = rpc
        except Exception:
            self._rpc = None

    def _ensure_config(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self._create_config()

    def _create_config(self):
        content = (
            f"server=1\ndaemon=0\n"
            f"rpcuser={self.rpc_user}\n"
            f"rpcpassword={self.rpc_password}\n"
            f"rpcport={self.rpc_port}\n"
            f"rpcallowip=127.0.0.1\nlisten=1\ntxindex=1\n"
        )
        self.config_file.write_text(content)

    def _load_rpc_config(self):
        if not self.config_file.exists():
            return
        for line in self.config_file.read_text(errors="ignore").splitlines():
            if "=" not in line:
                continue
            k, v = line.strip().split("=", 1)
            if k == "rpcuser":
                self.rpc_user = v
            elif k == "rpcpassword":
                self.rpc_password = v
            elif k == "rpcport":
                try:
                    self.rpc_port = int(v)
                except ValueError:
                    pass

    def check_for_update(self) -> Optional[str]:
        """Comprova si hi ha una versió més nova de Dogecoin Core.
        Retorna la versió nova si existeix, altrament None."""
        try:
            url = "https://api.github.com/repos/dogecoin/dogecoin/releases/latest"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if latest_tag:
                    current = version.parse(DOGECOIN_VERSION)
                    latest = version.parse(latest_tag)
                    if latest > current:
                        return latest_tag
        except Exception as e:
            logger.error(f"Error comprovant actualitzacions: {e}")
        return None