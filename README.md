# Proc Gaze — трекинг взгляда

### Запуск

```bash
docker compose up --build
```

### Открыть фронтенд

После запуска фронтенд доступен по адресу:

> **http://localhost/main**

### Полезные адреса

| Сервис           | URL                          |
|------------------|------------------------------|
| Фронтенд        | http://localhost/main         |
| Backend API      | http://localhost:8000         |
| RabbitMQ UI      | http://localhost:15672        |

### Логи

```bash
docker compose logs -f
```

### Остановка

```bash
docker compose down
```

Остановить и удалить данные (БД, volumes):

```bash
docker compose down -v
```

