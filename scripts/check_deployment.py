"""Read-only smoke checks. Uses API_BASE_URL and optional SMOKE_ACCESS_TOKEN.
Keep access tokens in your environment, never command arguments or source files.
"""
import os
import sys
import httpx

base = os.environ.get('API_BASE_URL', '').rstrip('/')
if not base.startswith('https://'):
    sys.exit('Set API_BASE_URL to your deployed HTTPS backend origin.')
with httpx.Client(base_url=base, timeout=30) as client:
    for path in ['/health', '/ready']:
        response = client.get(path)
        if response.status_code != 200:
            sys.exit(f'FAIL {path}: HTTP {response.status_code}; check backend configuration and logs.')
        data = response.json()
        if path == '/ready' and data.get('ready') is not True:
            sys.exit('FAIL /ready did not confirm database readiness.')
        print(f'PASS {path}')
    response = client.get('/api/devices')
    if response.status_code != 401:
        sys.exit('FAIL unauthenticated device access must return 401.')
    print('PASS unauthenticated data access is denied')
    origin = os.environ.get('FRONTEND_ORIGIN', 'https://hariprakashcit.github.io')
    response = client.options('/api/devices', headers={
        'Origin': origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization',
    })
    if response.headers.get('access-control-allow-origin') != origin:
        sys.exit('FAIL CORS: the published frontend origin is not permitted.')
    print('PASS published frontend origin is permitted')
    token = os.environ.get('SMOKE_ACCESS_TOKEN')
    if token:
        for path in ['/api/devices', '/api/profile', '/api/sessions', '/api/reports']:
            response = client.get(path, headers={'Authorization': 'Bearer '+token})
            if response.status_code != 200:
                sys.exit(f'FAIL authenticated {path}: HTTP {response.status_code}.')
            print(f'PASS authenticated {path}')
    else:
        print('Authenticated data and ESP32 ingestion still require a signed-in account and physical rehearsal.')
