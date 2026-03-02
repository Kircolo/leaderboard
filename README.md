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

The container does not provide Docker or `systemd`, so the primary local workflow uses Homebrew-installed Postgres and Redis plus repo-local automation.

### 1. Install Python dependencies

```bash
python3 -m pip install -r requirements-dev.txt
```

### 2. Install Postgres and Redis

```bash
brew install redis postgresql@16
```

### 3. Run environment checks

```bash
make doctor
```

### 4. Bootstrap the local environment

```bash
make bootstrap
```

This will:

- initialize `.postgres-data/` on first run
- start Postgres and Redis if they are not already running
- create `.env` if it does not exist
- set `LEADERBOARD_DATABASE_URL` for the current local user
- run `alembic upgrade head`

### 5. Start the API

```bash
make dev
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
curl -s -X POST http://127.0.0.1:8000/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"platform":"steam","user_id":"alice","score":100}' | jq
```

```bash
curl -s -X POST http://127.0.0.1:8000/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"platform":"psn","user_id":"bob","score":90}' | jq
```

```bash
curl -s -X POST http://127.0.0.1:8000/games/game_1/scores \
  -H 'Content-Type: application/json' \
  -d '{"platform":"xbox","user_id":"carol","score":90}' | jq
```

```bash
curl -s "http://127.0.0.1:8000/games/game_1/leaderboard?limit=10" | jq
```

```bash
curl -s "http://127.0.0.1:8000/games/game_1/platforms/psn/users/bob/context?window=2" | jq
```

### Stop local services

```bash
make infra-down
```

```bash
make clean
```

`make clean` stops Postgres and Redis, removes the local Postgres data directory, deletes local log files, and clears Python cache artifacts.

## Optional Docker path

Docker support is included for a more standard local setup outside this constrained container:

```bash
docker compose up --build
```

## API endpoints

### Submit score

`POST /games/{game_id}/scores`

Request:

```json
{
  "platform": "steam",
  "user_id": "user_123",
  "score": 9001
}
```

Response:

```json
{
  "game_id": "game_1",
  "platform": "steam",
  "user_id": "user_123",
  "submitted_score": 9001,
  "stored_score": 9001,
  "updated": true,
  "rank": 3
}
```

### Top leaderboard

`GET /games/{game_id}/leaderboard?limit=10`

Response:

```json
{
  "game_id": "game_1",
  "limit": 10,
  "entries": [
    {
      "rank": 1,
      "platform": "steam",
      "user_id": "user_a",
      "score": 9999
    }
  ]
}
```

### User context

`GET /games/{game_id}/platforms/{platform}/users/{user_id}/context?window=2`

Response:

```json
{
  "game_id": "game_1",
  "platform": "psn",
  "user_id": "user_123",
  "rank": 42,
  "score": 9001,
  "window": 2,
  "above": [
    {
      "rank": 40,
      "platform": "steam",
      "user_id": "user_x",
      "score": 9050
    }
  ],
  "below": [
    {
      "rank": 43,
      "platform": "xbox",
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

- Postgres holds canonical score rows keyed by `(game_id, platform, user_id)`.
- Redis stores `leaderboard:{game_id}` sorted sets using a composite `platform|user_id` member and score values.
- Read endpoints serve from Redis first.
- If Redis is empty or missing a known user, the service rebuilds the game leaderboard from Postgres.
- Displayed rank is computed as `count(scores strictly greater than target_score) + 1`.

See [ARCHITECTURE_FLOW_DIAGRAM.md](ARCHITECTURE_FLOW_DIAGRAM.md), [docs/architecture.md](docs/architecture.md), and [docs/architecture-diagram.svg](docs/architecture-diagram.svg).

## Tradeoffs and future improvements

- A single write currently updates Postgres first and Redis second. For the MVP, Postgres remains canonical and cache rebuilds handle drift.
- Authentication, rate limiting, and anti-cheat controls are intentionally excluded.
- A future iteration should add true end-to-end integration tests that run against live Postgres and Redis in CI and local Docker.
