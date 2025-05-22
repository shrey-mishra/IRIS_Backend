# API Documentation

## Auth Endpoints

### POST /auth/register
Registers a new user.

**Request Body:**
```json
{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

**Response Body:**
```json
{
    "email": "string",
    "id": "integer",
    "username": "string"
}
```

### POST /auth/login
Logs in an existing user.

**Request Body:**
```json
{
    "email": "string",
    "password": "string"
}
```

**Response Body:**
```json
{
    "access_token": "string",
    "token_type": "string",
    "email": "string",
    "id": "integer",
    "username": "string"
}
```

### POST /auth/change-password
Allows a user to change their password.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Response Body:**
```json
{
    "message": "Password changed successfully"
}
```

### DELETE /auth/user
Deletes an existing user.

**Request Body:**
```json
{
    "email": "string",
    "password": "string"
}
```

**Response Body:**
```json
{
    "message": "Account deleted"
}
```

### GET /auth/validate-binance-account
Validates the user's Binance account.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "status": "success",
    "wallets": "array"
}
```

### GET /auth/userstats
Retrieves user statistics.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "roi": "number",
    "total_assets": "number",
    "total_loss": "number"
}
```

### GET /auth/userinfo
Retrieves user information.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "username": "string",
    "email": "string",
    "binance_api_key": "string",
    "binance_api_secret": "string"
}
```

### POST /auth/logout
Logs out the current user.

### PUT /auth/binance_keys
Updates the user's Binance API keys.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "binance_api_key": "string",
    "binance_api_secret": "string"
}
```

**Response Body:**
```json
{
    "message": "string"
}

## Preferences Endpoints

### PUT /preferences/binance_keys
Updates the user's Binance API keys.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "binance_api_key": "string",
    "binance_api_secret": "string"
}
```

**Response Body:**
```json
{
    "message": "Binance keys updated successfully"
}
```

### POST /preferences/
Creates new user preferences.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "auto_trade": "boolean",
    "threshold_limit": "number"
}
```

**Response Body:**
```json
{
    "auto_trade": "boolean",
    "threshold_limit": "number",
    "id": "integer",
    "user_id": "integer"
}
```

### GET /preferences/
Retrieves user preferences.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "auto_trade": "boolean",
    "threshold_limit": "number",
    "id": "integer",
    "user_id": "integer"
}
```

### PUT /preferences/
Updates user preferences.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "auto_trade": "boolean",
    "threshold_limit": "number"
}
```

**Response Body:**
```json
{
    "auto_trade": "boolean",
    "threshold_limit": "number",
    "id": "integer",
    "user_id": "integer"
}
```

## Live Feeds Endpoints

### GET /live/trending
Retrieves trending coins.

**Response Body:**
```json
[
    {
        "symbol": "string",
        "volume": "number",
        "last": "number"
    }
]
```

### GET /live/block-orders
Retrieves block orders for a specific symbol.

**Parameters:**
- `symbol`: The trading symbol (e.g., BTC/USDT). Default is BTC/USDT.

**Response Body:**
```json
[
    {
        "info": "object",
        "timestamp": "integer",
        "datetime": "string",
        ...
    }
]
```

### GET /live/charts
Retrieves live chart data for a specific symbol.

**Parameters:**
- `symbol`: The trading symbol (e.g., BTC/USDT). Default is BTC/USDT.

**Response Body:**
```json
{
    "data": [
        "object",
        ...
    ],
    "layout": "object",
    "frames": [
        "object",
        ...
    ],
    "config": "object"
}
```

## Portfolio Endpoints

### POST /portfolio/add
Adds a new entry to the user's portfolio.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "btc_amount": "number",
    "purchase_price": "number"
}
```

**Response Body:**
```json
{
    "id": "integer",
    "user_id": "integer",
    "btc_amount": "number",
    "purchase_price": "number",
    "created_at": "string"
}
```

### GET /portfolio/
Retrieves the user's portfolio.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
[
    {
        "id": "integer",
        "user_id": "integer",
        "btc_amount": "number",
        "purchase_price": "number",
        "created_at": "string"
    }
]
```

### GET /portfolio/graph
Retrieves a graph of the user's portfolio.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "data": [
        "object",
        ...
    ],
    "layout": "object",
    "frames": [
        "object",
        ...
    ],
    "config": "object"
}
```

### GET /portfolio/wallet
Retrieves the user's Binance wallet balances.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "wallet": "object"
}
```

### GET /portfolio/summary
Retrieves a summary of the user's portfolio.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "portfolio_summary": "array",
    "total_value_usd": "number",
    "overall_gain_loss_percentage": "number"
}
```

### GET /portfolio/timeseries
Retrieves timeseries data for the user's portfolio.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
[
    {
        "name": "string",
        "Gain": "number",
        "Loss": "number",
        "amt": "number"
    }
]
```

### GET /portfolio/wallet/history
Retrieves the history of the user's wallet.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
[
    {
        "date": "string",
        "total_value": "string",
        "breakdown": "object"
    }
]
```

## Trading Endpoints

### GET /trading/signals/latest
Retrieves the latest trading signals.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
[
    {
        "coin": "string",
        "Confidence": "string",
        "Signal Date": "string",
        "Direction": "string"
    }
]
```

### POST /trading/execute
Executes a trade.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Request Body:**
```json
{
    "symbol": "string",
    "side": "string",
    "amount": "number",
    "stop_loss": "number | null"
}
```

**Response Body:**
```json
{
    "message": "string"
}

## Trade History Endpoints

### GET /history
Retrieves the user's trade history.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Parameters:**
- `symbol` (optional): The trading symbol to filter by (e.g., BTC/USDT).
- `from_date` (optional): The start date to filter by (e.g., 2023-01-01).
- `to_date` (optional): The end date to filter by (e.g., 2023-01-31).

**Response Body:**
```json
[
    {
        "symbol": "string",
        "action": "string",
        "amount": "number",
        "price": "number",
        "executed_at": "string"
    }
]

</final_file_content>

IMPORTANT: For any future changes to this file, use the final_file_content shown above as your reference. This content reflects the current state of the file, including any auto-formatting (e.g., if you used single quotes but the formatter converted them to double quotes). Always base your SEARCH/REPLACE operations on this final version to ensure accuracy.

<environment_details>
# VSCode Visible Files
README.md

# VSCode Open Tabs
app/tasks/trading_tasks.py
app/schemas/portfolio.py
app/api/trading.py
app/api/trade_history.py
app/models/portfolio.py
app/tasks/scheduler.py
main.py
app/tasks/wallet_tasks.py
app/api/portfolio.py
app/api/auth.py
README.md

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
README.md

# Current Time
5/23/2025, 12:38:08 AM (Asia/Calcutta, UTC+5.5:00)

# Context Window Usage
69,138 / 1,048.576K tokens used (7%)

# Current Mode
ACT MODE
</environment_details>
