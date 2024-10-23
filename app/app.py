import httpx
from xml.etree import ElementTree as ET
from quart import Quart, jsonify, request
from collections import defaultdict


app = Quart(__name__)
CBR_URL = 'http://www.cbr.ru/scripts/XML_daily.asp'


async def convert_currency(
        from_currency: str,
        to_currency: str,
        ):
    '''
    Конвертер валют
    :param from_currency: валюта, которую переводят
    :param to_currency: валюта, в которую переводят
    :return: отношение валют from_currency и to_currency
    '''
    async with httpx.AsyncClient() as client:
        response = await client.get(CBR_URL)

    if response.status_code != 200:
        raise Exception('CBR aren`t working! Please, try later')

    rates = defaultdict(float)
    tree = ET.ElementTree(ET.fromstring(response.text))
    for valute in tree.findall('Valute'):
        char = valute.findtext('CharCode').upper()
        nominal = int(valute.findtext('Nominal'))
        value = float(valute.findtext('Value').replace(',', '.'))
        if nominal is None or value is None:
            raise ValueError('CBR aren`t working correctly! Please, try later')
        rates[char] = value / nominal

    rates['RUB'] = 1.0
    if rates[from_currency] != 0 and rates[to_currency] != 0:
        return rates[from_currency] / rates[to_currency]
    else:
        raise ValueError('Invalid currency code')


@app.route('/api/rates', methods=['GET'])
async def get_currency_rate():
    '''
    Quart API
    :return: JSON with result or error
    '''
    try:
        from_cur = request.args.get('from').upper()
        to_cur = request.args.get('to').upper()
        value = float(request.args.get('value', 1))
        if not from_cur or not to_cur:
            raise ValueError('Parametr(s) from or to is empty')
        result = await convert_currency(from_cur, to_cur) * value
        return jsonify({'result': round(result, 2)})
    except ValueError as e:
        return jsonify(
            {
                'error': str(e)
            }
        ), 400
    except Exception as e:
        return jsonify(
            {
                'error': str(e)
            }
        )
