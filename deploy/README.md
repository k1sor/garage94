# Garage94 - деплой проекта

Практическая работа №18. Развернул проект локально как на сервере: контейнеры, nginx,
HTTPS и локальный домен. В интернет ничего не публикуется, сайт открывается только с этого
компьютера.

Файлы деплоя (docker-compose.yml, nginx и сертификаты) лежат в отдельном репозитории
`garage94-deploy`. В этой папке остались отчет и скриншоты.

## Архитектура

Приложение на Flask, страницы рендерятся на сервере. Отдельного фронтенда нет. База данных
теперь PostgreSQL в Supabase, это внешний сервис, поэтому отдельного контейнера с базой нет.
При развертывании получается два контейнера: приложение и nginx.

```mermaid
flowchart LR
    B[Браузер] -->|HTTP :80| N[nginx]
    N -->|301| B
    B -->|HTTPS :443| N
    N -->|proxy_pass| A["app: Flask + Gunicorn :5000"]
    A -->|DATABASE_URL| D[(Supabase, PostgreSQL)]
```

Браузер открывает https://garage94.localhost. Запрос принимает nginx, он один доступен
снаружи. Дальше nginx передает запрос приложению на http://app:5000, приложение обращается
к базе в Supabase и отдает страницу обратно через nginx.

## Сервисы

| Сервис | Технология | Внутренний порт | Продакшен-сервер |
| --- | --- | --- | --- |
| app | Flask 3, Python 3.12 | 5000 | Gunicorn, 2 workers |
| nginx | nginx 1.30-alpine | 80, 443 | нет |
| db | Supabase, PostgreSQL | 5432 | нет |

Порты открыты только у nginx и только на 127.0.0.1, поэтому сайт доступен только с этого
компьютера. У app ключа ports нет, он виден только внутри сети Docker Compose.

## Переменные окружения и секреты

Только имена, без значений:

| Имя | Где задается | Зачем |
| --- | --- | --- |
| DEBUG | docker-compose.yml | режим отладки, тут False |
| DATABASE_URL | .env | строка подключения к Supabase |
| SITE_URL | .env | адрес сайта для sitemap и Open Graph |
| SECRET_KEY | .env | секретный ключ Flask |

Файл `.env` в репозиторий не попадает, он в `.gitignore`. В нем лежат строка подключения
из Supabase (Project Settings, Database, Connection string, режим URI) и ключ Flask.

Для запуска без Docker используются переменные из `.env` в корне проекта приложения,
пример лежит в `.env.example`: SECRET_KEY, DEBUG, DATABASE_URL, SITE_URL. Если `DATABASE_URL`
не задан, приложение использует SQLite, это нужно только для локальной разработки и тестов.

## Запуск и остановка

Оба репозитория клонируются в одну папку:

```bash
git clone https://github.com/k1sor/garage94
git clone https://github.com/k1sor/garage94-deploy
```

Команды выполняются в папке `garage94-deploy`:

```bash
docker compose up --build -d     # собрать и запустить
docker compose ps                # проверить состояние
docker compose logs app          # журнал приложения
docker compose logs nginx        # журнал nginx
docker compose down              # остановить
```

После первого запуска база пустая, каталог заполняется командой:

```bash
docker compose exec app flask seed
```

Если Supabase запущен локально, база поднимается командой `npx supabase db start` в папке
проекта. Строка подключения тогда выглядит как
`postgresql://postgres:postgres@host.docker.internal:54322/postgres`.

Сайт открывается по адресу https://garage94.localhost. Если открыть http, будет редирект
301 на https.

Сертификат выпущен через mkcert:

```bash
mkcert -cert-file garage94.localhost.pem -key-file garage94.localhost-key.pem garage94.localhost
```

## Скриншоты

- `screenshots/docker_compose_ps.png` - вывод docker compose ps;
- `screenshots/site_https.png` - сайт по адресу https://garage94.localhost, в адресной
  строке замок;
- `screenshots/network_headers.png` - вкладка Network с запросом и заголовками ответа;
- `screenshots/docker_desktop_containers.png` - контейнеры в Docker Desktop с портами.

## Ошибки и как исправил

1. `failed to connect to the docker API ... dockerDesktopLinuxEngine` - Docker Desktop
   не был запущен. Запустил Docker Desktop и подождал, пока заработает демон.
2. `sqlite3.OperationalError: table users already exists` - на первом запуске с SQLite два
   воркера Gunicorn одновременно создавали таблицы. Контейнер перезапустился сам, потому
   что стоит `restart: unless-stopped`, со второго раза приложение поднялось.
3. `curl: schannel: CRYPT_E_NO_REVOCATION_CHECK` - у локального центра сертификации mkcert
   нет списков отзыва. В браузере сайт открывается без предупреждений, а для curl
   использовал флаг `--ssl-no-revoke`.
4. Docker Desktop один раз завершился во время работы, контейнеры остановились и браузер
   показывал `ERR_CONNECTION_REFUSED`. Запустил Docker Desktop заново и выполнил
   `docker compose up -d`.
5. После подключения Supabase приложение не стартовало, пока не установлен драйвер
   PostgreSQL. Добавил `psycopg[binary]` в `requirements.txt` и пересобрал образ.
6. Если поменять код приложения, образ надо пересобрать командой
   `docker compose up --build -d`, иначе изменения не появятся.

## Что поменять для публикации на реальном сервере

- арендовать сервер или хостинг и поставить туда Docker;
- зарегистрировать настоящий домен и сделать A-запись на IP сервера;
- получить сертификат в Let's Encrypt через Certbot и прописать его в nginx;
- убрать 127.0.0.1 у портов nginx, чтобы сайт был доступен из сети;
- создать проект в облачном Supabase, взять строку подключения и положить ее в `.env`;
- хранить SECRET_KEY не в локальном файле, а в хранилище секретов;
- настроить CD, чтобы сервер сам забирал готовый образ из реестра и перезапускал контейнер.

CI обязательный: `.github/workflows/docker-build.yml` в репозитории приложения при push,
pull request и ручном запуске проверяет, что Docker-образ собирается. Публикацию образа
в реестр и обновление проекта из реестра (CD) в этой работе не делал, это дополнительное
задание.
