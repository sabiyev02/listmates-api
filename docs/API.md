# Assignment 2 — API Prototype with Mocked Backend and Frontend

**Project:** ListMates, a social notes and to-do website
**Team:** Group 7 (Emin Ismayilzade, Suleyman Abiyev, Ali Garashli)
**Course:** CSCI 3509 Intro to Software Engineering, Fall 2026
**API version:** v1, base path `/api/v1`

> The assignment says error codes come from "the table in section 6". In this document, [section 6](#6-error-codes) is that table.

---

## 1. Project overview

### What ListMates is

ListMates is a website for notes and to-do lists, built around the idea of *socializing through productivity*. Users build lists with text and tasks, and choose who can see each list:

- **Personal:** only the owner can see it.
- **Network:** the owner's approved followers can see it.
- **Public:** everyone can see it. A user can have at most 4 Public lists, and they are shown on the user's profile.

Followers can comment, react and nudge friends who miss their daily tasks, and teams can share group lists. It is for university students and young professionals who stay more productive when friends can see their progress.

### What this prototype covers

This prototype builds the core of the "Create" stage of our customer journey: making, reading, changing and deleting lists. It runs on in-memory mock data instead of MongoDB, and uses fixed mock tokens instead of Google sign-in.

| Proposal requirement | Covered here |
|---|---|
| FR-02 Create, edit, reorder and delete lists and tasks | Yes: full CRUD on `lists`. Tasks are the list's `items`, and their order in the array is their order on screen. |
| FR-03 Add text, checklists, images, PDFs and links | Partly: `description` (text) and `items` (checklist). Images, PDFs and links come with the real database. |
| FR-04 Due dates and daily tasks | Yes: `items[].dueDate` and `items[].repeatDaily` |
| FR-05 Personal / Network / Public, max 4 Public | Yes: `visibility`, with `409 Conflict` for a 5th Public list |

### Main resource: `lists`

We chose `lists` because every other feature (comments, reactions, nudges, groups, the monthly report) hangs off a list. The resource also has an owner and a visibility level, so it naturally exercises authentication, ownership checks and a real business rule (the 4-Public-list limit).

### How the frontend prototype maps to this API

Our clickable prototype shows the screens these endpoints will power:

| Prototype screen or action | Endpoint |
|---|---|
| My lists page | `GET /api/v1/lists` |
| Opening a list | `GET /api/v1/lists/{id}` |
| "New list" button | `POST /api/v1/lists` |
| Editing the title or tasks, or changing "Who can see this list" | `PUT /api/v1/lists/{id}` |
| The "You already have 4 Public lists" error | `409 PUBLIC_LIST_LIMIT_REACHED` |
| "Delete this list" button | `DELETE /api/v1/lists/{id}` |

### Prototype tech stack

| Part | Choice | Why |
|---|---|---|
| Language and framework | Python 3.11 or newer, FastAPI | The backend stack from our proposal. FastAPI publishes OpenAPI docs at `/docs` automatically. |
| Server | Uvicorn | The standard server for FastAPI |
| Validation | Plain Python checks in `app/validation.py` | Our own messages, every problem listed at once, and checks that run in the order from section 4 |
| Mock data | In-memory Python dictionaries (`app/mock_data.py`), reached only through `app/store.py` | Matches the assignment; resets on every restart. Moving to MongoDB later only changes `store.py`. |
| Docs and tests | This Markdown file, Swagger UI at `/docs`, a Postman collection, 31 automated tests (pytest) | Readable docs, plus something to click and run |

**FastAPI defaults we override:**
- FastAPI normally answers problems with `422` and its own `{"detail": ...}` shape. Our exception handlers turn every error (404, 405, validation and unexpected errors) into the error envelope from section 5, with the status codes listed in section 6.
- We read the JSON body ourselves, after the token and ownership checks. That keeps the order of checks in section 4, and lets us reject unknown fields with our own messages.

---

## 2. Team and responsibilities

| Member | Student ID | Responsibilities in Assignment 2 |
|---|---|---|
| Emin Ismayilzade | 19879 | Response envelope and error handling (all error codes), request validation, API documentation, Postman collection |
| Suleyman Abiyev | 18699 | Project setup, in-memory mock data and data store (seed data, ID generation, paging), list CRUD endpoints, the 4-Public-list rule |
| Ali Garashli | 17420 | Bearer-token authentication, ownership and admin checks, HTML greeting page, automated tests |

The same table goes into `CONTRIBUTORS.md` and onto the greeting page.

---

## 3. The List resource

### Fields

| Field | Type | Set by | Rules |
|---|---|---|---|
| `id` | string | Server | Format `list_<number>`, for example `list_101`. New lists start at `list_301`. |
| `ownerId` | string | Server | Taken from the token of the user who created the list |
| `title` | string | Client | Required. Trimmed length 3–60 characters. |
| `description` | string | Client | Optional. Up to 300 characters. Default `""`. |
| `visibility` | string | Client | One of `personal`, `network`, `public`. Optional on create (default `personal`), required on update. Each owner can have at most 4 `public` lists. |
| `items` | array | Client | Optional. Up to 50 items. Default `[]`. The order in the array is the order on screen. |
| `items[].text` | string | Client | Required. Trimmed length 1–120 characters. |
| `items[].done` | boolean | Client | Optional. Default `false`. |
| `items[].dueDate` | string or null | Client | Optional. A real calendar date in `YYYY-MM-DD` format. Default `null`. |
| `items[].repeatDaily` | boolean | Client | Optional. Default `false`. |
| `createdAt` | string | Server | ISO 8601 UTC time, for example `2026-11-02T08:15:00Z` |
| `updatedAt` | string | Server | Refreshed on every successful update |

### Validation rules (create and update)

1. **Body:** must be valid JSON and a JSON object (not an array or a string). Otherwise `400 INVALID_JSON`.
2. **Required fields:** `title` on create. `title` and `visibility` on update, because `PUT` replaces the whole list.
3. **Types:**
   - `title`, `description` and `items[].text` must be strings.
   - `done` and `repeatDaily` must be booleans. `"yes"` and `1` are rejected.
   - `items` must be an array of objects.
4. **Lengths:** as in the table above. Leading and trailing spaces are trimmed before lengths are checked.
5. **Allowed values:**
   - `visibility` must be one of the three levels.
   - `dueDate` must be a real date, so `2026-02-30` is rejected.
6. **Unknown fields:** rejected, including unknown fields inside an item.
7. **Read-only fields:** `id`, `ownerId`, `createdAt` and `updatedAt` are rejected with the message "This field is set by the server."
8. **IDs:**
   - A badly formed ID such as `abc` returns `400 VALIDATION_ERROR`.
   - A well-formed ID that doesn't exist (or isn't yours) returns `404 LIST_NOT_FOUND`.
