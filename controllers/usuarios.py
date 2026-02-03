from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from utils import db, lm
from models import Usuario, Aluno, Professor, Tutor, ProfessorOrientador, SessaoTutoria, Disciplina

bp_usuarios = Blueprint('usuarios', __name__)

@lm.user_loader
def load_user(id):
    return Usuario.query.get(int(id))

@bp_usuarios.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    
    funcao_escolhida = request.form.get('funcao')
    dados = {
        'nome': request.form['nome'],
        'senha': request.form['senha'],
        'telefone': request.form['tell'],
        'email': request.form['email'],
        'funcao': funcao_escolhida
    }

    # DECISÃO DE CLASSE: 
    # Se for professor, usamos a classe Professor para preencher as duas tabelas
    if funcao_escolhida == 'professor':
        novo_usuario = Professor(**dados)
    elif funcao_escolhida == 'aluno':
        # Se você tiver a classe Aluno no models, use-a aqui. 
        # Se não tiver, pode manter Usuario(..).
        novo_usuario = Usuario(**dados) 
    else:
        novo_usuario = Usuario(**dados)

    db.session.add(novo_usuario)
    db.session.commit()

    flash('Dados cadastrados com sucesso')
    return redirect('/login')

@bp_usuarios.route('/autenticar', methods=['POST'])
def autenticar():
    email = request.form.get('email')
    senha = request.form.get('senha')

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and usuario.senha == senha:
        login_user(usuario)
        return redirect('/painel')

    flash('Dados incorretos')
    return redirect('/login')

@bp_usuarios.route('/login')
def login():
    return render_template('login.html')

@bp_usuarios.route('/logoff')
@login_required
def logoff():
    logout_user()
    return redirect('/')

@bp_usuarios.route('/usuarios')
@login_required
def listar():
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    usuarios = Usuario.query.all()
    return render_template('usuarios_listar.html', usuarios=usuarios)

@bp_usuarios.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    usuario = Usuario.query.get(id)

    if request.method == 'GET':
        return render_template('usuarios_editar.html', usuario=usuario)

    usuario.funcao = request.form['funcao']
    db.session.commit()

    return redirect('/usuarios')

