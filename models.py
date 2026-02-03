from utils import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    senha = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    funcao = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_on': funcao,
        'polymorphic_identity': 'usuario'
    }

#Servidor----------------------------------------

class Servidor(Usuario):
    __tablename__ = 'servidores'

    id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        primary_key=True
    )

    __mapper_args__ = {
        'polymorphic_identity': 'servidor'
    }


#Aluno----------------------------------------

class Aluno(Usuario):
    __tablename__ = 'alunos'

    id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        primary_key=True  
    )

                     
    __mapper_args__ = {
        'polymorphic_identity': 'aluno'
    }


#Servidor----------------------------------------

class Tutor(Aluno):
    __tablename__ = 'tutores'

    id = db.Column(
        db.Integer,
        db.ForeignKey('alunos.id'),
        primary_key=True
    )

    turno = db.Column(db.String(100))
    
    id_disciplina = db.Column(
        db.Integer,
        db.ForeignKey('disciplinas.id'),
        nullable=False
    )

    id_professorOrientador = db.Column(
        db.Integer,
        db.ForeignKey('professoresOrientadores.id'),
        nullable=False
    )


    __mapper_args__ = {
        'polymorphic_identity': 'tutor'
    }


#Professor----------------------------------------

class Professor(Usuario):
    __tablename__ = 'professores'

    id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        primary_key=True
    )

    disciplina_lecionada = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'professor'
    }


#ProfessorOrientador----------------------------------------

class ProfessorOrientador(Professor):
    __tablename__ = 'professoresOrientadores'

    id = db.Column(
        db.Integer,
        db.ForeignKey('professores.id'),
        primary_key=True
    )

    disciplina_orientação = db.Column(
        db.Integer,
        db.ForeignKey('disciplinas.id'),
        nullable=False
    )


    __mapper_args__ = {
        'polymorphic_identity': 'professor_orientador'
    }


#Disciplina----------------------------------------

class Disciplina(db.Model):
    __tablename__ = 'disciplinas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))


#SessãoTutoria----------------------------------------

class SessaoTutoria(db.Model):
    __tablename__ = 'sessoes_tutoria'

    id = db.Column(db.Integer, primary_key=True)

    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.Time, nullable=False)
    descricao = db.Column(db.Text)

    tutor_id = db.Column(
        db.Integer,
        db.ForeignKey('tutores.id'),
        nullable=False
    )

    professor_orientador_id = db.Column(
        db.Integer,
        db.ForeignKey('professoresOrientadores.id'),
        nullable=False
    )


#Grupodeestudos----------------------------------------

class GrupoEstudos(db.Model):
    __tablename__ = 'grupos_estudo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text)
    descricao = db.Column(db.Text)

    criador_id = db.Column(
        db.Integer,
        db.ForeignKey('alunos.id'),
        nullable=False
    )

#Tabelas resultantes dos relacionamentos N:N, associativas.

aluno_disciplina = db.Table(
    'aluno_disciplina',
    db.Column('aluno_id', db.Integer, db.ForeignKey('alunos.id'), primary_key=True),
    db.Column('disciplina_id', db.Integer, db.ForeignKey('disciplinas.id'), primary_key=True)
)

aluno_sessao_tutoria = db.Table(
    'aluno_sessao_tutoria',
    db.Column('aluno_id', db.Integer, db.ForeignKey('alunos.id'), primary_key=True),
    db.Column('sessao_tutoria_id', db.Integer, db.ForeignKey('sessoes_tutoria.id'), primary_key=True)
)

aluno_grupo_estudo = db.Table(
    'aluno_grupo_estudo',
    db.Column('aluno_id', db.Integer, db.ForeignKey('alunos.id'), primary_key=True),
    db.Column('grupo_estudo_id', db.Integer, db.ForeignKey('grupos_estudo.id'), primary_key=True)
)

professor_disciplina = db.Table(
    'professor_disciplina',
    db.Column('professor_id', db.Integer, db.ForeignKey('professores.id'), primary_key=True),
    db.Column('disciplina_id', db.Integer, db.ForeignKey('disciplinas.id'), primary_key=True)
)

professor_orientador_disciplina = db.Table(
    'professor_orientador_disciplina',
    db.Column('professor_orientador_id', db.Integer, db.ForeignKey('professoresOrientadores.id'), primary_key=True),
    db.Column('disciplina_id', db.Integer, db.ForeignKey('disciplinas.id'), primary_key=True)
)

tutor_servidor_etep = db.Table(
    'tutor_servidor_etep',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutores.id'),primary_key=True),
    db.Column('servidor_etep_id', db.Integer, db.ForeignKey('servidores.id'),primary_key=True)
)


servidor_etep_sessao_tutoria = db.Table(
    'servidor_etep_sessao_tutoria',
    db.Column('sessao_tutoria_id',db.Integer,db.ForeignKey('sessoes_tutoria.id'),primary_key=True),
    db.Column('servidor_etep_id', db.Integer, db.ForeignKey('servidores.id'), primary_key=True)
)