from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api
import yfinance as yf
from replit import db
import json
import threading

app = Flask(__name__)
api = Api(app)

'''
Database:
db[TICKER_SYMBOL] = {"value":float, "volume": integer}

'''

def getResponse(js):
    return Response(json.dumps(js), mimetype="application/json")


def get_ticker_key_info(symbol, key_info):

    try:
        info = yf.Ticker(symbol).info
        data = info[key_info]
        return data
    except:
        return "DNE"

'''curl http://127.0.0.1:5000:/current_price/AAPL'''


mutex = threading.Lock()

def add_to_database(ticker, value, volume):
  with mutex:
    db[ticker] = {"value": value, "volume": volume}

@app.route('/current_price/<ticker_symbol>', methods=['GET'])
def get_current_price(ticker_symbol):
    current_price = get_ticker_key_info(ticker_symbol, "currentPrice")
    return {"ticker": ticker_symbol, "value": current_price}


@app.route('/', methods=['GET'])
def query_records():
    retval = []
    for key in db.keys():
        retval.append({
            "ticker": key,
            "value": db[key]["value"],
            "volume": db[key]["volume"]
        })

    return getResponse(retval)


@app.route('/buy/<ticker_symbol>/<volume>', methods=['GET'])
def post_buy(ticker_symbol, volume):

    current_price = get_ticker_key_info(ticker_symbol, "currentPrice")
    retval = {}
  
    if current_price == 'DNE':
        retval = {
            "ticker": ticker_symbol,
            "value": current_price,
            "volume": 0
        }

    else:
        if ticker_symbol not in db.keys():
          db_thread = threading.Thread(target=add_to_database, args=(ticker_symbol, current_price, volume))
          db_thread.start()
          db_thread.join()  
          query_records()
          retval =  {
              "ticker": ticker_symbol,
              "value": current_price,
              "volume": volume
          }
        else:
            val1 = float(db[ticker_symbol]["value"]) * float(
                db[ticker_symbol]["volume"])
            val2 = float(current_price) * float(volume)
            tot_vol = float(db[ticker_symbol]["volume"]) + float(volume)
            val3 = float(val1 + val2) / float(tot_vol)

            db_thread = threading.Thread(target=add_to_database, args=(ticker_symbol, val3, tot_vol))
            db_thread.start()
            db_thread.join()
            retval = {
                "ticker": ticker_symbol,
                "value": db[ticker_symbol]["value"],
                "volume": db[ticker_symbol]["volume"]
            }
          
    return getResponse(retval)

'''curl -X POST http://127.0.0.1:5000/sell/aapl/5'''
@app.route('/sell/<ticker_symbol>/<volume>', methods=['POST'])
def post_sell(ticker_symbol, volume):    
    retval = {}
    current_price = get_ticker_key_info(ticker_symbol, "currentPrice")
    if ticker_symbol in db.keys():
        if current_price == 'DNE':
            retval = {
                "ticker": ticker_symbol,
                "value": current_price,
                "volume": 0
            }
        if int(volume) < int(db[ticker_symbol]["volume"]):

          tot_vol = int(db[ticker_symbol]["volume"]) - int(volume)
          db_thread = threading.Thread(target=add_to_database, args=(ticker_symbol, current_price, tot_vol))
          db_thread.start()
          db_thread.join()
          
          retval = {
                "ticker": ticker_symbol,
                "value": db[ticker_symbol]["value"],
                "volume": db[ticker_symbol]["volume"]
            }
    return getResponse(retval)


if __name__ == '__main__':
    app.run(debug=True)
