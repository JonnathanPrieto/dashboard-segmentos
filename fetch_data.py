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

def get_view_id(access_token, view_name):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views'
    r = requests.get(url, headers=headers)
    print(f'Views list status: {r.status_code}')
    data = r.json()
    views = data.get('data', {}).get('views', [])
    print(f'Total views found: {len(views)}')
    for v in views:
        print(f'  - {v.get("viewName")} ({v.get("viewId")})')
        if v.get('viewName') == view_name:
            return v.get('viewId')
    return None

def get_table_data(access_token, view_id):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{view_id}/data'
    params = {'config': json.dumps({'responseFormat': 'json'})}
    r = requests.get(url, headers=headers, params=params)
    print(f'Data fetch status: {r.status_code}')
    result = r.json()
    rows = result.get('data', {}).get('rows', [])
    cols = result.get('data', {}).get('columns', [])
    if not cols:
        print('No columns found:', r.text[:300])
        return []
    col_names = [c['columnName'] for c in cols]
    return [dict(zip(col_names, row)) for row in rows]

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    print('Token OK')
    os.makedirs('data', exist_ok=True)

    print('Buscando Segmentación acumulada Total...')
    seg_id = get_view_id(token, 'Segmentación acumulada Total')
    if seg_id:
        seg = get_table_data(token, seg_id)
        with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
            json.dump(seg, f, ensure_ascii=False, indent=2)
        print(f'{len(seg)} filas en segmentacion.json')
    else:
        print('Vista no encontrada')
        with open('data/segmentacion.json', 'w') as f:
            json.dump([], f)

    print('Buscando Transiciones de segmentos Total...')
    trans_id = get_view_id(token, 'Transiciones de segmentos Total')
    if trans_id:
        trans = get_table_data(token, trans_id)
        with open('data/transiciones.json', 'w', encoding='utf-8') as f:
            json.dump(trans, f, ensure_ascii=False, indent=2)
        print(f'{len(trans)} filas en transiciones.json')
    else:
        print('Vista no encontrada')
        with open('data/transiciones.json', 'w') as f:
            json.dump([], f)

if __name__ == '__main__':
    main()
