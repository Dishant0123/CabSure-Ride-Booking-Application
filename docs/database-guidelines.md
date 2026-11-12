# CabSure database guide

## Local development

The backend uses PostgreSQL through SQLAlchemy and psycopg 3. Create `backend/.env` from `backend/.env.example`, then set `DATABASE_URL` to your local PostgreSQL or Supabase connection string. The example URL points to a local development database and is not a production credential. SQLite remains available to isolated tests that create in-memory databases.

Development can apply the existing Alembic migrations at startup with `AUTO_MIGRATE=true`. To apply or inspect them manually from the `backend` directory:

```cmd
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
```

The command reads `DATABASE_URL` from `backend/.env`. Confirm it points to the intended database before running migrations.

## Supabase PostgreSQL

In the Supabase Dashboard, open the project and select **Connect** to copy a PostgreSQL connection string. A persistent backend can use the direct connection when its network supports IPv6 (or the project has IPv4 connectivity enabled). For an IPv4-only network, use the Supabase shared **Session pooler** connection. Use the supplied host and username; pooler hosts and usernames differ from direct connections. Add `sslmode=require` to require encryption. For certificate verification, configure the Supabase root certificate with `sslmode=verify-full` and `sslrootcert`.

The application accepts Supabase's `postgres://` and `postgresql://` URLs and maps them to the installed psycopg 3 driver. Reserved characters in the password must be URL-encoded. Keep the connection URL in the ignored `backend/.env` file or a deployment secret store. Never commit it. The backend connects directly through PostgreSQL; Supabase API keys are not database credentials.

## Production

Set `ENVIRONMENT=production` and `AUTO_MIGRATE=false`. The backend refuses to start if automatic migrations are enabled in production. Apply `alembic upgrade head` explicitly as a deployment step, then start the API with a runtime role that has only the permissions it needs. Confirm the revision with `alembic current`.

Keep provider-managed backups and create a separate PostgreSQL backup before schema changes. Use the connection mode recommended by Supabase for migrations and backups. Test restores periodically.

## Data rules

- Store money in integer paise and timestamps as timezone-aware UTC.
- Store Firebase UID and E.164 phone numbers; never store Firebase OTPs or raw Firebase tokens.
- Store Google place IDs and route snapshots, never Maps API keys.
- Keep KYC files in private object storage and persist only their storage keys.
- Use foreign keys, idempotency keys, immutable ride events, and audit/outbox records for critical operations.
- Apply all schema changes through new Alembic migrations. Do not use `create_all()` in runtime code.

## Troubleshooting

- **Connection timeout or DNS failure:** check whether the network supports the selected direct endpoint; try the Session pooler on IPv4-only networks.
- **Authentication failure:** verify the database password, username, and URL-encoding of reserved password characters.
- **SSL connection error:** confirm `sslmode=require` is present and the provider allows SSL connections.
- **Missing tables or an outdated revision:** from `backend`, run `alembic current`, then run `alembic upgrade head` against the intended `DATABASE_URL`.
