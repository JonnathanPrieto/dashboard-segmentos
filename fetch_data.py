import requests
import json
import os

REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
CLIENT_ID = os.environ['ZOHO_SELF_CLIENT_ID']
CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ORG_ID = '2917853000000155002'
WORKSPACE_ID = '2917853000000155002'

def get_access_token():
    r = requests.post('https://accounts.zoho.com/oauth/v2/token', data={
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token'
    })
    return r.json()['access_token']

def get_views(access_token):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    url = f'https://analyticsapi.zoho.com/api/v2/workspaces/{WORKSPACE_ID}/views'
    r = requests.get(url, headers=headers)
    print(f'Views status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
    return r.json()

def export_data(access_token, view_id):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    url = f'https://analyticsapi.zoho.com/api/v2/workspaces/{WORKSPACE_ID}/views/{view_id}/data'
    params = {'config': json.dumps({'responseFormat': 'json'})}
    r = requests.get(url, headers=headers, params=params)
    print(f'Export status: {r.status_code}')
    print(f'Export response: {r.text[:300]}')
    result = r.json()
    rows = result.get('data', {}).get('rows', [])
    cols = result.get('data', {}).get('columns', [])
    if not cols:
        return []
    col_names = [c['columnName'] for c in cols]
    return [dict(zip(col_names, row)) for row in rows]

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    print('Token OK')
    os.makedirs('data', exist_ok=True)

    views_data = get_views(token)
    views = views_data.get('data', {}).get('views', [])
    print(f'Total views: {len(views)}')
    for v in views:
        print(f'  - {v.get("viewName")} ({v.get("viewId")})')

    seg_id = next((v.get('viewId') for v in views if v.get('viewName') == 'Segmentación acumulada Total'), None)
    trans_id = next((v.get('viewId') for v in views if v.get('viewName') == 'Transiciones de segmentos Total'), None)

    if seg_id:
        seg = export_data(token, seg_id)
        with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
            json.dump(seg, f, ensure_ascii=False, indent=2)
        print(f'{len(seg)} filas en segmentacion.json')
    else:
        print('Segmentación no encontrada')
        with open('data/segmentacion.json', 'w') as f:
            json.dump([], f)

    if trans_id:
        trans = export_data(token, trans_id)
        with open('data/transiciones.json', 'w', encoding='utf-8') as f:
            json.dump(trans, f, ensure_ascii=False, indent=2)
        print(f'{len(trans)} filas en transiciones.json')
    else:
        print('Transiciones no encontrada')
        with open('data/transiciones.json', 'w') as f:
            json.dump([], f)

if __name__ == '__main__':
    main()
