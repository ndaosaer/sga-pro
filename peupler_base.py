"""
SGA Pro — Script de peuplement de la base de donnees
Cree : niveaux, classes, cours, etudiants, enseignants, notes, presences
Structure : Licence (L1,L2,L3) + Master (M1,M2) + Doctorat (D1)
Filieres : Statistique, Economie, Informatique Statistique
"""
import sqlite3, glob, os, sys, random, hashlib
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

# ── Trouver la base ──
db_path = None
for c in ["sga_pro/sga_pro.db","sga_pro/database.db","sga_pro/data.db"]:
    if os.path.exists(c): db_path=c; break
if not db_path:
    found=glob.glob("sga_pro/*.db")
    if found: db_path=found[0]
if not db_path:
    print("ERREUR: base introuvable. Lance depuis Projet_final_Dash\\"); sys.exit(1)

print(f"Base : {db_path}")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()
cur.execute("PRAGMA foreign_keys = OFF")

# ═══════════════════════════════════════════════
# 1. MIGRATION — nouvelles tables et colonnes
# ═══════════════════════════════════════════════
print("\n[1/6] Migration des tables...")

cur.execute("""CREATE TABLE IF NOT EXISTS niveaux (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL, abrev TEXT NOT NULL, ordre INTEGER DEFAULT 1
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL, code TEXT NOT NULL UNIQUE,
    niveau_id INTEGER REFERENCES niveaux(id),
    filiere TEXT, annee TEXT, effectif_max INTEGER DEFAULT 40,
    actif INTEGER DEFAULT 1, couleur TEXT, created_at DATETIME
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS cours_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT REFERENCES courses(code) ON DELETE CASCADE,
    classe_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    enseignant TEXT, created_at DATETIME
)""")

# Ajouter classe_id aux etudiants si absent
cur.execute("PRAGMA table_info(students)")
cols = [r["name"] for r in cur.fetchall()]
if "classe_id" not in cols:
    cur.execute("ALTER TABLE students ADD COLUMN classe_id INTEGER REFERENCES classes(id)")
    print("  + students.classe_id")

# Ajouter classe_id aux creneaux si absent
cur.execute("PRAGMA table_info(creneaux)")
if cur.fetchall():
    cur.execute("PRAGMA table_info(creneaux)")
    cren_cols = [r["name"] for r in cur.fetchall()]
    if "classe_id" not in cren_cols:
        cur.execute("ALTER TABLE creneaux ADD COLUMN classe_id INTEGER REFERENCES classes(id)")
        print("  + creneaux.classe_id")

# Ajouter teacher_username aux courses si absent
cur.execute("PRAGMA table_info(courses)")
course_cols = [r["name"] for r in cur.fetchall()]
for col, typ in [("teacher_username","TEXT"),("description","TEXT"),("couleur","TEXT")]:
    if col not in course_cols:
        cur.execute(f"ALTER TABLE courses ADD COLUMN {col} {typ}")
        print(f"  + courses.{col}")

conn.commit()
print("  ✓ Tables OK")

# ═══════════════════════════════════════════════
# 2. NIVEAUX
# ═══════════════════════════════════════════════
print("\n[2/6] Creation des niveaux...")
niveaux = [
    ("Licence", "L", 1),
    ("Master",  "M", 2),
    ("Doctorat","D", 3),
]
for nom, abrev, ordre in niveaux:
    cur.execute("SELECT id FROM niveaux WHERE abrev=?", (abrev,))
    if not cur.fetchone():
        cur.execute("INSERT INTO niveaux(nom,abrev,ordre) VALUES(?,?,?)", (nom,abrev,ordre))
conn.commit()

cur.execute("SELECT id,abrev FROM niveaux")
niv_map = {r["abrev"]: r["id"] for r in cur.fetchall()}
print(f"  ✓ {len(niv_map)} niveaux")

