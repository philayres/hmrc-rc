from flask import Flask
from flask import render_template
from flask import Response
from flask import request
import json
from io import StringIO
import csv
from exchange import Exchange
import os
import pathlib

dir_path = pathlib.Path('/tmp/tmp')
if not dir_path.exists():
    os.mkdir('/tmp/tmp')
dir_path = pathlib.Path('/tmp/xml')
if not dir_path.exists():
    os.mkdir('/tmp/xml')
dir_path = pathlib.Path('/tmp/json')
if not dir_path.exists():
    os.mkdir('/tmp/json')


app = Flask(__name__)


@app.route('/')
def index():

    title = "Download CSV HMRC Exchange Rates"
    view_base = 'index/'

    x = Exchange()
    years = range(x.earliest_year, x.latest_year + 1)
    currencies = x.available_currencies()

    return render_template(view_base + 'main.html', title=title, years=years, currencies=currencies)


@app.route('/exchange')
def exchange():

    try:
        format = request.args.get('format')
        if format is None:
            format = 'csv'

        currency = request.args.get('currency')
        if currency is None:
            raise Exception("Enter a currency")

        p = request.args.get('start_from_year')
        if p is None:
            raise Exception("Enter a Start Year")

        start_from_year = int(p)

        p = request.args.get('start_from_month')
        if currency is None:
            raise Exception("Enter a Start Month")

        start_from_month = int(p)

        x = Exchange()

        x.set_currency(currency)
        x.start_from(start_from_month, start_from_year)
        data = x.get_data()
    except Exception as e:
        return Response(str(e), status=400)
        return

    if format == 'csv':
        csvcontent = []
        fn = "hmrc-xr-{0}.csv".format(currency)

        data = [{
                    "period_start": 'period start',
                    "period_end": 'period end',
                    "rate": 'rate',
                    "currency": 'currency'
                }] + data

        for l in data:
            show_currency = l.get('currency', currency)
            resrow = [l["period_start"], l["period_end"], l["rate"], show_currency]
            line = StringIO()
            writer = csv.writer(line)
            writer.writerow(resrow)
            csvcontent.append(line.getvalue())

        return Response(
            csvcontent,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename={0}".format(fn)})

    if format == 'json':
        jdata = {
          "currency": currency,
          "rates": data
        }
        return json.dumps(jdata)


if __name__ == '__main__':
    app.run()
