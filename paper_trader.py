import json
import logging
import requests
import time
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

state = {
    'capital': config.INITIAL_CAPITAL,
    'positions': {},
    'history': []
}

def load_state():
    try:
        with open('paper_state.json', 'r') as f:
            loaded = json.load(f)
            state.update(loaded)
            # ✅ Reset capital a 1000 sin borrar historial ni posiciones
            state['capital'] = config.INITIAL_CAPITAL
            logger.info(f"Estado cargado: capital reseteado a ${state['capital']:.2f} | {len(state['positions'])} posiciones | {len(state['history'])} trades en historial")
            save_state()
    except FileNotFoundError:
        logger.info("Iniciando desde cero")
        save_state()

def save_state():
    with open('paper_state.json', 'w') as f:
        json.dump(state, f, indent=2)

def get_token_price(token_address):
    try:
        url = "https://public-api.birdeye.so/defi/price"
        headers = {"X-API-KEY": config.BIRDEYE_API_KEY}
        params = {"address": token_address}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('value')
    except Exception as e:
        logger.error(f"Error precio: {e}")
    return None

def copy_trade(wallet, token, action, amount):
    """Copia trade con sistema híbrido de 5%"""
    if action == 'buy':
        if token in state['positions']:
            return

        price = get_token_price(token)
        if not price:
            return

        position_size = config.calculate_position_size(state['capital'])

        if state['capital'] < position_size:
            logger.info(f"❌ Capital insuficiente: ${state['capital']:.2f}")
            return

        state['positions'][token] = {
            'wallet': wallet,
            'entry_price': price,
            'entry_time': time.time(),
            'amount': position_size
        }
        state['capital'] -= position_size

        logger.info(f"🟢 BUY {token[:8]} | {wallet[:8]} | ${position_size} @ ${price:.8f}")
        logger.info(f"💰 Capital: ${state['capital']:.2f} | Posiciones: {len(state['positions'])}")
        save_state()

    elif action == 'sell':
        if token not in state['positions']:
            return
        close_position(token, "WALLET_SELL")

def close_position(token, reason):
    if token not in state['positions']:
        return

    position = state['positions'][token]
    current_price = get_token_price(token)
    if not current_price:
        return

    entry_price = position['entry_price']
    amount = position['amount']
    pnl = amount * ((current_price - entry_price) / entry_price)
    pnl_percent = ((current_price - entry_price) / entry_price) * 100

    state['capital'] += amount + pnl

    trade_record = {
        'token': token,
        'wallet': position['wallet'],
        'entry_price': entry_price,
        'exit_price': current_price,
        'entry_time': position['entry_time'],
        'exit_time': time.time(),
        'hold_time': time.time() - position['entry_time'],
        'amount': amount,
        'pnl': pnl,
        'pnl_percent': pnl_percent,
        'reason': reason
    }
    state['history'].append(trade_record)
    del state['positions'][token]

    emoji = "🟢" if pnl > 0 else "🔴"
    logger.info(f"{emoji} CLOSE {token[:8]} | {reason} | PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)")
    logger.info(f"💰 Capital: ${state['capital']:.2f}")
    save_state()

def check_stop_loss():
    """Sin stop loss ni time limits - solo observación"""
    pass

def get_summary():
    total_pnl = sum(t['pnl'] for t in state['history'])
    wins = len([t for t in state['history'] if t['pnl'] > 0])
    losses = len([t for t in state['history'] if t['pnl'] <= 0])
    win_rate = (wins / len(state['history']) * 100) if state['history'] else 0

    return {
        "capital": round(state['capital'], 2),
        "initial_capital": config.INITIAL_CAPITAL,
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percent": round((total_pnl / config.INITIAL_CAPITAL) * 100, 2),
        "open_positions": len(state['positions']),
        "total_trades": len(state['history']),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "history": state['history'][-50:]
    }

def get_portfolio():
    result = []
    for token, position in state['positions'].items():
        current_price = get_token_price(token)
        pnl = 0
        pnl_percent = 0
        if current_price:
            pnl = position['amount'] * ((current_price - position['entry_price']) / position['entry_price'])
            pnl_percent = ((current_price - position['entry_price']) / position['entry_price']) * 100

        result.append({
            "token": token,
            "token_short": token[:8],
            "wallet": position['wallet'],
            "wallet_short": position['wallet'][:8],
            "entry_price": position['entry_price'],
            "current_price": current_price,
            "amount": position['amount'],
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "hold_time_hours": round((time.time() - position['entry_time']) / 3600, 1),
            "entry_time": position['entry_time']
        })
    return result

def print_summary():
    summary = get_summary()
    logger.info("=" * 60)
    logger.info(f"💰 CAPITAL: ${summary['capital']:.2f}")
    logger.info(f"📊 PnL: ${summary['total_pnl']:.2f} ({summary['total_pnl_percent']:+.2f}%)")
    logger.info(f"📈 {summary['total_trades']} trades | {summary['wins']}W / {summary['losses']}L ({summary['win_rate']:.1f}% WR)")
    logger.info(f"📦 Posiciones abiertas: {summary['open_positions']}")
    logger.info("=" * 60)

__all__ = ['copy_trade', 'check_stop_loss', 'load_state', 'save_state',
           'get_summary', 'get_portfolio', 'print_summary', 'state']
