import copy
import csv
import io
import math
import random
import time

import flask_excel as excel
import mysql.connector
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from mysql.connector import Error
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:@localhost/site"
db = SQLAlchemy(app)
dbCursor = mysql.connector.connect(host='localhost', database='mysql', user='root', password='')

lect = {}
thesis = {}

batch = None

MAX_SCHEDULE_PEJABAT = 0
MAX_SCHEDULE_NONPEJABAT = 0

countFit = 0

excel.init_excel(app)


def func1(c1, c2, c3):
    return c1 + c2 + c3


def func2(c1, c2, c3, c4, c5, c6):
    return c1 + c2 + c3 + c4 + c5 + c6


def func3(c1, c2, c3, c4, c5, c6, c7):
    return c1 + c2 + c3 + c4 + c5 + c6 + c7


class Thesis:
    def __init__(self, thesis_id, student_id, student_name, title):
        self.thesis_id = thesis_id
        self.student_id = student_id
        self.student_name = student_name
        self.title = title
        self.code = []
        self.lecturer_id = []
        self.schedule = 0
        self.isScheduled = False
        self.isExaminerScheduled = False
        self.isModeratorScheduled = False
        self.examiner = 0
        self.moderator = 0
        self.countFit = 0

    def addCode(self, code):
        self.code.append(code)

    def addLecturerId(self, id):
        self.lecturer_id.append(id)


class Lecturer:
    def __init__(self, lecturer_id, name, jja, experience, isPejabat):
        self.lecturer_id = lecturer_id
        self.name = name
        self.jja = jja
        self.experience = experience
        self.code = []
        self.schedule = []
        self.isPejabat = isPejabat
        self.scheduleCounter = 0

        # 0 -> NA
        # 1 -> TP
        # 2 -> AA
        # 3 -> L
        # 4 -> LK

    def addSchedule(self, period):
        self.schedule.append(period)

    def addCode(self, code):
        self.code.append(code)


class Particle_1:
    def __init__(self):
        self.pos = random.randint(0, 39)  # particle position
        self.vel = random.uniform(0, 39)  # particle velocity
        self.fit = 1  # particle fitness
        self.ind_best_pos = self.pos  # individual best position
        self.ind_best_fit = self.fit  # individual best fitness

    def update_vel(self, global_best_pos):
        w = 0.6  # inertial coefficient
        c1 = 2.0  # cognitive coefficient
        c2 = 2.0  # social coefficient

        r1 = random.random()
        r2 = random.random()
        # print("r1:", r1, "r2:", r2)
        inertia = w * self.vel
        cognitive = c1 * r1 * (self.ind_best_pos - self.pos)
        social = c2 * r2 * (global_best_pos - self.pos)
        # print("inertia:", inertia, "cognitive:", cognitive, "social:", social)
        a = inertia + cognitive + social
        # print("updated vel:", a)
        return a

    def update_pos(self, newVel):
        self.pos = self.pos + newVel
        # print("new pos", self.pos)
        if self.pos > 39:
            self.pos = 0
        if self.pos < 0:
            self.pos = 39

    def eval_fitness(self, func1, lect, thesis, j):
        # print("posisi:", self.pos)
        c1 = 0  # Jadwal gak bentrok
        c2 = 0  # Udah kejadwal
        c3 = 0  # kuota pejabat

        if len(thesis[j].lecturer_id) > 1:
            if lect[thesis[j].lecturer_id[0] - 1].schedule[math.floor(self.pos)] == 0 and \
                    lect[thesis[j].lecturer_id[1] - 1].schedule[math.floor(self.pos)] == 0:
                c1 = 0
            if lect[thesis[j].lecturer_id[0] - 1].schedule[math.floor(self.pos)] != 0 or \
                    lect[thesis[j].lecturer_id[1] - 1].schedule[math.floor(self.pos)] != 0:
                c1 = 100

        if len(thesis[j].lecturer_id) == 1:
            if lect[thesis[j].lecturer_id[0] - 1].schedule[math.floor(self.pos)] == 0:
                c1 = 0
            if lect[thesis[j].lecturer_id[0] - 1].schedule[math.floor(self.pos)] != 0:
                c1 = 100

        if thesis[j].isScheduled:
            c2 = 100
        if not thesis[j].isScheduled:
            c2 = 0
        # print("c1", c1, "c2", c2, "c3", c3)
        # evaluate fitness
        self.fit = func1(c1, c2, c3)

        # if current fitness is better,
        # update best values
        if self.fit < self.ind_best_fit:
            self.ind_best_pos = self.pos
            self.ind_best_fit = self.fit
        # print("vel:", self.vel)
        # print("fit:", self.fit)
        # print("indbestpos:", self.ind_best_pos, "indbestfit:", self.ind_best_fit)
        # print("")

