# from flask import Flask, render_template, request, redirect
# import json
from flask import Flask, render_template
from utils import db, lm
import os
from controllers.usuarios import bp_usuarios
from controllers.tutoria import bp_tutoria
from controllers.grupo import bp_grupo
from flask_migrate import Migrate
from flask_login import login_required, current_user

app = Flask(__name__)

app.register_blueprint(bp_usuarios)
app.register_blueprint(bp_tutoria)
app.register_blueprint(bp_grupo)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_usuario = os.getenv('DB_USERNAME')
db_senha = os.getenv('DB_PASSWORD')
db_mydb = os.getenv('DB_DATABASE')

conexao = f"mysql+pymysql://{db_usuario}:{db_senha}@{db_host}:{db_port}/{db_mydb}"
app.config['SQLALCHEMY_DATABASE_URI'] = conexao
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
lm.init_app(app)

migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/painel')
@login_required
def painel():
    if current_user.funcao == 'servidor':
        return render_template('servidor.html')
    if current_user.funcao == 'professor_orientador':
        return render_template('professor_orientador.html')
    if current_user.funcao == 'professor':
        return render_template('professor.html')
    if current_user.funcao == 'tutor':
        return render_template('tutor.html')
    return render_template('aluno.html')


@app.route('/acesso-negado')
def acesso_negado():
    return render_template('acesso_negado.html')


#index
# @app.route('/')
# def index():
#     return render_template('index.html')

# def dashboard():
#     dashboard = request.args.get("dashboard") == "1"
#     return dict(dashboar=dashboard)

# #login
# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/login_autenticacao', methods=['POST'])
# def login_autenticacao():
#     matricula = request.form['user']
#     senha = request.form['pin']
#     usuarios = "usuarios.json"
#     arquivo = open(usuarios, 'r', encoding='utf-8')
#     dados = json.load(arquivo)
#     arquivo.close()
#     for usuario in dados:
#         if usuario['user'] == matricula and usuario['senha'] == senha:
#             funcao = usuario['funcao']
#             return redirect(f'/{funcao}?user={usuario["user"]}')
        
#     return render_template('cadastro.html')

# @app.route('/cadastrar')
# def cadastrar():
#     return render_template('cadastro.html')

# #cadastro
# @app.route('/cadastro', methods=['post'])
# def cadastro():
#     user = request.form['user']
#     senha = request.form['pin']
#     funcao = request.form['funcao'] 
#     email= request.form['email'] 
#     telefone= request.form['telefone'] 

#     usuarios = "usuarios.json"

#     arquivo = open(usuarios, 'r', encoding='utf-8')
#     dados = json.load(arquivo)
#     arquivo.close()

#     novo_usuario = {
#         'user': user,
#         'funcao': funcao,
#         'senha': senha,
#         'telefone': telefone,
#          'email': email,
#     }

#     dados.append(novo_usuario)

#     arquivo = open(usuarios, 'w', encoding='utf-8')
#     json.dump(dados, arquivo, indent=4, ensure_ascii=False)
#     arquivo.close()

#     return redirect(f'/{funcao}?user==user')

# def carregar_usuarios():
#     with open('usuarios.json', 'r', encoding='utf-8') as f:
#         return json.load(f)


# def pesquisa(termo):
#     termo = termo.lower() 
#     usuarios = carregar_usuarios()
#     if termo:
#         return [u for u in usuarios if termo in u['funcao'].lower()]
#     else:
#         return []
    
# #servidor
# @app.route('/servidor')
# def servidor():
#     usuario = request.args.get('user') 
#     query = request.args.get('q', '')
#     resultados = pesquisa(query)
#     return render_template('servidor.html', usuario=usuario, resultados=resultados)

# #tutor
# @app.route('/tutor')
# def tutor():
#     usuario = request.args.get('user')
#     return render_template('tutor.html', usuario=usuario)

# #tutorado
# @app.route('/tutorado')
# def tutorado():
#     usuario = request.args.get('user')
#     return render_template('tutorado.html', usuario=usuario)

# #professor
# @app.route('/professor')
# def professor():
#     usuario = request.args.get('user')
#     return render_template('professor.html', usuario=usuario)

# #professor_orientador
# @app.route('/professor_orientador')
# def professor_orientador():
#     usuario = request.args.get('user')
#     return render_template('professor_orientador.html', usuario=usuario)

# #sessao_tutoria
# @app.route('/sessao_tutoria')
# def sessao_tutoria():
#     return render_template('sessao_tutoria.html')



if __name__ == '__main__':
    app.run(debug=True)