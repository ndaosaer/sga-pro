import pandas as pd
from datetime import datetime
from database import SessionLocal, init_db
from models import Student, Course, Grade

def migrate(filepath: str):
    init_db()
    db = SessionLocal()
    try:
        df_s = pd.read_excel(filepath, sheet_name="Etudiants")
        for _, r in df_s.iterrows():
            if not db.query(Student).filter_by(email=r["Email"]).first():
                db.add(Student(nom=r["Nom"], prenom=r["Prenom"], email=r["Email"]))
        df_c = pd.read_excel(filepath, sheet_name="Cours")
        for _, r in df_c.iterrows():
            if not db.query(Course).filter_by(code=r["Code"]).first():
                db.add(Course(code=r["Code"], libelle=r["Libelle"], volume_horaire=r["Volume_Horaire"]))
        db.commit()
        print("Migration terminee.")
    except Exception as e:
        db.rollback(); print(f"Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate("donnees.xlsx")