@bp_usuarios.route('/usuarios/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    usuario = Usuario.query.get(id)

    if request.method == 'GET':
        return render_template('usuarios_delete.html', usuario=usuario)

    db.session.delete(usuario)
    db.session.commit()
    return redirect('/usuarios')


@bp_usuarios.route('/usuarios/gerenciar-lista/<acao>/<funcao_alvo>')
@login_required
def gerenciar_lista(acao, funcao_alvo):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    if acao == 'promover' and funcao_alvo == 'professor':
        ids_orientadores = db.session.query(ProfessorOrientador.id).all()
        ids_ocupados = [i[0] for i in ids_orientadores]
        
        usuarios = Usuario.query.filter(
            Usuario.funcao == 'professor',
            ~Usuario.id.in_(ids_ocupados)
        ).all()
    else:
        # Para despromover ou para alunos, mantemos a busca normal
        usuarios = Usuario.query.filter_by(funcao=funcao_alvo).all()
    
    titulos = {
        'promover_aluno': "Promover Alunos para Tutoria",
        'promover_professor': "Promover Professores para Orientação",
        'despromover_tutor': "Remover Cargo de Tutor",
        'despromover_orientador': "Remover Cargo de Orientador"
    }
    
    chave = f"{acao}_{funcao_alvo}"
    titulo = titulos.get(chave, "Gerenciamento de Usuários")
        
    return render_template('servidor/gerenciar_usuarios.html', 
                           usuarios=usuarios, 
                           acao=acao, 
                           titulo=titulo)

@bp_usuarios.route('/usuarios/mudar-cargo/<acao>/<int:id>')
@login_required
def mudar_cargo(acao, id):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')
    
    usuario = Usuario.query.get_or_404(id)
    
    if acao == 'promover':
        if usuario.funcao == 'professor': 
            usuario.funcao = 'professor_orientador'
            flash(f'Professor {usuario.nome} agora é Orientador!')
    
    elif acao == 'despromover':
        if usuario.funcao == 'tutor':
            db.session.execute(db.text("DELETE FROM tutores WHERE id = :id"), {'id': id})
            usuario.funcao = 'aluno'
            
        elif usuario.funcao == 'professor_orientador':
            user_id = usuario.id
            nome_professor = usuario.nome 

            db.session.execute(
                db.text("UPDATE usuarios SET funcao = 'professor' WHERE id = :id"),
                {'id': user_id}
            )

            db.session.execute(
                db.text("DELETE FROM professoresOrientadores WHERE id = :id"),
                {'id': user_id}
            )
            
            db.session.commit()

            flash(f'Cargo removido. {nome_professor} agora é apenas Professor.')
            
            return redirect('/painel')
        
        db.session.commit()
        flash(f'Cargo removido. {usuario.nome} agora é apenas Professor.')
    
    db.session.commit()
    return redirect('/painel')

@bp_usuarios.route('/usuarios/configurar-promocao/<int:id>')
@login_required
def configurar_promocao(id):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')
    
    usuario = Usuario.query.get_or_404(id)
    
    orientadores = ProfessorOrientador.query.all()
    
    disciplinas = Disciplina.query.all()
    
    print(f"Disciplinas encontradas: {len(disciplinas)}")
    
    return render_template('servidor/configurar_tutor.html', 
                           usuario=usuario, 
                           disciplinas=disciplinas, 
                           orientadores=orientadores)

@bp_usuarios.route('/usuarios/efetivar-promocao', methods=['POST'])
@login_required
def efetivar_promocao():
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    usuario_id = request.form.get('usuario_id')
    disciplina_id = request.form.get('disciplina_id')
    orientador_id = request.form.get('orientador_id')
    turno = request.form.get('turno')

    usuario = Usuario.query.get(usuario_id)

  
    novo_tutor = Tutor(
        id=usuario.id,
        id_disciplina=disciplina_id,
        id_professorOrientador=orientador_id,
        turno=turno
    )
    
    usuario.funcao = 'tutor' 
    
    db.session.add(novo_tutor)
    db.session.commit()
    
    flash(f'{usuario.nome} promovido a Tutor com sucesso!')
    return redirect('/painel')


@bp_usuarios.route('/usuarios/configurar-orientacao/<int:id>')
@login_required
def configurar_orientacao(id):
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')
    
    usuario = Usuario.query.get_or_404(id)
    
    disciplinas_ocupadas = db.session.query(ProfessorOrientador.disciplina_orientação).all()
    ids_ocupados = [d[0] for d in disciplinas_ocupadas if d[0] is not None]
    
    disciplinas = Disciplina.query.filter(~Disciplina.id.in_(ids_ocupados)).all()
    
    return render_template('servidor/configurar_orientador.html', 
                           usuario=usuario, 
                           disciplinas=disciplinas)


@bp_usuarios.route('/usuarios/efetivar-orientacao', methods=['POST'])
@login_required
def efetivar_orientacao():
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    usuario_id = request.form.get('usuario_id')
    disciplina_id = request.form.get('disciplina_id')
    
    usuario = Usuario.query.get(usuario_id)
    
    if usuario:
        try:
            db.session.execute(
                db.text("INSERT IGNORE INTO professores (id) VALUES (:id)"),
                {'id': usuario_id}
            )

            usuario.funcao = 'professor_orientador'

            orientador_existente = db.session.query(ProfessorOrientador).filter_by(id=usuario_id).first()
            
            if not orientador_existente:
                sql = "INSERT INTO professoresOrientadores (id, disciplina_orientação) VALUES (:id, :discip)"
                db.session.execute(db.text(sql), {'id': usuario_id, 'discip': disciplina_id})
            else:
                orientador_existente.disciplina_orientação = disciplina_id

            db.session.commit()
            flash(f'Professor {usuario.nome} atualizado para Orientador!')
            
        except Exception as e:
            db.session.rollback()
            flash("Erro técnico ao atualizar cargo.")
            print(f"Erro detalhado: {e}")
    
    return redirect('/painel')


@bp_usuarios.route('/servidor/cadastrar-disciplina', methods=['GET', 'POST'])
@login_required
def cadastrar_disciplina():
    if current_user.funcao != 'servidor':
        return redirect('/acesso-negado')

    if request.method == 'GET':
        disciplinas = Disciplina.query.all()
        return render_template('servidor/cadastrar_disciplina.html', disciplinas=disciplinas)


    nome_disciplina = request.form.get('nome')
    if nome_disciplina:
        nova_disciplina = Disciplina(nome=nome_disciplina)
        db.session.add(nova_disciplina)
        db.session.commit()
        flash(f'Disciplina "{nome_disciplina}" cadastrada!')
    
    return redirect(url_for('usuarios.cadastrar_disciplina'))