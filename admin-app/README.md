# CabSure Admin

The Admin console is served by FastAPI at `http://localhost:8000/admin`.

Set `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD` in `backend/.env` before starting the backend for the first time. The backend creates that first admin account automatically and stores only its password hash.
