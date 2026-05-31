from fastapi import FastAPI
import yfinance as yf
import yaml

app = FastAPI()

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def get_daily_return(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")

        if len(hist) < 2:
            return 0

        previous = hist["Close"].iloc[-2]
        current = hist["Close"].iloc[-1]

        return ((current - previous) / previous) * 100
    except Exception:
        return 0

@app.get("/portfolio")
def portfolio():

    config = load_config()

    portfolio_value = float(config["portfolio_value"])
    allocations = config["allocations"]

    weighted_return = 0
    market_data = {}

    for symbol, allocation in allocations.items():

        daily_return = get_daily_return(symbol)

        market_data[symbol] = {
            "allocation": allocation,
            "daily_return_pct": round(daily_return, 2)
        }

        weighted_return += (allocation / 100) * daily_return

    dollar_change = portfolio_value * (weighted_return / 100)

    return {
        "portfolio_value": round(portfolio_value, 2),
        "portfolio_change_pct": round(weighted_return, 2),
        "portfolio_change_dollars": round(dollar_change, 2),
        "estimated_value": round(
            portfolio_value + dollar_change,
            2
        ),
        "holdings": market_data
    }
