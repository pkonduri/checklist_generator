from python_anvil.api import Anvil
from veryfi import Client
from flask import Flask
from flask import request
from flask import Response
from copy import deepcopy
import json
import time
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from os.path import basename

class LineItem:
  Description = 'Item Description'
  Qty = 'Item Quantity'
  UnitPrice = 'Item Unit Price'
  Total = 'Item Total Value'
  TotalINR = 'Item Total Value INR'
  Code = 'Item HTS Number'

USD_TO_INR = 77.25

def extract_line_items(invoice):
  line_items = []
  line_item_fields = ['Item Description', 'Item Quantity', 'Item Unit Price', 'Item Total Value', 'Item HTS Number']
  line_item = {}
  for item in invoice['annotations']:
    key = item.get('label')
    if key not in line_item_fields:
      continue
    if key in line_item_fields:
      if key in line_item: #we have already seen this key, so reset
        line_items.append(line_item)
        line_item = {}
      line_item[key] = item.get('text')
  if line_item:
    line_items += [line_item]
  return line_items

def get_field(invoice, field):
  for item in invoice['annotations']:
    if item['label'] == field:
      return item['text']
  return ''

def amend_total_amount(invoice):
  usd = float(get_field(invoice, 'Total Amount').replace(',',''))
  inr = int(USD_TO_INR * usd)
  return '{} (Rs. {})'.format(usd, inr)

def exchange_rate_str(invoice):
  return 'USD 1 = Rs. {}'.format(USD_TO_INR)

      
with open('../json/arriba_invoice_scale.json', 'r') as f:
  invoice_json = json.load(f)

line_items = extract_line_items(invoice_json)

app = Flask(__name__)

ANVIL_API_KEY = '9gdAke4H4TMfBVSZ9f2JvLUW74UyLPnv'
anvil = Anvil(api_key=ANVIL_API_KEY)

data = {
  "title": "Checklist Template Shipping",
  "fontSize": 10,
  "textColor": "#0356fc",
  "data": {
    "followingIsTheListOfDocumentAttached0": "Following is the list of document attached",
    "ExporterAddress": get_field(invoice_json, 'Shipment Origin Address'),
    "InvoiceNumber": get_field(invoice_json, 'Invoice Number'),
    "InvoiceDate": get_field(invoice_json, 'Invoice Date'),
    "InvoiceValue": amend_total_amount(invoice_json),
    "FobValue": amend_total_amount(invoice_json),
    "ConsigneeName": get_field(invoice_json, 'Destination Name'),
    "ConsigneeAddress": get_field(invoice_json, 'Destination Address'),
    "BuyerName": get_field(invoice_json, 'Buyer Name'),
    "BuyerAddress": get_field(invoice_json, 'Buyer Address'),
    "ExchangeRate": exchange_rate_str(invoice_json),
    "VendorName": get_field(invoice_json, 'Vendor Name'),
  }
}


if data['data']['ExporterAddress'] == '':
  data['data']["VendorAddress"] = get_field(invoice_json, 'Vendor Address')

def add_line_items_to_checklist(data, line_items):
  # num_lines = 7
  line_item_dict = {}
  for line in range(len(line_items)):
    total = line_items[line].get(LineItem.Total)
    if total == None:
      total = 0
    desc = line_items[line].get(LineItem.Description)
    if desc == None:
      desc = ''
    desc.replace('\n', ' ')

    data['data']['Item{}Code'.format(line+1)]=line_items[line].get(LineItem.Code)
    data['data']['Item{}Quantity'.format(line+1)]=line_items[line].get(LineItem.Qty)
    data['data']['Item{}Description'.format(line+1)]=desc
    # data['data']['Item{}UnitPrice'.format(line+1)]=line_items[line].get(LineItem.UnitPrice)
    data['data']['Item{}TotalValue'.format(line+1)]=float(total)
    data['data']['Item{}TotalValueINR'.format(line+1)]=float(total) * USD_TO_INR

  return data


data = add_line_items_to_checklist(data, line_items)
res = anvil.fill_pdf('xZU7h4c8S5SG9qubqHeD', data)

# Write the bytes to disk
with open('./checklist_generator.pdf', 'wb') as f:
    # f.write(request.data)
    f.write(res)

def send_mail(send_from: str, subject: str, text: str, send_to: list, files= None):

    send_to= default_address if not send_to else send_to

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = ', '.join(send_to)  
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil: 
            ext = f.split('.')[-1:]
            attachedfile = MIMEApplication(fil.read(), _subtype = ext)
            attachedfile.add_header(
                'content-disposition', 'attachment', filename=basename(f) )
        msg.attach(attachedfile)


    smtp = smtplib.SMTP(host="smtp.gmail.com", port= 587) 
    smtp.starttls()
    smtp.login(username,password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


username = 'abridge.server@gmail.com'
password = 'alkmkanzodfbwybg'
default_address = ['pradhith.konduri@gmail.com', 'founders@abridge.dev', 'pradhith@abridge.dev', 'vidhi@abridge.dev'] 

send_mail(send_from=username,
subject="Generated Checkist",
text="Please see the attached for your generated checklist. \n\n Sincerely,\n Abridge Bot",
send_to= default_address,
files=['/Users/pradhithkonduri/Documents/Projects/abridge/ocr/checklist_generator.pdf']
)