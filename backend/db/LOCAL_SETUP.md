# Local Database Setup

## Prerequisites

- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop/))

## Start Postgres

```bash
docker run -d \
  --name borough-postgres \
  -e POSTGRES_USER=borough \
  -e POSTGRES_PASSWORD=borough \
  -e POSTGRES_DB=borough \
  -p 5432:5432 \
  -v borough_pgdata:/var/lib/postgresql/data \
  postgres:15
```

This creates a container with:
- User: `borough`
- Password: `borough`
- Database: `borough`
- Port: `5432` (mapped to localhost)
- Data persisted in a Docker volume (`borough_pgdata`)

## Create Tables

Tables are created automatically when the app starts, or manually:

```bash
cd Borough
python -c "
import asyncio
from backend.db.connection import DatabaseProvider

async def main():
    provider = DatabaseProvider()
    await provider.initialize_tables()
    print('Tables created.')
    await provider.dispose()

asyncio.run(main())
"
```

## Container Management

```bash
docker ps                        # confirm running
docker logs borough-postgres     # check logs
docker stop borough-postgres     # stop
docker start borough-postgres    # restart
docker rm borough-postgres       # remove container (volume persists)
docker volume rm borough_pgdata  # remove data permanently
```

## Connect via psql

```bash
docker exec -it borough-postgres psql -U borough -d borough
```

Useful commands inside psql:

```sql
\dt                              -- list all tables
\d properties                    -- describe a table
SELECT * FROM properties LIMIT 10;
SELECT COUNT(*) FROM building_violations;
\q                               -- quit
```

## GUI Options

### pgAdmin (browser-based)

```bash
docker run -d --name borough-pgadmin \
  -e PGADMIN_DEFAULT_EMAIL=admin@borough.dev \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 \
  dpage/pgadmin4
```

Open `http://localhost:5050`, log in with `admin@borough.dev` / `admin`, add a server:
- Host: `host.docker.internal`
- Port: `5432`
- User: `borough`
- Password: `borough`

### DBeaver (desktop app)

Download from [dbeaver.io](https://dbeaver.io). Create a PostgreSQL connection with the same credentials.

### VS Code Extension

Install "Database Client" by Weijan Chen. Connect to `localhost:5432` with user/password `borough`/`borough`.

## Connection String

```
postgresql+asyncpg://borough:borough@localhost:5432/borough
```

This is set via `POSTGRES_DSN` in `backend/data_pipeline/.env`. The `DatabaseProvider` falls back to this value if the env var is unset.
