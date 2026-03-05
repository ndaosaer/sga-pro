from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role          = Column(String(50), default="teacher")
    created_at    = Column(DateTime)

class Student(Base):
    __tablename__ = "students"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    nom            = Column(String(100), nullable=False)
    prenom         = Column(String(100), nullable=False)
    email          = Column(String(200), unique=True, nullable=False)
    date_naissance = Column(Date, nullable=True)
    actif          = Column(Boolean, default=True)
    created_at     = Column(DateTime)
    attendances    = relationship("Attendance", back_populates="student", cascade="all, delete-orphan", lazy="select")
    grades         = relationship("Grade", back_populates="student", cascade="all, delete-orphan", lazy="select")

class Course(Base):
    __tablename__ = "courses"
    code           = Column(String(20), primary_key=True)
    libelle        = Column(String(200), nullable=False)
    volume_horaire = Column(Float, nullable=False)
    enseignant     = Column(String(200), nullable=True)
    description    = Column(Text, nullable=True)
    couleur        = Column(String(7), default="#00d4ff")
    created_at     = Column(DateTime)
    sessions       = relationship("Session", back_populates="course", cascade="all, delete-orphan", lazy="select")
    grades         = relationship("Grade", back_populates="course", cascade="all, delete-orphan", lazy="select")

class Session(Base):
    __tablename__ = "sessions"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(20), ForeignKey("courses.code", ondelete="CASCADE"), nullable=False)
    date        = Column(Date, nullable=False)
    duree       = Column(Float, nullable=False)
    theme       = Column(String(500), nullable=True)
    objectifs   = Column(Text, nullable=True)
    created_at  = Column(DateTime)
    course      = relationship("Course", back_populates="sessions", lazy="select")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan", lazy="select")

class Attendance(Base):
    __tablename__ = "attendance"
    id_session = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    id_student = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    justifiee  = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("id_session", "id_student", name="uq_attendance"),)
    session = relationship("Session", back_populates="attendances", lazy="select")
    student = relationship("Student", back_populates="attendances", lazy="select")

class Grade(Base):
    __tablename__ = "grades"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    id_student  = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_code = Column(String(20), ForeignKey("courses.code", ondelete="CASCADE"), nullable=False)
    note        = Column(Float, nullable=False)
    coefficient = Column(Float, nullable=False, default=1.0)
    commentaire = Column(Text, nullable=True)
    created_at  = Column(DateTime)
    __table_args__ = (UniqueConstraint("id_student", "course_code", name="uq_grade_student_course"),)
    student = relationship("Student", back_populates="grades", lazy="select")
    course  = relationship("Course", back_populates="grades", lazy="select")

class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    type       = Column(String(50), nullable=False)
    titre      = Column(String(200), nullable=False)
    message    = Column(Text, nullable=False)
    lu         = Column(Boolean, default=False)
    created_at = Column(DateTime)
