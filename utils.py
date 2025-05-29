import yfinance as yf
import pandas as pd


# Load ticker symbols from Wikipedia for a given stock index
def load_tickers(index):
    base = "https://en.wikipedia.org/wiki/"

    if index == "NDX":
        # Load NASDAQ-100 tickers from Wikipedia
        table = pd.read_html(f"{base}Nasdaq-100")
        tickers = table[4]["Ticker"].tolist()
        return tickers

    elif index == "DAX":
        # Load DAX 40 tickers from Wikipedia
        table = pd.read_html(f"{base}DAX")
        tickers = table[4]["Ticker"].tolist()
        return tickers

    elif index == "OMXS30":
        # Load OMXS30 tickers from Wikipedia and format for Yahoo Finance
        table = pd.read_html(f"{base}OMX_Stockholm_30")
        tickers = table[1]["Symbol"].tolist()
        tickers = [f"{ticker.replace(' ', '-')}.ST" for ticker in tickers]
        return tickers

    else:
        return False  # Return False for unknown index


# Download historical price data using yfinance
def load_data(tickers, start_date, end_date):
    data = yf.download(tickers, start=start_date, end=end_date, threads=False)
    return data


# Calculate rolling z-score for a time series
def get_z_score(data, window):
    sma = data.rolling(window).mean()  # Rolling mean
    std = data.rolling(window).std()  # Rolling standard deviation
    z_score = (data - sma) / std  # Z-score calculation
    return z_score


# Generate portfolio weights based on strategy and return data
def load_weights(nr_positions, strategy, log_returns):
    # Compute rolling indicators
    log_means = log_returns.rolling(7).mean()
    z_score = get_z_score(log_returns, 7)

    # Select indicator based on strategy type
    indicator = log_means if strategy == "TrendFollowing" else z_score

    # Resample indicators to weekly frequency (Friday close)
    weekly_indicator = indicator.resample("W-FRI").last()

    # Initialize empty weights DataFrame
    weights = pd.DataFrame(
        0.0, index=weekly_indicator.index, columns=weekly_indicator.columns
    )

    # Assign weights based on strategy
    for date, row in weekly_indicator.iterrows():
        row_fnc = row.nlargest if strategy == "TrendFollowing" else row.nsmallest
        positions = row_fnc(nr_positions).index
        weights.loc[date, positions] = 1 / nr_positions  # Equal weight allocation

    # Align weights to daily frequency and shift to avoid look-ahead bias
    weights = weights.reindex(log_returns.index).shift(1).dropna()

    # Forward-fill missing weights for daily usage
    daily_weights = weights.reindex(log_returns.index, method="ffill").fillna(0)

    return daily_weights
