from python_anvil.api import Anvil
from veryfi import Client
from flask import Flask
from flask import request
from flask import Response
import json
import time
import sys

app = Flask(__name__)

ANVIL_API_KEY = '9gdAke4H4TMfBVSZ9f2JvLUW74UyLPnv'
VERYFI_client_id = 'vrf1y2ZSTzb0jlLZcO70FX50k6mEY4zfLuC901i'
VERYFI_client_secret = 'dO3BKiCEKFOYjuW6PpxsYsnCAwX8t99FMsbTTaDhrjOo2jOFIjptEkslEvzVAByGitUZCOrWmnyIi0PaMsNcy0btuj1NT7wfri79rExfeduTjMPldHnS9Upxzc0cV8fC'
VERYFI_username = 'pradhith'
VERYFI_API_KEY = '89351e076d3241cc9c94f662ca5ef677'

def veryfi(file_path):
    # file_path = '/Users/pradhithkonduri/Documents/Projects/abridge/shipping_docs/modern/inv-pac-mf-02706032022.pdf'
    veryfi_client = Client(VERYFI_client_id, VERYFI_client_secret, VERYFI_username, VERYFI_API_KEY)
    response = veryfi_client.process_document(file_path)
    print(response)
    return response

@app.route('/result', methods=['GET', 'POST'])
def handle_request():
    file_name = request.args.get('file_name')
    print("file name is {}".format(file_name), flush=True)
    print("request data is {}".format(request.files['file']), flush=True)
    # invoice_json = veryfi(file_name)

    with open('./veryfi_invoice.json', 'r') as f:
      invoice_json = json.load(f)

    anvil = Anvil(api_key=ANVIL_API_KEY)

    # Your fill payload. A number of things can be styled at the
    # document-level, and each field can also be styled individually with the
    # same styling options.
    data = {
      "title": "Checklist Template",
      "fontSize": 8,
      "textColor": "#178705",
      "data": {
        "cast484e08e0fb2811ec809257a303fdb8fc": iec_code(invoice_json),
        "cast526f9230fb2811ec809257a303fdb8fc": iec_code(invoice_json),
        "cast5bf529a0fb2811ec809257a303fdb8fc": "???",
        "cast65ea24b0fb2811ec809257a303fdb8fc": gstin(invoice_json),
        "cast7dfdc750fb2811ec809257a303fdb8fc": exporter_name(invoice_json),
        "cast1923eb80fb2c11ec809257a303fdb8fc": exporter_address(invoice_json),
        "cast8972aba0fb2811ec809257a303fdb8fc": cosignee_name(invoice_json),
        "cast3d290000fb2d11ec809257a303fdb8fc": cosignee_address(invoice_json),
        "cast9402ae30fb2811ec809257a303fdb8fc": "port_of_loading",
        "caste48b13f0fb2e11ec809257a303fdb8fc": net_weight(invoice_json),
        "cast366cfdf0fb2f11ec809257a303fdb8fc": gross_weight(invoice_json),
        "castb21184d0fb2f11ec809257a303fdb8fc": exchange_rate(),
        "castdf3219c0fb2f11ec809257a303fdb8fc": hts_code(invoice_json),
        "cast098313f0fb3011ec809257a303fdb8fc": item_desc(invoice_json),
        "cast2851bc50fb3011ec809257a303fdb8fc": unit_price(invoice_json),
        "cast2da47f80fb3011ec809257a303fdb8fc": cost(invoice_json),
        "cast45a70b20fb3011ec809257a303fdb8fc": cost_inr(invoice_json),
        "cast6a71fd20fb3011ec809257a303fdb8fc": tax_inr(invoice_json),
        "cast8132f620fb3211ec809257a303fdb8fc": cost_inr(invoice_json),
        "castade8e260fb3211ec809257a303fdb8fc": fob_value_usd_inr(invoice_json),
        "castb773a9f0fb3211ec809257a303fdb8fc": fob_value_usd_inr(invoice_json),
        "castb1cfc410fb3311ec809257a303fdb8fc": marks_and_notes(invoice_json)
      }
    }

    # Fill the provided cast eid (see PDF Templates in your Anvil account)
    # with the data above. This will return bytes for use in directly writing
    # to a file.
    res = anvil.fill_pdf('CMIl2utivVsd29VkX9B9', data)

    # Write the bytes to disk
    with open('./file.pdf', 'wb') as f:
        # f.write(request.data)
        f.write(res)
    return Response(request.files['file'].read(), mimetype='application/pdf')


# values that can be manually configured
usd_to_inr = 77.25
tax_pct = .18


def iec_code(data):
    return data['ocr_text'].split('IEC Code: ')[1].split('\n')[0]

def gstin(data):
    return data['vat_number']

def exporter_name(data):
    return data['vendor']['name']

def exporter_address(data):
    return data['vendor']['address']

def cosignee_name(data):
    return data['bill_to_name']

def cosignee_address(data):
    return data['bill_to_address']

def net_weight(data):
    return data['ocr_text'].split('Net Wt. (Kgs.)')[1].split('\t')[1].split('\n')[0]

def gross_weight(data):
    return data['ocr_text'].split('Gross Wt. (Kgs.)')[1].split('\t')[1].split('\n')[0]

def exchange_rate():
    return "USD 1 = Rs. " + str(usd_to_inr)

def hts_code(data):
    return data['ocr_text'].split('HTS CODE ')[1].split('\n')[0]

def item_desc(data):
    return data['line_items'][0]['description']

def unit_price(data):
    return data['line_items'][0]['price']

def cost(data):
    return data['line_items'][0]['total']

def cost_inr(data):
    return cost(data) * usd_to_inr

def tax_inr(data):
    return cost_inr(data) * tax_pct

def fob_value_usd_inr(data):
    usd = cost(data)
    inr = cost_inr(data)
    return '{} (Rs. {})'.format(usd, inr)

def invoice_did_request_rodtep(data):
    if 'rodtep' in data['ocr_text'].lower():
        return 'Yes'
    return 'No'

def marks_and_notes(data):
    return 'Total Net Wt: {} Kgs. Was RoDTEP requested? : {}'.format(net_weight(data),invoice_did_request_rodtep(data))

if __name__ == '__main__':
    app.run(debug=True, port=2000)

