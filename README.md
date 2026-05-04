# Travel Agency SaaS - ThriftyBackpacker

This project includes the completed Phase 2 backend-to-UI integration for the Phase 1 backpacker budget planner.

## What is implemented

- FastAPI backend with Swagger at `http://localhost:8000/docs`
- Vue UI at `http://localhost:5173`
- Search APIs for flights, hotels, and attractions
- Aggregated trip planner API: `GET /api/v1/trips/search`
- Budget filtering: only complete trip combinations at or below the user's budget are returned
- Total cost calculation: `flight + (hostel price x nights) + activities`
- Cheapest-first sorting with shortest flight duration as the tie-breaker
- Budget warning in the UI when a selected trip exceeds the budget
- SaaS tenant pricing isolation with `tenant_a` and `tenant_b`
- Booking persistence with `POST /api/v1/bookings/`
- Booking verification with `GET /api/v1/bookings/{booking_id}`
- SQLite tables are created automatically on backend startup
- Demo user `User_Id = 1` is seeded automatically for UI bookings
- RapidAPI endpoints still exist; if `RAPIDAPI_KEY` is not configured, they return tenant-scoped demo data so the demo does not crash

## Run the backend

From the project root:

```bash
uv run uvicorn app.main:app --reload
```

or, if dependencies are installed in your active Python environment:

```bash
uvicorn app.main:app --reload
```

The API will run on:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Run the frontend

From the `frontend/` folder:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so the default UI configuration works with the backend above.

## Main demo flow

1. Start the backend.
2. Start the frontend.
3. Use the default search values: Tenant A, SFO to LON, London, budget 1500.
4. Click **Search trips**.
5. Confirm the results are sorted cheapest first.
6. Change selected flight, hostel, or activities and confirm the total updates immediately.
7. Lower the budget to trigger the budget warning.
8. Click **Book selected trip**.
9. The UI saves the booking and verifies persistence through `GET /api/v1/bookings/{booking_id}`.
10. Change the tenant to Tenant B and search again to demonstrate isolated agency-specific prices.

## Important endpoints

### Aggregated Phase 1/Phase 2 UI endpoint

```http
GET /api/v1/trips/search?tenant_id=tenant_a&from_code=SFO&to_code=LON&location=London&depart_date=2026-05-01&check_in=2026-05-01&check_out=2026-05-06&budget=1500
```

### Search APIs

```http
GET /api/v1/flights/search
GET /api/v1/hotels/search
GET /api/v1/attractions/search
```

### Booking APIs

```http
GET  /api/v1/bookings/
POST /api/v1/bookings/
GET  /api/v1/bookings/{booking_id}
```

## Environment variables

Optional:

```bash
RAPIDAPI_KEY=your_key_here
DATABASE_URL=sqlite:///./fallback.db
```

If `RAPIDAPI_KEY` is omitted, the project uses deterministic demo data for searches so the UI remains functional during review.
