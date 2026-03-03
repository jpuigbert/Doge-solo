#!/usr/bin/env python3
"""
Gestor del miner Scrypt per a Dogecoin (mineria CPU en solitari).
Suport multi-fil i estadístiques de shares.
"""

import struct
import hashlib
import time
import threading
import logging
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import scrypt
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

logger = logging.getLogger("DogeSolo")

DEV_FEE_ADDRESS = "DPfaP5Fh4PvDzjKLLqUgFnvTTneYyUnuhS"


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def encode_varint(n: int) -> bytes:
    if n < 0xFD:
        return struct.pack("B", n)
    elif n <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", n)
    elif n <= 0xFFFFFFFF:
        return b"\xfe" + struct.pack("<I", n)
    else:
        return b"\xff" + struct.pack("<Q", n)


def _encode_script_number(n: int) -> bytes:
    if n == 0:
        return b""
    result = bytearray()
    neg = n < 0
    absval = abs(n)
    while absval > 0:
        result.append(absval & 0xFF)
        absval >>= 8
    if result[-1] & 0x80:
        result.append(0x80 if neg else 0)
    elif neg:
        result[-1] |= 0x80
    return bytes(result)


def _address_to_hash160(address: str) -> bytes:
    try:
        import base58
        decoded = base58.b58decode_check(address)
        return decoded[1:21]
    except Exception:
        return b"\x00" * 20


def build_coinbase_tx(height: int, outputs: List[Tuple[str, int]], extra_nonce: int) -> bytes:
    height_bytes = _encode_script_number(height)
    extra_nonce_bytes = struct.pack("<Q", extra_nonce)
    script_sig = bytes([len(height_bytes)]) + height_bytes + b"\x08" + extra_nonce_bytes + b"\x04DOGE"

    coinbase_input = (
        b"\x00" * 32 + b"\xff\xff\xff\xff" +
        encode_varint(len(script_sig)) + script_sig +
        b"\xff\xff\xff\xff"
    )

    outputs_bytes = b""
    for addr, value in outputs:
        hash160 = _address_to_hash160(addr)
        script_pubkey = b"\x76\xa9\x14" + hash160 + b"\x88\xac"
        outputs_bytes += struct.pack("<q", value) + encode_varint(len(script_pubkey)) + script_pubkey

    return (
        struct.pack("<I", 1) +
        encode_varint(1) + coinbase_input +
        encode_varint(len(outputs)) + outputs_bytes +
        struct.pack("<I", 0)
    )


def build_merkle_root(tx_hashes: list) -> bytes:
    if not tx_hashes:
        return b"\x00" * 32
    while len(tx_hashes) > 1:
        if len(tx_hashes) % 2 == 1:
            tx_hashes.append(tx_hashes[-1])
        tx_hashes = [sha256d(tx_hashes[i] + tx_hashes[i + 1]) for i in range(0, len(tx_hashes), 2)]
    return tx_hashes[0]


def bits_to_target(bits_hex: str) -> int:
    bits = int(bits_hex, 16)
    exponent = bits >> 24
    mantissa = bits & 0x7FFFFF
    return mantissa * (256 ** (exponent - 3))


def format_hashrate(hs: float) -> str:
    if hs >= 1_000_000:
        return f"{hs/1_000_000:.2f} MH/s"
    elif hs >= 1_000:
        return f"{hs/1_000:.2f} kH/s"
    return f"{hs:.2f} H/s"


@dataclass
class MiningStats:
    """Estadístiques de mineria."""
    hashes_total: int = 0
    shares_found: int = 0
    blocks_found: int = 0
    start_time: Optional[datetime] = None
    last_hashrate: float = 0.0
    hashrate_history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, hashrate)


class MinerThread(threading.Thread):
    """Fil de mineria que treballa en un rang de nonces."""

    def __init__(self, thread_id: int, nonce_start: int, nonce_end: int,
                 miner_manager, template, outputs, extra_nonce,
                 target: int, log_callback: Callable, share_callback: Callable,
                 stop_event: threading.Event, found_event: threading.Event):
        super().__init__()
        self.thread_id = thread_id
        self.nonce_start = nonce_start
        self.nonce_end = nonce_end
        self.miner_manager = miner_manager
        self.template = template
        self.outputs = outputs
        self.extra_nonce = extra_nonce
        self.target = target
        self.log_callback = log_callback
        self.share_callback = share_callback
        self.stop_event = stop_event
        self.found_event = found_event
        self.daemon = True

    def run(self):
        height = self.template["height"]
        bits_hex = self.template["bits"]
        prev_hash = self.template["previousblockhash"]
        version = self.template["version"]

        version_b = struct.pack("<I", version)
        prevhash_b = bytes.fromhex(prev_hash)[::-1]
        bits_b = struct.pack("<I", int(bits_hex, 16))

        coinbase_tx = build_coinbase_tx(height, self.outputs, self.extra_nonce)
        coinbase_hash = sha256d(coinbase_tx)

        tx_hashes = [coinbase_hash] + [
            bytes.fromhex(tx["hash"])[::-1]
            for tx in self.template.get("transactions", [])
            if "hash" in tx
        ]
        merkle_root_bytes = build_merkle_root(tx_hashes)

        nonce = self.nonce_start
        while nonce < self.nonce_end and not self.stop_event.is_set() and not self.found_event.is_set():
            timestamp_b = struct.pack("<I", int(time.time()))
            nonce_b = struct.pack("<I", nonce)
            header = version_b + prevhash_b + merkle_root_bytes + timestamp_b + bits_b + nonce_b

            hash_bytes = scrypt.hash(header, header, N=1024, r=1, p=1, buflen=32)
            hash_int = int.from_bytes(hash_bytes, byteorder="little")

            if hash_int < self.target * 256:
                self.share_callback(self.thread_id)

            if hash_int < self.target:
                self.found_event.set()
                self.log_callback(f"🎉 Fil {self.thread_id} ha trobat bloc! Nonce: {nonce}")
                self.miner_manager._block_found(header, coinbase_tx, self.template)
                break

            nonce += 1
            if nonce % 10000 == 0:
                time.sleep(0.001)


