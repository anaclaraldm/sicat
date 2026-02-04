# from flask import Flask, render_template, request, redirect
# import json
from flask import Flask, render_template,flash, redirect
from utils import db, lm
import os
from dotenv import load_dotenv
from controllers.usuarios import bp_usuarios
from controllers.tutoria import bp_tutoria
from controllers.grupo import bp_grupo
from flask_migrate import Migrate
from flask_login import login_required, current_user
from commands.criar_servidor import criar_servidor
from models import Usuario, SessaoTutoria, Tutor, ProfessorOrientador, Disciplina

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

#---------------------------------------------------------------

@app.route('/aluno/home')
@login_required
def aluno_home():
    return render_template('aluno/aluno.html')

@app.route('/aluno/tutorias')
@login_required
def aluno_tutorias():
    return render_template('aluno/tutorias.html')

@app.route('/aluno/historico')
@login_required
def aluno_historico():
    return render_template('aluno/historico.html')

@app.route('/aluno/perfil')
@login_required
def aluno_perfil():
    return render_template('aluno/perfil.html')

@app.route('/aluno/marcar')
@login_required
def aluno_marcar():
    sessoes_vagas = SessaoTutoria.query.all() 
    disciplinas = Disciplina.query.all()
    
    lista_sessoes_js = []
    for s in sessoes_vagas:
        lista_sessoes_js.append({
            "id": s.id,
            "disciplina_id": s.tutor.disciplina_id, # Buscando via relação tutor -> disciplina
            "tutor": s.tutor.usuario.nome if s.tutor and s.tutor.usuario else "Tutor",
            "data": s.data.strftime('%d/%m/%Y'),
            "horario": s.horario.strftime('%H:%M')
        })
    
    return render_template('aluno/marcar.html', 
                           sessoes_js=lista_sessoes_js, 
                           disciplinas=disciplinas)
#---------------------------------------------------------


@app.route('/servidor/home')
@login_required
def servidor_home():
    contagens = {
        'usuarios': Usuario.query.count(),
        'tutorias': SessaoTutoria.query.count(),
        'tutores': Usuario.query.filter_by(funcao='tutor').count(),
        'orientadores': Usuario.query.filter_by(funcao='professor_orientador').count()
    }
    return render_template('servidor/servidor.html', status=contagens)

@app.route('/servidor/perfil')
@login_required
def servidor_perfil():
    return render_template('servidor/perfil.html')

@app.route('/servidor/tutorias')
@login_required
def servidor_tutorias():
    return render_template('servidor/tutorias.html')

@app.route('/servidor/pendentes')
@login_required
def servidor_pendentes():
    return render_template('servidor/pendentes.html')

@app.route('/servidor/comunicacao')
@login_required
def servidor_comunicacao():
    return render_template('servidor/comunicacao.html')
#-----------------------------------------------------------------


@app.route('/tutor/home')
@login_required
def tutor_home():
    return render_template('tutor/tutor.html')


@app.route('/tutor/perfil')
@login_required
def tutor_perfil():
    return render_template('tutor/perfil.html')

@app.route('/tutor/tutorias')
@login_required
def tutor_tutorias():
    return render_template('tutor/tutorias.html')


@app.route('/tutor/comunicacao')
@login_required
def tutor_comunicacao():
    return render_template('tutor/comunicacao.html')

@app.route('/tutor/historico')
@login_required
def tutor_historico():
    return render_template('tutor/historico.html')


@app.route('/tutor/pendentes') 
@login_required
def tutor_pendentes():
    if current_user.funcao != 'tutor':
        flash('Acesso negado')
        return redirect('/painel')

    atividades = SessaoTutoria.query.filter_by(tutor_id=current_user.id).order_by(SessaoTutoria.data.desc()).all()

    return render_template('tutor/pendentes.html', atividades=atividades)

#-----------------------------------------------------------------

@app.route('/painel')
@login_required
def painel():
    if current_user.funcao == 'servidor':
        contagens = {
            'usuarios': Usuario.query.count(),
            'tutorias': SessaoTutoria.query.count(),
            'tutores': Usuario.query.filter_by(funcao='tutor').count(),
            'orientadores': Usuario.query.filter_by(funcao='professor_orientador').count()
        }
        return render_template('servidor/servidor.html', status=contagens)
    if current_user.funcao == 'professor_orientador':
        return render_template('professor_orientador/professor_orientador.html')
    if current_user.funcao == 'professor':
        return render_template('professor/professor.html')
    if current_user.funcao == 'tutor':
        return render_template('tutor/tutor.html')
    return render_template('aluno/aluno.html')


@app.route('/acesso-negado')
def acesso_negado():
    return render_template('acesso_negado.html')


if __name__ == '__main__':
    app.run(debug=True)