9. **Business rule:** making a list Public when its owner already has 4 Public lists returns `409 PUBLIC_LIST_LIMIT_REACHED`.

Every failure lists all problems at once in `error.details`, so the frontend can mark every wrong field in one go.

---

## 4. Authentication and authorization

### Mock users

The API has no real login or password storage. Every `/lists` request sends one of three fixed tokens:

```http
Authorization: Bearer user-a-token
```

| Role | Token | User ID | Mock person | Permissions |
|---|---|---|---|---|
| Regular user A | `user-a-token` | `user-a` | Aysel Mammadova | Manages only her own lists |
| Regular user B | `user-b-token` | `user-b` | Leyla Hasanova | Manages only her own lists |
| Administrator | `admin-token` | `admin` | ListMates Admin | Reads, updates and deletes any list, and can filter by owner |

- **Authentication (who is calling?):**
  - No `Authorization` header returns `401 AUTH_REQUIRED`.
  - A header that isn't `Bearer <token>`, or a token not in the table, returns `401 INVALID_TOKEN`.
- **Authorization (are they allowed?):** the role and the list's `ownerId` decide, as shown in the matrix below.

### Access matrix (with the mock data from section 8)

| Request | User A | User B | Admin |
|---|---|---|---|
| `GET /lists` | 200, her 6 lists | 200, her 3 lists | 200, all 9 lists |
| `GET /lists/list_101` (A's list) | 200 | 404 | 200 |
| `PUT /lists/list_201` (B's list) | 404 | 200 | 200 |
| `DELETE /lists/list_203` (B's list) | 404 | 200 | 200 |
| `GET /lists?ownerId=user-b` | 403 | 200 (her own lists) | 200 |
| Any request without a token | 401 | 401 | 401 |

### Our choice: 404 instead of 403 for other users' lists

When a regular user asks for a list that belongs to someone else, the API answers **`404 LIST_NOT_FOUND`**, the same answer as for a list that does not exist.

- **Privacy is part of the product.** Personal lists are private by design. A `403` would confirm that `list_203` exists and belongs to someone, which is already information we don't want to leak.
- **IDs are easy to guess.** IDs are sequential (`list_201`, `list_202`, …), so with `403` anyone could map which IDs are taken by trying them one by one. With `404`, existing and missing lists look identical.
- **Admins never get this answer.** They can open every list, so they always get the real result.

**Where we do use `403 FORBIDDEN`:** when we already know who the user is, the request reveals nothing, and their role simply doesn't allow it. In this prototype that is a regular user filtering by another owner (`GET /lists?ownerId=user-b`). Only admins may browse lists by owner.

**What about Public lists?** In the full app, other people see your Public lists through your profile, using a separate read-only endpoint planned for later (`GET /api/v1/users/{userId}/public-lists`). `/api/v1/lists` is each user's own workspace, so it follows the assignment's rule: User A cannot read, update or delete User B's lists through it.

### Order of checks

The API runs its checks in this order, so every request gets exactly one predictable answer:

1. Unknown path returns `404 ROUTE_NOT_FOUND`. A method the path doesn't support returns `405 METHOD_NOT_ALLOWED`.
2. Missing or invalid token returns `401`.
3. Badly formed list ID or query parameters return `400 VALIDATION_ERROR`.
4. A list that doesn't exist, or isn't yours, returns `404 LIST_NOT_FOUND`. Because this runs before the body checks, you learn nothing about someone else's list even by sending a broken body.
5. Role check (owner filter) returns `403 FORBIDDEN`.
6. Broken JSON returns `400 INVALID_JSON`. Invalid fields return `400 VALIDATION_ERROR`.
7. Business rule: a 5th Public list returns `409 PUBLIC_LIST_LIMIT_REACHED`.

---

## 5. Response format

Every JSON response uses the same envelope. The HTTP status always matches it: `2xx` with `"success": true`, and `4xx` or `5xx` with `"success": false`.

**Success with one list:**

```json
{
  "success": true,
  "message": "List found.",
  "data": {
    "id": "list_101",
    "ownerId": "user-a",
    "title": "Books to read",
    "description": "Two books a month this semester.",
    "visibility": "public",
    "items": [
      { "text": "Atomic Habits", "done": true, "dueDate": null, "repeatDaily": false },
      { "text": "Deep Work", "done": false, "dueDate": "2026-11-30", "repeatDaily": false },
      { "text": "The Pragmatic Programmer", "done": false, "dueDate": null, "repeatDaily": false }
    ],
    "createdAt": "2026-11-02T08:15:00Z",
    "updatedAt": "2026-11-12T19:40:00Z"
  }
}
```

**Rules:**
- **Lists of results:** `data` is an array, and the response adds `meta` with `total`, `page` and `perPage`.
- **Deletes:** `data` is `null`.
- **Errors:** they carry `error.code` (from section 6) and a human-readable `error.message`. Validation errors also carry `error.details`, one entry per problem.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "title", "message": "Title is required and must contain at least 3 characters." }
    ]
  }
}
```

**What error messages never contain:** stack traces, file paths, Python exception names or internal data. Unexpected errors are logged on the server and the client gets only the generic `INTERNAL_ERROR` message.

---

## 6. Error codes

| `error.code` | HTTP status | When it happens | Example message |
|---|---:|---|---|
| `VALIDATION_ERROR` | 400 | A body or query field is missing, has the wrong type or length, isn't allowed, is unknown or is read-only. Also a badly formed list ID. | "The request contains invalid or missing fields." |
| `INVALID_JSON` | 400 | The body isn't valid JSON or isn't a JSON object | "The request body must be a valid JSON object." |
| `AUTH_REQUIRED` | 401 | No `Authorization` header | "Sign in first: add the header Authorization: Bearer <token>." |
| `INVALID_TOKEN` | 401 | The header isn't `Bearer <token>`, or the token is unknown | "The token is missing its Bearer prefix or is not valid." |
| `FORBIDDEN` | 403 | The user is known, but their role can't do this (filtering by another owner) | "Only administrators can filter lists by owner." |
| `LIST_NOT_FOUND` | 404 | No list with this ID, or it belongs to another user (for regular users) | "No list with ID list_999 was found." |
| `ROUTE_NOT_FOUND` | 404 | The path doesn't exist | "There is no endpoint at /api/v1/listz." |
| `METHOD_NOT_ALLOWED` | 405 | The path exists but not for this method. The response includes an `Allow` header. | "PATCH is not supported here. Use GET, PUT or DELETE." |
| `PUBLIC_LIST_LIMIT_REACHED` | 409 | The owner already has 4 Public lists | "You already have 4 Public lists. Make one of them Network or Personal first." |
| `INTERNAL_ERROR` | 500 | Anything unexpected | "Something went wrong on our side. Please try again." |

The frontend decides what to show from `error.code`. For example, `PUBLIC_LIST_LIMIT_REACHED` shows the red message under "Who can see this list", just like the prototype.

---

## 7. Endpoints

| Method | Path | Auth | What it does |
|---|---|---|---|
| `GET` | `/api/v1/lists` | Any token | List the caller's lists (all lists for admin), with paging and filters |
| `GET` | `/api/v1/lists/{id}` | Any token | Get one list |
| `POST` | `/api/v1/lists` | Any token | Create a list owned by the caller |
| `PUT` | `/api/v1/lists/{id}` | Owner or admin | Replace a list |
| `DELETE` | `/api/v1/lists/{id}` | Owner or admin | Delete a list |
| `GET` | `/api/v1/greeting` | None | HTML page about the project, the team and the API |

Other methods on these paths return `405 METHOD_NOT_ALLOWED`, for example `PATCH /api/v1/lists/{id}` or `DELETE /api/v1/lists`.

Every JSON response has the header `Content-Type: application/json; charset=utf-8`. In the examples below, the request line and headers are in an `http` block and the JSON body follows separately.

---

### 7.1 List lists — `GET /api/v1/lists`

**Headers and role**
- `Authorization: Bearer <token>`. Any role.
- Regular users see only their own lists. Admin sees all lists.

**Parameters** (query only, all optional)

| Name | Type | Rules | Default |
|---|---|---|---|
| `page` | integer | 1 or more | `1` |
| `perPage` | integer | 1–50 | `10` |
| `visibility` | string | `personal`, `network` or `public` | All levels |
| `ownerId` | string | A user ID such as `user-b`. Admin can pass any user ID. Regular users can only pass their own ID; anything else returns `403`. | All owners for admin, the caller for regular users |

**Validation**
- `page` and `perPage` must be whole numbers in range. `visibility` must be one of the three levels.
- Unknown query parameters are ignored.
- A `page` past the last page returns `200` with an empty `data` array and the real `meta.total`.

**Success:** `200 OK`. `data` is an array of lists, oldest first. `meta` holds `total`, `page` and `perPage`.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Bad `page`, `perPage` or `visibility` |
| 401 | `AUTH_REQUIRED` | No token |
| 401 | `INVALID_TOKEN` | Wrong or unknown token |
| 403 | `FORBIDDEN` | A regular user filters by another owner |
| 405 | `METHOD_NOT_ALLOWED` | `PUT`, `PATCH` or `DELETE` on `/api/v1/lists` |

**Example: User A, first page of 2**

```http
GET /api/v1/lists?page=1&perPage=2 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`200 OK`

