from config import STABLECOINS

def parse_swap(tx, wallet):
    try:
        meta = tx.get("meta", {})
        if meta.get("err"):
            return None

        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])

        pre_map = {}
        for b in pre_balances:
            if b.get("owner") == wallet:
                pre_map[b["mint"]] = float(b.get("uiTokenAmount", {}).get("uiAmount") or 0)

        post_map = {}
        for b in post_balances:
            if b.get("owner") == wallet:
                post_map[b["mint"]] = float(b.get("uiTokenAmount", {}).get("uiAmount") or 0)

        for mint in set(list(pre_map.keys()) + list(post_map.keys())):
            if mint in STABLECOINS:
                continue

            delta = post_map.get(mint, 0) - pre_map.get(mint, 0)

            if abs(delta) < 0.001:
                continue

            action = "BUY" if delta > 0 else "SELL"

            block_time = tx.get("blockTime", 0)
            sig = tx.get("transaction", {}).get("signatures", [""])[0] if isinstance(tx.get("transaction"), dict) else ""

            return {
                "wallet": wallet,
                "wallet_short": wallet[:6] + "..." + wallet[-4:],
                "token": mint,
                "token_short": mint[:6] + "..." + mint[-4:],
                "action": action,
                "amount": abs(delta),
                "block_time": block_time,
                "signature": sig,
            }

    except Exception as e:
        pass
    return None
