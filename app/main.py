from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.v1.router import api_router
from app.core.database import Base, SessionLocal, engine
import app.models  # noqa: F401 - registers SQLAlchemy models
from app.models.booking import Tenant, User
from app.services.trip_service import tenant_ids, tenant_name

app = FastAPI(
    title="Travel Agency API",
    description="Budget backpacker travel planner with search, aggregation, tenant pricing, and booking persistence.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



def _add_sqlite_column_if_missing(table_name: str, column_name: str, column_definition: str) -> None:
    """Compatibility migration for an existing local fallback.db from the earlier backend."""
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))

def initialize_database() -> None:
    """Create SQLite tables and seed tenants/demo users for local review."""
    Base.metadata.create_all(bind=engine)
    _add_sqlite_column_if_missing("users", "Tenant_Id", "VARCHAR")
    _add_sqlite_column_if_missing("bookings", "Tenant_Id", "VARCHAR")
    db = SessionLocal()
    try:
        for tenant_id in tenant_ids():
            if not db.query(Tenant).filter(Tenant.Tenant_Id == tenant_id).first():
                db.add(
                    Tenant(
                        Tenant_Id=tenant_id,
                        Name=tenant_name(tenant_id),
                        Description="Demo tenant for Phase 1 SaaS pricing isolation.",
                    )
                )

        if not db.query(User).filter(User.User_ID == 1).first():
            db.add(
                User(
                    User_ID=1,
                    Tenant_Id="tenant_a",
                    First_Name="Max",
                    Last_Name="Johnson",
                    Email="max.johnson@example.com",
                    Phone_Number="555-1500",
                )
            )

        for tenant_id in tenant_ids():
            email = f"demo.{tenant_id}@thriftybackpacker.example"
            if not db.query(User).filter(User.Email == email).first():
                db.add(
                    User(
                        Tenant_Id=tenant_id,
                        First_Name="Max",
                        Last_Name="Johnson",
                        Email=email,
                        Phone_Number="555-0100",
                    )
                )
        db.commit()
    finally:
        db.close()


initialize_database()
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "message": "Travel Agency API is running. Open /docs for Swagger or use /api/v1/trips/search.",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