```json
{
  "success": true,
  "message": "Found 6 lists.",
  "data": [
    {
      "id": "list_101",
      "ownerId": "user-a",
      "title": "Books to read",
      "description": "Two books a month this semester.",
      "visibility": "public",
      "items": [
        { "text": "Atomic Habits", "done": true, "dueDate": null, "repeatDaily": false },
        { "text": "Deep Work", "done": false, "dueDate": "2026-11-30", "repeatDaily": false },
        { "text": "The Pragmatic Programmer", "done": false, "dueDate": null, "repeatDaily": false }
      ],
      "createdAt": "2026-11-02T08:15:00Z",
      "updatedAt": "2026-11-12T19:40:00Z"
    },
    {
      "id": "list_102",
      "ownerId": "user-a",
      "title": "Daily habits",
      "description": "Small things, every day.",
      "visibility": "network",
      "items": [
        { "text": "Go to the gym", "done": false, "dueDate": null, "repeatDaily": true },
        { "text": "Read 20 pages", "done": false, "dueDate": null, "repeatDaily": true }
      ],
      "createdAt": "2026-11-03T07:00:00Z",
      "updatedAt": "2026-11-13T21:05:00Z"
    }
  ],
  "meta": { "total": 6, "page": 1, "perPage": 2 }
}
```