# ═══════════════════════════════════════════════
# 3. CLASSES
# ═══════════════════════════════════════════════
print("\n[3/6] Creation des classes...")
COULEURS = ["#2D6A3F","#B8922A","#8B5E3C","#1B4F72","#6C3483","#1A5276"]
classes_data = [
    ("L1 Statistique",         "L1-STAT", "L", "Statistique",              "#2D6A3F"),
    ("L2 Statistique",         "L2-STAT", "L", "Statistique",              "#2D6A3F"),
    ("L3 Statistique",         "L3-STAT", "L", "Statistique",              "#B8922A"),
    ("L3 Economie",            "L3-ECO",  "L", "Economie",                 "#8B5E3C"),
    ("M1 Statistique Appliquee","M1-STAT","M", "Statistique Appliquee",    "#1B4F72"),
    ("M2 Data Science",        "M2-DATA", "M", "Data Science & IA",        "#6C3483"),
]
for nom, code, niv, filiere, couleur in classes_data:
    cur.execute("SELECT id FROM classes WHERE code=?", (code,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO classes(nom,code,niveau_id,filiere,annee,effectif_max,actif,couleur,created_at)
                       VALUES(?,?,?,?,'2025-2026',40,1,?,?)""",
                    (nom, code, niv_map[niv], filiere, couleur, datetime.now()))
conn.commit()
cur.execute("SELECT id,code,nom FROM classes")
classe_map = {r["code"]: {"id":r["id"],"nom":r["nom"]} for r in cur.fetchall()}
print(f"  ✓ {len(classe_map)} classes")

# ═══════════════════════════════════════════════
# 4. ENSEIGNANTS + COURS
# ═══════════════════════════════════════════════
print("\n[4/6] Creation des enseignants et cours...")

enseignants = [
    ("prof.diallo",    "Mamadou Diallo",      "Statistiques Descriptives"),
    ("prof.ndiaye",    "Fatou Ndiaye",         "Mathematiques Appliquees"),
    ("prof.fall",      "Ibrahima Fall",        "Economie Generale"),
    ("prof.ba",        "Aissatou Ba",          "Probabilites et Statistiques"),
    ("prof.sow",       "Ousmane Sow",          "Informatique & Bases de Donnees"),
    ("prof.kane",      "Mariama Kane",         "Analyse de Donnees"),
    ("prof.traore",    "Seydou Traore",        "Econometrie"),
    ("prof.sarr",      "Rokhaya Sarr",         "Machine Learning"),
    ("prof.diouf",     "Cheikh Diouf",         "Serie Temporelles"),
    ("prof.mbaye",     "Ndéye Mbaye",          "Methodes d'Enquetes"),
]

# Creer les comptes enseignants
for username, nom_complet, specialite in enseignants:
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users(username,password_hash,role,created_at)
                       VALUES(?,?,?,?)""",
                    (username, generate_password_hash("prof2026"),
                     "teacher", datetime.now()))

conn.commit()

# Cours par classe
cours_data = [
    # code, libelle, volume_h, couleur, enseignant_username, classes
    ("STAT101","Statistiques Descriptives",  30,"#2D6A3F","prof.diallo",  ["L1-STAT","L2-STAT"]),
    ("MATH101","Mathematiques L1",           40,"#B8922A","prof.ndiaye",  ["L1-STAT"]),
    ("ECO101", "Introduction a l'Economie",  30,"#8B5E3C","prof.fall",    ["L1-STAT","L3-ECO"]),
    ("PROB201","Probabilites",               35,"#1B4F72","prof.ba",      ["L2-STAT"]),
    ("INFO201","Bases de Donnees",           25,"#6C3483","prof.sow",     ["L2-STAT","L3-STAT"]),
    ("STAT301","Statistiques Inferentielles",35,"#2D6A3F","prof.diallo",  ["L3-STAT"]),
    ("ECO301", "Microeconomie Avancee",      30,"#8B5E3C","prof.fall",    ["L3-ECO"]),
    ("ECON301","Econometrie",                35,"#B8922A","prof.traore",  ["L3-ECO","M1-STAT"]),
    ("ANAL401","Analyse Multivariee",        30,"#1B4F72","prof.kane",    ["M1-STAT"]),
    ("ENQT401","Methodes d'Enquetes",        25,"#8B5E3C","prof.mbaye",   ["M1-STAT"]),
    ("ML501",  "Machine Learning",           40,"#6C3483","prof.sarr",    ["M2-DATA"]),
    ("TSERIE","Series Temporelles",          30,"#1B4F72","prof.diouf",   ["M2-DATA","M1-STAT"]),
    ("DATAVIZ","Data Visualisation",         20,"#2D6A3F","prof.sow",     ["M2-DATA"]),
]

for code, libelle, vol, couleur, ens_username, classes_codes in cours_data:
    # Nom complet enseignant
    ens_nom = next((n for u,n,_ in enseignants if u==ens_username), ens_username)
    cur.execute("SELECT code FROM courses WHERE code=?", (code,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO courses(code,libelle,volume_horaire,enseignant,teacher_username,couleur,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (code, libelle, vol, ens_nom, ens_username, couleur, datetime.now()))
    else:
        cur.execute("UPDATE courses SET teacher_username=?,couleur=? WHERE code=?",
                    (ens_username, couleur, code))

    # Lier aux classes
    for cl_code in classes_codes:
        if cl_code in classe_map:
            cl_id = classe_map[cl_code]["id"]
            cur.execute("SELECT id FROM cours_classes WHERE course_code=? AND classe_id=?",
                        (code, cl_id))
            if not cur.fetchone():
                cur.execute("""INSERT INTO cours_classes(course_code,classe_id,enseignant,created_at)
                               VALUES(?,?,?,?)""", (code, cl_id, ens_nom, datetime.now()))

conn.commit()
print(f"  ✓ {len(enseignants)} enseignants, {len(cours_data)} cours")

# ═══════════════════════════════════════════════
# 5. ETUDIANTS (60 etudiants realistes)
# ═══════════════════════════════════════════════
print("\n[5/6] Creation des etudiants...")

PRENOMS_M = ["Mamadou","Ibrahima","Ousmane","Cheikh","Moussa","Abdou","Modou",
             "Saliou","Lamine","Serigne","Pape","Landing","Tidiane","Babacar","Daouda"]
PRENOMS_F = ["Fatou","Aminata","Mariama","Aissatou","Rokhaya","Ndéye","Khady",
             "Coumba","Sokhna","Adja","Mame","Yacine","Binta","Astou","Dieynaba"]
NOMS      = ["Diallo","Ndiaye","Fall","Ba","Sow","Kane","Traore","Sarr","Diouf",
             "Mbaye","Gueye","Diop","Faye","Toure","Cisse","Badji","Mendy","Manga",
             "Sagna","Tendeng","Diatta","Dieme","Sambou","Goudiaby","Bassene"]

rng = random.Random(42)  # seed fixe pour reproductibilite

# Repartition par classe
repartition = {
    "L1-STAT": 15, "L2-STAT": 12, "L3-STAT": 10,
    "L3-ECO":  10, "M1-STAT":  8, "M2-DATA":  5,
}

etu_created = 0
for cl_code, nb in repartition.items():
    cl_id = classe_map[cl_code]["id"]
    for i in range(nb):
        genre  = rng.choice(["M","F"])
        prenom = rng.choice(PRENOMS_M if genre=="M" else PRENOMS_F)
        nom    = rng.choice(NOMS).upper()
        email  = f"{prenom.lower().replace('é','e').replace('è','e')}.{nom.lower()}@etudiant.ensae.sn"
        ddn    = date(rng.randint(1998,2005), rng.randint(1,12), rng.randint(1,28))

        # Verifier doublon
        cur.execute("SELECT id FROM students WHERE email=?", (email,))
        if cur.fetchone():
            email = f"{prenom.lower()}.{nom.lower()}{rng.randint(10,99)}@etudiant.ensae.sn"

        cur.execute("""INSERT INTO students(nom,prenom,email,date_naissance,classe_id,actif,created_at)
                       VALUES(?,?,?,?,?,1,?)""",
                    (nom, prenom, email, ddn.isoformat(), cl_id, datetime.now()))
        stu_id = cur.lastrowid

        # Compte utilisateur etudiant
        username = f"etu.{prenom.lower().replace('é','e')[:4]}{nom.lower()[:4]}{stu_id}"
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO users(username,password_hash,role,linked_id,created_at)
                           VALUES(?,?,?,?,?)""",
                        (username, generate_password_hash("etu2026"),
                         "student", stu_id, datetime.now()))
        etu_created += 1

conn.commit()
print(f"  ✓ {etu_created} etudiants crees")

# ═══════════════════════════════════════════════
# 6. NOTES + PRESENCES (données réalistes)
# ═══════════════════════════════════════════════
print("\n[6/6] Generation des notes et presences...")

cur.execute("SELECT id,classe_id FROM students WHERE actif=1")
all_students = list(cur.fetchall())

cur.execute("SELECT code,couleur,teacher_username FROM courses")
all_courses = list(cur.fetchall())

cur.execute("SELECT course_code,classe_id FROM cours_classes")
cc_links = [(r["course_code"],r["classe_id"]) for r in cur.fetchall()]

notes_created   = 0
seances_created = 0

COEFFICIENTS = [1, 1, 2, 2, 3]

for course_code, classe_id in cc_links:
    # Etudiants de cette classe
    etudiants_classe = [s for s in all_students if s["classe_id"] == classe_id]
    if not etudiants_classe:
        continue

    # Creer 3 a 6 seances pour ce cours
    nb_seances = rng.randint(3, 6)
    seance_ids = []
    for k in range(nb_seances):
        jour = date(2025, rng.randint(9,12), rng.randint(1,28))
        try:
            cur.execute("""INSERT INTO sessions(course_code,date,duree,theme,created_at)
                           VALUES(?,?,?,?,?)""",
                        (course_code, jour.isoformat(),
                         rng.choice([1.5,2.0,2.5,3.0]),
                         f"Seance {k+1}", datetime.now()))
            seance_ids.append(cur.lastrowid)
            seances_created += 1
        except Exception:
            pass

    # Notes pour chaque etudiant
    for stu in etudiants_classe:
        # Profil de l'etudiant (bon/moyen/faible) fixe par seed
        rng2 = random.Random(stu["id"] * 31 + hash(course_code) % 1000)
        profil = rng2.gauss(12.5, 3.5)  # moyenne autour de 12.5
        note   = max(0, min(20, round(rng2.gauss(profil, 1.5), 2)))
        coef   = rng.choice(COEFFICIENTS)

        cur.execute("SELECT id FROM grades WHERE id_student=? AND course_code=?",
                    (stu["id"], course_code))
        if not cur.fetchone():
            cur.execute("""INSERT INTO grades(id_student,course_code,note,coefficient,created_at)
                           VALUES(?,?,?,?,?)""",
                        (stu["id"], course_code, note, coef, datetime.now()))
            notes_created += 1

        # Absences (15% de chance d'etre absent a chaque seance)
        for seance_id in seance_ids:
            if rng.random() < 0.15:
                cur.execute("SELECT id_session FROM attendance WHERE id_session=? AND id_student=?",
                            (seance_id, stu["id"]))
                if not cur.fetchone():
                    cur.execute("""INSERT INTO attendance(id_session,id_student,justifiee)
                                   VALUES(?,?,?)""",
                                (seance_id, stu["id"], rng.random() < 0.3))

conn.commit()

# ═══════════════════════════════════════════════
# RESUME
# ═══════════════════════════════════════════════
cur.execute("SELECT COUNT(*) FROM students WHERE actif=1")
nb_etu = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
nb_prof = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM classes")
nb_classes = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM courses")
nb_cours = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM grades")
nb_notes = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM sessions")
nb_seances = cur.fetchone()[0]

conn.execute("PRAGMA foreign_keys = ON")
conn.close()

print(f"""
╔══════════════════════════════════════╗
║      BASE DE DONNEES PEUPLEE        ║
╠══════════════════════════════════════╣
║  Niveaux       : 3 (L, M, D)        ║
║  Classes       : {nb_classes:<4} (L1→M2)         ║
║  Etudiants     : {nb_etu:<4}                 ║
║  Enseignants   : {nb_prof:<4}                 ║
║  Cours         : {nb_cours:<4}                 ║
║  Notes         : {nb_notes:<4}                 ║
║  Seances       : {nb_seances:<4}                 ║
╠══════════════════════════════════════╣
║  Comptes enseignants :               ║
║    prof.diallo / prof2026            ║
║    prof.ndiaye / prof2026            ║
║    prof.fall   / prof2026            ║
║    ... (10 enseignants)              ║
╚══════════════════════════════════════╝
""")
