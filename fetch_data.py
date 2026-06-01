import requests
import json
import os

REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
CLIENT_ID = os.environ['ZOHO_SELF_CLIENT_ID']
CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ORG_ID = '2917853000000155002'
WORKSPACE_ID = '2917853000007172372'

def get_access_token():
    r = requests.post('https://accounts.zoho.com/oauth/v2/token', data={
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token'
    })
    return r.json()['access_token']

def get_table_data(access_token, table_name):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views'
    params = {
        'action': 'DATA',
        'viewName': table_name,
        'responseFormat': 'json'
    }
    r = requests.get(url, headers=headers, params=params)
    print(f'Response {table_name}:', r.status_code, r.text[:300])
    try:
        result = r.json()
        rows = result.get('data', {}).get('rows', [])
        cols = result.get('data', {}).get('columns', [])
        if not cols:
            return []
        col_names = [c['columnName'] for c in cols]
        return [dict(zip(col_names, row)) for row in rows]
    except:
        return []

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    print('Token OK')
    os.makedirs('data', exist_ok=True)

    print('Obteniendo Segmentación acumulada Total...')
    seg = get_table_data(token, 'Segmentación acumulada Total')
    with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    print(f'{len(seg)} filas en segmentacion.json')

    print('Obteniendo Transiciones de segmentos Total...')
    trans = get_table_data(token, 'Transiciones de segmentos Total')
    with open('data/transiciones.json', 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)
    print(f'{len(trans)} filas en transiciones.json')

if __name__ == '__main__':
    main()
