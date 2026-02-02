# from flask import Flask, render_template, request, redirect
# import json
from flask import Flask, render_template
from utils import db, lm
import os
from dotenv import load_dotenv
from controllers.usuarios import bp_usuarios
from controllers.tutoria import bp_tutoria
from controllers.grupo import bp_grupo
from flask_migrate import Migrate
from flask_login import login_required, current_user
from commands.criar_servidor import criar_servidor

load_dotenv()

app = Flask(__name__)

app.register_blueprint(bp_usuarios)
app.register_blueprint(bp_tutoria)
app.register_blueprint(bp_grupo)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db_usuario = os.getenv('DB_USERNAME')
db_senha = os.getenv('DB_PASSWORD')
db_mydb = os.getenv('DB_DATABASE')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

conexao = f"mysql+pymysql://{db_usuario}:{db_senha}@{db_host}:{db_port}/{db_mydb}"
app.config['SQLALCHEMY_DATABASE_URI'] = conexao
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
lm.init_app(app)
migrate = Migrate(app, db)
app.cli.add_command(criar_servidor)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/tutor/home')

def tutor_home():
    return render_template('tutor/tutor_home.html')

@app.route("/tutor/perfil")
def perfil():
    return render_template("tutor/perfil.html")

@app.route("/tutor/historico")
def historico():
    return render_template ("tutor/historico.html")



@app.route('/tutor/tutorias')
@login_required
def tutor_tutorias():
    return render_template('tutor/tutor_tutorias.html')

@app.route('/tutorado/home')
def tutorado_home():
    return render_template('tutorado/home.html')

@app.route('/tutorado/marcar')
def tutorado_marcar():
    return render_template('tutorado/marcar.html')


@app.route('/tutorado/historico')
def tutorado_historico():
    return render_template('tutorado/historico.html')


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


if __name__ == '__main__':
    app.run(debug=True)