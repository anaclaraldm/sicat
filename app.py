# from flask import Flask, render_template, request, redirect
# import json
from flask import Flask, render_template,flash, redirect, request, url_for
from utils import db, lm
import os
from dotenv import load_dotenv
from controllers.usuarios import bp_usuarios
from controllers.tutoria import bp_tutoria
from controllers.grupo import bp_grupo
from flask_migrate import Migrate
from flask_login import login_required, current_user
from commands.criar_servidor import criar_servidor
from models import Usuario, SessaoTutoria, Tutor, ProfessorOrientador, Disciplina, Aluno

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
    return render_template('aluno/aluno.html',usuario=current_user)

@app.route('/aluno/tutorias')
@login_required
def aluno_tutorias():
    return render_template('aluno/tutorias.html',usuario=current_user)

@app.route('/aluno/historico')
@login_required
def aluno_historico():
    return render_template('aluno/historico.html',usuario=current_user)

@app.route('/aluno/perfil')
@login_required
def aluno_perfil():
    return render_template('aluno/perfil.html',usuario=current_user)


@app.route('/aluno/marcar', methods=['GET', 'POST'])
@login_required
def aluno_marcar():
    if request.method == 'GET':
        disciplinas = Disciplina.query.all()
        sessoes = SessaoTutoria.query.all()
        
        sessoes_js = []
        for s in sessoes:
            tutor_obj = Tutor.query.get(s.tutor_id)
            id_da_disciplina = tutor_obj.id_disciplina if tutor_obj else None
            nome_tutor = tutor_obj.nome if tutor_obj else "Tutor não identificado"
            turno_tutor = tutor_obj.turno if tutor_obj else "N/A"

            sessoes_js.append({
                'id': s.id,
                'disciplina_id': id_da_disciplina,
                'turno': turno_tutor,
                'data': s.data.strftime('%d/%m/%Y') if s.data else "Data a definir",
                'horario': s.horario.strftime('%H:%M') if s.horario else "Horário a definir",
                'tutor_nome': nome_tutor
            })
            
        return render_template('aluno/marcar.html', disciplinas=disciplinas, sessoes_js=sessoes_js)

    id_sessao = request.form.get('id_sessao')
    
    if id_sessao:
        try:
            db.session.execute(db.text(
                """
                INSERT INTO aluno_sessao_tutoria (aluno_id, sessao_tutoria_id) 
                VALUES (:a_id, :s_id)
                """
            ), {'a_id': current_user.id, 's_id': id_sessao})
            
            db.session.commit()
            flash('Solicitação enviada! Agora o tutor precisa confirmar.')
            print(f"DEBUG: Aluno {current_user.id} agendado na sessão {id_sessao}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao agendar: {e}")
            flash('Você já solicitou agendamento para esta tutoria ou ocorreu um erro.')

    return redirect(url_for('aluno_tutorias'))


@app.route('/tutor/decisao/<int:sessao_id>/<int:aluno_id>/<string:opcao>')
@login_required
def decisao_tutoria(sessao_id, aluno_id, opcao):
    if current_user.funcao != 'tutor':
        flash("Acesso restrito a tutores.")
        return redirect('/painel')

    if opcao == 'aceitar':
        flash(f"Você aceitou a tutoria!")
        
    elif opcao == 'recusar':
        try:
            # Também atualizado para sessao_tutoria_id
            db.session.execute(db.text(
                "DELETE FROM aluno_sessao_tutoria WHERE aluno_id = :a_id AND sessao_tutoria_id = :s_id"
            ), {'a_id': aluno_id, 's_id': sessao_id})
            db.session.commit()
            flash("Tutoria recusada. O registro foi removido.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao recusar: {e}")
            flash("Erro ao processar recusa.")

    return redirect(url_for('tutor_tutorias'))

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
    return render_template('servidor/perfil.html',usuario=current_user)

@app.route('/servidor/tutorias')
@login_required
def servidor_tutorias():
    return render_template('servidor/tutorias.html',usuario=current_user)


@app.route('/servidor/comunicacao')
@login_required
def servidor_comunicacao():
    return render_template('servidor/comunicacao.html',usuario=current_user)
#-----------------------------------------------------------------


@app.route('/tutor/home')
@login_required
def tutor_home():
    return render_template('tutor/tutor.html', usuario=current_user)


@app.route('/tutor/perfil')
@login_required
def tutor_perfil():
    return render_template('tutor/perfil.html', usuario=current_user)

@app.route('/tutor/tutorias')
@login_required
def tutor_tutorias():
    # 1. Pegamos as sessões criadas por este tutor
    sessoes_db = SessaoTutoria.query.filter_by(tutor_id=current_user.id).all()
    
    lista_formatada = []
    for s in sessoes_db:
        # 2. Vamos buscar os IDs dos alunos que estão na tabela de ligação para esta sessão
        alunos_ids = db.session.execute(db.text(
            "SELECT aluno_id FROM aluno_sessao_tutoria WHERE sessao_tutoria_id = :s_id"
        ), {'s_id': s.id}).fetchall()
        
        lista_alunos = []
        for row in alunos_ids:
            aluno_obj = Usuario.query.get(row[0])
            if aluno_obj:
                lista_alunos.append(aluno_obj)

        lista_formatada.append({
            'sessao': s,
            'alunos': lista_alunos
        })

    return render_template('tutor/tutorias.html', sessoes=lista_formatada)

@app.route('/tutor/comunicacao')
@login_required
def tutor_comunicacao():
    return render_template('tutor/comunicacao.html', usuario=current_user)

@app.route('/tutor/historico')
@login_required
def tutor_historico():
    return render_template('tutor/historico.html', usuario=current_user)


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