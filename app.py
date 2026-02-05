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
    # Sessões CONFIRMADAS (vínculo existe)
    sql_confirmadas = db.text("""
        SELECT s.*
        FROM sessoes_tutoria s
        JOIN aluno_sessao_tutoria ast
            ON s.id = ast.sessao_tutoria_id
        WHERE ast.aluno_id = :aluno
    """)

    tutorias_confirmadas = db.session.execute(
        sql_confirmadas,
        {'aluno': current_user.id}
    ).fetchall()

    return render_template(
        'aluno/tutorias.html',
        confirmadas=tutorias_confirmadas
    )

@app.route('/aluno/historico')
@login_required
def aluno_historico():
    return render_template('aluno/historico.html', usuario=current_user)


@app.route('/aluno/perfil')
@login_required
def aluno_perfil():
    return render_template('aluno/perfil.html',usuario=current_user)

@app.route('/aluno/marcar', methods=['GET', 'POST'])
@login_required
def aluno_marcar():
    if request.method == 'POST':
        sessao_id = request.form.get('id_sessao')
        
        if not sessao_id:
            flash('Selecione uma sessão válida.')
            return redirect(url_for('aluno_marcar'))

        try:
            db.session.execute(db.text("INSERT IGNORE INTO alunos (id) VALUES (:id)"), {'id': current_user.id})
            
            sql = db.text("INSERT INTO aluno_sessao_tutoria (aluno_id, sessao_tutoria_id) VALUES (:a, :s)")
            db.session.execute(sql, {'a': current_user.id, 's': sessao_id})
            
            db.session.commit()
            flash('Inscrição confirmada com sucesso!')
            return redirect('/painel')
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO DE GRAVAÇÃO: {e}") # Olhe o terminal do VS Code/Python
            flash('Erro: Você já está inscrito ou a sessão é inválida.')
            return redirect('/painel')

    disciplinas = Disciplina.query.all()
    sessoes_db = SessaoTutoria.query.all()

    sessoes_lista = []
    
    for s in sessoes_db:
        tutor_u = Usuario.query.get(s.tutor_id)
        tutor_t = Tutor.query.get(s.tutor_id)
        sessoes_lista.append({
            'id': s.id,
            'data': s.data.strftime('%d/%m/%Y') if s.data else '',
            'horario': s.horario.strftime('%H:%M') if s.horario else '',
            'tutor_nome': tutor_u.nome if tutor_u else 'Tutor',
            'disciplina_id': tutor_t.id_disciplina if tutor_t else None,
            'turno': tutor_t.turno if tutor_t else 'N/A'
        })

    return render_template('aluno/marcar.html', disciplinas=disciplinas, sessoes_js=sessoes_lista)


@app.route('/tutor/decisao/<int:sessao_id>/<int:aluno_id>/<opcao>')
@login_required
def decisao_tutoria(sessao_id, aluno_id, opcao):
    # Verifica se o usuário é tutor
    if current_user.funcao != 'tutor':
        flash('Acesso negado')
        return redirect('/painel')

    if opcao == 'recusar':
        try:
            sql = db.text("""
                DELETE FROM aluno_sessao_tutoria 
                WHERE aluno_id = :aluno_id AND sessao_tutoria_id = :sessao_id
            """)
            db.session.execute(sql, {'aluno_id': aluno_id, 'sessao_id': sessao_id})
            db.session.commit()
            flash('Aluno removido da sessão com sucesso!')
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao deletar: {e}")
            flash('Erro ao processar a remoção.')

    return redirect(url_for('tutor_historico'))

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

    sessoes_db = SessaoTutoria.query.all()

    lista_formatada = []

    for s in sessoes_db:

        sql_alunos = db.text("""
            SELECT u.id, u.nome
            FROM aluno_sessao_tutoria ast
            JOIN alunos a ON a.id = ast.aluno_id
            JOIN usuarios u ON u.id = a.id
            WHERE ast.sessao_tutoria_id = :sid
        """)

        alunos_inscritos = db.session.execute(
            sql_alunos,
            {'sid': s.id}
        ).fetchall()

        sql_prof = db.text("""
            SELECT u.nome
            FROM professoresOrientadores po
            JOIN professores p ON p.id = po.id
            JOIN usuarios u ON u.id = p.id
            WHERE po.id = :pid
        """)

        professor = db.session.execute(
            sql_prof,
            {'pid': s.professor_orientador_id}
        ).fetchone()

        lista_formatada.append({
            'sessao': s,
            'alunos': alunos_inscritos,
            'professor_orientador': professor.nome if professor else 'Não informado'
        })

    return render_template(
        'servidor/tutorias.html',
        sessoes=lista_formatada
    )



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


@app.route('/tutor/historico')
@login_required
def tutor_historico():
    # 1. Busca as sessões que pertencem ao tutor logado
    sessoes_db = SessaoTutoria.query.filter_by(tutor_id=current_user.id).all()
    
    lista_formatada = []
    for s in sessoes_db:
        # 2. Busca manual dos alunos vinculados via SQL JOIN
        sql = db.text("""
            SELECT u.id, u.nome 
            FROM usuarios u
            JOIN aluno_sessao_tutoria ast ON u.id = ast.aluno_id
            WHERE ast.sessao_tutoria_id = :sid
        """)
        alunos_inscritos = db.session.execute(sql, {'sid': s.id}).fetchall()
        
        lista_formatada.append({
            'sessao': s,
            'alunos': alunos_inscritos
        })

    return render_template('tutor/historico.html', sessoes=lista_formatada)


@app.route('/tutor/comunicacao')
@login_required
def tutor_comunicacao():
    return render_template('tutor/comunicacao.html', usuario=current_user)



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