from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import pytz
import psycopg2
import os
import psycopg2.extras
import unicodedata
app = Flask(__name__)

# Definindo o fuso horário de Brasília (BRT - Brasilia Time)
brasilia_tz = pytz.timezone('America/Sao_Paulo')

# Obtendo o horário atual no fuso horário de Brasília
horario_br = datetime.now(brasilia_tz).strftime("%d/%m/%Y %H:%M:%S")
# Função para conectar ao PostgreSQL usando URI de Conexão
def conectar_db():
    # URI de Conexão do PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:etrm7kirRbmCKAGh@maliciously-factual-longspur.data-1.use1.tembo.io:5432/postgres')
    
    # Conexão com o PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Criando a tabela (realize isso no banco de dados se ainda não existir)
def criar_tabela():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS folhaponto (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        entrada TEXT,
        saida TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Inicializando a tabela ao iniciar o app
criar_tabela()

# Função para obter os registros de ponto
def lregistros():
    conn = conectar_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # Usando RealDictCursor
    cur.execute("SELECT * FROM folhaponto")
    registros = cur.fetchall()
    conn.close()
    print(registros)
    return registros

# Função para salvar os registros em um arquivo JSON
def lsavlar():
    registros = lregistros()
    with open("listaponto.json", "w") as lre:
        json.dump(registros, lre, indent=4)

@app.route('/')
def index():
    registros = lregistros()
    return render_template('index.html', registros=registros)

@app.route("/<nome>", methods=["GET"])
def requerir(nome):
    conn = conectar_db()
    cur = conn.cursor()

    # Definir a consulta SQL
    query = "SELECT * FROM folhaponto WHERE nome = %s"
    
    # Executar a consulta passando o nome
    cur.execute(query, (nome,))

    # Obter os resultados
    resultados = cur.fetchall()

    # Fechar o cursor e a conexão
    cur.close()
    conn.close()

    # Inicializar a lista de registros filtrados
    registroreturn = []

    # Filtra os registros onde 'saida' não é None (supondo que 'saida' seja o índice 2)
    for registro in resultados:
        if registro[2] is not None:  # A coluna 'saida' está no índice 2 (ajuste conforme necessário)
            registroreturn.append({
                "id": registro[0],  # Ajuste os índices conforme a estrutura da sua tabela
                "nome": registro[1],
                "entrada": registro[2],
                "saida": registro[3]
            })

    def normalizar(texto):
        return unicodedata.normalize('NFC', texto).strip().lower()

    # Normalizar o nome e filtrar os registros
    registroreturn = [
        registro for registro in registroreturn if normalizar(registro['nome']) == normalizar(nome)
    ]
    
    return jsonify(registroreturn)


@app.route('/registrar_entrada', methods=['POST'])  
def registrar_entrada():
    nome = request.form['nome']
    horario = datetime.now(brasilia_tz).strftime("%D  %H:%M:%S")

    # Verifica se já existe um registro de entrada sem saída
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM folhaponto WHERE nome = %s AND saida IS NULL", (nome,))
    existe_entrada = cur.fetchone()

    if not existe_entrada:
        cur.execute("INSERT INTO folhaponto (nome, entrada, saida) VALUES (%s, %s, %s)", (nome, horario, None))
        conn.commit()
    conn.close()
    print(lregistros)
    return redirect(url_for('index'))

@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    nome = request.form['nome']
    horario = datetime.now(brasilia_tz).strftime("%D  %H:%M:%S")

    # Atualiza o registro de saída
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE folhaponto
    SET saida = %s
    WHERE nome = %s AND saida IS NULL
    """, (horario, nome))
    conn.commit()
    conn.close()
    print(lregistros)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)