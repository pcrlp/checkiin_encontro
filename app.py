import streamlit as st
import requests
import unicodedata
from datetime import datetime, timezone, timedelta
import os

st.set_page_config(page_title="Check-in Encontro com Deus", page_icon="⛪", layout="centered")

# ─── Config & Supabase (Sem Login) ───────────────────────────────────────────
# Busca as chaves de forma segura, sem gerar erro caso o nome esteja diferente
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", "")).rstrip("/")
SUPABASE_SERVICE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""))

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    st.error("⚠️ As chaves SUPABASE_URL e SUPABASE_SERVICE_KEY não foram encontradas nos Secrets.")
    st.stop()

API = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

BRT = timezone(timedelta(hours=-3))

def strip_accents(text):
    if not text: return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def norm(s):
    if not s: return ""
    return strip_accents(str(s)).strip().lower()

def is_encounterist(cat):
    return "encontr" in norm(cat)

# ─── Custom CSS (Light Mode / Clean SaaS) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 600px;}
html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] { background: #F8FAFC; }
[data-testid="stHeader"] { background: transparent; }

/* Title - compact & clean */
.shine-title { text-align: center; padding: 0.5rem 0 0.5rem 0; }
.shine-title h1 { font-weight: 500; font-size: 1.2rem; color: #64748B; margin: 0; letter-spacing: 1px; text-transform: uppercase;}
.shine-title h2 { font-weight: 700; font-size: 1.8rem; color: #16A34A; margin: 0; }
.shine-title p { font-size: 0.8rem; color: #94A3B8; margin: 0; }

/* Stats - Branco com texto escuro e verde */
.stats-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 0.5rem 0 1rem 0;
}
.stats-box { 
    background: #FFFFFF; 
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border-radius: 12px; 
    padding: 0.8rem; 
    text-align: center;
}
.stats-title {
    font-size: 0.85rem;
    color: #475569;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 0.3rem;
}
.stats-row {
    display: flex;
    justify-content: space-between;
    margin-top: 0.3rem;
}
.stat-item { text-align: center; flex: 1; }
.stat-number { font-size: 1.3rem; font-weight: 700; }
.stat-number.arrived { color: #16A34A; }
.stat-number.missing { color: #EF4444; }
.stat-label { font-size: 0.65rem; color: #64748B; text-transform: uppercase; font-weight: 600; }

/* Search bar */
[data-testid="stTextInput"] > div { background: transparent !important; }
[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    color: #1E293B !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #94A3B8 !important; }
[data-testid="stTextInput"] label { display: none !important; }

/* ── Person row ── */
.p-row {
    display: flex;
    align-items: center;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    margin: 0.35rem 0;
    gap: 0.5rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.p-row.done {
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-left: 4px solid #10B981;
}
.p-row-text {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.p-row .name {
    color: #0F172A;
    font-size: 0.9rem;
    font-weight: 600;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.p-row.done .name { color: #065F46; }
.p-row .room {
    color: #64748B;
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 0.1rem;
}
.p-row.done .room { color: #047857; }
.p-row .time {
    color: #10B981;
    font-size: 0.65rem;
    font-weight: 600;
    margin-top: 0.1rem;
}
.p-row .ok-icon {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #10B981;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.p-row .ok-icon svg { width: 16px; height: 16px; stroke: white; }

/* ── Buttons ── */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0 !important;
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child {
    flex: 1 !important;
    min-width: 0 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child {
    max-width: 95px !important;
    min-width: 90px !important;
    display: flex; align-items: center; justify-content: center;
}
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    padding: 0.4rem 0.6rem !important;
    border-radius: 20px !important;
    min-height: 0 !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    background: transparent !important;
    width: 100% !important;
}
.stButton > button:not(:disabled) {
    color: #16A34A !important;
    border: 1.5px solid #16A34A !important;
}
.stButton > button:not(:disabled):hover {
    background: #F0FDF4 !important;
}

hr { border-color: #E2E8F0 !important; margin: 0.5rem 0 !important; }
.no-results { color: #64748B; text-align: center; font-size: 0.9rem; margin-top: 1rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── JS: instant search ──
st.markdown("""
<script>
const doc = window.parent.document;
function setupInstantSearch() {
    const input = doc.querySelector('[data-testid="stTextInput"] input');
    if (!input || input.dataset.instantBound) return;
    input.dataset.instantBound = 'true';
    let timer = null;
    input.addEventListener('input', function() {
        clearTimeout(timer);
        timer = setTimeout(() => {
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.blur();
            setTimeout(() => input.focus(), 50);
        }, 350);
    });
}
setTimeout(setupInstantSearch, 500);
new MutationObserver(setupInstantSearch).observe(
    window.parent.document.body, {childList: true, subtree: true}
);
</script>
""", unsafe_allow_html=True)

# ── Helpers de Banco de Dados ───────────────────────────────────────
def load_participants():
    r = requests.get(f"{API}/Participants?select=Id,Name,Category,Gender,CheckInStatus,CheckInTime&order=Name.asc", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def load_rooms_map():
    r_assigns = requests.get(f"{API}/RoomAssignments?select=ParticipantId,RoomId", headers=HEADERS)
    r_assigns.raise_for_status()
    assigns = r_assigns.json()
    
    r_rooms = requests.get(f"{API}/Rooms?select=Id,Name", headers=HEADERS)
    r_rooms.raise_for_status()
    rooms = {rm["Id"]: rm["Name"] for rm in r_rooms.json()}
    
    return {a["ParticipantId"]: rooms.get(a["RoomId"], "Sem Quarto") for a in assigns}

def do_checkin(record_id):
    now = datetime.now(BRT).isoformat()
    requests.patch(
        f"{API}/Participants?Id=eq.{record_id}",
        headers=HEADERS,
        json={"CheckInStatus": True, "CheckInTime": now},
    ).raise_for_status()

def undo_checkin(record_id):
    requests.patch(
        f"{API}/Participants?Id=eq.{record_id}",
        headers=HEADERS,
        json={"CheckInStatus": False, "CheckInTime": None},
    ).raise_for_status()

def format_time(iso_str):
    if not iso_str: return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M")
    except: return ""

# ── UI ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="shine-title">
    <h1>Check-in</h1>
    <h2>Encontro com Deus</h2>
    <p>Recepção e Credenciamento</p>
</div>
""", unsafe_allow_html=True)

try:
    all_parts = load_participants()
    rooms_map = load_rooms_map()
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados. Verifique suas chaves no Streamlit Cloud.")
    st.stop()

# 1. FILTRA APENAS ENCONTRISTAS
encontristas = [p for p in all_parts if is_encounterist(p.get("Category"))]

# 2. CÁLCULO DAS ESTATÍSTICAS POR GÊNERO
homens = [p for p in encontristas if p.get("Gender") == 1]
mulheres = [p for p in encontristas if p.get("Gender") == 2]

h_chegaram = sum(1 for h in homens if h.get("CheckInStatus"))
h_faltam = len(homens) - h_chegaram

m_chegaram = sum(1 for m in mulheres if m.get("CheckInStatus"))
m_faltam = len(mulheres) - m_chegaram

# Reader (Cards de Gênero)
st.markdown(f"""
<div class="stats-container">
    <div class="stats-box">
        <div class="stats-title">👨 Homens ({len(homens)})</div>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-number arrived">{h_chegaram}</div>
                <div class="stat-label">Chegaram</div>
            </div>
            <div class="stat-item">
                <div class="stat-number missing">{h_faltam}</div>
                <div class="stat-label">Faltam</div>
            </div>
        </div>
    </div>
    <div class="stats-box">
        <div class="stats-title">👩 Mulheres ({len(mulheres)})</div>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-number arrived">{m_chegaram}</div>
                <div class="stat-label">Chegaram</div>
            </div>
            <div class="stat-item">
                <div class="stat-number missing">{m_faltam}</div>
                <div class="stat-label">Faltam</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

search = st.text_input("Buscar", placeholder="🔍 Digite o nome do encontrista...")

# Aplica Busca na lista de encontristas
data_to_show = encontristas
if search:
    term = norm(search)
    data_to_show = [p for p in data_to_show if term in norm(p.get("Name", ""))]

if not data_to_show and len(encontristas) > 0:
    st.markdown('<p class="no-results">Nenhum encontrista encontrado com esse nome.</p>', unsafe_allow_html=True)
elif len(encontristas) == 0:
    st.markdown('<p class="no-results">Nenhum encontrista cadastrado no sistema ainda.</p>', unsafe_allow_html=True)

CHECK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'

# Renderiza a Lista
for person in data_to_show:
    pid = person["Id"]
    name = person.get("Name", "Sem Nome")
    quarto = rooms_map.get(pid, "Sem quarto atribuído") 
    checked = person.get("CheckInStatus", False)
    checked_at = person.get("CheckInTime", None)

    col1, col2 = st.columns([5, 2])

    with col1:
        cls = "p-row done" if checked else "p-row"
        icon = f'<div class="ok-icon">{CHECK_SVG}</div>' if checked else ""
        time_str = f'<div class="time">✓ Entrou às {format_time(checked_at)}</div>' if checked and checked_at else ""
        
        st.markdown(
            f'<div class="{cls}">'
            f'  <div class="p-row-text">'
            f'    <div class="name">{name}</div>'
            f'    <div class="room">🏠 {quarto}</div>'
            f'    {time_str}'
            f'  </div>'
            f'  {icon}'
            f'</div>',
            unsafe_allow_html=True
        )

    with col2:
        if checked:
            st.markdown("""<style>div[data-testid="stHorizontalBlock"] div:has(button:contains("DESFAZER")) button { border-color: #94A3B8 !important; color: #64748B !important; }</style>""", unsafe_allow_html=True)
            if st.button("DESFAZER", key=f"undo_{pid}"):
                undo_checkin(pid)
                st.rerun()
        else:
            if st.button("ENTRAR", key=f"chk_{pid}"):
                do_checkin(pid)
                st.rerun()
