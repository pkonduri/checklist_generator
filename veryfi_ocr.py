# client id vrf1y2ZSTzb0jlLZcO70FX50k6mEY4zfLuC901i

import requests

CLIENT_ID = "vrf1y2ZSTzb0jlLZcO70FX50k6mEY4zfLuC901i"
ENVIRONMENT_URL = "https://api.veryfi.com/"

username = "pradhith"
api_key = "89351e076d3241cc9c94f662ca5ef677"
process_file_url = '{0}api/v7/partner/documents/'.format(ENVIRONMENT_URL)
headers = {
    "Accept": "application/json",
    "CLIENT-ID": CLIENT_ID,
    "AUTHORIZATION": "apikey {0}:{1}".format(username, api_key)
}

# file path and file name
image_path = '/Users/pradhithkonduri/Documents/Projects/abridge/shipping_docs/invoice_and_packing_list.PDF'
file_name = 'invoice_and_packing_list.pdf'

# You can send the list of categories that is relevant to your case
# Veryfi will try to choose the best one that fits this document
categories = ["Office Expense", "Meals & Entertainment", "Utilities", "Automobile"]
payload = {
    'file_name': file_name,
    'categories': categories
}
files = {'file': ('file', open(image_path, 'rb'), 'pdf')}
response = requests.post(url=process_file_url, headers=headers, data=payload, files=files)

print(response.json())