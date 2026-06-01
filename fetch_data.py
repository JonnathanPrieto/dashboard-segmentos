import requests
import json
import os
import time

REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
CLIENT_ID = os.environ['ZOHO_SELF_CLIENT_ID']
CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ORG_ID = '855872271'
WORKSPACE_ID = '2917853000000155002'
SEG_VIEW_ID = '2917853000007172106'
TRANS_VIEW_ID = '2917853000007985686'

def get_access_token():
    r = requests.post('https://accounts.zoho.com/oauth/v2/token', data={
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token'
    })
    return r.json()['access_token']

def export_view(access_token, view_id, name):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }

    # Iniciar exportación asíncrona
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{view_id}/data'
    params = {
        'config': json.dumps({'responseFormat': 'json'}),
        'exportType': 'async'
    }
    r = requests.get(url, headers=headers, params=params)
    print(f'{name} init: {r.status_code} {r.text[:400]}')

    try:
        result = r.json()
    except:
        print(f'{name} JSON parse error')
        return []

    job_id = result.get('data', {}).get('jobId')
    print(f'{name} jobId: {job_id}')

    if not job_id:
        print(f'{name} no jobId found')
        return []

    # Polling
    job_url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/exportjobs/{job_id}'
    for i in range(20):
        time.sleep(5)
        rj = requests.get(job_url, headers=headers)
        job_data = rj.json()
        status = job_data.get('data', {}).get('status', '')
        print(f'{name} job [{i}]: {status}')

        if status == 'completed':
            dl_url = job_data.get('data', {}).get('downloadUrl', '')
            if dl_url:
                rd = requests.get(dl_url, headers=headers)
                try:
                    data = rd.json()
                    rows = data.get('data', {}).get('rows', [])
                    cols = data.get('data', {}).get('columns', [])
                    if cols:
                        col_names = [c['columnName'] for c in cols]
                        return [dict(zip(col_names, row)) for row in rows]
                    return rows
                except:
                    return []
        elif status in ['failed', 'error']:
            print(f'{name} failed: {job_data}')
            return []

    return []

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    print('Token OK')
    os.makedirs('data', exist_ok=True)

    print('Exportando Segmentación acumulada Total...')
    seg = export_view(token, SEG_VIEW_ID, 'Segmentacion')
    with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    print(f'{len(seg)} filas en segmentacion.json')

    print('Exportando Transiciones de segmentos Total...')
    trans = export_view(token, TRANS_VIEW_ID, 'Transiciones')
    with open('data/transiciones.json', 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)
    print(f'{len(trans)} filas en transiciones.json')

if __name__ == '__main__':
    main()