**Example: User A tries to filter by User B**

```http
GET /api/v1/lists?ownerId=user-b HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`403 Forbidden`

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only administrators can filter lists by owner."
  }
}
```

**Example: bad paging values**

```http
GET /api/v1/lists?page=0&perPage=200&visibility=friends HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "page", "message": "Page must be a whole number of 1 or more." },
      { "field": "perPage", "message": "perPage must be between 1 and 50." },
      { "field": "visibility", "message": "Visibility must be personal, network or public." }
    ]
  }
}
```

---

### 7.2 Get one list — `GET /api/v1/lists/{id}`

**Headers and role**
- `Authorization: Bearer <token>`.
- The owner or admin gets the list. Any other regular user gets `404`.

**Parameters**

| Name | In | Rules |
|---|---|---|
| `id` | path | Required. Format `list_<number>`. |

**Validation:** a badly formed ID returns `400`. An unknown ID, or one owned by someone else, returns `404`.

**Success:** `200 OK`. `data` is the list.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | ID isn't in the `list_<number>` format |
| 401 | `AUTH_REQUIRED` | No token |
| 401 | `INVALID_TOKEN` | Wrong or unknown token |
| 404 | `LIST_NOT_FOUND` | The ID doesn't exist, or the list belongs to another user |
| 405 | `METHOD_NOT_ALLOWED` | `POST` or `PATCH` on `/api/v1/lists/{id}` |

**Example: admin opens User B's list**

```http
GET /api/v1/lists/list_201 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer admin-token
```

`200 OK`

```json
{
  "success": true,
  "message": "List found.",
  "data": {
    "id": "list_201",
    "ownerId": "user-b",
    "title": "Books I loved",
    "description": "My favorites from this year.",
    "visibility": "public",
    "items": [
      { "text": "Atomic Habits", "done": true, "dueDate": null, "repeatDaily": false },
      { "text": "Klara and the Sun", "done": false, "dueDate": null, "repeatDaily": false }
    ],
    "createdAt": "2026-11-01T10:00:00Z",
    "updatedAt": "2026-11-10T18:30:00Z"
  }
}
```

**Example: User A tries the same list**

