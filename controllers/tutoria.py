from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from models import SessaoTutoria, Tutor, ProfessorOrientador, db, Aluno, aluno_sessao_tutoria
from datetime import datetime

bp_tutoria = Blueprint('tutoria', __name__)

@bp_tutoria.route('/sessoes')
@login_required
def listar_sessoes():
    sessoes = SessaoTutoria.query.all()
    return render_template('sessao_tutoria_listar.html', sessoes=sessoes)

@bp_tutoria.route('/sessoes/cadastrar', methods=['GET', 'POST'])
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
    sessao = SessaoTutoria.query.get_or_404(id)
    
    if current_user.funcao != 'servidor' and sessao.tutor_id != current_user.id:
        flash('Acesso negado!')
        return redirect('/painel')

    if request.method == 'POST':
        data_horario_str = request.form.get('data_horario')
        try:
            # Converte a string do HTML "YYYY-MM-DDTHH:MM" para objeto datetime
            dt_obj = datetime.strptime(data_horario_str, '%Y-%m-%dT%H:%M')
            
            sessao.data = dt_obj.date()
            sessao.horario = dt_obj.time()
            sessao.descricao = request.form.get('descricao')
            
            db.session.commit()
            flash('Sessão atualizada com sucesso!')
            return redirect('/tutor/pendentes') # Ou a rota de listagem que preferir
        except ValueError:
            flash('Erro no formato da data.')
    
    return render_template('tutor/editar_atividade.html', sessao=sessao)

@bp_tutoria.route('/sessoes/deletar/<int:id>')
@login_required
def deletar_sessao(id):
    sessao = SessaoTutoria.query.get_or_404(id)
    
    # Segurança
    if current_user.funcao != 'servidor' and sessao.tutor_id != current_user.id:
        flash('Acesso negado!')
    else:
        db.session.delete(sessao)
        db.session.commit()
        flash('Sessão excluída com sucesso!')
        
    return redirect('/painel')

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

@bp_tutoria.route('/tutores/perfil/<int:id>')
@login_required
def perfil_tutor(id):

    tutor = Tutor.query.get_or_404(id)
    return render_template('tutor_perfil.html', tutor=tutor)



@bp_tutoria.route('/sessoes/historico')
@login_required
def listar_historico():
    if current_user.funcao == 'servidor':
        sessoes = SessaoTutoria.query.all()
        titulo = "Histórico Geral de Tutorias"
    
    elif current_user.funcao == 'aluno':
        sessoes = [s for s in SessaoTutoria.query.all() if current_user in s.alunos]
        titulo = "Meus Atendimentos Realizados"
    
    else:
        flash("Acesso não autorizado para esta função.")
        return redirect('/painel')

    return render_template('sessao_tutoria_listar.html', sessoes=sessoes, titulo=titulo, modo='historico')

#----------------------------------------------------------------------------

@bp_tutoria.route('/sessoes/registrar-atividade', methods=['POST'])
@login_required
def registrar_atividade():
    if current_user.funcao != 'tutor':
        flash('Acesso negado')
        return redirect('/painel')

    tipo_atividade = request.form.get('tipo_atividade')
    data_horario_str = request.form.get('data_horario') # Recebe 'YYYY-MM-DDTHH:MM'
    descricao = request.form.get('descricao')
    matricula = request.form.get('matricula')

    try:
        dt_obj = datetime.strptime(data_horario_str, '%Y-%m-%dT%H:%M')

        data_final = dt_obj.date()   # Extrai apenas 2026-02-03
        horario_final = dt_obj.time() # Extrai apenas 22:30:00

        tutor_info = Tutor.query.get(current_user.id)

        nova_sessao = SessaoTutoria(
            horario=horario_final, # Agora é um objeto Time
            data=data_final,       # Agora é um objeto Date
            descricao=descricao,
            tutor_id=current_user.id,
            professor_orientador_id=tutor_info.id_professorOrientador if tutor_info else None
        )

        # 5. Vínculo com o Aluno (se houver matrícula)
        if tipo_atividade == 'aluno' and matricula:
            aluno = Aluno.query.get(matricula)
            if aluno:
                nova_sessao.alunos.append(aluno)
            else:
                flash(f'Aviso: Aluno {matricula} não encontrado. Sessão salva sem vínculo.')

        db.session.add(nova_sessao)
        db.session.commit()
        flash('Atividade registrada com sucesso!')

    except ValueError as e:
        print(f"Erro de formato de data: {e}")
        flash('Formato de data/hora inválido.')
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar: {e}")
        flash('Erro interno ao salvar no banco.')

    return redirect('/painel')
