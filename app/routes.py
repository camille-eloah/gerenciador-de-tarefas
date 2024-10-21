from flask import render_template, request, redirect, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection, routes
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import User

@app.route('/')
@app.route('/index')
def index():
    user_nome = current_user.user_nome if current_user.is_authenticated else None
    return render_template('index.html', user_nome=user_nome)

@app.route('/logout')
@login_required
def logout():
    logout_user() 
    return render_template('index.html')

@app.route('/cadastro', methods=['POST', 'GET'])
def cadastro():
    if request.method =='POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['pass']

        hashed_senha = generate_password_hash(senha)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO tb_usuarios(user_nome, user_email, user_senha) VALUES(%s,%s,%s)", (nome,email,hashed_senha ))
            conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template ('cadastro.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['pass'] 

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tb_usuarios WHERE user_email = %s', (email,))
            usuario = cursor.fetchone()

            if usuario and check_password_hash(usuario['user_senha'], senha):
                user = User(usuario['user_id'], usuario['user_nome'], usuario['user_email'], usuario['user_senha'])
                login_user(user)
                print("Autenticado")
                return redirect('/')
            else:
                return "Email ou senha inválidos."

    return render_template('login.html')

@login_required
@app.route('/<int:id>/atualizar_tarefa', methods=['GET', 'POST'])  # Edita as tarefas 
def atualizar_tarefa(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nova_desc = request.form['novadesc']
        novo_status = request.form['novostatus']
        novo_prazo = request.form['novoprazo']

        with conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tb_tarefas SET trf_descricao = %s, trf_status = %s, trf_data_limite = %s WHERE trf_id = %s", 
                           (nova_desc, novo_status, novo_prazo, id))
            conn.commit()
        return redirect(url_for('listar_trf'))  

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tb_tarefas WHERE trf_id = %s", (id,))
        tarefa = cursor.fetchone()  

    if tarefa is None:
        return "Tarefa não encontrada", 404
    
    return render_template('atualizar_trf.html', tarefa=tarefa)

@login_required
@app.route('/<int:id>/excluir_tarefa', methods=['GET','POST']) #Remove tarefas por meio do id
def excluir_tarefa(id):
    conn = get_db_connection()
    
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM tb_tarefas WHERE trf_id = %s", (id,))
        conn.commit()
    conn.close()

    return redirect(url_for('listar_trf'))

@login_required
@app.route('/add_trf', methods=['POST', 'GET'])#Adiciona tarefas
def add_trf():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        print(request.form)
        descricao = request.form['desc']
        data_criacao = request.form['data_criacao']
        data_limite = request.form['data_limite']
        status = request.form['status']
        prioridade = request.form['prioridade']
        categoria = request.form['categoria']
        user_id = current_user.id 

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO tb_tarefas(trf_descricao,trf_data_criacao, trf_data_limite, trf_status, trf_prioridade, trf_categoria, trf_user_id) VALUES(%s,%s,%s,%s,%s,%s, %s)", (descricao, data_criacao, data_limite, status, prioridade, categoria, user_id))
            conn.commit()
        conn.close()
        return redirect(url_for('add_trf'))
    
    return render_template ('add_trf.html')

@login_required
@app.route('/listar_trf', methods=['GET', 'POST'])
def listar_trf():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    conn = get_db_connection()
    query = "SELECT * FROM tb_tarefas WHERE trf_user_id = %s"
    params = [current_user.id]
    
    filtro = None

    if request.method == 'POST':
        filtro = request.form.get('filtro')
        # Se houver filtro, chamar a função de filtragem
        if filtro:
            query, params = filtrar_tarefa(filtro, request.form, current_user.id)

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            tarefas = cursor.fetchall()
    except Exception as e:
        print(f"Erro na execução da query: {e}")
        tarefas = []  # Evita que 'tarefas' fique indefinido em caso de erro
    finally:
        conn.close()

    return render_template('listar_trf.html', tarefas=tarefas, filtro=filtro)

def filtrar_tarefa(filtro, form_data, user_id):
    query = "SELECT * FROM tb_tarefas WHERE trf_user_id = %s"
    params = [user_id]

    if not filtro or filtro not in ['Status', 'Data_criacao', 'Data_limite', 'Prioridade', 'Descricao', 'Categoria']:
        return query, params 

    if filtro == 'Status':
        status = form_data.get('status')
        if status:  
            query += " AND trf_status = %s"
            params.append(status)

    elif filtro == 'Data_criacao':
        data_inicial = form_data.get('data_inicial')
        data_final = form_data.get('data_final')
        if data_inicial and data_final:  
            query += " AND trf_data_criacao BETWEEN %s AND %s"
            params.extend([data_inicial, data_final])


    elif filtro == 'Data_limite':
        prazo_inicial = form_data.get('prazo_inicial')
        prazo_final = form_data.get('prazo_final')
        # Verifica tarefas que faltam 3 dias ou que já venceram
        query += " AND (trf_data_limite <= CURDATE() OR trf_data_limite BETWEEN %s AND %s)"
        params.extend([prazo_inicial, prazo_final])


    elif filtro == 'Prioridade':
        prioridade = form_data.get('prioridade')
        if prioridade:  
            query += " AND trf_prioridade = %s"
            params.append(prioridade)

    elif filtro == 'Descricao':
        descricao = form_data.get('descricao')
        if descricao:  
            query += " AND trf_descricao LIKE %s"
            params.append(f"%{descricao}%")

    elif filtro == 'Categoria':
        categoria = form_data.get('categoria')
        if categoria:  
            query += " AND trf_categoria LIKE %s"
            params.append(f"%{categoria}%")

    return query, params