```http
GET /api/v1/lists/list_201 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`404 Not Found`

```json
{
  "success": false,
  "error": {
    "code": "LIST_NOT_FOUND",
    "message": "No list with ID list_201 was found."
  }
}
```

**Example: badly formed ID**

```http
GET /api/v1/lists/abc HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "id", "message": "List IDs look like list_101." }
    ]
  }
}
```

---

### 7.3 Create a list — `POST /api/v1/lists`

**Headers and role**
- `Authorization: Bearer <token>`. Any role.
- `Content-Type: application/json`.
- The new list is always owned by the caller.

**Parameters** (body)

| Field | Required | Rules |
|---|---|---|
| `title` | Yes | String, 3–60 characters after trimming |
| `description` | No | String, up to 300 characters |
| `visibility` | No | `personal` (default), `network` or `public` |
| `items` | No | Array of up to 50 items. Each item has `text` (required, 1–120 characters), `done` (boolean), `dueDate` (`YYYY-MM-DD` or `null`) and `repeatDaily` (boolean). |

**Validation:** all rules from section 3. Read-only and unknown fields are rejected.

**Success:** `201 Created`.
- `data` is the new list.
- The `Location` header points to it.
- The server fills in `id`, `ownerId`, `createdAt`, `updatedAt` and any defaults.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | `INVALID_JSON` | Body isn't valid JSON or isn't an object |
| 400 | `VALIDATION_ERROR` | Any field rule broken |
| 401 | `AUTH_REQUIRED` | No token |
| 401 | `INVALID_TOKEN` | Wrong or unknown token |
| 409 | `PUBLIC_LIST_LIMIT_REACHED` | `visibility` is `public` and the caller already has 4 Public lists |

**Example: User A creates a Personal list**

```http
POST /api/v1/lists HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
Content-Type: application/json
```

```json
{
  "title": "Gifts for December",
  "description": "Ideas for the New Year.",
  "visibility": "personal",
  "items": [
    { "text": "Book for Leyla", "dueDate": "2026-12-20" },
    { "text": "Scarf for Mom" }
  ]
}
```

`201 Created` with `Location: /api/v1/lists/list_301`

```json
{
  "success": true,
  "message": "List created successfully.",
  "data": {
    "id": "list_301",
    "ownerId": "user-a",
    "title": "Gifts for December",
    "description": "Ideas for the New Year.",
    "visibility": "personal",
    "items": [
      { "text": "Book for Leyla", "done": false, "dueDate": "2026-12-20", "repeatDaily": false },
      { "text": "Scarf for Mom", "done": false, "dueDate": null, "repeatDaily": false }
    ],
    "createdAt": "2026-11-14T09:20:00Z",
    "updatedAt": "2026-11-14T09:20:00Z"
  }
}
```

**Example: many validation problems at once**

```json
{
  "title": "Hi",
  "visibility": "secret",
  "ownerId": "user-b",
  "items": [
    { "text": "", "done": "yes" },
    { "text": "Pay rent", "dueDate": "2026-02-30" }
  ]
}
```

`400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "title", "message": "Title is required and must contain at least 3 characters." },
      { "field": "visibility", "message": "Visibility must be personal, network or public." },
      { "field": "ownerId", "message": "This field is set by the server." },
      { "field": "items[0].text", "message": "Item text must contain 1 to 120 characters." },
      { "field": "items[0].done", "message": "done must be true or false." },
      { "field": "items[1].dueDate", "message": "dueDate must be a real date in YYYY-MM-DD format." }
    ]
  }
}
```

**Example: a 5th Public list**

User A already has 4 Public lists in the mock data.

```json
{
  "title": "Places to visit in Baku",
  "visibility": "public"
}
```

`409 Conflict`

```json
{
  "success": false,
  "error": {
    "code": "PUBLIC_LIST_LIMIT_REACHED",
    "message": "You already have 4 Public lists. Make one of them Network or Personal first."
  }
}
```

**Example: broken JSON**

The body is `{"title": "Gifts",` and the closing brace is missing.

`400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "The request body must be a valid JSON object."
  }
}
```

---

### 7.4 Update a list — `PUT /api/v1/lists/{id}`

**Headers and role**
- `Authorization: Bearer <token>`.
- `Content-Type: application/json`.
- Allowed for the owner or admin. Any other regular user gets `404`.

**What PUT does:** it replaces the whole list.
- Send `title` and `visibility` every time.
- If you leave out `description` or `items`, they are reset to `""` and `[]`.
- `id`, `ownerId` and `createdAt` never change. `updatedAt` is refreshed.

**Parameters**

| Name | In | Rules |
|---|---|---|
| `id` | path | Required. Format `list_<number>`. |
| `title` | body | Required. 3–60 characters. |
| `visibility` | body | Required. `personal`, `network` or `public`. |
| `description` | body | Optional. Up to 300 characters. |
| `items` | body | Optional. Same rules as for create. |

**Validation**
- All rules from section 3.
- **The Public limit:** it counts the owner's other Public lists. A list that is already Public can be saved again without hitting the limit.
- **Admin edits:** when an admin makes a user's list Public, the limit uses that user's count, not the admin's.

**Success:** `200 OK`. `data` is the updated list.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Badly formed ID, or any field rule broken |
| 400 | `INVALID_JSON` | Body isn't valid JSON or isn't an object |
| 401 | `AUTH_REQUIRED` | No token |
| 401 | `INVALID_TOKEN` | Wrong or unknown token |
| 404 | `LIST_NOT_FOUND` | The ID doesn't exist, or the list belongs to another user |
| 409 | `PUBLIC_LIST_LIMIT_REACHED` | Changing to `public` when the owner already has 4 other Public lists |

**Example: User A shares her midterm list with her network and updates the tasks**

```http
PUT /api/v1/lists/list_103 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
Content-Type: application/json
```

```json
{
  "title": "SE midterm prep",
  "description": "Midterm on 23 November: Pressman chapters 1-4.",
  "visibility": "network",
  "items": [
    { "text": "Re-read Pressman ch. 1-4 notes", "done": true },
    { "text": "Solve last year's practice questions", "dueDate": "2026-11-20" },
    { "text": "Review mistakes with a teammate", "dueDate": "2026-11-22" }
  ]
}
```

`200 OK`

```json
{
  "success": true,
  "message": "List updated successfully.",
  "data": {
    "id": "list_103",
    "ownerId": "user-a",
    "title": "SE midterm prep",
    "description": "Midterm on 23 November: Pressman chapters 1-4.",
    "visibility": "network",
    "items": [
      { "text": "Re-read Pressman ch. 1-4 notes", "done": true, "dueDate": null, "repeatDaily": false },
      { "text": "Solve last year's practice questions", "done": false, "dueDate": "2026-11-20", "repeatDaily": false },
      { "text": "Review mistakes with a teammate", "done": false, "dueDate": "2026-11-22", "repeatDaily": false }
    ],
    "createdAt": "2026-11-04T16:45:00Z",
    "updatedAt": "2026-11-14T09:25:00Z"
  }
}
```

**Example: missing required fields on PUT**

```json
{
  "description": "Only a description"
}
```

`400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "title", "message": "Title is required and must contain at least 3 characters." },
      { "field": "visibility", "message": "Visibility is required when replacing a list." }
    ]
  }
}
```

**Example: User B tries to edit User A's list**

A `PUT /api/v1/lists/list_101` with `Authorization: Bearer user-b-token` returns `404 Not Found`:

```json
{
  "success": false,
  "error": {
    "code": "LIST_NOT_FOUND",
    "message": "No list with ID list_101 was found."
  }
}
```

---

### 7.5 Delete a list — `DELETE /api/v1/lists/{id}`

**Headers and role**
- `Authorization: Bearer <token>`.
- Allowed for the owner or admin. Any other regular user gets `404`.

**Parameters**

| Name | In | Rules |
|---|---|---|
| `id` | path | Required. Format `list_<number>`. |

**Validation:** a badly formed ID returns `400`. An unknown ID, or one owned by someone else, returns `404`. Deleting the same ID twice returns `404` the second time.

**Success:** `200 OK` with `data: null`. We return 200 rather than 204 so the client still gets the envelope and a message.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | ID isn't in the `list_<number>` format |
| 401 | `AUTH_REQUIRED` | No token |
| 401 | `INVALID_TOKEN` | Wrong or unknown token |
| 404 | `LIST_NOT_FOUND` | The ID doesn't exist, or the list belongs to another user |

**Example: User A deletes one of her Public lists**

```http
DELETE /api/v1/lists/list_105 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer user-a-token
```

`200 OK`

```json
{
  "success": true,
  "message": "List list_105 was deleted.",
  "data": null
}
```

After this, User A has 3 Public lists, so the same `POST` that returned `409` in 7.3 now succeeds. This is a good moment to show in the demo.

**Example: an ID that doesn't exist**

`DELETE /api/v1/lists/list_999` with `Authorization: Bearer admin-token` returns `404 Not Found`:

```json
{
  "success": false,
  "error": {
    "code": "LIST_NOT_FOUND",
    "message": "No list with ID list_999 was found."
  }
}
```

**Example: wrong method on a list**

`PATCH /api/v1/lists/list_101` returns `405 Method Not Allowed` with the header `Allow: GET, PUT, DELETE`:

```json
{
  "success": false,
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "PATCH is not supported here. Use GET, PUT or DELETE."
  }
}
```

---

### 7.6 HTML greeting page — `GET /api/v1/greeting`

**Headers and role:** no token needed, so the page opens straight in a browser.

**Response:** `200 OK` with `Content-Type: text/html; charset=utf-8`. Other methods return `405` with the JSON error envelope. Opening the server's root address (`http://127.0.0.1:8000/`) redirects here.

