import pymongo
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
import requests
import time
from bson.json_util import dumps
from flask import request, jsonify
import json
import ast
from importlib.machinery import SourceFileLoader
from dotenv import load_dotenv
import os
import threading
import time
load_dotenv()
USER = os.getenv("USER")
PASSWORD = os.getenv("psswd")
helper_module = SourceFileLoader('*', './helpers.py').load_module()

app = Flask(__name__)
#change this to old string
client = pymongo.MongoClient(
    f"mongodb://{USER}:{PASSWORD}@ac-s9wxd5z-shard-00-00.mhhdqxv.mongodb.net:27017,ac-s9wxd5z-shard-00-01.mhhdqxv.mongodb.net:27017,ac-s9wxd5z-shard-00-02.mhhdqxv.mongodb.net:27017/?ssl=true&replicaSet=atlas-gf2b72-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client.get_database('Cluster0')
records = db.Crypto
# Steps to get data for Graphs and Presentation
ranks = []
names = []
prices = []

cursor = records.find()
for record in cursor[:20]:
    names.append(record["name"])
    ranks.append(record["rank"])
    prices.append(record["price"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/BarChartRanks")
def BarChart():
    labels = names
    values = ranks
    return render_template('BarChart.html', labels=labels, values=values)


@app.route("/BarChartPrices")
def BarChartPrices():
    labels = names
    values = prices
    return render_template('BarChartPrices.html', labels=labels, values=values)


@app.route("/detail")
def getDetail():
    details = []
    detailsVal = records.find()
    for detail in detailsVal[:20]:
        details.append(
            {'name': detail['name'], 'price': str(round(float(detail['price']), 2)), 'symbol': detail['symbol'],
             'rank': detail['rank'], 'volume': str(round(float(detail['volume']), 2))})
        # (details)
        # details = {'name': index['name'], 'price': index['priceUsd'], 'symbol': index['symbol'],
        # 'rank': index['rank'], 'volume': index['volumeUsd24Hr']}
    return render_template('detailPage.html', details=details)


# API to get all Cryptocurrency assets
@app.route("/api/v1/getAllAssets", methods=['GET'])
def fetch_users():
    try:
        # Call the function to get the query params
        query_params = helper_module.parse_query_params(request.query_string)
        # Check if dictionary is not empty
        if query_params:
            query = {k: v if isinstance(v, str) and v.isdigit(
            ) else v for k, v in query_params.items()}
            # Fetch all the record(s)
            records_fetched = records.find(query)
            # Check if the records are found
            if records_fetched.count() > 0:
                # Prepare the response
                return dumps(records_fetched)
            else:
                # No records are found
                return "", 404
        else:
            # Return all the records as query string parameters are not available
            if records.find().count() > 0:
                return dumps(records.find())
            else:
                return jsonify([])
    except:
        return "", 500


def update_db():
    print('CONNECTED TO DB')

    url = " https://api.coincap.io/v2/assets"
    # Get Data from mentioned url and store into the Mongo DB
    while(1):
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            # print(data)
            for indexVal in data['data'][:5]:
                records.insert_one({"name": indexVal['name'], "symbol": indexVal['symbol'], "rank": indexVal['rank'],
                                    "price": indexVal['priceUsd'],
                                    "volume": indexVal['volumeUsd24Hr']})
        time.sleep(3600*24)


def run_web_server():
    print("RUNNING WEB SERVER")
    app.debug = False
    app.run()


if __name__ == "__main__":
    t1 = threading.Thread(target=update_db)
    t2 = threading.Thread(target=run_web_server)
    t2.start()
    t1.start()
