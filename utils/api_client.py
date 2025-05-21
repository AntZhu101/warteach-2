import os
import aiohttp

# URL вашего API (можно брать из .env или задавать здесь)
API_URL = os.getenv('API_URL', 'http://192.168.0.249:8000/api/employees/')

# Замените '<YOUR_TOKEN_HERE>' на реальный токен или задайте через переменные окружения
API_TOKEN = os.getenv('API_TOKEN', 'bf685ad3a4485265532a88de9ef1829143a9c747')

async def upsert_employee(data: dict) -> dict:
    headers = {
        'Authorization': f'Token {API_TOKEN}',
        'Content-Type': 'application/json',
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=data, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

async def get_mentors(city: str, role: str = "mentor") -> list:
    """
    Возвращает список сотрудников с заданным городом и ролью.
    """
    params = {'city': city, 'role': role}
    headers = {
        'Authorization': f'Token {API_TOKEN}',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()