import requests
from app.core.config import settings

def get_prediction_from_model(symbol: str):
    url = f"{settings.ML_MODEL_URL}/predict?symbol={symbol}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise ValueError(f"ML model prediction API failed: {e}")