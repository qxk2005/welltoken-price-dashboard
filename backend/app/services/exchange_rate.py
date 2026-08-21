import httpx
from datetime import datetime

class ExchangeRateService:
    def __init__(self):
        self.current_rate: float = 7.30
        self.last_updated: datetime | None = None
        self.api_url = "https://open.er-api.com/v6/latest/USD"

    async def fetch_real_rate(self) -> float:
        """真实拉取最新全球外汇 USD -> CNY 汇率"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    cny = data.get("rates", {}).get("CNY")
                    if cny and isinstance(cny, (int, float)):
                        self.current_rate = round(float(cny), 4)
                        self.last_updated = datetime.utcnow()
                        print(f"[ExchangeRateService] Real exchange rate fetched: 1 USD = {self.current_rate} CNY")
                        return self.current_rate
        except Exception as e:
            print(f"[ExchangeRateService] Failed to fetch real exchange rate, fallback to {self.current_rate}: {e}")
        return self.current_rate

exchange_rate_service = ExchangeRateService()