class Particle_2:
    def __init__(self, thesis):
        self.pos = random.randint(0, len(thesis) - 1)  # particle position (skripsi yang mana)
        self.vel = random.uniform(0, len(thesis) - 1)  # particle velocity
        self.fit = 2  # particle fitness
        self.ind_best_pos = self.pos  # individual best position
        self.ind_best_fit = self.fit  # individual best fitness

    def update_vel(self, global_best_pos):
        w = 0.6  # inertial coefficient
        c1 = 2.0  # cognitive coefficient
        c2 = 2.0  # social coefficient

        r1 = random.random()
        r2 = random.random()
        # print("r1:", r1, "r2:", r2)
        inertia = w * self.vel
        cognitive = c1 * r1 * (self.ind_best_pos - self.pos)
        social = c2 * r2 * (global_best_pos - self.pos)
        # print("inertia:", inertia, "cognitive:", cognitive, "social:", social)
        a = inertia + cognitive + social
        # print("updated vel:", a)
        return a

    def update_pos(self, newVel):
        self.pos = self.pos + newVel
        # print("new pos", self.pos)
        if self.pos > len(thesis) - 1:
            self.pos = 0
        if self.pos < 0:
            self.pos = len(thesis) - 1

    def eval_fitness(self, func2, lect, thesis, j):
        # print("posisi:", self.pos)
        c1 = 0  # Jadwal gak bentrok
        c2 = 0  # jja
        c3 = 0  # koce AP
        c4 = 0  # penguji udah kejadwal
        c5 = 0  # Pembimbing == penguji
        c6 = 0  # kuota pejabat

        flag = False
        flag2 = False
        if lect[j].schedule[math.floor(thesis[math.floor(self.pos)].schedule)] == 0:
            c1 = 0
        if lect[j].schedule[math.floor(thesis[math.floor(self.pos)].schedule)] != 0:
            c1 = 100

        if lect[j].jja > 1:
            c2 = 0
        if lect[j].jja < 2:
            c2 = 100

        for i in range(0, len(thesis[math.floor(self.pos)].code)):
            for k in range(0, len(lect[j].code)):
                if thesis[math.floor(self.pos)].code[i] == lect[j].code[k]:
                    flag = True

        if flag:
            c3 = 0
        if not flag:
            c3 = 1

        if thesis[math.floor(self.pos)].isExaminerScheduled:
            c4 = 100
        if not thesis[math.floor(self.pos)].isExaminerScheduled:
            c4 = 0

        for i in range(0, len(thesis[math.floor(self.pos)].lecturer_id)):
            if thesis[math.floor(self.pos)].lecturer_id[i] == lect[j].lecturer_id:
                flag2 = True

        if flag2:
            c5 = 100
        if not flag2:
            c5 = 0

        if lect[j].isPejabat:
            if lect[j].scheduleCounter < MAX_SCHEDULE_PEJABAT:
                c6 = 0
            else:
                c6 = 100
        else:
            if lect[j].scheduleCounter < MAX_SCHEDULE_NONPEJABAT:
                c6 = 0
            else:
                c6 = 100

        # print("c1", c1, "c2", c2, "c3", c3, "c4", c4, "c5", c5, "c6", c6)
        # evaluate fitness
        self.fit = func2(c1, c2, c3, c4, c5, c6)
        # if current fitness is better,
        # update best values
        if self.fit < self.ind_best_fit:
            self.ind_best_pos = self.pos
            self.ind_best_fit = self.fit
        # print("vel:", self.vel)
        # print("fit:", self.fit)
        # print("indbestpos:", self.ind_best_pos, "indbestfit:", self.ind_best_fit)
        # print("")