**What the page shows:**

1. **Header:**
   - **Name:** ListMates.
   - **Tagline:** "Lists you share with friends, so you actually finish them."
   - **Description:** ListMates helps university students and young professionals stay productive together. They make notes and to-do lists, choose who sees each one (Personal, Network or Public), and keep each other on track with comments, reactions and nudges.
2. **Status panel:**
   - "API is running", version `v1`, and the server start time.
   - The live count of mock lists and users, for example "9 lists, 3 users".
   - A note that mock data resets when the server restarts.
3. **Team:** one card per member with name, student ID and what they built:
   - Emin Ismayilzade: response envelope, error handling, validation and the API documentation
   - Suleyman Abiyev: project setup, mock data store and the list CRUD endpoints
   - Ali Garashli: token authentication, role checks, this greeting page and the automated tests
4. **Endpoints:** a table of every endpoint from the start of section 7, with method, path, required token and a one-line description. It also links to the Swagger docs at `/docs`.
5. **Try it:** the three mock tokens and one ready-to-copy `curl` command.
6. **Footer:** Group 7, CSCI 3509 Intro to Software Engineering, Fall 2026.

**Styling:**
- **Colors and font:** the same as our prototype and customer journey map. Ink `#1D2B3A` text on a light `#EEF3F5` background, teal `#1F7A8C` for the status badge, and a different color for each HTTP method label. Bricolage Grotesque, falling back to the system sans-serif font.
- **Layout:** cards with clear spacing. Body text is 16 px and lines stay under about 75 characters.
- **Mobile:** below 700 px wide, the team cards stack into one column and the endpoints table scrolls sideways inside its own box, so the page never scrolls sideways.
- **Viewport:** the page sets `<meta name="viewport" content="width=device-width, initial-scale=1">`.

**Example (shortened):**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ListMates API</title>
    <style>/* layout, typography and spacing */</style>
  </head>
  <body>
    <header>
      <h1>ListMates</h1>
      <p>Lists you share with friends, so you actually finish them.</p>
    </header>
    <section class="status"><span class="badge">API is running</span> Version v1. 9 lists, 3 users. Mock data resets on restart.</section>
    <section class="team"><!-- one card per member --></section>
    <section class="endpoints"><!-- table of endpoints --></section>
  </body>
</html>
```

---

## 8. Mock data

The mock data lives in memory (`app/mock_data.py`) and **resets every time the server restarts**. The README says so as well.

### Users

| User ID | Name | Token | Role |
|---|---|---|---|
| `user-a` | Aysel Mammadova | `user-a-token` | Regular user |
| `user-b` | Leyla Hasanova | `user-b-token` | Regular user |
| `admin` | ListMates Admin | `admin-token` | Administrator |

### Lists

| ID | Owner | Title | Visibility | Items |
|---|---|---|---|---:|
| `list_101` | user-a | Books to read | public | 3 |
| `list_102` | user-a | Daily habits | network | 2 |
| `list_103` | user-a | SE midterm prep | personal | 2 |
| `list_104` | user-a | Films to watch | public | 3 |
| `list_105` | user-a | Weekend in Sheki | public | 3 |
| `list_106` | user-a | Recipes to try | public | 3 |
| `list_201` | user-b | Books I loved | public | 2 |
| `list_202` | user-b | 5K running plan | network | 3 |
| `list_203` | user-b | Thesis to-dos | personal | 2 |

**What each part of the data demonstrates:**
- **User A has 6 lists, 4 of them Public.** A 5th Public list returns `409` straight away.
- **User B has 3 lists**, covering all three visibility levels.
- **Admin owns no lists but can reach all 9.** This shows admin access.
- **`list_999` never exists.** Use it for `404 Not Found`.
- **New lists get IDs from `list_301` upward,** so they never clash with the seed data.

---

## 9. Running the prototype (README notes)

**Requirements:** Python 3.11 or newer, and Git.

```bash
git clone https://github.com/<sabiyev02>/listmates-api.git
cd listmates-api
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt    # fastapi, uvicorn, pytest, httpx2
uvicorn app.main:app --reload
```

Then open:
- `http://127.0.0.1:8000`, which redirects to the HTML greeting page at `/api/v1/greeting`
- `http://127.0.0.1:8000/docs`, the Swagger UI, where you can click "Authorize" and paste a mock token

