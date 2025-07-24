import requests

BITRIX24_WEBHOOK_URL = "https://b24-0p52kg.bitrix24.ru/rest/1/3sgl85h7ahmsxwl8/"

def create_lead(title, name=None, phone=None, email=None, custom_fields=None):
    url = BITRIX24_WEBHOOK_URL + "crm.lead.add.json"
    fields = {
        "TITLE": title,
        "NAME": name or "",
        "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}] if phone else [],
        "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}] if email else [],
    }
    if custom_fields:
        fields.update(custom_fields)
    payload = {"fields": fields}
    resp = requests.post(url, json=payload)
    print("Bitrix24 response:", resp.status_code, resp.text)
    return resp.json()

def get_contact(contact_id):
    url = BITRIX24_WEBHOOK_URL + "crm.contact.get.json"
    params = {"ID": contact_id}
    resp = requests.get(url, params=params)
    print("Bitrix24 get_contact response:", resp.status_code, resp.text)
    return resp.json() 