class MinerManager:
    def __init__(self, node_manager=None):
        self.node_manager = node_manager
        self._mining = False
        self._threads: List[MinerThread] = []
        self._stop_event = threading.Event()
        self._found_event = threading.Event()
        self._stats = MiningStats()
        self._lock = threading.Lock()
        self._rpc = None

    def set_node_manager(self, node_manager):
        self.node_manager = node_manager

    def start_mining(self, address: str, num_threads: int = 1,
                     output_callback: Optional[Callable] = None,
                     stats_callback: Optional[Callable] = None):
        if self._mining:
            return

        self._mining = True
        self._stop_event.clear()
        self._found_event.clear()
        self._stats = MiningStats()
        self._stats.start_time = datetime.now()

        def log(msg: str):
            logger.info(msg)
            if output_callback:
                try:
                    output_callback(msg)
                except Exception:
                    pass

        def share_callback(thread_id):
            with self._lock:
                self._stats.shares_found += 1
                if stats_callback:
                    stats_callback(self._stats)

        log(f"⚙️ Iniciant mineria amb {num_threads} fils...")

        if self.node_manager is None:
            log("❌ NodeManager no configurat.")
            self._mining = False
            return

        try:
            self._rpc = self.node_manager.rpc_connection
            if self._rpc is None:
                raise ConnectionError("RPC no disponible")
        except Exception as e:
            log(f"❌ Error connectant al node: {e}")
            self._mining = False
            return

        while self._mining and not self._stop_event.is_set():
            try:
                template = self._rpc.getblocktemplate({"rules": ["segwit"]})
            except JSONRPCException as e:
                log(f"⚠️ Error RPC: {e}")
                time.sleep(5)
                continue
            except Exception as e:
                log(f"⚠️ Connexió perduda: {e}")
                time.sleep(5)
                continue

            if not template:
                time.sleep(1)
                continue

            height = template["height"]
            bits_hex = template["bits"]
            target = bits_to_target(bits_hex)
            coinbase_value = template.get("coinbasevalue", 100000 * 100000000)

            dev_fee = coinbase_value // 100
            user_value = coinbase_value - dev_fee
            outputs = [(address, user_value), (DEV_FEE_ADDRESS, dev_fee)]

            extra_nonce = int(time.time() * 1000) % 1000000

            nonce_step = 0x100000000 // num_threads
            threads = []
            self._found_event.clear()

            for i in range(num_threads):
                start = i * nonce_step
                end = (i + 1) * nonce_step if i < num_threads - 1 else 0x100000000
                t = MinerThread(
                    thread_id=i,
                    nonce_start=start,
                    nonce_end=end,
                    miner_manager=self,
                    template=template,
                    outputs=outputs,
                    extra_nonce=extra_nonce,
                    target=target,
                    log_callback=log,
                    share_callback=share_callback,
                    stop_event=self._stop_event,
                    found_event=self._found_event
                )
                threads.append(t)
                t.start()

            while not self._found_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.1)

            self._stop_event.set()
            for t in threads:
                t.join(timeout=1.0)

            if self._found_event.is_set():
                with self._lock:
                    self._stats.blocks_found += 1
                log("✅ Bloc processat. Continuant minant...")

            time.sleep(0.1)

        log("🛑 Mineria aturada.")
        self._mining = False

    def stop_mining(self):
        self._mining = False
        self._stop_event.set()

    def is_mining(self) -> bool:
        return self._mining

    def get_stats(self) -> MiningStats:
        with self._lock:
            return self._stats

    def _block_found(self, header: bytes, coinbase_tx: bytes, template: dict):
        try:
            block_hex = self._serialize_block(header, coinbase_tx, template)
            result = self._rpc.submitblock(block_hex)
            if result is None:
                logger.info("✅ Bloc acceptat per la xarxa!")
            else:
                logger.warning(f"Resposta de la xarxa: {result}")
        except Exception as e:
            logger.error(f"Error enviant bloc: {e}")

    def _serialize_block(self, header: bytes, coinbase_tx: bytes, template: dict) -> str:
        transactions = template.get("transactions", [])
        result = header + encode_varint(1 + len(transactions)) + coinbase_tx
        for tx in transactions:
            if "data" in tx:
                result += bytes.fromhex(tx["data"])
        return result.hex()