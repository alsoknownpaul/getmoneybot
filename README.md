# GetMoney Bot

Telegram бот для запроса и учёта денежных средств между админом и пользователем.

## Возможности

### Для пользователя (жена)
- Запрос средств с выбором суммы (кнопки или произвольная сумма)
- Добавление комментария к запросу
- Просмотр запросов за текущий/прошлый месяц со статистикой
- Отмена запроса (пока не отправлены средства)
- Подтверждение получения или сообщение о неполучении
- Напоминание админу

### Для админа (муж)
- Уведомления о новых запросах
- Одобрение с указанием ETA (когда будут отправлены)
- Мгновенная отправка без ETA
- Отклонение с возможностью указать причину
- Просмотр всех активных запросов

## Статусы запроса

```
pending → approved → sent → confirmed (получено)
   ↓         ↓        ↓
rejected  cancelled  disputed (спорный)
                        ↓
                       sent (повторно)
```

## Стек технологий

- **Python 3.12** + **aiogram 3.x**
- **PostgreSQL 16**
- **SQLAlchemy 2.0** + **asyncpg**
- **Docker Compose**
- **Terraform** + **Ansible** для инфраструктуры

## Быстрый старт (локально)

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USER/getmoney.git
cd getmoney

# Создать .env
cp env.example .env
# Заполнить BOT_TOKEN, ADMIN_USER_ID, USER_USER_ID, DB_PASSWORD

# Запустить
docker compose up -d --build

# Проверить логи
docker compose logs -f bot
```

## Развёртывание на Yandex Cloud

### Подготовка

1. **Создать Telegram бота**:
   - Открыть [@BotFather](https://t.me/BotFather)
   - Отправить `/newbot`
   - Сохранить токен

2. **Узнать Telegram user_id**:
   - Отправить любое сообщение [@userinfobot](https://t.me/userinfobot)
   - Записать ID для себя и жены

3. **Настроить Yandex Cloud**:
   ```bash
   # Установить CLI
   brew install yandex-cloud-cli
   
   # Инициализировать
   yc init
   
   # Получить данные для Terraform
   yc config get cloud-id
   yc config get folder-id
   ```

4. **Сгенерировать SSH-ключ**:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/getmoney -C "getmoney-bot"
   ```

### Terraform

```bash
cd infra/terraform

# Создать конфиг
cp terraform.tfvars.example terraform.tfvars
# Заполнить yc_token, yc_cloud_id, yc_folder_id

# Создать инфраструктуру
terraform init
terraform plan
terraform apply

# Сохранить IP
terraform output instance_external_ip
```

### Ansible

```bash
cd infra/ansible

# Обновить IP в inventory.yml
# ansible_host: <IP из terraform output>

# Настроить сервер
ansible-playbook playbook.yml
```

### Деплой бота

```bash
# SSH на сервер
ssh -i ~/.ssh/getmoney ubuntu@<IP>

# Перейти в директорию
cd /opt/getmoney

# Создать .env
cp env.example .env
nano .env
# Заполнить: BOT_TOKEN, ADMIN_USER_ID, USER_USER_ID, DB_PASSWORD

# Запустить
docker compose up -d --build

# Проверить
docker compose logs -f bot
```

## Обновление

```bash
ssh ubuntu@<IP>
cd /opt/getmoney
git pull
docker compose up -d --build
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы, показ главного меню |
| `/help` | Справка |
| `/id` | Показать свой Telegram ID |
| `/active` | (Админ) Показать активные запросы |

## Структура проекта

```
getmoney/
├── infra/
│   ├── terraform/          # Инфраструктура Yandex Cloud
│   └── ansible/            # Настройка сервера
├── src/getmoney/
│   ├── handlers/           # Telegram handlers
│   ├── keyboards/          # Inline keyboards
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Business logic
│   └── db/                 # Database utilities
├── alembic/                # Database migrations
├── tests/                  # Pytest tests
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Разработка

```bash
# Установить rye
curl -sSf https://rye-up.com/get | bash

# Установить зависимости
rye sync

# Запустить тесты
rye run pytest

# Форматирование
rye run black src tests
rye run ruff check src tests
```

## Лицензия

MIT
