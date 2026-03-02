# Global Gaming

## Leaderboard REST API Service

Production-oriented REST API for a global gaming leaderboard. The service accepts score submissions per game, returns top-ranked users, and returns a user’s current rank with nearby leaderboard context.

## Why this design

- `FastAPI` provides a concise and strongly typed HTTP layer.
- `Postgres` is the source of truth for durable user high scores.
- `Redis` sorted sets provide fast leaderboard reads and neighborhood lookups.
- Cache drift is acceptable for the MVP because Redis can be rebuilt from Postgres for a single game on demand.

## Core behavior

- Scores are scoped by `game_id`.
- Highest score wins per user per game.
- Lower or equal submissions are accepted but do not replace the stored score.
- Ties use competition ranking: `1, 2, 2, 4`.
- User context returns a configurable window, defaulting to 2 users above and 2 below.

## Project structure

```text
leaderboard/
  app/
  alembic/
  docs/
  tests/
  .github/workflows/
  docker-compose.yml
  Dockerfile
  Makefile
```

## Local setup for this interview container

The container does not provide Docker or `systemd`, so the primary local workflow is:

- install Python dependencies with `pip`
- install `postgresql@16` and `redis` with Homebrew
- start Postgres and Redis manually
- point the app at the container's local Postgres user

### 1. Install Python dependencies

```bash
python3 -m pip install -r requirements-dev.txt
```

### 2. Install Postgres and Redis

```bash
brew install redis postgresql@16
```

### 3. Add Postgres binaries to `PATH`

```bash
export PATH="/home/linuxbrew/.linuxbrew/opt/postgresql@16/bin:$PATH"
```

### 4. Start Postgres manually

```bash
initdb -D /workspaces/leaderboard/.postgres-data
pg_ctl -D /workspaces/leaderboard/.postgres-data -l /workspaces/leaderboard/.postgres.log start
createdb leaderboard
```

### 5. Start Redis manually

```bash
redis-server --daemonize yes --dir /workspaces/leaderboard --logfile /workspaces/leaderboard/.redis.log
```

### 6. Create a local `.env`

Copy the example file:

```bash
cp .env.example .env
```

Then update the database URL so it uses the local container user created by `initdb`:

```env
LEADERBOARD_DATABASE_URL=postgresql+asyncpg://vscode@localhost:5432/leaderboard
LEADERBOARD_REDIS_URL=redis://localhost:6379/0
```

### 7. Run the migration

```bash
alembic upgrade head
```

### 8. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify locally

Use `jq` for readable output:

```bash
curl -s http://127.0.0.1:8000/health/live | jq
```

```bash
curl -s http://127.0.0.1:8000/health/ready | jq
```

```bash
curl -s -X POST http://127.0.0.1:8000/v1/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"alice","score":100}' | jq
```

```bash
curl -s -X POST http://127.0.0.1:8000/v1/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"bob","score":90}' | jq
```

```bash
curl -s -X POST http://127.0.0.1:8000/v1/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"carol","score":90}' | jq
```

```bash
curl -s "http://127.0.0.1:8000/v1/games/game_1/leaderboard?limit=10" | jq
```

```bash
curl -s "http://127.0.0.1:8000/v1/games/game_1/users/bob/context?window=2" | jq
```

### Stop local services

```bash
pg_ctl -D /workspaces/leaderboard/.postgres-data stop
```

```bash
redis-cli shutdown
```

## Optional Docker path

Docker support is included for a more standard local setup outside this constrained container:

```bash
docker compose up --build
```

## API endpoints

### Submit score

`POST /v1/games/{game_id}/scores`

Request:

```json
{
  "user_id": "user_123",
  "score": 9001
}
```

Response:

```json
{
  "game_id": "game_1",
  "user_id": "user_123",
  "submitted_score": 9001,
  "stored_score": 9001,
  "updated": true,
  "rank": 3
}
```

### Top leaderboard

`GET /v1/games/{game_id}/leaderboard?limit=10`

Response:

```json
{
  "game_id": "game_1",
  "limit": 10,
  "entries": [
    {
      "rank": 1,
      "user_id": "user_a",
      "score": 9999
    }
  ]
}
```

### User context

`GET /v1/games/{game_id}/users/{user_id}/context?window=2`

Response:

```json
{
  "game_id": "game_1",
  "user_id": "user_123",
  "rank": 42,
  "score": 9001,
  "window": 2,
  "above": [
    {
      "rank": 40,
      "user_id": "user_x",
      "score": 9050
    }
  ],
  "below": [
    {
      "rank": 43,
      "user_id": "user_y",
      "score": 8999
    }
  ]
}
```

### Health checks

GET /health/live
GET /health/ready

`/health/ready` validates both Postgres and Redis.

## Development commands

```bash
make install-dev
make migrate
make run
make test
make lint
```

## Testing strategy

- Unit tests cover competition ranking and service-level score semantics.
- Integration coverage includes API contract presence and is structured to expand with live dependency-backed tests.
- CI runs linting and tests on every push and pull request.

## Architecture notes

- Postgres holds canonical score rows keyed by `(game_id, user_id)`.
- Redis stores `leaderboard:{game_id}` sorted sets using `user_id` members and score values.
- Read endpoints serve from Redis first.
- If Redis is empty or missing a known user, the service rebuilds the game leaderboard from Postgres.
- Displayed rank is computed as `count(scores strictly greater than target_score) + 1`.

See [docs/architecture.md](/workspaces/leaderboard/docs/architecture.md) and [docs/architecture-diagram.svg](/workspaces/leaderboard/docs/architecture-diagram.svg).

## Tradeoffs and future improvements

- A single write currently updates Postgres first and Redis second. For the MVP, Postgres remains canonical and cache rebuilds handle drift.
- Authentication, rate limiting, and anti-cheat controls are intentionally excluded.
- A future iteration should add true end-to-end integration tests that run against live Postgres and Redis in CI and local Docker.
