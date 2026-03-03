#!/usr/bin/env python3
"""
Gestor de cartera Dogecoin: consulta de saldo, enviament i historial.
Tota la comunicació és via RPC amb el node local.
"""

import logging
from typing import Optional, List, Dict, Any
from bitcoinrpc.authproxy import JSONRPCException

logger = logging.getLogger("DogeSolo")


class WalletManager:
    def __init__(self, node_manager):
        self.node_manager = node_manager
        self._label = "mining_reward"  # Etiqueta per a l'adreça de mineria

    # ── Propietats ────────────────────────────────────────────────────
    @property
    def _rpc(self):
        return self.node_manager.rpc_connection

    # ── Saldo ─────────────────────────────────────────────────────────
    def get_balance(self) -> Optional[float]:
        """Saldo confirmat de la cartera."""
        try:
            return float(self._rpc.getbalance())
        except Exception as e:
            logger.debug(f"get_balance error: {e}")
            return None

    def get_unconfirmed_balance(self) -> Optional[float]:
        """Saldo pendent de confirmar."""
        try:
            info = self._rpc.getwalletinfo()
            return float(info.get("unconfirmed_balance", 0))
        except Exception:
            return None

    # ── Adreces ───────────────────────────────────────────────────────
    def get_receiving_address(self) -> Optional[str]:
        """
        Retorna l'adreça receptora principal (etiquetada com 'mining_reward').
        Si no existeix, en crea una de nova.
        """
        try:
            # Intenta obtenir les adreces amb l'etiqueta
            addresses = self._rpc.getaddressesbylabel(self._label)
            if addresses:
                # Retorna la primera clau (l'adreça)
                return next(iter(addresses.keys()))
            # Si no n'hi ha, crea'n una de nova amb l'etiqueta
            return self._rpc.getnewaddress(self._label)
        except JSONRPCException as e:
            logger.error(f"Error RPC obtenint adreça: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperat obtenint adreça: {e}")
            return None

    def validate_address(self, address: str) -> bool:
        """Comprova si una adreça Dogecoin és vàlida."""
        if not address or not address.startswith("D") or len(address) < 26:
            return False
        try:
            result = self._rpc.validateaddress(address)
            return bool(result.get("isvalid", False))
        except Exception:
            # Si el node no és accessible, fem validació bàsica
            return len(address) in range(26, 35) and address[0] == 'D'

    # ── Transaccions ──────────────────────────────────────────────────
    def send_doge(
        self,
        destination: str,
        amount: float,
        comment: str = "",
        subtract_fee: bool = False,
    ) -> Optional[str]:
        """
        Envia DOGE a una adreça.

        :param destination: Adreça Dogecoin destí.
        :param amount: Quantitat en DOGE.
        :param comment: Comentari opcional.
        :param subtract_fee: Si True, la comissió es desconta del total enviat.
        :return: txid si èxit, None si error.
        :raises ValueError: Si l'adreça és invàlida o el saldo és insuficient.
        :raises RuntimeError: Si el node no és accessible.
        """
        if not self.validate_address(destination):
            raise ValueError(f"Adreça invàlida: {destination}")

        balance = self.get_balance()
        if balance is None:
            raise RuntimeError("El node no és accessible. Comprova que està en marxa.")

        if amount <= 0:
            raise ValueError("La quantitat ha de ser major que 0.")

        # Comissió estimada ~1 DOGE per ser segur a la xarxa Dogecoin
        fee_margin = 1.0
        if not subtract_fee and (amount + fee_margin) > balance:
            raise ValueError(
                f"Saldo insuficient. Disponible: {balance:.2f} DOGE, "
                f"necessari: {amount + fee_margin:.2f} DOGE (inclou ~{fee_margin} DOGE comissió)"
            )

        try:
            if subtract_fee:
                # sendtoaddress amb subtractfeefromamount
                txid = self._rpc.sendtoaddress(
                    destination, round(amount, 8), comment, "", True
                )
            else:
                txid = self._rpc.sendtoaddress(
                    destination, round(amount, 8), comment
                )
            logger.info(f"Enviament: {amount} DOGE → {destination} | txid: {txid}")
            return txid

        except JSONRPCException as e:
            error_msg = str(e)
            if "insufficient funds" in error_msg.lower():
                raise ValueError("Saldo insuficient per completar la transacció.")
            elif "invalid address" in error_msg.lower():
                raise ValueError(f"Adreça invàlida: {destination}")
            elif "wallet locked" in error_msg.lower():
                raise RuntimeError(
                    "La cartera està xifrada. Desbloqueja-la primer a la pestanya Cartera."
                )
            else:
                raise RuntimeError(f"Error RPC: {error_msg}")

    def estimate_fee(self, blocks: int = 6) -> float:
        """Estima la comissió recomanada (DOGE/KB) per confirmar en N blocs."""
        try:
            result = self._rpc.estimatefee(blocks)
            if result and result > 0:
                return float(result)
        except Exception:
            pass
        return 1.0  # Comissió mínima segura per defecte

    def list_transactions(self, count: int = 50) -> List[Dict[str, Any]]:
        """Llista les últimes N transaccions de la cartera."""
        try:
            return self._rpc.listtransactions("*", count, 0, True)
        except Exception:
            return []

    def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        """Detalls d'una transacció per txid."""
        try:
            return self._rpc.gettransaction(txid)
        except Exception:
            return None

    # ── Seguretat cartera ─────────────────────────────────────────────
    def is_wallet_locked(self) -> bool:
        """Comprova si la cartera està xifrada i bloquejada."""
        try:
            info = self._rpc.getwalletinfo()
            return "unlocked_until" in info and info["unlocked_until"] == 0
        except Exception:
            return False

    def unlock_wallet(self, passphrase: str, seconds: int = 300) -> bool:
        """Desbloqueja la cartera durant N segons per a enviaments."""
        try:
            self._rpc.walletpassphrase(passphrase, seconds)
            return True
        except JSONRPCException:
            return False

    def lock_wallet(self):
        """Bloqueja la cartera immediatament."""
        try:
            self._rpc.walletlock()
        except Exception:
            pass

    def backup_wallet(self, destination_path: str) -> bool:
        """Fa una còpia de seguretat del wallet.dat."""
        try:
            self._rpc.backupwallet(destination_path)
            logger.info(f"Backup cartera → {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error backup: {e}")
            return False