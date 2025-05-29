from utils import load_tickers, load_data, load_weights
from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
from datetime import datetime
import plotly.io as pio
import numpy as np

# Initialize Flask application
app = Flask(__name__)


# Main route handling form submission and portfolio simulation
@app.route("/", methods=["GET", "POST"])
def index():
    chart_html = ""
    error_message = ""
    selected_index = "NDX"
    start_date = "2020-01-01"
    end_date = "2025-01-01"
    strategy = "TrendFollowing"
    nr_positions = 5
    tickers = load_tickers(selected_index)

    if request.method == "POST":
        # Read form inputs
        selected_index = request.form.get("index")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        strategy = request.form.get("strategy")
        nr_positions = int(request.form.get("nr_positions"))

        # Validate date input
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            today = datetime.today().date()

            if start > end:
                error_message = "Start date must be before end date."
            elif end >= today:
                error_message = "End date cannot be today or in the future."
        except Exception as e:
            error_message = "Invalid date format."

        if not error_message:
            # Load tickers and historical data
            tickers = load_tickers(selected_index)
            data = load_data(tickers, start_date, end_date)

            # Compute returns
            pct_returns = data["Close"].pct_change(fill_method=None)
            log_returns = np.log1p(pct_returns).iloc[1:].replace(np.nan, 0)

            # Compute portfolio weights
            weights = load_weights(nr_positions, strategy, log_returns)

            # Calculate strategy and index performance
            strategy_returns = (weights * log_returns).sum(axis=1)
            index_returns = log_returns.mean(axis=1)

            # Accumulate portfolio value over time
            initial_capital = 10000
            strategy_value = initial_capital * (strategy_returns.cumsum() + 1)
            index_value = initial_capital * (index_returns.cumsum() + 1)

            # Plot performance chart
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=strategy_value.index, y=strategy_value.values, name="Strategy"
                )
            )
            fig.add_trace(
                go.Scatter(x=index_value.index, y=index_value.values, name="Index")
            )
            fig.update_layout(
                title={"text": "Portfolio Value", "x": 0.5, "xanchor": "center"},
                xaxis_title="Date",
                yaxis_title="Value (USD)",
            )
            chart_html = pio.to_html(fig, full_html=False)

    # Render template with chart and form data
    return render_template(
        "index.html",
        chart=chart_html,
        tickers=tickers,
        selected_index=selected_index,
        strategy=strategy,
        nr_positions=nr_positions,
        start_date=start_date,
        end_date=end_date,
        error_message=error_message,
    )


# Endpoint to fetch tickers dynamically via AJAX
@app.route("/get_tickers", methods=["POST"])
def get_tickers():
    index = request.json.get("index")
    tickers = load_tickers(index)
    return jsonify(tickers)


# Run the Flask app
if __name__ == "__main__":
    app.run("127.0.0.1", port=5000, debug=False)
