from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import time
import random
from datetime import datetime

app = FastAPI()

DATA_FILE = 'clicker_data.json'

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
            'boost_until': 0,
            'clicks': 0,
            'last_daily': '',
            'chest_ready': 0,
            'achievements': [],
            'theme': 'default'
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
    is_crit = False
    # Крит-клик 10% шанс
    if random.random() < 0.1:
        mult *= 5
        is_crit = True
    if user.get('boost_until', 0) > time.time():
        mult *= 3
    user['score'] += mult
    user['clicks'] = user.get('clicks', 0) + 1
    # Сундук раз в 50 кликов
    chest = False
    if user['clicks'] % 50 == 0:
        user['chest_ready'] = 1
        chest = True
    # Ачивки
    new_ach = None
    if user['clicks'] == 100 and '100_clicks' not in user['achievements']:
        user['achievements'].append('100_clicks')
        new_ach = '100_clicks'
    if user['upgrades'].get('multiplier', 0) >= 10 and '10_mult' not in user['achievements']:
        user['achievements'].append('10_mult')
        new_ach = '10_mult'
    update_user(user_id, user)
    return {'score': user['score'], 'multiplier': mult, 'is_crit': is_crit, 'chest': chest, 'new_ach': new_ach}

@app.post('/api/chest')
def open_chest(request: Request):
    user_id = request.query_params['user_id']
    user = get_user(user_id)
    if user.get('chest_ready', 0):
        prize = random.choice(['score', 'boost', 'upgrade'])
        msg = ''
        if prize == 'score':
            amount = random.randint(50, 200)
            user['score'] += amount
            msg = f'+{amount} очков!'
        elif prize == 'boost':
            user['boost_until'] = time.time() + 60
            msg = 'Буст x3 на 1 минуту!'
        elif prize == 'upgrade':
            upg = random.choice(['auto_click', 'multiplier'])
            user['upgrades'][upg] = user['upgrades'].get(upg, 0) + 1
            msg = f'Бесплатный апгрейд: {upg}!'
        user['chest_ready'] = 0
        update_user(user_id, user)
        return {'success': True, 'msg': msg}
    return {'success': False, 'msg': 'Нет сундука'}

@app.post('/api/daily')
def daily(request: Request):
    user_id = request.query_params['user_id']
    user = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    if user.get('last_daily', '') != today:
        user['score'] += 100
        user['last_daily'] = today
        update_user(user_id, user)
        return {'success': True, 'msg': '+100 очков за ежедневный бонус!'}
    return {'success': False, 'msg': 'Бонус уже получен'}

@app.post('/api/theme')
def set_theme(request: Request):
    user_id = request.query_params['user_id']
    theme = request.query_params['theme']
    user = get_user(user_id)
    user['theme'] = theme
    update_user(user_id, user)
    return {'success': True}

@app.get('/api/themes')
def get_themes():
    return {'themes': ['default', 'dark', 'neon', 'sunset']}

# --- Статика (frontend) ---
app.mount('/', StaticFiles(directory='static', html=True), name='static') 