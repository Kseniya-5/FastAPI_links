# API-сервис сокращения ссылок

Сервис позволяет пользователям сокращать длинные ссылки, управлять ими и самим добавлять дополнительное "сокращение" для ссылки при желании. Пользователь вводит длинный URL, сервис генерирует для него короткую ссылку, которую можно использовать для быстрого доступа.

## Описание базы данных
Создаем 4 таблицы в нашей БД links_db

![image](https://github.com/user-attachments/assets/d73d0dac-fdbe-4d04-8671-b35bb3589658)

## Таблица ссылок (links)
![image](https://github.com/user-attachments/assets/7f8a8870-31a3-46ea-9753-fb4790ed49e2)

Изначально данная таблица не содержит в себе никаких данных тк мы с ней еще не начали работу

![image](https://github.com/user-attachments/assets/adc236eb-2ec3-41f6-9292-5b9886e330ad)

## Работа ручек
1. Создание короткой ссылки `POST /links/shorten`

   Параметры запроса:

    * original_url - оригинальный URL
    * custom_alias - уникальный alias, для создания кастомных ссылок
    * expires_at - указание времени жизни ссылки в формате даты с точностью до минуты 

![image](https://github.com/user-attachments/assets/dd338e0f-acab-4690-b426-a64cdc64399f)

Тут показана отработки ошибок. В данном случае ошибка создания - короткая ссылка уже есть

![image](https://github.com/user-attachments/assets/79eaef4e-20d1-4b1a-90e6-1b85a8cb66a6)

Ошибка создания - такой alias уже есть

![image](https://github.com/user-attachments/assets/bb381e28-7f95-4503-9c07-e0a291b03293)

Смотрим на содержимое таблицы, после создания

![image](https://github.com/user-attachments/assets/59e1fb12-dfb1-4715-b9e9-53317d27648c)

2. Поиск ссылки по оригинальному URL `GET /links/search`

   Параметры запроса:

    * original_url - оригинальный URL

Пытаемся получить короткую ссылку или alias для полной ссылки

![image](https://github.com/user-attachments/assets/a24f7c9e-dd92-4088-bcd7-96a833beb851)

3. Перенаправляет на оригинальный URL `GET /links/{short_code}`

   Параметры запроса:

    * short_code - alias ссылки

![image](https://github.com/user-attachments/assets/1a950a87-8e33-444f-9698-9b61d323dccc)

Содержимое таблицы после перенаправления 

![image](https://github.com/user-attachments/assets/c1d2e3f1-2f7c-402f-982f-fe7cc2ed506d)

4. Обновляет URL `PUT /links/{short_code}`

   Параметры запроса:

    * short_code - alias ссылки
    * new_url - новый URL, к которому привязываем раннее созданный alias

Изменяем ссылку для конкретного short_code

![image](https://github.com/user-attachments/assets/252bd54b-f7e1-438d-9ff0-09d59c0f3f26)

5. Отображает оригинальный URL, возвращает дату создания, количество переходов, дату последнего использовани `GET /links/{short_code}/stats`

   Параметры запроса:

    * short_code - alias ссылки

Получаем информацию о ссылке из таблицы по short_code

![image](https://github.com/user-attachments/assets/4b4e961e-58e8-4728-9fd8-21d8292a7505)


6. Удаление ссылки по short_code `DELETE /links/delete_by_short_code/{short_code}`

   Параметры запроса:

    * short_code - alias ссылки

![image](https://github.com/user-attachments/assets/b1d4fbbc-457e-4ae1-8177-7d27b907121d)

Смотрим на результат удаления

![image](https://github.com/user-attachments/assets/a14121b2-aafa-4242-88d9-52930b024457)

Теперь создадим ссылку еще раз и воспользуемся удалением другим методом

7. Удаление ссылки по custom_alias `DELETE /delete_by_custom_alias/{custom_alias}`

    Параметры запроса:

    * custom_alias - уникальный alias, для создания кастомных ссылок

![image](https://github.com/user-attachments/assets/0595db64-22f8-48fd-af12-4fe6286e2ff7)

8. Фоновая очистка таблицы

Помимо всего, в приложении запущена фоновая очистка таблицы от "потухших ссылок", где expires_at < time.Now().

Запустить можно это двумя способами:
1) Локально и без докера:
    - создаем виртуальное окружение: python -m venv venv
    - включаем его : source venv/bin/activate
    - устанавливаем все зависимости: pip install -r requirements.txt
    - должна быть развернута база данных на localhost:5432
    - запускаем приложение: python main.py

2) Локальный запуск из контейнера:
    - билдим контейнер: docker build -t web-python .
    - должна быть развернута база данных на localhost:5432
    - запускаем контейнер: docker run -d --network host --name web web-python
