# soa-rest

## General
This is a REST Flask-based service that handles users statistics in games and generates PDF reports with the accumulated data.

It uses RabbitMQ for the report creation. SQLite3 is used as DBMS. JWT authorization is supported. Password encryption supported.

Simply setup containers with Docker Compose (`docker-compose up -d`) and check the `examples` directory with a Jupyter Notebook that explains `requests`-based client side.

The applization is not fault-tolerant in current state, but you can mount the container's `/app/stats.db`, `/app/img/` and `/app/stats.db` to the host machine on demand in `docker-compose.yml`.

Statistics server image [is available on Docker Hub](https://hub.docker.com/repository/docker/haidaansko/soa-stats-server).

## REST API

* `GET /users` - list all users;
* `POST /users` - register a new user and receive a JWT token;
* `POST /login` - login and receive a JWT token;

##### JWT auth dependant
* `GET /users/{user_id}` - get user info; only self;
* `PATCH/PUT /users/{user_id}` - modify user info; only self;
* `DELETE /users/{user_id}` - delete user; only self;
* `GET /users/me` - get self info;

* `GET /users/{user_id}/stats` - return user's game statistics; only self;
* `PATCH/PUT /users/{user_id}/stats` - modify user's game statistics; only self;

* `POST /users/{user_id}/pdf` - generate pdf and save;
* `GET /users/{user_id}/pdf` - return pdf (binary) if exists;
