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
    "username": "string",
    "binance_api_key": "string | null",
    "binance_api_secret": "string | null"
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
    "token_type": "string"
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
    "email": "string"
}
```

### POST /auth/logout
Logs out the current user.

**Request Headers:**
- `Authorization`: `Bearer <access_token>`

**Response Body:**
```json
{
    "message": "string"
}
```

### POST /auth/binance_keys
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
```

## Preferences Endpoints

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

## Trading Endpoints

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
