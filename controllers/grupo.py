from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from models import GrupoEstudos, db

bp_grupo = Blueprint('grupo', __name__)

@bp_grupo.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
def criar_grupo():
    if current_user.funcao != 'aluno':
        flash('Acesso negado')
        return redirect('/painel')

    if request.method == 'GET':
        return render_template('grupo_criar.html')

    grupo = GrupoEstudos(
        descricao=request.form['descricao'],
        criador_id=current_user.id
    )
    db.session.add(grupo)
    db.session.commit()
    grupo.alunos.append(current_user)
    db.session.commit()
    flash('Grupo criado!')
    return redirect('/grupos')

@bp_grupo.route('/grupos/entrar/<int:id>')
@login_required
def entrar_grupo(id):
    grupo = GrupoEstudos.query.get(id)
    if current_user in grupo.alunos:
        flash('Você já participa')
    else:
        grupo.alunos.append(current_user)
        db.session.commit()
        flash('Você entrou no grupo!')
    return redirect('/grupos')


