import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from database import init_db, init_users
from components.sidebar import create_sidebar

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="SGA Pro",
    update_title=None,
)
server = app.server

PUBLIC_PATHS = {"/accueil", "/auth", "/login"}

ROLE_ROUTES = {
    "/portail-etudiant":   ["student"],
    "/portail-parent":     ["parent"],
    "/portail-secretaire": ["secretary"],
    "/gestion-comptes":    ["admin"],
    "/bulletin":           ["admin","teacher","student"],
    "/alertes":            ["admin","teacher"],
    "/comparateur":        ["admin","teacher"],
    "/analytics":          ["admin","teacher"],
    "/calendrier":         ["admin","teacher","secretary"],
    "/appel":              ["admin","teacher"],
    "/presences":          ["admin","teacher"],
    "/cours":              ["admin","teacher"],
    "/etudiants":          ["admin","teacher"],
}

SIDEBAR_ROLES = {"admin","teacher"}
NO_SIDEBAR    = {"/portail-etudiant","/portail-parent","/portail-secretaire"}

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="app-shell"),
])

@app.callback(
    Output("app-shell","children"),
    Input("url","pathname"),
    Input("session-store","data"),
)
def render_shell(path, session):
    path = path or "/"

    if path in PUBLIC_PATHS:
        return html.Div(dash.page_container, style={"minHeight":"100vh"})

    if not session or not session.get("logged_in"):
        return dcc.Location(href="/auth", id="redir-auth")

    role     = session.get("role","")
    username = session.get("username","")

    if path in ROLE_ROUTES and role not in ROLE_ROUTES[path]:
        return html.Div([
            html.Div([
                html.Div("⛔", style={"fontSize":"64px","textAlign":"center","marginBottom":"16px"}),
                html.Div("Accès non autorisé",
                         style={"fontFamily":"Times New Roman,serif","fontSize":"32px",
                                "fontWeight":"700","textAlign":"center",
                                "color":"var(--red)","marginBottom":"8px"}),
                html.Div(f"Cette page est réservée aux rôles : {', '.join(ROLE_ROUTES[path])}",
                         style={"textAlign":"center","color":"var(--muted)","fontSize":"14px",
                                "marginBottom":"24px"}),
                html.Div(dcc.Link("← Retour", href="/",
                         style={"color":"var(--gold)","textDecoration":"none"}),
                         style={"textAlign":"center"}),
            ], style={"maxWidth":"480px","margin":"120px auto","padding":"48px",
                      "background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px"}),
        ])

    if path in NO_SIDEBAR:
        return html.Div(dash.page_container, style={"minHeight":"100vh"})

    if role in SIDEBAR_ROLES:
        return html.Div([
            create_sidebar(role=role, username=username),
            html.Div(dash.page_container, className="main-content"),
        ], style={"minHeight":"100vh"})

    return dcc.Location(href="/auth", id="redir-fb")


if __name__ == "__main__":
    init_db()
    init_users()
    import threading, webbrowser
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8050/accueil")).start()
    app.run(debug=False)
