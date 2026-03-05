import dash, json
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Concours, Candidat, Communique
from datetime import datetime, date

dash.register_page(__name__, path="/concours", name="Concours")

TYPE_COLORS = {"info": "var(--gold)", "urgent": "var(--red)", "resultat": "var(--green)"}
TYPE_LABELS = {"info": "Information", "urgent": "Urgent", "resultat": "Resultats"}

STATUT_LABELS = {
    "en_attente":        ("var(--muted)",  "Dossier recu — en cours de traitement"),
    "dossier_incomplet": ("var(--copper)", "Dossier incomplet — pieces manquantes"),
    "dossier_complet":   ("var(--green)",  "Dossier complet — en cours de validation"),
    "valide":            ("var(--gold)",   "Dossier valide — en attente d'admission"),
    "rejete":            ("var(--red)",    "Dossier rejete"),
    "admis":             ("var(--green)",  "Felicitations — vous etes admis"),
}

def layout():
    return html.Div([
        dcc.Store(id="pc-refresh", data=0),
        dcc.Store(id="pc-tab",     data="accueil"),
        dcc.Store(id="pc-cand-id", data=None),

        # NAVBAR
        html.Div([
            html.Div([
                html.Span("SGA", style={"color":"var(--gold)","fontFamily":"Times New Roman,serif",
                    "fontSize":"22px","fontWeight":"700","letterSpacing":"4px"}),
                html.Span(" PRO", style={"fontFamily":"Times New Roman,serif",
                    "fontSize":"22px","fontStyle":"italic"}),
                html.Span(" — Concours", style={"fontSize":"13px","color":"var(--muted)",
                    "marginLeft":"12px","letterSpacing":"2px"}),
            ]),
            html.Div([
                html.Button("Accueil",         id="pc-nav-accueil", n_clicks=0, className="btn-sga"),
                html.Button("S'inscrire",       id="pc-nav-inscrire", n_clicks=0, className="btn-sga btn-gold"),
                html.Button("Mon dossier",      id="pc-nav-dossier", n_clicks=0, className="btn-sga"),
                html.Button("Admis",            id="pc-nav-admis", n_clicks=0, className="btn-sga"),
                dcc.Link("← App", href="/",
                         style={"fontSize":"10px","color":"var(--muted)","textDecoration":"none",
                                "letterSpacing":"2px","textTransform":"uppercase","padding":"8px"}),
            ], style={"display":"flex","gap":"8px","alignItems":"center"}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "padding":"16px 40px","background":"var(--bg-card)",
                  "borderBottom":"1px solid var(--border)","position":"sticky","top":"0","zIndex":"10"}),

        html.Div(id="pc-content", style={"maxWidth":"960px","margin":"0 auto","padding":"40px 24px"}),
    ], style={"minHeight":"100vh","background":"var(--bg-primary)"})


# ── Navigation ──
@callback(
    Output("pc-tab", "data"),
    Input("pc-nav-accueil",  "n_clicks"),
    Input("pc-nav-inscrire", "n_clicks"),
    Input("pc-nav-dossier",  "n_clicks"),
    Input("pc-nav-admis",    "n_clicks"),
    prevent_initial_call=True,
)
def nav(n1, n2, n3, n4):
    mapping = {
        "pc-nav-accueil":  "accueil",
        "pc-nav-inscrire": "inscrire",
        "pc-nav-dossier":  "dossier",
        "pc-nav-admis":    "admis",
    }
    return mapping.get(ctx.triggered_id, "accueil")


# ── Rendu principal ──
@callback(
    Output("pc-content", "children"),
    Input("pc-tab", "data"),
    Input("pc-refresh", "data"),
)
def render(tab, refresh):
    db = SessionLocal()
    try:
        concours = db.query(Concours).filter_by(actif=True).order_by(Concours.annee.desc()).first()

        if tab == "accueil":
            return _render_accueil(concours, db)
        elif tab == "inscrire":
            return _render_inscription(concours)
        elif tab == "dossier":
            return _render_suivi()
        elif tab == "admis":
            return _render_admis(concours, db)
    finally:
        db.close()



def _build_comm_list(comms):
    if not comms:
        return [html.Div("Aucun communique publie.", style={"color":"var(--muted)",
                "padding":"24px","textAlign":"center"})]
    items = []
    for comm in comms:
        col = TYPE_COLORS.get(comm.type_comm, "var(--gold)")
        items.append(html.Div([
            html.Div([
                html.Span(TYPE_LABELS.get(comm.type_comm, comm.type_comm).upper(),
                          style={"fontSize":"9px","letterSpacing":"2px","fontWeight":"700",
                                 "color":col, "border":f"1px solid {col}",
                                 "padding":"2px 8px","borderRadius":"2px","marginRight":"12px"}),
                html.Span(comm.titre, style={"fontWeight":"700","fontSize":"15px"}),
                html.Span(comm.created_at.strftime("%d/%m/%Y") if comm.created_at else "",
                          style={"marginLeft":"auto","fontSize":"11px","color":"var(--muted)"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"10px"}),
            html.Div(comm.contenu, style={"fontSize":"13px","color":"var(--muted)","lineHeight":"1.8"}),
        ], style={"padding":"20px","background":"var(--bg-card)","borderRadius":"6px",
                  "border":"1px solid var(--border)","marginBottom":"12px",
                  "borderLeft":f"4px solid {col}"}))
    return items

def _render_accueil(concours, db):
    if not concours:
        return html.Div([
            html.Div("Aucun concours en cours.", style={"textAlign":"center","fontSize":"20px",
                     "color":"var(--muted)","padding":"80px"}),
        ])

    def fmt(d): return d.strftime("%d %B %Y") if d else "A confirmer"

    comms = db.query(Communique).filter_by(concours_id=concours.id, publie=True)\
               .order_by(Communique.created_at.desc()).limit(10).all()

    today = date.today()
    ouverte = (concours.date_ouverture <= today if concours.date_ouverture else True)
    fermee  = (concours.date_cloture < today if concours.date_cloture else False)
    statut_badge = (
        html.Span("Inscriptions fermees", style={"background":"var(--red)","color":"#fff",
            "padding":"4px 16px","borderRadius":"20px","fontSize":"12px","fontWeight":"700"})
        if fermee else
        html.Span("Inscriptions ouvertes", style={"background":"var(--green)","color":"#fff",
            "padding":"4px 16px","borderRadius":"20px","fontSize":"12px","fontWeight":"700"})
        if ouverte else
        html.Span("Bientot ouvert", style={"background":"var(--gold)","color":"var(--bg-primary)",
            "padding":"4px 16px","borderRadius":"20px","fontSize":"12px","fontWeight":"700"})
    )

    return html.Div([
        # Hero
        html.Div([
            statut_badge,
            html.Div(concours.nom, style={"fontFamily":"Times New Roman,serif","fontSize":"44px",
                     "fontWeight":"700","margin":"16px 0 8px","lineHeight":"1.1"}),
            html.Div(f"Concours {concours.annee}", style={"fontSize":"18px","color":"var(--muted)",
                     "marginBottom":"24px","letterSpacing":"2px"}),
            html.Div(concours.description or "", style={"fontSize":"15px","lineHeight":"1.8",
                     "color":"var(--text-primary)","maxWidth":"640px","marginBottom":"32px"}),
            html.Div([
                html.Button("S'inscrire maintenant", id="btn-hero-inscrire", n_clicks=0,
                            className="btn-sga btn-gold",
                            style={"fontSize":"14px","padding":"14px 32px"}),
                html.Button("Suivre mon dossier", id="btn-hero-dossier", n_clicks=0,
                            className="btn-sga",
                            style={"fontSize":"14px","padding":"14px 32px"}),
            ], style={"display":"flex","gap":"12px"}),
        ], style={"marginBottom":"48px","paddingBottom":"48px",
                  "borderBottom":"1px solid var(--border)"}),

        # Dates cles
        html.Div([
            html.Div("Dates cles", style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                     "fontWeight":"700","marginBottom":"20px"}),
            html.Div([
                _date_card("Ouverture des inscriptions", fmt(concours.date_ouverture),  "var(--green)"),
                _date_card("Cloture des inscriptions",   fmt(concours.date_cloture),    "var(--copper)"),
                _date_card("Date du concours",           fmt(concours.date_epreuve),    "var(--gold)"),
                _date_card("Publication des resultats",  fmt(concours.date_resultats),  "var(--muted)"),
            ], style={"display":"grid","gridTemplateColumns":"repeat(2,1fr)","gap":"16px","marginBottom":"40px"}),
        ]),

        # Frais
        html.Div([
            html.Div("Frais de dossier", style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                     "fontWeight":"700","marginBottom":"16px"}),
            html.Div([
                html.Div(f"{concours.frais_dossier:,.0f}", style={"fontFamily":"Times New Roman,serif",
                         "fontSize":"56px","fontWeight":"700","color":"var(--gold)","lineHeight":"1"}),
                html.Div("FCFA", style={"fontSize":"18px","color":"var(--muted)","marginLeft":"8px",
                         "alignSelf":"flex-end","paddingBottom":"8px"}),
            ], style={"display":"flex","alignItems":"baseline","marginBottom":"8px"}),
            html.Div("Paiement accepte : Wave, Orange Money, carte bancaire",
                     style={"fontSize":"13px","color":"var(--muted)"}),
        ], style={"padding":"32px","background":"var(--bg-card)","borderRadius":"6px",
                  "border":"1px solid var(--border)","marginBottom":"40px"}),

        # Communiques
        html.Div([
            html.Div("Communiques officiels", style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                     "fontWeight":"700","marginBottom":"20px"}),
            *_build_comm_list(comms),
        ]),
    ])


