import requests
import json
import os
import time

REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
CLIENT_ID = os.environ['ZOHO_SELF_CLIENT_ID']
CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ORG_ID = '855872271'
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
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views'
    r = requests.get(url, headers=headers)
    return r.json()

def export_data_async(access_token, view_id):
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    # Iniciar exportación asíncrona
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{view_id}/data'
    params = {'config': json.dumps({'responseFormat': 'json', 'exportType': 'async'})}
    r = requests.get(url, headers=headers, params=params)
    print(f'Async export init: {r.status_code} {r.text[:200]}')
    result = r.json()
    job_id = result.get('data', {}).get('jobId')
    if not job_id:
        # Intentar exportación CSV directa
        params2 = {'config': json.dumps({'fileType': 'csv'})}
        r2 = requests.get(url, headers=headers, params=params2)
        print(f'CSV export: {r2.status_code} {r2.text[:200]}')
        if r2.status_code == 200 and r2.text:
            lines = r2.text.strip().split('\n')
            if len(lines) < 2:
                return []
            cols = [c.strip('"') for c in lines[0].split(',')]
            rows = []
            for line in lines[1:]:
                vals = [v.strip('"') for v in line.split(',')]
                rows.append(dict(zip(cols, vals)))
            return rows
        return []
    # Esperar y descargar
    job_url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/exportjobs/{job_id}'
    for _ in range(10):
        time.sleep(3)
        rj = requests.get(job_url, headers=headers)
        job = rj.json()
        status = job.get('data', {}).get('status')
        print(f'Job status: {status}')
        if status == 'completed':
            dl_url = job.get('data', {}).get('downloadUrl')
            rd = requests.get(dl_url, headers=headers)
            return rd.json()
        elif status == 'failed':
            return []
    return []

def main():
    print('Obteniendo access token...')
    token = get_access_token()
    print('Token OK')
    os.makedirs('data', exist_ok=True)

    views_data = get_views(token)
    views = views_data.get('data', {}).get('views', [])

    seg_id = next((v.get('viewId') for v in views if v.get('viewName') == 'Segmentación acumulada Total'), None)
    trans_id = next((v.get('viewId') for v in views if v.get('viewName') == 'Transiciones de segmentos Total'), None)

    print(f'seg_id: {seg_id}, trans_id: {trans_id}')

    if seg_id:
        seg = export_data_async(token, seg_id)
        with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
            json.dump(seg, f, ensure_ascii=False, indent=2)
        print(f'{len(seg)} filas en segmentacion.json')
    else:
        with open('data/segmentacion.json', 'w') as f:
            json.dump([], f)

    if trans_id:
        trans = export_data_async(token, trans_id)
        with open('data/transiciones.json', 'w', encoding='utf-8') as f:
            json.dump(trans, f, ensure_ascii=False, indent=2)
        print(f'{len(trans)} filas en transiciones.json')
    else:
        with open('data/transiciones.json', 'w') as f:
            json.dump([], f)

if __name__ == '__main__':
    main()
