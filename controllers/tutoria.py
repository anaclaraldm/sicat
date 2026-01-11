from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from models import SessaoTutoria, Tutor, ProfessorOrientador, db, Aluno, aluno_sessao_tutoria

bp_tutoria = Blueprint('tutoria', __name__)

@bp_tutoria.route('/sessoes')
@login_required
def listar_sessoes():
    sessoes = SessaoTutoria.query.all()
    return render_template('sessao_tutoria_listar.html', sessoes=sessoes)

@bp_tutoria.route('/sessoes/novo', methods=['GET', 'POST'])
@login_required
def criar_sessao():
    if current_user.funcao != 'tutor':
        flash('Acesso negado')
        return redirect('/painel')

    if request.method == 'GET':
        return render_template('sessao_tutoria_criar.html', tutores=[current_user])

    nova_sessao = SessaoTutoria(
        horario_inicio=request.form['horario_inicio'],
        horario_fim=request.form['horario_fim'],
        descricao=request.form['descricao'],
        tutor_id=current_user.id,
        professor_orientador_id=request.form['professor_orientador_id']
    )
    db.session.add(nova_sessao)
    db.session.commit()
    flash('Sessão criada com sucesso!')
    return redirect('/sessoes')

@bp_tutoria.route('/sessoes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_sessao(id):
    sessao = SessaoTutoria.query.get(id)
    if current_user.id != sessao.tutor_id:
        flash('Acesso negado')
        return redirect('/painel')

    if request.method == 'GET':
        return render_template('sessao_tutoria_editar.html', sessao=sessao)

    sessao.horario_inicio = request.form['horario_inicio']
    sessao.horario_fim = request.form['horario_fim']
    sessao.descricao = request.form['descricao']
    db.session.commit()
    flash('Sessão atualizada!')
    return redirect('/sessoes')

@bp_tutoria.route('/sessoes/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def deletar_sessao(id):
    sessao = SessaoTutoria.query.get(id)
    if current_user.id != sessao.tutor_id:
        flash('Acesso negado')
        return redirect('/painel')

    db.session.delete(sessao)
    db.session.commit()
    flash('Sessão deletada!')
    return redirect('/sessoes')

@bp_tutoria.route('/sessoes/agendar/<int:id>')
@login_required
def agendar_sessao(id):
    sessao = SessaoTutoria.query.get(id)
    if current_user.funcao != 'aluno':
        flash('Acesso negado')
        return redirect('/painel')

    if current_user in sessao.alunos:
        flash('Você já está inscrito')
        return redirect('/sessoes')
    
    sessao.alunos.append(current_user)
    db.session.commit()
    flash('Agendamento realizado!')
    return redirect('/sessoes')

@bp_tutoria.route('/sessoes/cancelar/<int:id>')
@login_required
def cancelar_sessao(id):
    sessao = SessaoTutoria.query.get(id)
    if current_user.funcao != 'aluno':
        flash('Acesso negado')
        return redirect('/painel')

    if current_user not in sessao.alunos:
        flash('Você não está inscrito')
        return redirect('/sessoes')
    
    sessao.alunos.remove(current_user)
    db.session.commit()
    flash('Agendamento cancelado!')
    return redirect('/sessoes')

@bp_tutoria.route('/tutores')
@login_required
def listar_tutores():
    tutores = Tutor.query.all()
    return render_template('tutores_listar.html', tutores=tutores)

@bp_tutoria.route('/sessoes/filtro')
@login_required
def sessoes_filtro():
    turno = request.args.get('turno')
    dia = request.args.get('dia')
    tutor_id = request.args.get('tutor')

    query = SessaoTutoria.query

    if turno:
        query = query.filter_by(turno=turno)

    if dia:
        query = query.filter(SessaoTutoria.horario_inicio.like(f'{dia}%'))

    if tutor_id:
        query = query.filter_by(tutor_id=tutor_id)

    sessoes = query.all()
    return render_template('sessao_tutoria_listar.html', sessoes=sessoes)