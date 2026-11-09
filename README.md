# Card Craft RPG

Catalog the content of your tabletop RPG campaigns (systems, campaigns, items, races, race skills,
classes and class skills), filter it on any page and print it as **6 × 9 cm cards**, nine per A4 sheet.

| Layer | Stack |
| --- | --- |
| Backend | Python 3.12+, Django 6.1, Django REST Framework, PostgreSQL 16 |
| Frontend | React 19, TypeScript, Vite, Mantine 9, TanStack Query, React Router |

## Quick start

```bash
# 1. Database
docker compose up -d db

# 2. Backend (http://localhost:8000/api/)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_demo        # optional sample data
python manage.py runserver

# 3. Frontend (http://localhost:5173)
cd ../frontend
npm install
npm run dev                       # proxies /api to localhost:8000
```

Configuration comes from environment variables; see `backend/.env.example`.

### Tests and checks

```bash
cd backend && pytest              # unit + API integration tests (needs PostgreSQL)
cd frontend && npm run typecheck && npm run lint && npm run build
```

## Printing

Select cards (or use **Print all / Print matching** to take every card that matches the current
filters), check the preview and press **Print**. In the browser print dialog keep the scale at
**100%** and enable **background graphics**. Cards are laid out 3 × 3 on A4 with dashed cut guides.
Long descriptions shrink automatically to fit the card.

## Card appearance

Every card has a **background color** (white by default; presets or any hex color) and an optional
**image** shown below the title. The form shows a live preview. Text switches to light ink on dark
backgrounds automatically. Images must be PNG, JPEG, WebP or GIF up to 5 MB; the backend checks the
real file content with Pillow. Files are stored in `backend/media/cards/` (Django storage API, so
S3 or similar can be plugged in through settings) and served by Django in development.

## Architecture (backend)

Clean Architecture: dependencies point inwards only.

```
backend/cardcraft/
├── domain/            Entities with self-validation, value objects, repository ports. No Django.
├── application/       Generic use cases (Create/Update/Get/List/Delete, Set/Remove image),
│                      integrity rules and ports for external services (ImageStorage, ImageInspector).
├── infrastructure/
│   ├── images.py      Pillow inspector + Django storage adapter for card images.
│   └── persistence/   Django app: ORM models, migrations, mappers, DjangoRepository, seed command.
├── presentation/api/  DRF serializers, one generic EntityViewSet, exception handler, routes.
└── container.py       Composition root: wires repositories, rules and use cases.
```

- **Single responsibility**: one class per use case; serializers only validate HTTP shape; entities own their invariants.
- **Open/closed**: relationships are enforced by composable `IntegrityRule`s (`ReferenceExists`,
  `CampaignBelongsToSystem`, `ImmutableField`). A new resource is a new entity, model, serializer and
  one line in `container.py` / `urls.py`.
- **Liskov / interface segregation**: every repository implements the small `Repository[E]` port; unit tests
  use an in-memory implementation.
- **Dependency inversion**: use cases depend on the port, never on Django.

### Domain rules

- Items, races and classes belong to a system and optionally to one campaign **of that system**.
- The image of a card is only changed through its image endpoint, never through create/update input.
  Replacing, removing or deleting a card removes the old file.
- A campaign cannot move to another system after creation.
- Deleting a system deletes everything in it; deleting a campaign keeps its content (unlinked);
  deleting a race or class deletes its skills.

## API

All resources live under `/api/` and share the same contract.

| Resource | Path | Filters (query params) |
| --- | --- | --- |
| RPG systems | `/api/systems/` | — |
| Campaigns | `/api/campaigns/` | `system` |
| Items | `/api/items/` | `system`, `campaign`, `rarity`, `item_type` |
| Races | `/api/races/` | `system`, `campaign` |
| Race skills | `/api/race-skills/` | `system`, `race`, `kind`, `level` |
| Classes | `/api/classes/` | `system`, `campaign` |
| Class skills | `/api/class-skills/` | `system`, `character_class`, `kind`, `level` |

Every list also accepts `search`, `ordering` (field name, `-` for descending), `page`, `page_size` (max 500)
and `ids=1,2,3`. Lists answer `{count, page, page_size, total_pages, results}`. Validation errors answer
`400` with `{field: [messages]}`, whether they come from the serializer or from a domain rule.
`GET /api/meta/` returns the rarity and skill-kind choices.

Every resource also has `POST /api/<resource>/<id>/image/` (multipart field `image`) to set or replace
the card image and `DELETE /api/<resource>/<id>/image/` to remove it. Cards expose `background_color`
(writable, `#rrggbb`) and `image_url` (read-only).

## Frontend structure

```
frontend/src/
├── api/          fetch wrapper, typed REST client per resource
├── domain/       entity types and choices (rarities, skill kinds)
├── resources/    one declarative definition per resource: form fields, filters, columns, card mapping
├── components/   generic EntityPage (filters in the URL, cards/table views, selection), form modal,
│                 GameCard (6 × 9 cm), print dialog and print sheet
└── pages/        getting started
```

Adding a resource to the UI is a new entry in `resources/definitions.tsx`.

## Not in this MVP

No authentication or per-user data; A4 only (Letter fits only two rows of cards). Images of cards removed
by a cascade (e.g. deleting a whole system) stay on disk.
