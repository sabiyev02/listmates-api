"""Mock users and seed lists (docs/API.md, section 8).

Everything here lives in memory. It resets every time the server restarts.
"""

USERS = {
    "user-a": {"id": "user-a", "name": "Aysel Mammadova", "role": "user", "token": "user-a-token"},
    "user-b": {"id": "user-b", "name": "Leyla Hasanova", "role": "user", "token": "user-b-token"},
    "admin": {"id": "admin", "name": "ListMates Admin", "role": "admin", "token": "admin-token"},
}

USERS_BY_TOKEN = {user["token"]: user for user in USERS.values()}

# New lists get IDs from list_301 upward, so they never clash with the seed data.
FIRST_NEW_ID = 301


def _item(text: str, done: bool = False, due_date: str | None = None, repeat_daily: bool = False) -> dict:
    return {"text": text, "done": done, "dueDate": due_date, "repeatDaily": repeat_daily}


def seed_lists() -> dict[str, dict]:
    """Return a fresh copy of the 9 seed lists, keyed by ID."""
    lists = [
        # User A (Aysel): 6 lists, 4 of them Public, so a 5th Public list returns 409.
        {"id": "list_101", "ownerId": "user-a", "title": "Books to read",
         "description": "Two books a month this semester.", "visibility": "public",
         "items": [_item("Atomic Habits", done=True),
                   _item("Deep Work", due_date="2026-11-30"),
                   _item("The Pragmatic Programmer")],
         "createdAt": "2026-11-02T08:15:00Z", "updatedAt": "2026-11-12T19:40:00Z"},
        {"id": "list_102", "ownerId": "user-a", "title": "Daily habits",
         "description": "Small things, every day.", "visibility": "network",
         "items": [_item("Go to the gym", repeat_daily=True),
                   _item("Read 20 pages", repeat_daily=True)],
         "createdAt": "2026-11-03T07:00:00Z", "updatedAt": "2026-11-13T21:05:00Z"},
        {"id": "list_103", "ownerId": "user-a", "title": "SE midterm prep",
         "description": "Pressman chapters 1-4 and the lecture slides.", "visibility": "personal",
         "items": [_item("Prepare for SE midterm", due_date="2026-11-23"),
                   _item("Email Kamran the lab report", due_date="2026-11-16")],
         "createdAt": "2026-11-04T16:45:00Z", "updatedAt": "2026-11-11T10:00:00Z"},
        {"id": "list_104", "ownerId": "user-a", "title": "Films to watch",
         "description": "Friday film nights with friends.", "visibility": "public",
         "items": [_item("Cinema Paradiso", done=True), _item("Spirited Away"), _item("Past Lives")],
         "createdAt": "2026-11-05T18:20:00Z", "updatedAt": "2026-11-09T22:10:00Z"},
        {"id": "list_105", "ownerId": "user-a", "title": "Weekend in Sheki",
         "description": "Trip with friends after the midterms.", "visibility": "public",
         "items": [_item("Book the guesthouse", due_date="2026-11-20"), _item("Try piti"),
                   _item("Visit the Khan's Palace")],
         "createdAt": "2026-11-06T12:00:00Z", "updatedAt": "2026-11-06T12:00:00Z"},
        {"id": "list_106", "ownerId": "user-a", "title": "Recipes to try",
         "description": "Things I want to cook this autumn.", "visibility": "public",
         "items": [_item("Plov", done=True), _item("Lentil soup"), _item("Shakarbura")],
         "createdAt": "2026-11-07T19:10:00Z", "updatedAt": "2026-11-08T09:30:00Z"},
        # User B (Leyla): 3 lists, one for each visibility level.
        {"id": "list_201", "ownerId": "user-b", "title": "Books I loved",
         "description": "My favorites from this year.", "visibility": "public",
         "items": [_item("Atomic Habits", done=True), _item("Klara and the Sun")],
         "createdAt": "2026-11-01T10:00:00Z", "updatedAt": "2026-11-10T18:30:00Z"},
        {"id": "list_202", "ownerId": "user-b", "title": "5K running plan",
         "description": "Training for my first 5K in December.", "visibility": "network",
         "items": [_item("Week 1: run 1 min, walk 2", done=True),
                   _item("Week 2: run 2 min, walk 2", done=True),
                   _item("Week 3: run 5 min, walk 1")],
         "createdAt": "2026-11-02T06:30:00Z", "updatedAt": "2026-11-12T07:15:00Z"},
        {"id": "list_203", "ownerId": "user-b", "title": "Thesis to-dos",
         "description": "Final-year project.", "visibility": "personal",
         "items": [_item("Email my supervisor", due_date="2026-11-18"),
                   _item("Write the chapter 2 outline")],
         "createdAt": "2026-11-08T14:00:00Z", "updatedAt": "2026-11-08T14:00:00Z"},
    ]
    return {lst["id"]: lst for lst in lists}
