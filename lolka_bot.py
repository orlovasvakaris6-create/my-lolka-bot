import os
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Данные для настройки
LOLKA_TOKEN = "ODc0Mzk1MzczODE0Nzg1.zk6XxNpWxI8Tg6jH3EHH5nD-z4glNOm80lPLLKTnw20"
CHANNEL_ID = "874345569781760"
LOLKA_API_URL = "https://lolka.app"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Application(BaseModel):
    server: str
    roleType: str
    nick: str
    age: int
    discord: str
    social: str
    about: str
    xf_username: str = "Гость"
    xf_user_id: str = "0"


def send_lolka_request(endpoint, method="POST", payload=None):
    headers = {
        "Authorization": f"Bot {LOLKA_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{LOLKA_API_URL}{endpoint}"
    if method == "POST":
        return requests.post(url, json=payload, headers=headers)
    elif method == "PATCH":
        return requests.patch(url, json=payload, headers=headers)


@app.post("/api/apply")
async def create_apply(data: Application):
    profile_link = (
        f"https://funysmobileforum.sampproject.ru/members/{data.xf_user_id}/"
        if data.xf_user_id != "0"
        else data.xf_username
    )

    text_content = (
        f"📩 **{data.roleType} | {data.server}**\n\n"
        f"🌐 **Профиль:** {profile_link}\n"
        f"👤 **Ник:** {data.nick}\n"
        f"🎂 **Возраст:** {data.age}\n"
        f"💬 **Lolka Tag:** {data.discord}\n"
        f"🔗 **Связь:** {data.social}\n"
        f"📝 **О себе:** {data.about}\n\n"
        f"📌 **Статус:** 🟡 **Ожидает проверки**\n"
        f"────────────────────────\n"
        f"Реакции для админов: ⏳ (Рассмотрение) | ✅ (Одобрить) | ❌ (Отказать)"
    )

    payload = {"channel_id": CHANNEL_ID, "content": text_content}

    res = send_lolka_request(
        f"/channels/{CHANNEL_ID}/messages", method="POST", payload=payload
    )

    print(f"Ответ от Lolka API: Status {res.status_code}, Body: {res.text}")

    if res.status_code in [200, 201]:
        return {"status": "success", "lolka_response": res.text}
    return {"status": "error", "details": res.text}


@app.post("/lolka-webhook")
async def handle_reaction(request: Request):
    data = await request.json()

    if data.get("event") == "message_reaction_add":
        msg_id = data.get("message_id")
        channel_id = data.get("channel_id")
        emoji = data.get("emoji")
        user_name = data.get("username", "Администратор")

        new_status = ""
        if emoji == "⏳":
            new_status = f"⏳ **На рассмотрении** (Взял: {user_name})"
        elif emoji == "✅":
            new_status = f"🟢 **Одобрено** (Проверил: {user_name})"
        elif emoji == "❌":
            new_status = f"🔴 **Отказано** (Проверил: {user_name})"

        if new_status:
            update_payload = {
                "content": f"Решение вынесено!\n📌 **Новый статус:** {new_status}"
            }
            send_lolka_request(
                f"/channels/{channel_id}/messages/{msg_id}",
                method="PATCH",
                payload=update_payload,
            )

    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