Run the automated tests with `python -m pytest` (31 tests).

> Mock data is kept in memory. Every restart (including the automatic restarts from `--reload`) brings back the 9 seed lists and drops anything you created.

**Project structure**

```
listmates-api/
  app/
    main.py            # app setup: error handlers and routers
    envelope.py        # success and error envelopes, one shortcut per error code
    handlers.py        # turns every error into the error envelope
    mock_data.py       # mock users and the 9 seed lists
    store.py           # data access; the only file that changes for MongoDB later
    auth.py            # Bearer token -> user
    permissions.py     # ownership and admin rules (404 / 403)
    validation.py      # request validation rules (section 3)
    routes/
      lists.py         # GET, POST, PUT, DELETE /api/v1/lists
      greeting.py      # GET /api/v1/greeting
    templates/
      greeting.html
  docs/
    API.md             # this document
  postman/
    ListMates.postman_collection.json
  tests/               # 31 automated tests
  requirements.txt
  pytest.ini
  README.md
  CONTRIBUTORS.md
  .gitignore
```

---

## 10. Example requests and Postman collection

### Postman setup

**Import:** in Postman choose Import and select `postman/ListMates.postman_collection.json`.

**Variables:** the collection already holds `baseUrl` = `http://127.0.0.1:8000/api/v1`, plus `tokenA`, `tokenB` and `tokenAdmin`.

**Run it:** restart the server so the mock data is fresh, then run the whole collection top to bottom. Every request checks its own status code (and error code), so a clean run shows every check passing. The requests are numbered in the order they must run.

| # | Folder | Request | Token | Expected |
|---:|---|---|---|---|
| 1 | Greeting page | `GET /greeting` | none | 200, HTML |
| 2 | CRUD as User A | `GET /lists` | A | 200, total 6 |
| 3 | CRUD as User A | `GET /lists/list_101` | A | 200 |
| 4 | CRUD as User A | `POST /lists` (Gifts for December) | A | 201, `list_301` |
| 5 | CRUD as User A | `PUT /lists/list_103` (to Network) | A | 200 |
| 6 | CRUD as User A | `POST /lists` (a 5th Public list) | A | 409 `PUBLIC_LIST_LIMIT_REACHED` |
| 7 | CRUD as User A | `DELETE /lists/list_105` | A | 200, `data: null` |
| 8 | CRUD as User A | `POST /lists` (the same Public list again) | A | 201 |
| 9 | Authentication and authorization | `GET /lists` without a header | none | 401 `AUTH_REQUIRED` |
| 10 | Authentication and authorization | `GET /lists` with `Bearer wrong-token` | wrong | 401 `INVALID_TOKEN` |
| 11 | Authentication and authorization | `GET /lists/list_201` | A | 404 `LIST_NOT_FOUND` |
| 12 | Authentication and authorization | `PUT /lists/list_101` | B | 404 `LIST_NOT_FOUND` |
| 13 | Authentication and authorization | `DELETE /lists/list_101` | B | 404 `LIST_NOT_FOUND` |
| 14 | Authentication and authorization | `GET /lists?ownerId=user-b` | A | 403 `FORBIDDEN` |
| 15 | Admin | `GET /lists` | Admin | 200, lists from both users |
| 16 | Admin | `GET /lists?ownerId=user-b` | Admin | 200, total 3 |
| 17 | Admin | `PUT /lists/list_201` | Admin | 200 |
| 18 | Admin | `DELETE /lists/list_203` | Admin | 200 |
| 19 | Validation | `POST /lists` with many bad fields | A | 400 `VALIDATION_ERROR`, 6 details |
| 20 | Validation | `POST /lists` with broken JSON | A | 400 `INVALID_JSON` |
| 21 | Validation | `PUT /lists/list_103` without title and visibility | A | 400 `VALIDATION_ERROR` |
| 22 | Validation | `GET /lists/abc` | A | 400 `VALIDATION_ERROR` |
| 23 | Validation | `GET /lists?page=0&perPage=200&visibility=friends` | A | 400 `VALIDATION_ERROR` |
| 24 | Other errors | `PATCH /lists/list_101` | A | 405 `METHOD_NOT_ALLOWED`, `Allow: GET, PUT, DELETE` |
| 25 | Other errors | `GET /lists/list_999` | Admin | 404 `LIST_NOT_FOUND` |
| 26 | Other errors | `GET /listz` | A | 404 `ROUTE_NOT_FOUND` |

### The same in curl

```bash
BASE=http://127.0.0.1:8000/api/v1

# 2. User A lists her lists
curl -s "$BASE/lists" -H "Authorization: Bearer user-a-token"

# 4. User A creates a list
curl -s -X POST "$BASE/lists" \
  -H "Authorization: Bearer user-a-token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Gifts for December","visibility":"personal","items":[{"text":"Book for Leyla","dueDate":"2026-12-20"}]}'

# 6. Fifth Public list -> 409
curl -s -X POST "$BASE/lists" \
  -H "Authorization: Bearer user-a-token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Places to visit in Baku","visibility":"public"}'

# 9. No token -> 401
curl -s "$BASE/lists"

# 11. User A tries User B's list -> 404
curl -s "$BASE/lists/list_201" -H "Authorization: Bearer user-a-token"

# 14. User A filters by another owner -> 403
curl -s "$BASE/lists?ownerId=user-b" -H "Authorization: Bearer user-a-token"

# 24. Wrong method -> 405
curl -s -i -X PATCH "$BASE/lists/list_101" -H "Authorization: Bearer user-a-token"

# 1. Greeting page
curl -s -i "$BASE/greeting"
```

