"""Точка входа в бота."""
# import vk_api

# # Твой токен сообщества
# TOKEN = 'vk1.a.He0WtlilSPgweUd6rljYEgRgNTn554hPiXLtiLOy1Yd3r7OowVKjFWvc69epozuejaCQbc_95GLulS1MOuLqP-B51PAJpxZlRmT-dy_48YokM6oUPtrQVrkSYNKUdgXTVB-57DCiBKVdRyufeyFxJx6u53yaYVuMfIzRx5PtNsNw5BoSIvPFUfcSQZfgq3L3aTrs_NHTPjgmecWSE5-ZdA'
# # Буквенный адрес группы (без https://vk.com/)
# GROUP_SHORT_NAME = 'club240686337'

# # Инициализация API
# vk = vk_api.VkApi(token=TOKEN)
# api = vk.get_api()

# # Получаем информацию о группе
# try:
#     group_info = api.groups.getById(group_id=GROUP_SHORT_NAME)
#     numeric_id = group_info[0]['id']
#     print(f"✅ Числовой ID группы: {numeric_id}")
#     print(f"📝 Название: {group_info[0]['name']}")
# except Exception as e:
#     print(f" Ошибка: {e}")



# import requests


# class VK:

#    def __init__(self, access_token, user_id, version='5.199'):
#        self.token = access_token
#        self.id = user_id
#        self.version = version
#        self.params = {'access_token': self.token, 'v': self.version}


#    def users_info(self):
#        url = 'https://api.vk.com/method/users.get'
#        params = {'user_ids': self.id}
#        response = requests.get(url, params={**self.params, **params})
#        return response.json()

# access_token = 'vk1.a.He0WtlilSPgweUd6rljYEgRgNTn554hPiXLtiLOy1Yd3r7OowVKjFWvc69epozuejaCQbc_95GLulS1MOuLqP-B51PAJpxZlRmT-dy_48YokM6oUPtrQVrkSYNKUdgXTVB-57DCiBKVdRyufeyFxJx6u53yaYVuMfIzRx5PtNsNw5BoSIvPFUfcSQZfgq3L3aTrs_NHTPjgmecWSE5-ZdA'
# user_id = 'g_u_k_69'
# vk = VK(access_token, user_id)

# print(vk.users_info())