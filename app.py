from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import time

app = FastAPI()

DATA_FILE = '../clicker_data.json'

# --- Вспомогательные функции ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_user(user_id):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            'score': 0,
            'upgrades': {},
            'last_auto_click': time.time(),
            'boost_until': 0
        }
        save_data(data)
    return data[str(user_id)]

def update_user(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

# --- API ---
@app.get('/api/status')
def status():
    return {'status': 'ok'}

@app.get('/api/get')
def get(user_id: str):
    user = get_user(user_id)
    return user

@app.post('/api/click')
def click(request: Request):
    user_id = request.query_params['user_id']
    user = get_user(user_id)
    mult = 1 + user['upgrades'].get('multiplier', 0)
    if user.get('boost_until', 0) > time.time():
        mult *= 3
    user['score'] += mult
    update_user(user_id, user)
    return {'score': user['score'], 'multiplier': mult}

@app.post('/api/upgrade')
def upgrade(request: Request):
    user_id = request.query_params['user_id']
    upgrade_type = request.query_params['type']
    user = get_user(user_id)
    costs = {'auto_click': 100, 'multiplier': 200, 'boost': 300}
    if user['score'] >= costs[upgrade_type]:
        user['score'] -= costs[upgrade_type]
        user['upgrades'][upgrade_type] = user['upgrades'].get(upgrade_type, 0) + 1
        if upgrade_type == 'boost':
            user['boost_until'] = time.time() + 120
        update_user(user_id, user)
        return {'success': True, 'score': user['score']}
    return {'success': False, 'score': user['score']}

# --- Статика (frontend) ---
app.mount('/', StaticFiles(directory='static', html=True), name='static') 