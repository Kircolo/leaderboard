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
- Users are identified per game by `(platform, user_id)`.
- Highest score wins per user-platform pair per game.
- Lower or equal submissions are accepted but do not replace the stored score.
- Ties use competition ranking: `1, 2, 2, 4`.
- User context returns a configurable window, defaulting to 2 users above and 2 below.
- New `game_id` values are accepted as-is; the first score submission creates that leaderboard namespace.

## Project structure

```text
leaderboard2/
  app/
  alembic/
  docs/
  tests/
  scripts/
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

If another Postgres cluster is already using `localhost:5432`, the bootstrap step now fails fast instead of silently reusing the wrong database. Stop that cluster first, then rerun `make bootstrap` or `make dev`.

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

The Docker path uses the default `.env.example` connection settings and starts a dedicated `postgres`, `redis`, and `api` container set.

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

Behavior:

- If this is the first score for `(game_id, platform, user_id)`, a new row is created.
- If the user-platform entry already exists, only a higher score replaces the stored score.
- `updated=false` means the submission was accepted but did not beat the existing high score.

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

Behavior:

- `limit` defaults to `10` and is capped at `100`.
- Rankings are game-wide across all platforms.
- Ties share the same rank.
- Same-score ordering is deterministic, but tied users may appear in either order depending on the cache member ordering.

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

Behavior:

- `window` defaults to `2` and is capped at `10`.
- The requested user is identified by both `platform` and `user_id`.
- Nearby entries can include players on other platforms.
- If another player has the same score, they may appear in `above` or `below` depending on deterministic tie ordering.

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

- Unit tests cover competition ranking, score semantics, identifier validation, and response serialization.
- Integration coverage verifies the documented API contract in the README.
- CI runs linting and tests on every push and pull request.
- The local workflow has also been exercised manually against live Postgres and Redis with end-to-end HTTP smoke checks.

## Architecture notes

- Postgres holds canonical score rows keyed by `(game_id, platform, user_id)`.
- Redis stores `leaderboard:{game_id}` sorted sets using a composite `platform|user_id` member and score values.
- Read endpoints serve from Redis first.
- If Redis is empty or missing a known user, the service rebuilds the game leaderboard from Postgres.
- Displayed rank is computed as `count(scores strictly greater than target_score) + 1`.

See [docs/architecture.md](docs/architecture.md) and [docs/architecture-diagram.svg](docs/architecture-diagram.svg).

## Tradeoffs and future improvements

- A single write currently updates Postgres first and Redis second. For the MVP, Postgres remains canonical and cache rebuilds handle drift.
- Same-score ordering is deterministic but not explicitly product-shaped yet; if tie presentation needs stronger semantics, we should define a dedicated secondary ordering rule.
- Authentication, rate limiting, and anti-cheat controls are intentionally excluded.
- A future iteration should add true end-to-end integration tests that run against live Postgres and Redis in CI and local Docker.
