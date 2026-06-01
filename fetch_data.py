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
    print('Token response:', r.json())
    return r.json()['access_token']

def get_table_data(access_token, table_name):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    # Listar todas las vistas del workspace
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views'
    r = requests.get(url, headers=headers)
    print(f'Views response for {table_name}:', r.status_code, r.text[:500])
    data = r.json()
    views = data.get('data', {}).get('views', [])
    view_id = None
    for v in views:
        if v.get('viewName') == table_name:
            view_id = v.get('viewId')
            break
    if not view_id:
        print(f'Vista no encontrada: {table_name}')
        print('Vistas disponibles:', [v.get('viewName') for v in views])
        return []
    # Exportar datos
    export_url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{view_id}'
    params = {'action': 'export', 'config': json.dumps({'fileType': 'json', 'responseFormat': 'json'})}
    r = requests.get(export_url, headers=headers, params=params)
    print(f'Export response {table_name}:', r.status_code, r.text[:500])
    try:
        return r.json()
    except:
        return []

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    os.makedirs('data', exist_ok=True)

    print('Obteniendo Segmentación acumulada Total...')
    seg = get_table_data(token, 'Segmentación acumulada Total')
    with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)

    print('Obteniendo Transiciones de segmentos Total...')
    trans = get_table_data(token, 'Transiciones de segmentos Total')
    with open('data/transiciones.json', 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