class Particle_3:
    def __init__(self, thesis):
        self.pos = random.randint(0, len(thesis) - 1)  # particle position (skripsi yang mana)
        self.vel = random.uniform(0, len(thesis) - 1)  # particle velocity
        self.fit = 1  # particle fitness
        self.ind_best_pos = self.pos  # individual best position
        self.ind_best_fit = self.fit  # individual best fitness

    def update_vel(self, global_best_pos):
        w = 0.6  # inertial coefficient
        c1 = 2.0  # cognitive coefficient
        c2 = 2.0  # social coefficient

        r1 = random.random()
        r2 = random.random()

        inertia = w * self.vel
        cognitive = c1 * r1 * (self.ind_best_pos - self.pos)
        social = c2 * r2 * (global_best_pos - self.pos)

        a = inertia + cognitive + social

        return a

    def update_pos(self, newVel):
        self.pos = self.pos + newVel

        if self.pos > len(thesis) - 1:
            self.pos = 0
        if self.pos < 0:
            self.pos = len(thesis) - 1

    def eval_fitness(self, func3, lect, thesis, j):
        c1 = 0  # Jadwal gak bentrok
        c2 = 0  # jja
        c3 = 0  # pengalaman
        c4 = 0  # penguji udah kejadwal
        c5 = 0  # Pembimbing == ketua
        c6 = 0  # penguji == ketua sidang
        c7 = 0  # kuota pejabat
        flag = False

        if lect[j].schedule[math.floor(thesis[math.floor(self.pos)].schedule)] == 0:
            c1 = 0
        if lect[j].schedule[math.floor(thesis[math.floor(self.pos)].schedule)] != 0:
            c1 = 100

        if lect[j].jja > 1:
            c2 = 0
        if lect[j].jja < 2:
            c2 = 100

        if lect[j].experience:
            c3 = 0
        if not lect[j].experience:
            c3 = 100

        if thesis[math.floor(self.pos)].isModeratorScheduled:
            c4 = 100
        if not thesis[math.floor(self.pos)].isModeratorScheduled:
            c4 = 0

        for i in range(0, len(thesis[math.floor(self.pos)].lecturer_id)):
            if thesis[math.floor(self.pos)].lecturer_id[i] == lect[j].lecturer_id:
                flag = True

        if flag:
            c5 = 100
        if not flag:
            c5 = 0

        if thesis[math.floor(self.pos)].examiner == lect[j].lecturer_id - 1:
            c6 = 100
        if thesis[math.floor(self.pos)].examiner != lect[j].lecturer_id - 1:
            c6 = 0

        if lect[j].isPejabat:
            if lect[j].scheduleCounter < MAX_SCHEDULE_PEJABAT:
                c7 = 0
            else:
                c7 = 100
        else:
            if lect[j].scheduleCounter < MAX_SCHEDULE_NONPEJABAT:
                c7 = 0
            else:
                c7 = 100

        self.fit = func3(c1, c2, c3, c4, c5, c6, c7)

        if self.fit < self.ind_best_fit:
            self.ind_best_pos = self.pos
            self.ind_best_fit = self.fit


class PSO_1:
    def __init__(self, func1, num_particles, max_iter, lect, thesis):
        global_best_fit = 1
        global_best_pos = 0
        global_best_id = 0
        swarm = []
        for i in range(0, num_particles):
            swarm.append(Particle_1())

        i = 0
        while i < max_iter:
            for j in range(0, num_particles):
                swarm[j].eval_fitness(func1, lect, thesis, j)
                if swarm[j].fit < global_best_fit:
                    global_best_fit = swarm[j].fit
                    global_best_pos = swarm[j].pos
                    global_best_id = j

            for j in range(0, num_particles):
                swarm[j].vel = swarm[j].update_vel(global_best_pos)
                swarm[j].update_pos(swarm[j].vel)

            i += 1

        thesis[global_best_id].schedule = global_best_pos
        if global_best_fit > 0:
            thesis[global_best_id].isScheduled = False
        elif global_best_fit == 0:
            thesis[global_best_id].isScheduled = True
        for i in range(0, len(thesis[global_best_id].lecturer_id)):
            lect[thesis[global_best_id].lecturer_id[i] - 1].schedule[math.floor(global_best_pos)] = 1
            lect[thesis[global_best_id].lecturer_id[i] - 1].scheduleCounter += 1


class PSO_2:
    def __init__(self, func2, num_particles, max_iter, lect, thesis):
        global_best_fit = 2
        global_best_pos = 0
        global_best_id = 0
        swarm = []
        # global countFit

        for i in range(0, num_particles):
            swarm.append(Particle_2(thesis))

        i = 0
        while i < max_iter:
            for j in range(1, num_particles):
                # if j == 0:
                #     continue
                swarm[j].eval_fitness(func2, lect, thesis, j)
                if swarm[j].fit < global_best_fit:
                    global_best_fit = swarm[j].fit
                    global_best_pos = swarm[j].pos
                    global_best_id = j
            # print("gbest pos:", global_best_pos, "gbest fit", global_best_fit)
            # print("")

            for j in range(1, num_particles):
                # if j == 0:
                #     continue
                swarm[j].vel = swarm[j].update_vel(global_best_pos)
                swarm[j].update_pos(swarm[j].vel)
            # print("")
            i += 1
        # print("penguji", global_best_pos, global_best_fit, global_best_id)
        # print("")
        # countFit += math.floor(global_best_fit)
        if global_best_fit > 1:
            thesis[math.floor(global_best_pos)].isExaminerScheduled = False
        elif global_best_fit <= 1:
            thesis[math.floor(global_best_pos)].countFit = global_best_fit
            thesis[math.floor(global_best_pos)].isExaminerScheduled = True
        lect[global_best_id].schedule[math.floor(thesis[math.floor(global_best_pos)].schedule)] = 1
        thesis[math.floor(global_best_pos)].examiner = global_best_id
        lect[global_best_id].scheduleCounter += 1