def _render_inscription(concours):
    if not concours:
        return html.Div("Aucun concours en cours.", style={"textAlign":"center","color":"var(--muted)","padding":"80px"})

    return html.Div([
        html.Div("Inscription au concours", style={"fontFamily":"Times New Roman,serif","fontSize":"36px",
                 "fontWeight":"700","marginBottom":"8px"}),
        html.Div(f"{concours.nom} — {concours.annee}", style={"color":"var(--muted)","marginBottom":"32px",
                 "letterSpacing":"2px","fontSize":"14px"}),

        html.Div([
            # Section identite
            html.Div("Informations personnelles", className="sga-card-title", style={"marginBottom":"16px"}),
            html.Div([
                html.Div([html.Div("Nom", className="sga-label"),
                          dcc.Input(id="insc-nom", placeholder="Votre nom de famille",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"1"}),
                html.Div([html.Div("Prenom", className="sga-label"),
                          dcc.Input(id="insc-prenom", placeholder="Votre prenom",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),

            html.Div([
                html.Div([html.Div("Email", className="sga-label"),
                          dcc.Input(id="insc-email", type="email", placeholder="votre@email.com",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"2"}),
                html.Div([html.Div("Telephone", className="sga-label"),
                          dcc.Input(id="insc-tel", placeholder="+221 7X XXX XX XX",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),

            html.Div([
                html.Div([html.Div("Date de naissance", className="sga-label"),
                          dcc.Input(id="insc-ddn", type="date", className="sga-input", style={"width":"100%"})],
                         style={"flex":"1"}),
                html.Div([html.Div("Nationalite", className="sga-label"),
                          dcc.Input(id="insc-nat", placeholder="Senegalaise",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","marginBottom":"24px"}),

            # Section cursus
            html.Div("Cursus academique", className="sga-card-title",
                     style={"marginBottom":"16px","paddingTop":"16px","borderTop":"1px solid var(--border)"}),
            html.Div([
                html.Div([html.Div("Niveau d'etudes actuel", className="sga-label"),
                          dcc.Dropdown(id="insc-niveau",
                                       options=[{"label":v,"value":v} for v in
                                                ["Bac","Bac+1","Bac+2 (DEUG/BTS/DUT)","Licence (Bac+3)",
                                                 "Master 1","Master 2","Doctorat"]],
                                       placeholder="Selectionner...", clearable=False)],
                         style={"flex":"1"}),
                html.Div([html.Div("Etablissement actuel", className="sga-label"),
                          dcc.Input(id="insc-etab", placeholder="Universite / Ecole",
                                    className="sga-input", style={"width":"100%"})],
                         style={"flex":"2"}),
            ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),

            html.Div([html.Div("Filiere / Specialite", className="sga-label"),
                      dcc.Input(id="insc-filiere", placeholder="ex: Mathematiques, Economie...",
                                className="sga-input", style={"width":"100%"})],
                     style={"marginBottom":"24px"}),

            # Bouton
            html.Button("Soumettre ma candidature", id="btn-insc-submit", n_clicks=0,
                        className="btn-sga btn-gold",
                        style={"fontSize":"13px","padding":"14px 32px","justifyContent":"center","width":"100%"}),
            html.Div(id="insc-feedback", style={"marginTop":"16px"}),

        ], className="sga-card"),
    ])


def _render_suivi():
    return html.Div([
        html.Div("Suivi de mon dossier", style={"fontFamily":"Times New Roman,serif","fontSize":"36px",
                 "fontWeight":"700","marginBottom":"8px"}),
        html.Div("Entrez votre email pour consulter l'etat de votre dossier.",
                 style={"color":"var(--muted)","marginBottom":"32px","fontSize":"14px"}),

        html.Div([
            html.Div("Email de candidature", className="sga-label"),
            html.Div([
                dcc.Input(id="suivi-email", type="email", placeholder="votre@email.com",
                          className="sga-input", style={"flex":"1"}),
                html.Button("Rechercher", id="btn-suivi", n_clicks=0,
                            className="btn-sga btn-gold", style={"flexShrink":"0"}),
            ], style={"display":"flex","gap":"12px","marginBottom":"20px"}),
            html.Div(id="suivi-result"),
        ], className="sga-card"),
    ])


def _render_admis(concours, db):
    if not concours:
        return html.Div("Aucun concours en cours.", style={"textAlign":"center","color":"var(--muted)","padding":"80px"})
    admis = db.query(Candidat).filter_by(concours_id=concours.id, admis=True).order_by(Candidat.nom).all()

    return html.Div([
        html.Div("Liste des admis", style={"fontFamily":"Times New Roman,serif","fontSize":"36px",
                 "fontWeight":"700","marginBottom":"8px"}),
        html.Div(f"{concours.nom} — {concours.annee}", style={"color":"var(--muted)",
                 "marginBottom":"32px","letterSpacing":"2px","fontSize":"14px"}),

        html.Div([
            html.Div(f"{len(admis)} candidat(s) admis", className="sga-card-title",
                     style={"marginBottom":"20px"}),
            html.Table([
                html.Thead(html.Tr([html.Th("N°"), html.Th("Nom & Prenom"), html.Th("Statut")])),
                html.Tbody([html.Tr([
                    html.Td(a.numero_candidat or f"#{a.id:04d}",
                            style={"fontFamily":"JetBrains Mono,monospace","color":"var(--gold)","fontWeight":"700"}),
                    html.Td(f"{a.nom.upper()} {a.prenom}", style={"fontWeight":"600"}),
                    html.Td(html.Span("ADMIS", style={"color":"var(--green)","fontWeight":"700","fontSize":"11px",
                                                      "letterSpacing":"2px"})),
                ]) for a in admis]),
            ], className="sga-table", style={"width":"100%"})
            if admis else
            html.Div("La liste des admis n'est pas encore publiee.",
                     style={"textAlign":"center","color":"var(--muted)","padding":"48px"}),
        ], className="sga-card"),
    ])


# ── Boutons hero -> navigation ──
@callback(
    Output("pc-tab", "data", allow_duplicate=True),
    Input("btn-hero-inscrire", "n_clicks"),
    Input("btn-hero-dossier",  "n_clicks"),
    prevent_initial_call=True,
)
def hero_nav(n1, n2):
    return "inscrire" if ctx.triggered_id == "btn-hero-inscrire" else "dossier"


# ── Soumettre candidature ──
@callback(
    Output("insc-feedback", "children"),
    Output("pc-refresh", "data", allow_duplicate=True),
    Input("btn-insc-submit", "n_clicks"),
    State("insc-nom",     "value"),
    State("insc-prenom",  "value"),
    State("insc-email",   "value"),
    State("insc-tel",     "value"),
    State("insc-ddn",     "value"),
    State("insc-nat",     "value"),
    State("insc-niveau",  "value"),
    State("insc-etab",    "value"),
    State("insc-filiere", "value"),
    State("pc-refresh",   "data"),
    prevent_initial_call=True,
)
def soumettre(n, nom, prenom, email, tel, ddn, nat, niveau, etab, filiere, refresh):
    if not all([nom, prenom, email]):
        return html.Div("Nom, prenom et email sont obligatoires.",
                        className="sga-alert sga-alert-warning"), dash.no_update

    db = SessionLocal()
    try:
        concours = db.query(Concours).filter_by(actif=True).order_by(Concours.annee.desc()).first()
        if not concours:
            return html.Div("Aucun concours actif.", className="sga-alert sga-alert-danger"), dash.no_update

        # Verifier doublons
        existant = db.query(Candidat).filter_by(concours_id=concours.id, email=email).first()
        if existant:
            return html.Div(
                f"Un dossier existe deja avec cet email (N° candidat : {existant.numero_candidat or existant.id}).",
                className="sga-alert sga-alert-warning"), dash.no_update

        cand = Candidat()
        cand.concours_id    = concours.id
        cand.nom            = nom.strip().upper()
        cand.prenom         = prenom.strip()
        cand.email          = email.strip().lower()
        cand.telephone      = tel
        cand.date_naissance = datetime.strptime(ddn, "%Y-%m-%d").date() if ddn else None
        cand.nationalite    = nat
        cand.niveau_etudes  = niveau
        cand.etablissement  = etab
        cand.filiere        = filiere
        cand.statut         = "en_attente"
        cand.paiement_statut = "non_paye"
        cand.created_at     = datetime.now()
        db.add(cand)
        db.flush()
        cand.numero_candidat = f"{concours.annee}-{cand.id:04d}"
        db.commit()

        return html.Div([
            html.Div(f"Candidature enregistree avec succes.",
                     className="sga-alert sga-alert-success"),
            html.Div([
                html.Div("Votre numero de candidat :", style={"fontSize":"12px","color":"var(--muted)","marginBottom":"4px"}),
                html.Div(cand.numero_candidat, style={"fontFamily":"Times New Roman,serif","fontSize":"32px",
                         "fontWeight":"700","color":"var(--gold)","marginBottom":"8px"}),
                html.Div("Conservez ce numero pour suivre votre dossier.",
                         style={"fontSize":"12px","color":"var(--muted)"}),
            ], style={"padding":"20px","background":"var(--bg-secondary)","borderRadius":"6px",
                      "border":"1px solid var(--border)","textAlign":"center","marginTop":"12px"}),
        ]), (refresh or 0) + 1

    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Suivi dossier ──
@callback(
    Output("suivi-result", "children"),
    Input("btn-suivi", "n_clicks"),
    State("suivi-email", "value"),
    prevent_initial_call=True,
)
def suivi(n, email):
    if not email:
        return html.Div("Entrez votre email.", className="sga-alert sga-alert-warning")
    db = SessionLocal()
    try:
        cands = db.query(Candidat).filter_by(email=email.strip().lower()).all()
        if not cands:
            return html.Div("Aucun dossier trouve avec cet email.",
                            className="sga-alert sga-alert-danger")
        results = []
        for cand in cands:
            col, msg = STATUT_LABELS.get(cand.statut, ("var(--muted)", cand.statut))
            pcol = "var(--green)" if cand.paiement_statut == "paye" else \
                   "var(--copper)" if cand.paiement_statut == "simule" else "var(--red)"
            plbl = "Paye" if cand.paiement_statut == "paye" else \
                   "Simule" if cand.paiement_statut == "simule" else "Non paye"
            results.append(html.Div([
                html.Div([
                    html.Div(f"N° {cand.numero_candidat or cand.id}",
                             style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                                    "fontWeight":"700","color":"var(--gold)","marginBottom":"4px"}),
                    html.Div(f"{cand.prenom} {cand.nom}",
                             style={"fontWeight":"600","fontSize":"16px","marginBottom":"16px"}),
                ]),
                html.Div([
                    html.Div(style={"width":"12px","height":"12px","borderRadius":"50%",
                                    "background":col,"flexShrink":"0","marginTop":"3px"}),
                    html.Div([
                        html.Div("Statut du dossier", style={"fontSize":"10px","color":"var(--muted)",
                                 "letterSpacing":"1px","textTransform":"uppercase"}),
                        html.Div(msg, style={"fontWeight":"700","color":col}),
                    ]),
                ], style={"display":"flex","gap":"10px","marginBottom":"12px"}),
                html.Div([
                    html.Div(style={"width":"12px","height":"12px","borderRadius":"50%",
                                    "background":pcol,"flexShrink":"0","marginTop":"3px"}),
                    html.Div([
                        html.Div("Paiement des frais", style={"fontSize":"10px","color":"var(--muted)",
                                 "letterSpacing":"1px","textTransform":"uppercase"}),
                        html.Div(plbl, style={"fontWeight":"700","color":pcol}),
                    ]),
                ], style={"display":"flex","gap":"10px","marginBottom":"16px"}),

                # Bouton paiement simulé si pas encore payé
                (html.Div([
                    html.Button("Simuler le paiement Wave/Orange Money",
                                id={"type":"btn-payer","index":cand.id},
                                n_clicks=0, className="btn-sga btn-gold",
                                style={"fontSize":"11px","padding":"10px 20px"}),
                ]) if cand.paiement_statut == "non_paye" else html.Div()),

                html.Div(id={"type":"pay-feedback","index":cand.id}),

                html.Div(cand.note_admin, style={"marginTop":"12px","padding":"12px",
                         "background":"var(--bg-secondary)","borderRadius":"4px",
                         "fontSize":"13px","color":"var(--muted)","fontStyle":"italic"})
                if cand.note_admin else html.Div(),
            ], className="sga-card", style={"marginBottom":"16px"}))
        return html.Div(results)
    finally:
        db.close()


# ── Paiement simule ──
@callback(
    Output({"type":"pay-feedback","index":dash.ALL}, "children"),
    Input({"type":"btn-payer","index":dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def payer(n_clicks):
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return [dash.no_update] * len(n_clicks)
    cand_id = triggered["index"]
    results = [dash.no_update] * len(n_clicks)
    db = SessionLocal()
    try:
        cand = db.query(Candidat).get(cand_id)
        if cand:
            cand.paiement_statut = "simule"
            cand.paiement_ref    = f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cand.paiement_date   = datetime.now()
            cand.paiement_mode   = "simulation"
            if cand.statut == "en_attente":
                cand.statut = "dossier_complet"
            db.commit()
            idx = next((i for i, t in enumerate(ctx.inputs_list[0]) if t["id"]["index"] == cand_id), None)
            if idx is not None:
                results[idx] = html.Div(
                    f"Paiement simule confirme. Reference : {cand.paiement_ref}",
                    className="sga-alert sga-alert-success")
        return results
    finally:
        db.close()


def _date_card(label, val, color):
    return html.Div([
        html.Div(label, style={"fontSize":"10px","letterSpacing":"2px","textTransform":"uppercase",
                               "color":"var(--muted)","marginBottom":"8px"}),
        html.Div(val, style={"fontFamily":"Times New Roman,serif","fontSize":"20px",
                             "fontWeight":"700","color":color}),
    ], style={"padding":"20px","background":"var(--bg-card)","borderRadius":"6px",
              "border":"1px solid var(--border)","borderLeft":f"4px solid {color}"})
