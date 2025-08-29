from app.tasks import celery  # Import from parent module
from app.core.database import SessionLocal
from app.services.auth_service import get_user_by_email
from app.core.config import settings
from cryptography.fernet import Fernet
from ccxt import binance
from app.models.auto_trading import AutoTradingSettings
from app.models.user import User
from app.api.trading import store_trade_record, get_market_signals
from app.models.user import User

@celery.task
def validate_user_binance_keys(user_email: str):
    db = SessionLocal()
    try:
        user = get_user_by_email(db, user_email)
        if not user or not user.binance_api_key or not user.binance_api_secret:
            return {"status": "failed", "message": "No credentials"}
        
        cipher = Fernet(settings.FERNET_KEY.encode())
        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        exchange.load_markets()
        return {"status": "success", "message": "Keys valid"}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    finally:
        db.close()


@celery.task
def run_auto_trading_for_all_users():
    db = SessionLocal()
    try:
        settings_rows = db.query(AutoTradingSettings).filter(AutoTradingSettings.enabled == True).all()
        results = []
        print(f"AUTO: Starting auto-trading run for {len(settings_rows)} users with enabled settings")
        for row in settings_rows:
            user = db.query(User).filter(User.id == row.user_id).first()
            if not user:
                print(f"AUTO: Skipping settings id={row.id} - user not found")
                results.append({"user_id": row.user_id, "email": None, "decisions": [], "note": "user_not_found"})
                continue

            # decrypt keys
            try:
                cipher = Fernet(settings.FERNET_KEY.encode())
                api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
                api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()
            except Exception as e:
                print(f"AUTO: Skipping {user.email} - failed to decrypt API keys: {e}")
                results.append({"user_id": user.id, "email": user.email, "decisions": [], "note": "decrypt_failed"})
                continue

            exchange = binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })

            pairs = [p.strip() for p in (row.allowed_pairs.split(',') if row.allowed_pairs else []) if p.strip()]
            if not pairs:
                print(f"AUTO: {user.email} - no allowed pairs configured")
                results.append({"user_id": user.id, "email": user.email, "decisions": [], "note": "no_pairs"})
                continue

            user_result = {"user_id": user.id, "email": user.email, "decisions": []}
            for symbol in pairs:
                decision = {"symbol": symbol}
                try:
                    # fetch market signal (public)
                    signal_data = get_market_signals(symbol, user.email)
                    signal = signal_data.get('signal', 'NEUTRAL')
                    strength = signal_data.get('strength', 50)
                    decision.update({"signal": signal, "strength": strength})

                    # threshold check
                    min_strength = getattr(row, 'min_signal_strength', 60) or 60
                    if signal == 'NEUTRAL' or strength < min_strength:
                        reason = f"skip_threshold signal={signal} strength={strength}"
                        print(f"AUTO: {user.email} {symbol} - {reason}")
                        decision.update({"action": "skipped", "reason": reason})
                        user_result["decisions"].append(decision)
                        continue

                    ticker = exchange.fetch_ticker(symbol)
                    price = ticker['last']
                    base_usd = max(5.0, (getattr(row, 'max_trade_size', 25.0) or 25.0) * ((getattr(row, 'risk_level', 3) or 3) / 5.0))
                    qty = base_usd / price

                    side = 'buy' if signal in ['STRONG_BUY', 'BUY'] else 'sell'

                    # balance check
                    try:
                        balance = exchange.fetch_balance()
                        if side == 'buy':
                            usdt_balance = balance.get('USDT', {}).get('free', 0)
                            if usdt_balance < base_usd:
                                reason = f"skip_balance need_USDT>={base_usd:.2f} have={usdt_balance:.2f}"
                                print(f"AUTO: {user.email} {symbol} - {reason}")
                                decision.update({"action": "skipped", "reason": reason})
                                user_result["decisions"].append(decision)
                                continue
                        else:
                            base_asset = symbol.split('/')[0]
                            asset_balance = balance.get(base_asset, {}).get('free', 0)
                            asset_value = asset_balance * price
                            if asset_value < base_usd:
                                reason = f"skip_balance need_{base_asset}_value>={base_usd:.2f} have={asset_value:.2f}"
                                print(f"AUTO: {user.email} {symbol} - {reason}")
                                decision.update({"action": "skipped", "reason": reason})
                                user_result["decisions"].append(decision)
                                continue
                    except Exception as bal_e:
                        print(f"AUTO: {user.email} {symbol} - balance check failed: {bal_e}. Proceeding without check")

                    order = exchange.create_market_order(symbol, side, qty)

                    store_trade_record(user.email, {
                        'symbol': symbol,
                        'side': side,
                        'quantity': qty,
                        'price': price,
                        'usd_amount': base_usd,
                        'order_id': order['id'],
                        'source': 'celery',
                    }, db)

                    decision.update({
                        "action": "executed",
                        "side": side,
                        "qty": qty,
                        "price": price,
                        "usd": base_usd,
                        "order_id": order.get('id')
                    })
                    print(f"AUTO: {user.email} {symbol} - executed {side} qty={qty:.8f} price={price:.2f} usd={base_usd:.2f}")
                except Exception as e:
                    reason = f"error {e}"
                    print(f"AUTO: {user.email} {symbol} - {reason}")
                    decision.update({"action": "error", "reason": str(e)})
                finally:
                    user_result["decisions"].append(decision)
            results.append(user_result)
        return {"status": "ok", "processed": len(settings_rows), "results": results}
    finally:
        db.close()