class PSO_3:
    def __init__(self, func3, num_particles, max_iter, lect, thesis):
        global_best_fit = 1
        global_best_pos = 0
        global_best_id = 0
        swarm = []

        for i in range(0, num_particles):
            swarm.append(Particle_3(thesis))

        i = 0
        while i < max_iter:
            for j in range(1, num_particles):
                # if j == 0:
                #     continue
                swarm[j].eval_fitness(func3, lect, thesis, j)
                if swarm[j].fit < global_best_fit:
                    global_best_fit = swarm[j].fit
                    global_best_pos = swarm[j].pos
                    global_best_id = j

            for j in range(1, num_particles):
                # if j == 0:
                #     continue
                swarm[j].vel = swarm[j].update_vel(global_best_pos)
                swarm[j].update_pos(swarm[j].vel)
            # print("iter i", i)
            i += 1
        # print("ketua", global_best_pos, global_best_fit, global_best_id)
        if global_best_fit > 0:
            thesis[math.floor(global_best_pos)].isModeratorScheduled = False
        elif global_best_fit == 0:
            thesis[math.floor(global_best_pos)].isModeratorScheduled = True
        lect[global_best_id].schedule[math.floor(thesis[math.floor(global_best_pos)].schedule)] = 1
        thesis[math.floor(global_best_pos)].moderator = global_best_id
        lect[global_best_id].scheduleCounter += 1


class Dosen(db.Model):
    lecturer_id = db.Column(db.Integer, primary_key=True)
    lecturer_name = db.Column(db.String(100), nullable=False)
    jja = db.Column(db.Integer, nullable=False)
    code1 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=False)
    code2 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    code3 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    code4 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    code5 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    experience = db.Column(db.Boolean, nullable=False, default=False)
    isPejabat = db.Column(db.Boolean, nullable=False, default=False)
    scheduleCounter = db.Column(db.Integer, nullable=False, default=0)
    mysql_engine = 'InnoDB'


class Mahasiswa(db.Model):
    thesis_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(12), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    code1 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=False)
    code2 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    code3 = db.Column(db.Integer, db.ForeignKey('code.id'), nullable=True)
    lecturer_id1 = db.Column(db.Integer, db.ForeignKey('dosen.lecturer_id'), nullable=False, default=18)
    lecturer_id2 = db.Column(db.Integer, db.ForeignKey('dosen.lecturer_id'), nullable=True, default=18)
    schedule = db.Column(db.Integer, nullable=False, default=0)
    isScheduled = db.Column(db.Boolean, nullable=False, default=False)
    isExaminerScheduled = db.Column(db.Boolean, nullable=False, default=False)
    isModeratorScheduled = db.Column(db.Boolean, nullable=False, default=False)
    examinerId = db.Column(db.Integer, db.ForeignKey('dosen.lecturer_id'), nullable=False, default=18)
    moderatorId = db.Column(db.Integer, db.ForeignKey('dosen.lecturer_id'), nullable=False, default=18)
    mysql_engine = 'InnoDB'


class Jadwal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.Integer, nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('dosen.lecturer_id'), nullable=False)
    mysql_engine = 'InnoDB'


