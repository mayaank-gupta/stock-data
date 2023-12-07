from flask import Flask, request, jsonify
import yfinance as yf
import datetime

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, world!'

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Check if the 'symbols' key exists in the JSON data
        if 'symbols' not in data:
            return jsonify({'error': 'Missing key "symbols" in JSON data'}), 400

        # Retrieve the array of stock symbols from the JSON data
        symbols = data['symbols']
        date = data.get('date', None)

        # Fetch data from Yahoo Finance for each symbol
        stock_data = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                third_trading_day = None
                sixth_trading_day = None
                month_trading_session = None
                next_day = None

                if date:
                    start_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                    end_date = start_date + datetime.timedelta(days=35)
                    data = stock.history(start=date, end=end_date)
                    lastest_data = stock.history(period="1d")
                    
                    if len(data) >= 2:
                        next_day = data.iloc[1]

                    if len(data) >= 3:
                        third_trading_day = data.iloc[2]  # 0-based indexing, so 2 means the 3rd trading day

                    if len(data) >= 6:
                        sixth_trading_day = data.iloc[5]
                    
                    if len(data) >= 23:
                        month_trading_session = data.iloc[22]

                else:
                    data = stock.history(period="1d")
                close_price = data['Close'].values[0] if not data.empty else None
                open_price = data['Open'].values[0] if not data.empty else None
                day_change = data['Close'].values[0] - data['Open'].values[0] if not data.empty else None
                day_change_percentage = (day_change / data['Open'].values[0]) * 100 if not data.empty else None
                modified_string  = symbol.replace(".NS", "")
                if date:
                    latest_price = lastest_data['Close'].values[0] if not data.empty else None
                    third_day_close = third_trading_day['Close'] if third_trading_day is not None else None
                    sixth_trading_day = sixth_trading_day['Close'] if sixth_trading_day is not None else None
                    month_trading_session = month_trading_session['Close'] if month_trading_session is not None else None
                    next_day = next_day['Close'] if next_day is not None else None
                    stock_data[modified_string] = {
                        'date_price': "{:.2f}".format(close_price),
                        'latest_price': "{:.2f}".format(latest_price),
                        'change_percentage': "{:.2f}".format(((latest_price - close_price)/close_price) * 100),
                        'next_day': "{:.2f}".format(next_day) if next_day is not None else None,
                        'third_trading_day': "{:.2f}".format(third_day_close) if third_day_close is not None else None,
                        'sixth_trading_day': "{:.2f}".format(sixth_trading_day) if sixth_trading_day is not None else None,
                        'month_trading_session': "{:.2f}".format(month_trading_session) if month_trading_session is not None else None
                    }
                    # Calculate percentage change for 'third_trading_day' if it's not None
                    if stock_data[modified_string]['third_trading_day'] is not None:
                        stock_data[modified_string]['third_day_change_percentage'] = "{:.2f}".format(
                            ((third_day_close - close_price) / close_price) * 100
                        )
                    
                    if stock_data[modified_string]['next_day'] is not None:
                        stock_data[modified_string]['next_day_percentage_change'] = "{:.2f}".format(
                            ((next_day - close_price) / close_price) * 100
                        )

                    # Calculate percentage change for 'sixth_trading_day' if it's not None
                    if stock_data[modified_string]['sixth_trading_day'] is not None:
                        stock_data[modified_string]['sixth_day_change_percentage'] = "{:.2f}".format(
                            ((sixth_trading_day - close_price) / close_price) * 100
                        )
                    
                    if stock_data[modified_string]['month_trading_session'] is not None:
                        stock_data[modified_string]['month_trading_change_percentage'] = "{:.2f}".format(
                            ((month_trading_session - close_price) / close_price) * 100
                        )

                else:
                    stock_data[modified_string] = {
                    'open': "{:.2f}".format(open_price),
                    'close': "{:.2f}".format(close_price),
                    'day_change_percentage': "{:.2f}".format(day_change_percentage)
                    }
            except Exception as e:
                stock_data[symbol] = {'error': str(e)}

        return jsonify(stock_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/backtest', methods=['POST'])
def backtest_data():
    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Check if the 'symbols' key exists in the JSON data
        if 'symbols' not in data:
            return jsonify({'error': 'Missing key "symbols" in JSON data'}), 400
        
        if 'date' not in data:
            return jsonify({'error': 'Missing key "date" in JSON data'}), 400
        
        if 'fixed_investment' not in data:
            return jsonify({'error': 'Missing key "fixed_investment" in JSON data'}), 400

        # Retrieve the array of stock symbols from the JSON data
        symbols = data['symbols']
        date = data.get('date', None)
        fixed_investment = data['fixed_investment']

        # Fetch data from Yahoo Finance for each symbol
        stock_data = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                start_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                end_date = start_date + datetime.timedelta(days=5)
                data = stock.history(start=date, end=end_date)
                latest_data = stock.history(period="1d")
                lowest_price = stock.history(start=date, interval="1wk")
                lowest_price = lowest_price['Low'].min()

                close_price = data['Close'].values[0] if not data.empty else None
                number_of_stocks = create_fixed_investment_portfolio({symbol: close_price}, fixed_investment)
                modified_string  = symbol.replace(".NS", "")
                latest_price = latest_data['Close'].values[0] if not data.empty else None
                stock_data[modified_string] = {
                    'date_price': "{:.2f}".format(close_price),
                    'latest_price': "{:.2f}".format(latest_price),
                    'change_percentage': "{:.2f}".format(((latest_price - close_price)/close_price) * 100),
                    'number_of_stocks': number_of_stocks[modified_string] or 1,
                    'total_stock_value': "{:.2f}".format(number_of_stocks[modified_string] * close_price) if number_of_stocks[modified_string] is not None else None,
                    'lowest_price':  "{:.2f}".format(lowest_price) if lowest_price is not None else None,
                    'lowest_percentage': "{:.2f}".format(((lowest_price - close_price)/close_price) * 100),
                }
            except Exception as e:
                stock_data[symbol] = {'error': str(e)}

        return jsonify(stock_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def create_fixed_investment_portfolio(stock_prices, fixed_investment):
    num_stocks = len(stock_prices)
    # Calculate the investment per stock
    investment_per_stock = fixed_investment / num_stocks
    
    # Calculate the number of shares for each stock
    portfolio_shares = {stock.replace(".NS", ""): round(investment_per_stock / price) or 1 for stock, price in stock_prices.items()}
    return portfolio_shares

if __name__ == '__main__':
    app.run(debug=True)