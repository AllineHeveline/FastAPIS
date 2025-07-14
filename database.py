import sqlite3
import hashlib

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect('database.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
# Tabela de Metas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    init_db()
    print("Banco de dados inicializado com sucesso.")

def hash_password(password):
    """Retorna a criptografia de senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    """Adiciona um novo usuário ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Ocorre se o username já existir
        return False
    finally:
        conn.close()

def check_user(username, password):
    """Verifica se um usuário existe e se a senha está correta."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return user

def add_goal(user_id, name, target_amount):
    """Adiciona uma nova meta para um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO goals (user_id, name, target_amount) VALUES (?, ?, ?)",
        (user_id, name, target_amount)
    )
    conn.commit()
    conn.close()

def get_goals(user_id):
    """Retorna todas as metas de um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
    goals = cursor.fetchall()
    conn.close()
    return goals

def get_total_saved(user_id):
    """Calcula o saldo total economizado por um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(current_amount) FROM goals WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0

def update_goal_progress(goal_id, amount_to_add):

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_amount FROM goals WHERE id = ?", (goal_id,))
    current_amount = cursor.fetchone()['current_amount']
    new_amount = current_amount + amount_to_add

    cursor.execute(
        "UPDATE goals SET current_amount = ? WHERE id = ?",
        (new_amount, goal_id)
    )
    conn.commit()
    conn.close()
