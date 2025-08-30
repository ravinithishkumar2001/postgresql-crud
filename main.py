from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(
        dbname="demo",
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port="5432"
    )


class User(BaseModel):
    name: str
    email: str

class UpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.get("/")
def read_root():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    conn.close()
    return {"PostgreSQL version": version}

@app.post("/users")
def create_user(user: User):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
        (user.name, user.email)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": user_id, "name": user.name, "email": user.email}

@app.get("/users")
def get_users():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users;")
    users = cur.fetchall()
    conn.close()
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user if user else {"error": "User not found"}

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UpdateUser):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    existing = cur.fetchone()
    if not existing:
        conn.close()
        return {"error": "User not found"}

    if user.name:
        cur.execute("UPDATE users SET name = %s WHERE id = %s;", (user.name, user_id))
    if user.email:
        cur.execute("UPDATE users SET email = %s WHERE id = %s;", (user.email, user_id))

    conn.commit()
    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    updated_user = cur.fetchone()
    conn.close()
    return updated_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return {"error": "User not found"}

    cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
    conn.commit()
    conn.close()
    return {"message": f"User {user_id} deleted successfully"}
