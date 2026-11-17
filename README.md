# ListMates API (Assignment 2 prototype)

ListMates is a social notes and to-do website: you make lists, choose who can see each one (Personal, Network or Public), and friends keep you on track. This repository is the first prototype of its backend: a REST API for **lists**, with mock users, token authentication, role checks, validation and an HTML greeting page.

- **Full API documentation:** [`docs/API.md`](docs/API.md)
- **Interactive docs:** `http://127.0.0.1:8000/docs` while the server is running
- **Demo video (5 min):** [YOUTUBE LINK]

> **Mock data:** the API uses in-memory mock data (9 lists, 3 users) instead of a real database. It resets every time the server restarts, including the automatic restarts from `--reload`.

## Requirements

- Python 3.11 or newer
- Git

## Install and run

```bash
git clone https://github.com/<sabiyev02>/listmates-api.git
cd listmates-api
python -m venv .venv
```

Activate the virtual environment:

| System | Command |
|---|---|
| macOS / Linux | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `.venv\Scripts\activate.bat` |

Then:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. It takes you to the greeting page at `/api/v1/greeting`.

## Mock tokens

Send one of these as `Authorization: Bearer <token>`:

| Token | User | Role |
|---|---|---|
| `user-a-token` | Aysel Mammadova (`user-a`) | Regular user: her own lists only |
| `user-b-token` | Leyla Hasanova (`user-b`) | Regular user: her own lists only |
| `admin-token` | ListMates Admin (`admin`) | Administrator: every list |

```bash
curl http://127.0.0.1:8000/api/v1/lists -H "Authorization: Bearer user-a-token"
```

## Endpoints

| Method | Path | Token | What it does |
|---|---|---|---|
| GET | `/api/v1/greeting` | None | HTML page about the project, team and API |
| GET | `/api/v1/lists` | Any | Your lists (every list for admin), with paging and filters |
| GET | `/api/v1/lists/{id}` | Any | One list, for its owner or an admin |
| POST | `/api/v1/lists` | Any | Create a list you own |
| PUT | `/api/v1/lists/{id}` | Owner or admin | Replace a list |
| DELETE | `/api/v1/lists/{id}` | Owner or admin | Delete a list |

Errors always use the same JSON envelope and one of ten error codes. See section 6 of [`docs/API.md`](docs/API.md).

## Example requests (Postman)

1. In Postman, choose **Import** and select `postman/ListMates.postman_collection.json`.
2. Restart the server so the mock data is fresh.
3. Open the collection, choose **Run**, and run all 26 requests in order. Each request checks its own status code.

## Automated tests

```bash
python -m pytest
```

The tests reset the mock data before each test, so they never depend on each other.

## Project structure

```
app/
  main.py          app setup: error handlers and routers
  envelope.py      success and error envelopes, error codes
  handlers.py      turns every error into the error envelope
  mock_data.py     mock users and the 9 seed lists
  store.py         data access (the only file that changes for MongoDB later)
  auth.py          Bearer token -> user
  permissions.py   ownership and admin rules
  validation.py    request validation rules
  routes/
    lists.py       /api/v1/lists endpoints
    greeting.py    /api/v1/greeting page
  templates/
    greeting.html
docs/API.md        API documentation
postman/           Postman collection
tests/             automated tests
```

## Team and contributions

| Member | Student ID | Built |
|---|---|---|
| Emin Ismayilzade | 19879 | Response envelope and error handling, validation, API documentation, Postman collection |
| Suleyman Abiyev | 18699 | Project setup, mock data and data store, list CRUD endpoints |
| Ali Garashli | 17420 | Token authentication, role checks, HTML greeting page, automated tests |

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) for details.

### Commits per member

```text
[PASTE THE OUTPUT OF: git shortlog -sn --all]
```
