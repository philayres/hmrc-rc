import xml.etree.ElementTree as ET
import json
import xmltodict
import os
import requests
import pathlib
import datetime


url_tmp = 'http://www.hmrc.gov.uk/softwaredevelopers/rates/exrates-monthly-{0:02d}{1}.xml'


class Exchange:

    latest_month = None
    latest_year = None
    earliest_year = 16

    def __init__(self):
        now = datetime.datetime.now()
        self.latest_year = now.year - 2000
        self.latest_month = now.month
        return

    def start_from(self, month, year):
        self.start_from_month = month
        self.start_from_year = year

    def set_currency(self, currency):
        self.currency = currency

    def available_currencies(self):
        month = self.latest_month
        year = self.latest_year

        # Use the previous month, as this one may not be ready yet
        month -= 1
        if month == 0:
            month = 12
            year -= 1

        data = self.get_xml(month, year)
        ml = data["exchangeRateMonthList"]
        currencies = []
        for item in ml["exchangeRate"]:
            currencies.append({
                "currencyCode": item["currencyCode"],
                "currencyName": item["currencyName"]
            })
        return currencies

    def validate_month_year(self, month, year):
        if not (isinstance(month, int) and month >= 1 and month <= 12):
            raise Exception("Specified month is not an integer between 1 and 12")

        if not (isinstance(year, int) and year >= self.earliest_year and year <= self.latest_year):
            msg = "Specified year is not an integer between {0} and now".format(self.earliest_year)
            raise Exception(msg)

        if year == self.latest_year and month > self.latest_month:
            raise Exception("Specified month and year is later than now")

    def get_xml(self, month, year):

        self.validate_month_year(month, year)

        url = url_tmp.format(month, year)
        fn_data = 'xr-{0:02d}{1}.xml'.format(month, year)
        fn_tmp = '/tmp/tmp/{0}'.format(fn_data)
        fn_xml = '/tmp/xml/{0}'.format(fn_data)

        fn_path = pathlib.Path(fn_xml)
        if fn_path.exists():
            with open(fn_xml, 'r') as xml_file:
                print('using existing file')
                xmldata = xml_file.read()
        else:
            print("downloading file: {0}".format(url))
            response = requests.get(url)

            fn_path = pathlib.Path(fn_tmp)
            if fn_path.exists():
                os.remove(fn_tmp)

            if response.status_code == 200:
                xmldata = response.content
                with open(fn_tmp, 'wb') as xml_file:
                    xml_file.write(xmldata)
                os.rename(fn_tmp, fn_xml)

            else:
                if year == self.latest_year and month == self.latest_month:
                    print("Failed to retrieve requested XML from HMRC, but it is the latest month, so just ignore")
                    return
                else:
                    raise Exception("Failed to retrieve requested XML from HMRC")

        data = ET.fromstring(xmldata)

        xmlstr = ET.tostring(data, encoding='utf8', method='xml')

        data_dict = dict(xmltodict.parse(xmlstr))

        fn_json = '/tmp/json/xr-{0}{1}.json'.format(month, year)
        with open(fn_json, 'w') as json_file:
            json.dump(data_dict, json_file, indent=4, sort_keys=True)

        return data_dict

    def get_data(self):

        self.validate_month_year(self.start_from_month, self.start_from_year)

        first_year = True
        results = []

        for year in range(self.start_from_year, self.latest_year + 1):

            final_year = (year == self.latest_year)

            for month in range(1, 13):

                if first_year and month < self.start_from_month:
                    continue

                if final_year and month > self.latest_month:
                    break

                data = self.get_xml(month, year)

                if data is None:
                    print("Didn't get a result. Stop trying.")
                    return results

                ml = data["exchangeRateMonthList"]

                period = ml["@Period"]
                period_r = period.split(' to ')

                rate = [item["rateNew"] for item in ml["exchangeRate"] if item["currencyCode"] == self.currency]

                results.append({
                    "period_start": period_r[0],
                    "period_end": period_r[1],
                    "rate": rate[0]
                })

            first_year = False

        return results
