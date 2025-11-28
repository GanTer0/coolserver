# from fastapi.testclient import TestClient
# from main import app
# import requests

# client = TestClient(app)

# class Test_get_html_point:
#     def test_server_is_online(self):
#         """Проверяем что реальный сервер выключен"""
#         try:
#             response = requests.get("http://localhost:8000/", timeout=2)
#             print('Сервер запущен')
#         except:
#             print('Сервер не запущен')

#     def test_main_page(self):
#         """проверяет что главная страница отвечает"""
#         response = client.get("/")
#         assert response.status_code == 200, 'запрос на главную страницу не удался'

#     def test_registration_page(self):
#         """проверяет что страница регистрации отвечает на get запрос"""
#         response = client.get("/registration")
#         assert response.status_code == 200, 'get запрос на страницу регистрации не удался'

# class Test_email_validation:
#     def test_repeat_email(self):
#         """Тест на уже существующую почту"""
#         response = client.post("/registration", data={
#             "email": "test@gmail.com",
#             "password": "12345678",
#             "repeat_password": "12345678"
#         })
#         data = response.json()
#         assert data["error"] == 'Эта почта уже используется'