---

## 11. Demo video plan (5 minutes at most)

The numbers refer to the Postman requests in section 10.

| Time | What we show | Who narrates |
|---|---|---|
| 0:00–0:30 | The greeting page in a browser, first full width, then in a narrow (phone-sized) window (request 1) | Ali |
| 0:30–1:30 | CRUD as User A in Postman: list (2), get (3), create (4), update to Network (5) | Suleyman |
| 1:30–2:00 | The 4-Public-list rule: a 5th Public list returns 409 (6), delete `list_105` (7), the same request now returns 201 (8) | Suleyman |
| 2:00–3:00 | Authorization: no token (9), wrong token (10), A opens B's list (11), B edits and deletes A's list (12, 13), A filters by owner (14) | Ali |
| 3:00–3:30 | Admin sees both users' lists (15, 16), edits (17) and deletes (18) User B's lists | Ali |
| 3:30–4:20 | Validation: many bad fields (19), broken JSON (20), PUT without required fields (21), bad ID (22), bad paging (23), wrong method (24), unknown ID (25), unknown endpoint (26) | Emin |
| 4:20–5:00 | `python -m pytest` passing, a server restart to show the mock data reset, and a quick look at `/docs` | Emin |

The finished video goes on YouTube as Unlisted, and the link goes in the README.

---

## 12. Git workflow and contributions

- **Branches:** one feature branch per feature, merged into `main` through a pull request that another team member approves. Merge with **Create a merge commit** (not Squash), so every small commit stays in the history.
- **Order:** a branch starts only when the branches in its "Starts after" column are merged, so `main` works after every merge.

| # | Branch | Owner | Starts after | Commits |
|---:|---|---|---|---|
| 1 | `feature/project-setup` | Suleyman | Repository created | `Add .gitignore and requirements`, `Add FastAPI app skeleton` |
| 2 | `feature/error-envelope` | Emin | 1 | `Add success and error envelope helpers`, `Return every error in the error envelope` |
| 3 | `feature/mock-data` | Suleyman | 1 | `Add mock users and seed lists`, `Add data access functions for lists` |
| 4 | `feature/token-auth` | Ali | 2 and 3 | `Return 401 for missing or invalid tokens` |
| 5 | `feature/validation` | Emin | 2 | `Validate list IDs, query parameters and JSON bodies`, `Validate list fields and reject unknown fields` |
| 6 | `feature/greeting-page` | Ali | 2 and 3 | `Add HTML greeting page template`, `Serve the greeting page at /api/v1/greeting` |
| 7 | `feature/role-checks` | Ali | 2 and 3 | `Return 404 for lists owned by other users`, `Allow only admins to filter lists by owner` |
| 8 | `feature/list-crud` | Suleyman | 4, 5, 6 and 7 | `Add GET endpoints for lists`, `Add POST, PUT and DELETE for lists`, `Return 409 when the owner has 4 public lists` |
| 9 | `feature/api-tests` | Ali | 8 | `Add tests for CRUD and authorization`, `Add tests for validation and error responses` |
| 10 | `docs/api-docs` | Emin | 8 | `Add API documentation`, `Add Postman collection`, `Add README and contributors list` |
| 11 | `docs/final-readme` | Emin | 9, 10 and the demo video | `Add demo video link and commit summary to README` |

- **Commits:** small, one change each, with imperative messages. Everyone commits from their own GitHub account, with `git config user.email` set to the email on that account.
- **`.gitignore`:** includes `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.env`, `.DS_Store`, `.idea/` and `.vscode/`. No secrets are committed. The mock tokens are not secrets, because they only exist for this prototype.
- **`CONTRIBUTORS.md`:** each member's name, student ID, responsibilities and branches.
- **README:** includes the output of `git shortlog -sn --all` and a short summary of who built what.

```text
$ git shortlog -sn --all
    11  Suleyman Abiyev
     9  Ali Garashli
     7  Emin Ismayilzade(Emin's previous Git account name)
     4  Emin Ismayilzada
     2  sabiyev02 (Suleyman's previous Git Account Name)
```

(Paste the real output before submitting. The counts include merge commits, which belong to whoever clicks Merge on GitHub, so they won't match the table above exactly.)

---

## 13. Grading checklist

| Criterion | Weight | Where it is covered |
|---|---:|---|
| Resource-oriented API design and endpoint naming | 20% | Plural noun `lists`, no verbs in paths, versioned `/api/v1`, `{id}` for single lists (sections 1 and 7) |
| CRUD functionality using mocked data | 20% | Five endpoints (7.1–7.5) over 9 in-memory seed lists (section 8) |
| Authentication and role-based authorization | 20% | Bearer mock tokens, three roles, the access matrix, and the 404-versus-403 reasoning (section 4) |
| Validation, status codes and structured responses | 20% | Field rules (section 3), the envelope (section 5), ten error codes (section 6), and every error per endpoint (section 7) |
| Documentation and demonstration | 20% | This document, Swagger at `/docs`, the 26-request Postman collection (section 10), 31 automated tests, the README notes (section 9) and the video plan (section 11) |

### Before submitting

- [x ] Student IDs filled in (section 2, `CONTRIBUTORS.md` and the greeting page)
- [ x] GitHub repository link in the README
- [x ] `git shortlog -sn --all` output pasted into the README
- [x ] Postman collection exported to `postman/`
- [x ] YouTube demo link (5 minutes or less) in the README