class Code(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code_name = db.Column(db.String(50), nullable=False)
    mysql_engine = 'InnoDB'


def listDosen():
    return Dosen.query.order_by(Dosen.lecturer_id).all()


class AddMahasiswaForm(FlaskForm):
    student_id = StringField('NIM', validators=[DataRequired()])
    student_name = StringField('Nama Mahasiswa', validators=[DataRequired()])
    title = StringField('Judul Skripsi', validators=[DataRequired()])
    code1 = QuerySelectField('Kode Area Penelitian 1', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name", validators=[DataRequired()])
    code2 = code1 = QuerySelectField('Kode Area Penelitian 2',
                                     query_factory=lambda: Code.query.order_by(Code.id).all(), get_label="code_name")
    code3 = code1 = QuerySelectField('Kode Area Penelitian 3',
                                     query_factory=lambda: Code.query.order_by(Code.id).all(), get_label="code_name")
    lecturer_id1 = QuerySelectField('Dosen Pembimbing 1',
                                    query_factory=lambda: Dosen.query.order_by(Dosen.lecturer_id).all(),
                                    get_label="lecturer_name")
    lecturer_id2 = QuerySelectField('Dosen Pembimbing 2',
                                    query_factory=lambda: Dosen.query.order_by(Dosen.lecturer_id).all(),
                                    get_label="lecturer_name")
    submit1 = SubmitField('Tambah')
    submit2 = SubmitField('Edit')


class AddDosenForm(FlaskForm):
    lecturer_name = StringField('Nama Dosen', validators=[DataRequired()])
    jja = SelectField('Jenjang Jabatan Akademik', choices=[('0', 'Not Available'),
                                                           ('1', 'Tenaga Pengajar'),
                                                           ('2', 'Asisten Ahli'),
                                                           ('3', 'Lektor'),
                                                           ('4', 'Lektor Kepala'),
                                                           ('5', 'Guru Besar')])
    code1 = QuerySelectField('Kode Area Penelitian 1', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name")
    code2 = QuerySelectField('Kode Area Penelitian 2', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name")
    code3 = QuerySelectField('Kode Area Penelitian 3', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name")
    code4 = QuerySelectField('Kode Area Penelitian 4', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name")
    code5 = QuerySelectField('Kode Area Penelitian 5', query_factory=lambda: Code.query.order_by(Code.id).all(),
                             get_label="code_name")
    experience = SelectField('Pengalaman Ketua', choices=[('1', 'True'), ('0', 'False')])
    isPejabat = SelectField('Pejabat', choices=[('1', 'True'), ('0', 'False')])
    submit1 = SubmitField('Tambah')
    submit2 = SubmitField('Edit')


class NewScheduleForm(FlaskForm):
    batch = SelectField('Batch', validators=[DataRequired()], choices=[('1', 'Batch 1'), ('2', 'Batch 2')])
    maxPejabat = IntegerField('Maksimal Kuota Pejabat', validators=[DataRequired()])
    maxNonPejabat = IntegerField('Maksimal Kuota Non-Pejabat', validators=[DataRequired()])
    submit = SubmitField('Buat Jadwal')


class NewJadwalForm(FlaskForm):
    daynumber = SelectField('Hari', validators=[DataRequired()],
                            choices=[('1', 'Senin'), ('2', 'Selasa'), ('3', 'Rabu'), ('4', 'Kamis'), ('5', 'Jumat')])
    period = SelectField('Jam', validators=[DataRequired()],
                         choices=[('1', '08:00-10:00'), ('2', '10:00-12:00'), ('3', '13:00-15:00'),
                                  ('4', '15:00-17:00')])
    submit = SubmitField('Tambah Jadwal')


@app.route("/")
@app.route("/student")
def student():
    mahasiswa = db.engine.execute('select s.thesis_id, s.student_id, s.student_name, s.title, c1.code_name as kode1, '
                                  'c2.code_name as kode2, c3.code_name as kode3, d1.lecturer_name as dp1, '
                                  'd2.lecturer_name as dp2 from mahasiswa as s, code as c1, code as c2, code as c3, '
                                  'dosen as d1, dosen as d2 '
                                  'where c1.id = s.code1 and c2.id = s.code2 and c3.id = s.code3 and '
                                  'd1.lecturer_id = s.lecturer_id1 and d2.lecturer_id = s.lecturer_id2'
                                  ' order by s.thesis_id asc')
    jadwal = Jadwal.query.all()
    return render_template('home.html', mahasiswa=mahasiswa, jadwal=jadwal)


@app.route("/lecturer")
def lecturer():
    dosen = db.engine.execute('select d.lecturer_id, d.lecturer_name, d.jja, c1.code_name as code1, '
                              'c2.code_name as code2, c3.code_name as code3, c4.code_name as code4, '
                              'c5.code_name as code5, d.experience, d.isPejabat '
                              'from dosen as d, code as c1, code as c2, code as c3, code as c4, code as c5 '
                              'where c1.id = d.code1 and c2.id = d.code2 and c3.id = code3 and c4.id = d.code4 and '
                              'c5.id = d.code5 '
                              'order by d.lecturer_id')
    return render_template('dosen.html', title='Dosen', dosen=dosen)


@app.route("/lecturer/<int:lecturer_id>", methods=['GET', 'POST'])
def jadwal(lecturer_id):
    selected = Dosen.query.get_or_404(lecturer_id)
    jadwal = db.engine.execute('select id, period from jadwal where lecturer_id = %s', (int(selected.lecturer_id)))
    return render_template('jadwal.html', selected=selected, jadwal=jadwal)


@app.route("/student/new", methods=['GET', 'POST'])
def addmahasiswa():
    form = AddMahasiswaForm()
    if form.validate_on_submit():
        nim = form.student_id.data
        nama_mahasiswa = form.student_name.data
        judul_skripsi = form.title.data
        id_dosen1 = form.lecturer_id1.data.lecturer_id
        id_dosen2 = form.lecturer_id2.data.lecturer_id
        mahasiswa = Mahasiswa(student_id=nim, student_name=nama_mahasiswa, title=judul_skripsi,
                              code1=form.code1.data.id, code2=form.code2.data.id, code3=form.code3.data.id,
                              lecturer_id1=id_dosen1, lecturer_id2=id_dosen2)
        db.session.add(mahasiswa)
        db.session.commit()
        flash(f'Mahasiswa atas nama{form.student_name.data} berhasil di tambahkan', 'success')
        return redirect(url_for('student'))
    return render_template('addmahasiswa.html', title='Mahasiswa', form=form)


@app.route("/lecturer/new", methods=['GET', 'POST'])
def adddosen():
    form = AddDosenForm()
    if form.validate_on_submit():
        nama = form.lecturer_name.data
        jabatan = int(form.jja.data)
        dosen = Dosen(lecturer_name=nama, jja=jabatan, code1=form.code1.data.id, code2=form.code2.data.id,
                      code3=form.code3.data.id, code4=form.code4.data.id, code5=form.code5.data.id,
                      experience=int(form.experience.data), isPejabat=int(form.isPejabat.data))
        db.session.add(dosen)
        db.session.commit()
        flash(f'Dosen atas nama{form.lecturer_name.data} berhasil ditambahkan', 'success')
        return redirect(url_for('lecturer'))
    return render_template('adddosen.html', title='Dosen', form=form)


@app.route("/schedule", methods=['GET', 'POST'])
def schedule():

    start = time.time()
    form = NewScheduleForm()
    ctr = 0
    dosen = listDosen()
    mhs = Mahasiswa.query.all()
    if form.validate_on_submit():
        # breakpoint()
        global batch
        batch = int(form.batch.data)

        global MAX_SCHEDULE_PEJABAT
        MAX_SCHEDULE_PEJABAT = form.maxPejabat.data
        global MAX_SCHEDULE_NONPEJABAT
        MAX_SCHEDULE_NONPEJABAT = form.maxNonPejabat.data

        for i in mhs:
            i.schedule = 0
            i.isScheduled = 0
            i.isExaminerScheduled = 0
            i.isModeratorScheduled = 0
            i.examinerId = 18
            i.moderatorId = 18

        for i in dosen:
            i.scheduleCounter = 0

        for i in range(0, len(dosen)):
            lect[i] = Lecturer(int(dosen[i].lecturer_id), dosen[i].lecturer_name, int(dosen[i].jja),
                               bool(dosen[i].experience), bool(dosen[i].isPejabat))

        for i in range(0, len(lect)):
            if dosen[i].code1 is not None:
                lect[i].addCode(dosen[i].code1)
            if dosen[i].code2 is not None:
                lect[i].addCode(dosen[i].code2)
            if dosen[i].code3 is not None:
                lect[i].addCode(dosen[i].code3)
            if dosen[i].code4 is not None:
                lect[i].addCode(dosen[i].code4)
            if dosen[i].code5 is not None:
                lect[i].addCode(dosen[i].code5)

        for i in range(len(lect)):
            for j in range(0, 40):
                lect[i].addSchedule(0)

        if batch == 1:
            for i in range(len(lect)):
                sched = db.engine.execute('select period, lecturer_id from jadwal where lecturer_id = %s', i + 1)
                for a in sched:
                    lect[i].schedule[a.period] = 1
                    lect[i].schedule[int(a.period) + 20] = 1

        for i in range(len(mhs)):
            # print(i)
            thesis[i] = Thesis(int(mhs[i].thesis_id), mhs[i].student_id, mhs[i].student_name, mhs[i].title)

        for i in range(len(thesis)):
            if mhs[i].code1 != 12:
                thesis[i].addCode(mhs[i].code1)
            if mhs[i].code2 != 12:
                thesis[i].addCode(mhs[i].code2)
            if mhs[i].code3 != 12:
                thesis[i].addCode(mhs[i].code3)

        for i in range(len(thesis)):
            if mhs[i].lecturer_id1 != 18:
                thesis[i].addLecturerId(mhs[i].lecturer_id1)
            if mhs[i].lecturer_id2 != 18:
                thesis[i].addLecturerId(mhs[i].lecturer_id2)

        total = len(thesis)

        flag = False
        counter = 0
        while not flag:
            tempLect = copy.deepcopy(lect)
            # PENJADWALAN WAKTU SIDANG
            for i in range(0, len(thesis)):
                PSO_1(func1, total, 20, tempLect, thesis)

            # PENJADWALAN PENGUJI
            for i in range(0, len(thesis)):
                PSO_2(func2, len(lect), 20, tempLect, thesis)

            # PENJADWALAN KETUA SIDANG
            for i in range(0, len(thesis)):
                PSO_3(func3, len(lect), 20, tempLect, thesis)

            for i in range(0, len(thesis)):
                if not thesis[i].isModeratorScheduled or not thesis[i].isScheduled or not thesis[i].isExaminerScheduled:
                    # RESET DATA
                    for j in range(0, len(thesis)):
                        thesis[j].isScheduled = False
                        thesis[j].isExaminerScheduled = False
                        thesis[j].isModeratorScheduled = False
                    for j in range(0, len(tempLect)):
                        tempLect[j].scheduleCounter = 0
                    print(ctr, "FAILED")
                    ctr += 1
                    flag = False
                    break
                flag = True

        for i in range(0, len(thesis)):
            counter += thesis[i].countFit
        print("Fitness :", counter)
        end = time.time()
        print(end - start)
        for i in range(0, len(lect)):
            lect[i].scheduleCounter = tempLect[i].scheduleCounter
            # print(lect[i].name, lect[i].scheduleCounter)
            for j in range(0, len(lect[i].schedule)):
                lect[i].schedule[j] = tempLect[i].schedule[j]

        # breakpoint()
        for i in lect:
            db.engine.execute('update dosen set scheduleCounter = %s where lecturer_id = %s',
                              (lect[i].scheduleCounter, lect[i].lecturer_id))

        for i in thesis:
            db.engine.execute('update mahasiswa set schedule = %s, isScheduled = %s, isExaminerScheduled = %s,'
                              'isModeratorScheduled = %s, examinerId = %s, moderatorId = %s where thesis_id = %s',
                              (thesis[i].schedule, thesis[i].isScheduled, thesis[i].isExaminerScheduled,
                               thesis[i].isModeratorScheduled, thesis[i].examiner + 1, thesis[i].moderator + 1,
                               thesis[i].thesis_id))

        if flag:
            return redirect(url_for('view'))

    return render_template('schedule.html', title='Jadwal', form=form)


@app.route("/schedule/view")
def view():
    global batch
    mahasiswa = db.engine.execute('select m.student_id, m.student_name, m.title, d1.lecturer_name as dospem1, '
                                  'd2.lecturer_name as dospem2, m.schedule, d3.lecturer_name as penguji, '
                                  'd4.lecturer_name as ketua '
                                  'from mahasiswa as m, dosen as d1, dosen as d2, dosen as d3, dosen as d4 '
                                  'where d1.lecturer_id = m.lecturer_id1 and d2.lecturer_id = m.lecturer_id2 and '
                                  'd3.lecturer_id = m.examinerId and d4.lecturer_id = m.moderatorId '
                                  'order by m.schedule')
    return render_template('viewschedule.html', mahasiswa=mahasiswa, batch=batch)


@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        nim = ""
        nama = ""
        judul = ""
        kode1 = 0
        kode2 = 0
        kode3 = 0
        dosen1 = 0
        dosen2 = 0

        f = request.files['file']
        if not f:
            return "No file"

        stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
        print(stream)
        csv_input = csv.reader(stream)
        print(csv_input)
        count = 0
        for row in csv_input:
            for j in range(0, len(row[0].split(';'))):
                if j == 0:
                    nim = row[0].split(';')[j]
                if j == 1:
                    nama = row[0].split(';')[j]
                if j == 2:
                    judul = row[0].split(';')[j]
                if j == 3:
                    kode1 = row[0].split(';')[j]
                if j == 4:
                    kode2 = row[0].split(';')[j]
                if j == 5:
                    kode3 = row[0].split(';')[j]
                if j == 6:
                    dosen1 = row[0].split(';')[j]
                if j == 7:
                    dosen2 = row[0].split(';')[j]
            count += 1
            mahasiswa = Mahasiswa(student_id=nim, student_name=nama, title=judul,
                                  code1=kode1, code2=kode2, code3=kode3,
                                  lecturer_id1=dosen1, lecturer_id2=dosen2)
            db.session.add(mahasiswa)
            db.session.commit()

        flash(f'File berhasil di-upload! {count} Mahasiswa berhasil di tambahkan', 'success')
        return redirect(url_for('student'))
    return render_template("upload.html")


@app.route("/lecturer/<int:lecturer_id>/new", methods=['GET', 'POST'])
def addjadwal(lecturer_id):
    form = NewJadwalForm()
    if form.validate_on_submit():
        daynumber = form.daynumber.data
        period = form.period.data
        periodToSave = 0
        if int(daynumber) == 1:
            if int(period) == 1:
                periodToSave = 0
            if int(period) == 2:
                periodToSave = 1
            if int(period) == 3:
                periodToSave = 2
            if int(period) == 4:
                periodToSave = 3

        if int(daynumber) == 2:
            if int(period) == 1:
                periodToSave = 4
            if int(period) == 2:
                periodToSave = 5
            if int(period) == 3:
                periodToSave = 6
            if int(period) == 4:
                periodToSave = 7

        if int(daynumber) == 3:
            if int(period) == 1:
                periodToSave = 8
            if int(period) == 2:
                periodToSave = 9
            if int(period) == 3:
                periodToSave = 10
            if int(period) == 4:
                periodToSave = 11

        if int(daynumber) == 4:
            if int(period) == 1:
                periodToSave = 12
            if int(period) == 2:
                periodToSave = 13
            if int(period) == 3:
                periodToSave = 14
            if int(period) == 4:
                periodToSave = 15

        if int(daynumber) == 5:
            if int(period) == 1:
                periodToSave = 16
            if int(period) == 2:
                periodToSave = 17
            if int(period) == 3:
                periodToSave = 18
            if int(period) == 4:
                periodToSave = 19

        jadwal = Jadwal(period=periodToSave, lecturer_id=lecturer_id)
        db.session.add(jadwal)
        db.session.commit()
        flash(f'Jadwal berhasil ditambahkan', 'success')
        return redirect(url_for('jadwal', lecturer_id=lecturer_id))
    return render_template('addjadwal.html', title='Dosen', form=form)


@app.route("/student/<int:thesis_id>/update_mahasiswa",  methods=['GET', 'POST'])
def updatemahasiswa(thesis_id):
    form = AddMahasiswaForm()
    mahasiswa = Mahasiswa.query.get_or_404(thesis_id)
    if form.validate_on_submit():
        mahasiswa.student_id = form.student_id.data
        mahasiswa.student_name = form.student_name.data
        mahasiswa.title = form.title.data
        mahasiswa.lecturer_id1 = form.lecturer_id1.data.lecturer_id
        mahasiswa.lecturer_id2 = form.lecturer_id2.data.lecturer_id
        mahasiswa.code1 = form.code1.data.id
        mahasiswa.code2 = form.code2.data.id
        mahasiswa.code3 = form.code3.data.id
        db.session.commit()
        flash(f'Mahasiswa atas nama {form.student_name.data} berhasil di ubah', 'success')
        return redirect(url_for('student'))
    elif request.method == 'GET':
        form.student_id.data = mahasiswa.student_id
        form.student_name.data = mahasiswa.student_name
        form.title.data = mahasiswa.title
        dosen_pembimbing1 = Dosen.query.get(mahasiswa.lecturer_id1)
        dosen_pembimbing2 = Dosen.query.get(mahasiswa.lecturer_id2)
        code1 = Code.query.get(mahasiswa.code1)
        code2 = Code.query.get(mahasiswa.code2)
        code3 = Code.query.get(mahasiswa.code3)
        form.lecturer_id1.data = dosen_pembimbing1.lecturer_name
        form.lecturer_id1.data = dosen_pembimbing2.lecturer_name
        form.code1.data = code1.code_name
        form.code2.data = code2.code_name
        form.code3.data = code3.code_name
    return render_template('addmahasiswa.html', title='Update Mahasiswa', form=form, thesis_id=thesis_id)


@app.route("/student/delete_mahasiswa", methods=['POST'])
def deletemahasiswa():
    thesis_id = request.form['thesis-id']
    # print(thesis_id)
    # breakpoint()
    db.engine.execute('delete from mahasiswa where mahasiswa.thesis_id = %s', thesis_id)
    flash('Mahasiswa Berhasil Dihapus', 'danger')
    return redirect(url_for('student'))


@app.route("/lecturer/<int:lecturer_id>/update_dosen",  methods=['GET', 'POST'])
def updatedosen(lecturer_id):
    form = AddDosenForm()
    dosen = Dosen.query.get_or_404(lecturer_id)
    if form.validate_on_submit():
        dosen.lecturer_name = form.lecturer_name.data
        dosen.jja = form.jja.data
        dosen.code1 = form.code1.data.id
        dosen.code2 = form.code2.data.id
        dosen.code3 = form.code3.data.id
        dosen.code4 = form.code4.data.id
        dosen.code5 = form.code5.data.id
        dosen.experience = int(form.experience.data)
        dosen.isPejabat = int(form.isPejabat.data)
        db.session.commit()
        flash(f'Dosen atas nama {form.lecturer_name.data} berhasil di ubah', 'success')
        return redirect(url_for('lecturer'))
    elif request.method == 'GET':
        form.lecturer_name.data = dosen.lecturer_name
        code1 = Code.query.get(dosen.code1)
        code2 = Code.query.get(dosen.code2)
        code3 = Code.query.get(dosen.code3)
        code4 = Code.query.get(dosen.code4)
        code5 = Code.query.get(dosen.code5)
        form.jja.data = dosen.jja

        form.experience.data = dosen.experience
        form.isPejabat.data = dosen.isPejabat
        form.code1.data = code1.code_name
        form.code2.data = code2.code_name
        form.code3.data = code3.code_name
        form.code4.data = code4.code_name
        form.code5.data = code5.code_name
    return render_template('adddosen.html', title='Update Mahasiswa', form=form, lecturer_id=lecturer_id)

@app.route("/lecturer/delete_jadwal", methods=['POST'])
def deletejadwal():
    lect_id = request.form['lect-id']
    schedule_id = request.form['schedule-id']
    print("lect", lect_id, "sched", schedule_id)
    # breakpoint()
    db.engine.execute('delete from jadwal where jadwal.id = %s', schedule_id)
    flash('Jadwal Berhasil Dihapus', 'danger')
    return redirect(url_for('jadwal', lecturer_id=lect_id))


@app.route("/lecturer/delete_dosen", methods=['POST'])
def deletedosen():
    lecturer_id = request.form['lect-id2']
    print(lecturer_id)
    # breakpoint()
    db.engine.execute('delete from dosen where lecturer_id = %s', lecturer_id)
    flash('Dosen Berhasil Dihapus', 'danger')
    return redirect(url_for('lecturer'))


def connect():
    conn = ""
    try:
        conn = mysql.connector.connect(host='localhost',
                                       database='site',
                                       user='root',
                                       password='')
        if conn.is_connected():
            print('Connected to MySQL database')

    except Error as e:
        print(e)

    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
