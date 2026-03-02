# Architecture Overview

The service uses FastAPI for the request layer, Postgres as the source of truth, and Redis sorted sets as the fast-read cache for leaderboard views.

## Request lifecycle

1. Client calls the FastAPI route.
2. Request validation is performed with Pydantic models and typed query/path parameters.
3. The service layer applies highest-score-wins logic.
4. Postgres stores the canonical score row for `(game_id, user_id)`.
5. Redis updates the sorted set for the game when the score improves.
6. Read endpoints serve from Redis and rebuild from Postgres if the cache is cold or incomplete.

## Ranking model

- Leaderboards are stored in Redis sorted sets keyed by `leaderboard:{game_id}`.
- Higher numeric scores rank above lower scores.
- Ties are displayed with competition ranking.
- Redis position is used only to locate a user and fetch a neighborhood window.
- Display rank is derived in the service layer based on the number of players with strictly higher scores.

## Failure model

- Postgres is the canonical store.
- Redis is a derived cache and can be rebuilt per game.
- If Redis is empty or missing a user that exists in Postgres, the service rebuilds the cache for that game before returning data.

