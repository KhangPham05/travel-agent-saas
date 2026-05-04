# ThriftyBackpacker Vue UI

This Vue/Vite frontend is connected to the FastAPI backend.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

The dev server proxies `/api` to `http://localhost:8000`, so start the backend first with:

```bash
uv run uvicorn app.main:app --reload
```

Implemented UI behavior:

- Searches `GET /api/v1/trips/search`
- Shows complete flight + hostel + activity trip plans
- Calculates total trip cost in real time
- Filters returned plans by budget
- Displays cheapest plans first
- Shows a budget warning for over-budget custom selections
- Demonstrates tenant-specific pricing with `tenant_a` and `tenant_b`
- Saves and verifies bookings through the backend booking APIs
