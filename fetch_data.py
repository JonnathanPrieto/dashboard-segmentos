import requests
import json
import os
import time

REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
CLIENT_ID = os.environ['ZOHO_SELF_CLIENT_ID']
CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ORG_ID = '2917853000000155002'
WORKSPACE_ID = '2917853000007172372'

def get_access_token():
    print('Obteniendo access token...')
    r = requests.post('https://accounts.zoho.com/oauth/v2/token', data={
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token'
    })
    token = r.json().get('access_token')
    if not token:
        raise Exception(f'Error obteniendo token: {r.text}')
    print('Token OK')
    return token

def get_view_id(token, table_name):
    url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views'
    headers = {
        'Authorization': f'Zoho-oauthtoken {token}',
        'ZANALYTICS-ORGID': ORG_ID
    }
    r = requests.get(url, headers=headers)
    views = r.json().get('data', {}).get('views', [])
    for v in views:
        if v.get('viewName') == table_name:
            return v.get('viewId')
    raise Exception(f'No se encontró la vista: {table_name}')

def export_async(token, view_id, table_name):
    """Inicia exportación asíncrona y espera el resultado."""
    headers = {
        'Authorization': f'Zoho-oauthtoken {token}',
        'ZANALYTICS-ORGID': ORG_ID
    }

    # 1. Iniciar el export asíncrono
    export_url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{view_id}/data'
    params = {
        'config': json.dumps({
            'responseFormat': 'json',
            'exportType': 'asynch'
        })
    }
    print(f'Iniciando export asíncrono: {table_name}...')
    r = requests.get(export_url, headers=headers, params=params)
    result = r.json()

    if result.get('status') == 'failure':
        raise Exception(f'Error iniciando export: {result}')

    job_id = result.get('data', {}).get('jobId')
    if not job_id:
        raise Exception(f'No se obtuvo jobId: {result}')

    print(f'JobId obtenido: {job_id}. Esperando...')

    # 2. Polling hasta que el job termine
    status_url = f'https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/exportjobs/{job_id}'
    for attempt in range(30):  # máximo ~5 minutos
        time.sleep(10)
        r = requests.get(status_url, headers=headers)
        job = r.json().get('data', {})
        status = job.get('jobStatus')
        print(f'  Intento {attempt + 1}: status={status}')

        if status == 'JOB_COMPLETED':
            download_url = job.get('downloadUrl')
            if not download_url:
                raise Exception('Job completado pero sin downloadUrl')
            break
        elif status in ('JOB_FAILURE', 'JOB_FAILED'):
            raise Exception(f'Job fallido: {job}')
    else:
        raise Exception('Timeout esperando el job de exportación')

    # 3. Descargar el resultado
    print(f'Descargando datos...')
    r = requests.get(download_url, headers=headers)
    result = r.json()

    rows = result.get('data', {}).get('rows', [])
    cols = result.get('data', {}).get('columns', [])
    col_names = [c['columnName'] for c in cols]
    records = [dict(zip(col_names, row)) for row in rows]
    print(f'{len(records)} filas obtenidas de {table_name}')
    return records

def main():
    token = get_access_token()
    os.makedirs('data', exist_ok=True)

    # Segmentación
    print('\nConsultando Segmentación acumulada Total...')
    view_id = get_view_id(token, 'Segmentación acumulada Total')
    seg = export_async(token, view_id, 'Segmentación acumulada Total')
    with open('data/segmentacion.json', 'w', encoding='utf-8') as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    print(f'{len(seg)} filas en segmentacion.json')

    # Transiciones
    print('\nConsultando Transiciones de segmentos Total...')
    view_id = get_view_id(token, 'Transiciones de segmentos Total')
    trans = export_async(token, view_id, 'Transiciones de segmentos Total')
    with open('data/transiciones.json', 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)
    print(f'{len(trans)} filas en transiciones.json')

if __name__ == '__main__':
    main()
