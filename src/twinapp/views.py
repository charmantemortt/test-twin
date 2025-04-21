import os
import json
import time
import logging
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from telegram import Bot
from telegram.utils.request import Request

from .environ import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TWIN_EMAIL,
    TWIN_PASSWORD,
    TWIN_SCENARIO_ID,
    TWIN_CALLER_ID,
    TWIN_WEBHOOK_URL,
)

LOG_PATH = os.path.join(os.path.dirname(__file__), 'twin_debug.log')
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

bot = Bot(token=TELEGRAM_BOT_TOKEN, request=Request())

def get_twin_token():
    logging.info("Получение токена от TWIN...")
    try:
        response = requests.post("https://iam.twin24.ai/api/v1/auth/login", json={
            "email": TWIN_EMAIL,
            "password": TWIN_PASSWORD,
            "ttl": 3600
        })
        logging.info(f"Ответ авторизации: {response.status_code} — {response.text}")
        if response.status_code == 200:
            return response.json().get("token")
    except Exception as e:
        logging.error(f"Ошибка при получении токена: {e}")
    return None

def launch_twin_call(name, phone):
    logging.info(f"Запуск обзвона для {name}, номер: {phone}")
    token = get_twin_token()
    if not token:
        logging.error("Токен не получен. Прерывание.")
        return

    job_payload = {
        "name": f"Обзвон от {name}",
        "defaultExec": "robot",
        "defaultExecData": TWIN_SCENARIO_ID,
        "secondExec": "end",
        "cidType": "gornum",
        "cidData": TWIN_CALLER_ID,
        "startType": "manual",
        "cps": 1.01,
        "webhookUrls": [TWIN_WEBHOOK_URL],
        "additionalOptions": {
            "fullListMethod": "reject",
            "fullListTime": 30,
            "recordCall": True,
            "recTrimLeft": 0
        },
        "redialStrategyOptions": {
            "redialStrategyEn": False,
            "busy": {"redial": False},
            "noAnswer": {"redial": False},
            "answerMash": {"redial": False},
            "congestion": {"redial": False},
            "answerNoList": {"redial": False}
        }
    }

    try:
        logging.info(f"Создание задания payload: {json.dumps(job_payload, indent=2, ensure_ascii=False)}")
        job_resp = requests.post(
            "https://cis.twin24.ai/api/v1/telephony/autoCall",
            headers={"Authorization": f"Bearer {token}"},
            json=job_payload
        )
        logging.info(f"Ответ создания задания: {job_resp.status_code} — {job_resp.text}")
    except Exception as e:
        logging.error(f"Ошибка при создании задания: {e}")
        return

    job_id = job_resp.json().get("id", {}).get("identity")
    if not job_id:
        logging.error("Не удалось получить job_id. Завершение.")
        return

    time.sleep(5)

    candidate_payload = {
        "batch": [{
            "phone": [phone],
            "variables": {
                "имя": name
            },
            "autoCallId": job_id
        }],
        "forceStart": True
    }

    try:
        logging.info(f"Добавление кандидатов payload: {json.dumps(candidate_payload, indent=2, ensure_ascii=False)}")
        candidate_resp = requests.post(
            "https://cis.twin24.ai/api/v1/telephony/autoCallCandidate/batch",
            headers={"Authorization": f"Bearer {token}"},
            json=candidate_payload
        )
        logging.info(f"Ответ добавления кандидатов: {candidate_resp.status_code} — {candidate_resp.text}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении кандидатов: {e}")
    else:
        logging.info(f"Кандидат успешно добавлен в задание {job_id}")

def form_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        logging.info(f"Форма отправлена: имя={name}, номер={phone}")
        launch_twin_call(name, phone)
        return render(request, "form.html", context={"success": True})
    return render(request, "form.html")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def twin_webhook(request):
    if request.method == "POST":
        try:
            payload = request.body.decode('utf-8')
            print(payload)
            data = json.loads(payload)
            print(data)
        except json.JSONDecodeError:
            logging.error("Ошибка парсинга JSON в webhook")
            return JsonResponse({"error": "invalid JSON"}, status=400)

        logging.info(f"Webhook пришёл: {json.dumps(data, indent=2, ensure_ascii=False)}")

        try:
            result = data.get("result", {})
            call_status = data.get("status", "unknown")

            name = result.get("Имя", result.get("initialVariables", {}).get("имя", "Не указано")).strip()
            color = result.get("Цвет", result.get("initialVariables", {}).get("цвет", "Не указан")).strip()
            phone = result.get("initialVariables", {}).get("phone", "Не указан")

            logging.info(f"Извлечено: имя={name}, цвет={color}, номер={phone}")

            if call_status == "call_finished":
                message = (
                    f"Результат звонка:\n\n"
                    f"Имя: {name}\n"
                    f"Цвет: {color}\n"
                    f"Номер: {phone}\n"
                    f"Статус: Звонок завершён"
                )
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                logging.info(f"Telegram отправлено: {message}")

            if result.get("confirmation") == "есть_цвет":
                text = f"{name}\n{color}\n{phone}"
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
                logging.info(f"Telegram отправлено (подтверждение цвета): {text}")
            else:
                logging.info("Webhook получен без подтверждения цвета")

        except Exception as e:
            logging.error(f"Ошибка в webhook: {e}")
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Ошибка обработки webhook: {str(e)}")

        return JsonResponse({"status": "ok"}, status=200)

    return JsonResponse({"status": "twin webhook active"}, status=200)
