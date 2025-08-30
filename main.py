from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def read_root():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    conn.close()
    return {"PostgreSQL version": version}

@app.post("/users")
def create_user(name: str, email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
        (name, email)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": user_id, "name": name, "email": email}

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
def update_user(user_id: int, name: str = None, email: str = None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return {"error": "User not found"}

    if name:
        cur.execute("UPDATE users SET name = %s WHERE id = %s;", (name, user_id))
    if email:
        cur.execute("UPDATE users SET email = %s WHERE id = %s;", (email, user_id))

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
