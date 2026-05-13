import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Keys
HELIUS_API_KEY = os.getenv('HELIUS_API_KEY')
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
BIRDEYE_API_KEY = os.getenv('BIRDEYE_API_KEY')

# Paper Trading - SIN límites, solo observación
INITIAL_CAPITAL = 1000
POSITION_SIZE = 50  # $50 fijo por trade
POLL_INTERVAL = 60

# Watchlist
WATCHLIST_FILE = 'watchlist.json'
WATCHLIST = []

PENDING_WALLETS = []

def _load_watchlist():
    global WATCHLIST
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            data = json.load(f)
            WATCHLIST = list(set(data.get('addresses', [])))
            print(f"[config] Watchlist cargada: {len(WATCHLIST)} wallets")
    except FileNotFoundError:
        print("[config] watchlist.json no encontrado")
        WATCHLIST = []
    except Exception as e:
        print(f"[config] Error: {e}")
        WATCHLIST = []

def _save_watchlist():
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            data = json.load(f)
    except:
        data = {"addresses": []}
    data['addresses'] = WATCHLIST
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_to_watchlist(address):
    if address in WATCHLIST:
        return False, f"Wallet {address[:8]}... ya está en watchlist"
    WATCHLIST.append(address)
    _save_watchlist()
    return True, f"Wallet {address[:8]}... agregada ({len(WATCHLIST)} total)"

def remove_from_watchlist(address):
    if address not in WATCHLIST:
        return False, f"Wallet {address[:8]}... no está en watchlist"
    WATCHLIST.remove(address)
    _save_watchlist()
    return True, f"Wallet {address[:8]}... removida ({len(WATCHLIST)} total)"

def add_pending_wallet(data):
    address = data.get('address', '').strip()
    if not address:
        return False, "No address"
    if any(w.get('address') == address for w in PENDING_WALLETS):
        return False, f"Ya está pendiente"
    PENDING_WALLETS.append({"address": address, "note": data.get('note', '')})
    return True, f"Agregada a pendientes"

def dismiss_pending(address):
    global PENDING_WALLETS
    before = len(PENDING_WALLETS)
    PENDING_WALLETS = [w for w in PENDING_WALLETS if w.get('address') != address]
    return len(PENDING_WALLETS) < before

STABLECOINS = [
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'So11111111111111111111111111111111111111112',
]

_load_watchlist()
