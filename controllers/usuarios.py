from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_user, logout_user, login_required
from utils import db, lm
from models import Usuario

bp_usuarios = Blueprint('usuarios', __name__)

@lm.user_loader
def load_user(id):
    return Usuario.query.get(int(id))

@bp_usuarios.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    
    usuario = Usuario(
        nome = request.form['nome'],
        senha = request.form['senha'],
        telefone = request.form['tell'],
        email = request.form['email'],
        funcao = request.form['funcao']
    )

    db.session.add(usuario)
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


