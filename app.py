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

def get_returns(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # Daily return
        daily_hist = ticker.history(period="2d")

        if len(daily_hist) < 2:
            daily_return = 0
        else:
            previous = daily_hist["Close"].iloc[-2]
            current = daily_hist["Close"].iloc[-1]
            daily_return = ((current - previous) / previous) * 100

        # 30-day return
        monthly_hist = ticker.history(period="1m")

        if len(monthly_hist) < 2:
            monthly_return = 0
        else:
            current = monthly_hist["Close"].iloc[-1]

            # Find price closest to 30 days ago
            start_price = monthly_hist["Close"].iloc[0]

            monthly_return = ((current - start_price) / start_price) * 100

        return daily_return, monthly_return

    except Exception:
        return 0, 0

@app.get("/portfolio")
def portfolio():

    config = load_config()

    portfolio_value = float(config["portfolio_value"])
    allocations = config["allocations"]

    weighted_daily_return = 0
    weighted_30day_return = 0

    market_data = {}

    for symbol, allocation in allocations.items():

        daily_return, monthly_return = get_returns(symbol)

        market_data[symbol] = {
            "allocation": allocation,
            "daily_return_pct": round(daily_return, 2),
            "thirty_day_return_pct": round(monthly_return, 2)
        }

        weighted_daily_return += (
            allocation / 100
        ) * daily_return

        weighted_30day_return += (
            allocation / 100
        ) * monthly_return

    daily_dollar_change = (
        portfolio_value * (weighted_daily_return / 100)
    )

    thirty_day_dollar_change = (
        portfolio_value * (weighted_30day_return / 100)
    )

    return {
        "portfolio_value": round(portfolio_value, 2),

        "portfolio_change_pct": round(
            weighted_daily_return,
            2
        ),

        "portfolio_change_dollars": round(
            daily_dollar_change,
            2
        ),

        "thirty_day_change_pct": round(
            weighted_30day_return,
            2
        ),

        "thirty_day_change_dollars": round(
            thirty_day_dollar_change,
            2
        ),

        "estimated_value": round(
            portfolio_value + daily_dollar_change,
            2
        ),

        "holdings": market_data
    }
    
@app.get("/homepage")
def homepage():
    data = portfolio()

    return {
        "value": f"${data['estimated_value']:,.0f}",
        "change": f"${data['portfolio_change_dollars']:,.0f}",
        "percent": round(data['portfolio_change_pct'], 2),
        "thirty_day_change": f"${data['thirty_day_change_dollars']:,.0f}"
    }
