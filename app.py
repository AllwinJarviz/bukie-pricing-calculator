import streamlit as st
import os
import json
from datetime import datetime
from anthropic import Anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BOOKING_LINK = "https://appt.link/bukie-signatureQB94tuiF/signature-audit"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Pricing Leak Calculator — Bukie Signature Consulting",
    page_icon="💷",
    layout="centered",
)

# Brand CSS: light palette (cream bg), dark purple hero, purple+gold accents
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Hide Streamlit chrome so hero fills top edge */
  #MainMenu { visibility: hidden; }
  header[data-testid="stHeader"] { display: none !important; }
  footer { visibility: hidden; }
  [data-testid="stToolbar"] { display: none !important; }
  [data-testid="stDecoration"] { display: none !important; }

  /* Light page background */
  .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
  section[data-testid="stSidebar"] {
    background-color: #f8f4fc !important;
    color: #1a0a2e !important;
  }
  .main .block-container {
    background-color: #f8f4fc !important;
    padding-top: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 760px !important;
  }

  /* Default text: dark on light */
  p, span, label, div, h1, h2, h3, h4, h5, h6 { color: #1a0a2e; }

  /* Step labels */
  .step-label { font-weight: 600; color: #721496 !important; margin-bottom: 0.2rem; font-size: 0.95rem; }

  /* Inputs */
  input[type="number"], input[type="text"], input[type="email"],
  [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {
    background-color: #fff !important;
    color: #1a0a2e !important;
    border: 1px solid #721496 !important;
    border-radius: 6px !important;
  }
  [data-testid="stNumberInput"], [data-testid="stTextInput"] {
    background-color: #fff !important;
    border: 1px solid #721496 !important;
    border-radius: 6px !important;
  }
  [data-testid="stNumberInput"] button {
    background-color: #fff !important;
    color: #721496 !important;
    border: none !important;
  }

  /* Radio buttons */
  [data-testid="stRadio"] label { color: #1a0a2e !important; }
  [data-testid="stRadio"] div[role="radiogroup"] label span { color: #1a0a2e !important; }
  [data-testid="stRadio"] div[data-baseweb="radio"] div:first-child {
    background-color: #fff !important;
    border-color: #721496 !important;
  }
  [data-testid="stRadio"] div[data-baseweb="radio"] [aria-checked="true"] div:first-child {
    background-color: #721496 !important;
    border-color: #721496 !important;
  }
  input[type="radio"]:checked + div { background-color: #721496 !important; }
  /* Selected option: white text — use :has() to beat global div colour rule */
  [data-testid="stRadio"] label:has([aria-checked="true"]) p,
  [data-testid="stRadio"] label:has([aria-checked="true"]) span,
  [data-testid="stRadio"] label:has([aria-checked="true"]) div { color: #fff !important; }
  [data-testid="stRadio"] [aria-checked="true"] p { color: #fff !important; }
  [data-testid="stRadio"] [aria-checked="true"] span { color: #fff !important; }

  /* Primary button — explicit white text overrides global dark-text rule */
  .stButton > button, [data-testid="stFormSubmitButton"] > button {
    background: #721496 !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    width: 100% !important;
  }
  .stButton > button *, .stButton > button p, .stButton > button span,
  [data-testid="stFormSubmitButton"] > button *,
  [data-testid="stFormSubmitButton"] > button p,
  [data-testid="stFormSubmitButton"] > button span { color: #fff !important; }
  .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    background: #5a0f78 !important;
  }

  /* Link button (CTA): white text on dark box, always visible */
  [data-testid="stLinkButton"] a {
    background: #fff !important;
    color: #721496 !important;
    font-weight: 700 !important;
    border: 2px solid #fff !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    text-decoration: none !important;
    font-size: 1rem !important;
  }
  [data-testid="stLinkButton"] a:hover { background: #f0e0ff !important; color: #4f1964 !important; }

  /* Form card covers Q3-5. Q1-Q2 sit on the cream bg above it — clean and readable */
  div[data-testid="stForm"] {
    background-color: #fff !important;
    border: 1px solid #e0cef5 !important;
    border-radius: 12px !important;
    padding: 1.5rem 1.8rem 1.5rem !important;
    margin-bottom: 1.5rem !important;
  }

  /* HR */
  hr { border-color: #e0cef5 !important; }

  /* Caption */
  [data-testid="stCaptionContainer"] p, small { color: #7a5c9a !important; }

  /* Markdown */
  [data-testid="stMarkdownContainer"] p { color: #1a0a2e !important; }
  [data-testid="stMarkdownContainer"] em { color: #4f1964 !important; }

  /* Error */
  [data-testid="stAlert"] { background-color: #f5eeff !important; border-color: #721496 !important; }
  [data-testid="stAlert"] p { color: #4f1964 !important; }

  /* Spinner */
  [data-testid="stSpinner"] p { color: #721496 !important; }

  /* Result cards: white with purple left accent */
  .result-card {
    background: #fff;
    border: 1px solid #e0cef5;
    border-left: 4px solid #721496;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin: 1rem 0;
    color: #1a0a2e;
  }
  .result-card .label {
    color: #721496;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .result-card .number {
    font-size: 2.4rem;
    font-weight: 700;
    color: #721496;
    margin: 0.3rem 0;
  }
  .result-card .insight { color: #3d1660; font-size: 0.95rem; line-height: 1.6; }

  /* ── Hero block ── */
  .hero {
    background: linear-gradient(135deg, #4f1964 0%, #9b2fd4 100%);
    border-bottom: 3px solid #c060f0;
    padding: 3rem 2rem 2.5rem;
    margin-bottom: 2rem;
    margin-left: -1rem;
    margin-right: -1rem;
  }
  .hero .eyebrow {
    color: #ffde59;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
  }
  .hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0 0 1rem; color: #fff !important; line-height: 1.2; }
  .hero h1 span { color: #ffde59; }
  .hero p { color: #e0cef5 !important; margin: 0; font-size: 1.05rem; line-height: 1.6; }

  /* CTA box: solid dark so it pops on the light page */
  .cta-box {
    background: #1a0a2e;
    border-radius: 12px;
    padding: 2rem 1.8rem 1.4rem;
    text-align: center;
    margin-top: 2rem;
  }
  .cta-box h3 { color: #ffde59 !important; margin: 0 0 0.6rem; font-size: 1.35rem; font-weight: 700; }
  .cta-box p { color: #e0cef5 !important; margin: 0 0 1.4rem; font-size: 1rem; line-height: 1.6; }

  /* Section headings */
  h3 { color: #721496 !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_gbp(n):
    return f"£{n:,.0f}"

def get_sheets_service():
    import json as _json
    token = ROOT / "token.json"
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    elif "gcp_token" in st.secrets:
        creds = Credentials.from_authorized_user_info(_json.loads(st.secrets["gcp_token"]), SCOPES)
    else:
        return None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("sheets", "v4", credentials=creds)

def save_lead(email, name, inputs, results):
    try:
        sheet_id = os.getenv("LEADS_SHEET_ID", "")
        if not sheet_id:
            return
        svc = get_sheets_service()
        if not svc:
            return
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            name, email,
            inputs["years"], inputs["charge_type"],
            inputs["current_rate"], inputs["volume"],
            inputs["years_since_raise"],
            results["monthly_leak"], results["annual_leak"],
            results["clients_can_lose"],
        ]
        svc.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()
    except Exception:
        pass  # silent — don't break the user experience

def calculate(current_rate, charge_type, volume, years_since_raise, years_in_business):
    """
    Uplift is a function of BOTH years in business AND time since last raise.
    More experienced founders who haven't raised in longer = larger gap.

    years_since_raise index: 0=within last year, 1=1-2 years, 2=3+ years, 3=never
    years_in_business: "1–2 years", "3–5 years", "6–10 years", "10+ years"
    """
    # 2D uplift table: (years_in_business, years_since_raise) -> uplift %
    UPLIFT_TABLE = {
        ("1-2 years",  0): 0.15, ("1-2 years",  1): 0.20, ("1-2 years",  2): 0.25, ("1-2 years",  3): 0.25,
        ("3-5 years",  0): 0.20, ("3-5 years",  1): 0.25, ("3-5 years",  2): 0.30, ("3-5 years",  3): 0.30,
        ("6-10 years", 0): 0.25, ("6-10 years", 1): 0.30, ("6-10 years", 2): 0.35, ("6-10 years", 3): 0.35,
        ("10+ years",  0): 0.25, ("10+ years",  1): 0.30, ("10+ years",  2): 0.35, ("10+ years",  3): 0.35,
    }
    uplift = UPLIFT_TABLE.get((years_in_business, years_since_raise), 0.30)

    # Monthly current income
    if charge_type == "Monthly Retainer":
        monthly_current = current_rate * volume
    else:
        # Per Project / Package: volume = projects per month
        monthly_current = current_rate * volume

    monthly_at_fair  = monthly_current * (1 + uplift)
    monthly_leak     = monthly_at_fair - monthly_current
    annual_leak      = monthly_leak * 12
    three_year_leak  = annual_leak * 3

    # Retention risk: units you could lose at the raised rate and still break even
    rate_raised = round(current_rate * (1 + uplift))
    units_needed = monthly_current / rate_raised
    units_can_lose = volume - units_needed

    units_can_lose = max(0, units_can_lose)

    return {
        "monthly_leak": round(monthly_leak),
        "annual_leak": round(annual_leak),
        "three_year_leak": round(three_year_leak),
        "clients_can_lose": round(units_can_lose, 1),
        "units_needed": round(units_needed, 1),
        "rate_raised": rate_raised,
        "monthly_current": round(monthly_current),
        "uplift_pct": round(uplift * 100),
    }

def generate_reframe(name, inputs, results):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    charge_label = inputs["charge_type"].lower()
    if inputs["charge_type"] == "Monthly Retainer":
        volume_label = f"{inputs['volume']} active clients"
    else:
        volume_label = f"{inputs['volume']} projects/month"

    prompt = f"""You are writing a personalised reframe for {name}, a {inputs['years']} service business owner
who charges {charge_label} (£{inputs['current_rate']}/unit), with {volume_label},
and hasn't raised prices in {inputs['years_since_raise_label']}.

Their numbers: leaving £{results['monthly_leak']:,}/month on the table. Annual leak: £{results['annual_leak']:,}.

Write 3 sentences in the voice of Bukie Signature Consulting: direct, identity-focused, warm but honest.
Use phrases like "your work has evolved but your pricing hasn't", "pricing from an older version of yourself",
"the leader you've already become". Do NOT use hype or motivational fluff.
End with a sentence that creates urgency without panic. No bullet points. Plain paragraph."""

    r = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text.strip()

# ── App ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="eyebrow">Bukie Signature Consulting</div>
  <h1>What Is Your <span>Pricing Leak?</span></h1>
  <p>You put in the years. You do great work. And somewhere along the way, you started pricing like you were still figuring things out.<br><br>
  <strong style="color:#fff;">Answer 5 questions and find out what that gap is actually costing you.</strong></p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = "questions"
if "results" not in st.session_state:
    st.session_state.results = None
if "charge_type_sel" not in st.session_state:
    st.session_state.charge_type_sel = "Per Project / Package"
    # Remove hourly from legacy sessions that may have stored it
    if st.session_state.get("charge_type_sel") == "Hourly / Day Rate":
        st.session_state.charge_type_sel = "Per Project / Package"

# ── STEP 1: Questions ─────────────────────────────────────────────────────────
if st.session_state.step == "questions":

    st.markdown('<p class="step-label">1. How long have you been running your business?</p>', unsafe_allow_html=True)
    years = st.radio(
        "", ["1-2 years", "3-5 years", "6-10 years", "10+ years"],
        index=1, label_visibility="collapsed", horizontal=True,
        key="years_sel",
    )

    # Q2 is OUTSIDE the form so changing it triggers an immediate rerun
    # and Q3/Q4 labels update before the user sees the form.
    st.markdown('<p class="step-label">2. How do you currently charge?</p>', unsafe_allow_html=True)
    charge_type = st.radio(
        "", ["Monthly Retainer", "Per Project / Package"],
        key="charge_type_sel", label_visibility="collapsed", horizontal=True,
    )

    with st.form("calculator"):
        # Question 3: rate label depends on charge type (already selected above)
        if charge_type == "Monthly Retainer":
            rate_label = "Your monthly retainer per client (£)"
            rate_min, rate_default, rate_step = 100, 1500, 100
        else:
            rate_label = "Your typical project or package fee (£)"
            rate_min, rate_default, rate_step = 250, 3000, 250

        st.markdown(f'<p class="step-label">3. {rate_label}</p>', unsafe_allow_html=True)
        current_rate = st.number_input("", min_value=rate_min, max_value=100000,
                                        value=rate_default, step=rate_step,
                                        label_visibility="collapsed")

        # Question 4: volume label depends on charge type
        if charge_type == "Monthly Retainer":
            volume_label = "How many active retainer clients do you have?"
            volume_min, volume_max, volume_default = 1, 50, 5
        else:
            volume_label = "How many projects do you take on per month?"
            volume_min, volume_max, volume_default = 1, 30, 3

        st.markdown(f'<p class="step-label">4. {volume_label}</p>', unsafe_allow_html=True)
        volume = st.number_input("", min_value=volume_min, max_value=volume_max,
                                  value=volume_default, label_visibility="collapsed")

        st.markdown('<p class="step-label">5. When did you last raise your prices?</p>', unsafe_allow_html=True)
        raise_options = ["Within the last year", "1–2 years ago", "3+ years ago", "I haven't changed them"]
        years_since_raise_label = st.radio("", raise_options, index=2, label_visibility="collapsed")
        years_since_raise = raise_options.index(years_since_raise_label)

        submitted = st.form_submit_button("Calculate my pricing leak →", use_container_width=True)

    if submitted:
        st.session_state.inputs = {
            "years": years,
            "charge_type": charge_type,
            "current_rate": current_rate,
            "volume": volume,
            "years_since_raise": years_since_raise,
            "years_since_raise_label": years_since_raise_label,
        }
        st.session_state.step = "email"
        st.rerun()

# ── STEP 2: Email capture ─────────────────────────────────────────────────────
elif st.session_state.step == "email":
    st.markdown("### Almost there. Where should we send your results?")
    st.caption("We'll save your breakdown so you can reference it in a strategy session.")

    with st.form("email_form"):
        name  = st.text_input("Your first name")
        email = st.text_input("Your email address")
        go    = st.form_submit_button("Show my results →", use_container_width=True)

    if go:
        if not name or not email or "@" not in email:
            st.error("Please enter your name and a valid email address.")
        else:
            st.session_state.name  = name
            st.session_state.email = email
            with st.spinner("Calculating your pricing leak..."):
                inputs  = st.session_state.inputs
                results = calculate(
                    inputs["current_rate"],
                    inputs["charge_type"],
                    inputs["volume"],
                    inputs["years_since_raise"],
                    inputs["years"],
                )
                try:
                    reframe = generate_reframe(name, inputs, results)
                except Exception:
                    reframe = ("Your work has evolved but your pricing hasn't caught up yet. "
                               "Every month at current rates is another month pricing from an older version of yourself. "
                               "The leader you've already become deserves an income that reflects it.")

                results["reframe"] = reframe
                st.session_state.results = results
                save_lead(email, name, inputs, results)
            st.session_state.step = "results"
            st.rerun()

# ── STEP 3: Results ───────────────────────────────────────────────────────────
elif st.session_state.step == "results":
    r = st.session_state.results
    name = st.session_state.get("name", "")
    inputs = st.session_state.inputs

    # Friendly label for the volume metric shown in cards
    if inputs["charge_type"] == "Monthly Retainer":
        volume_unit = "clients"
        retention_noun = "clients"
        unit_singular = "client"
    else:
        volume_unit = "projects/month"
        retention_noun = "projects per month"
        unit_singular = "project"

    st.markdown(f"### {name}, here's your estimated pricing gap.")
    st.markdown('<p style="color:#7a5c9a;font-size:0.9rem;margin-top:-0.5rem;">Based on market benchmarks for service businesses at your stage. These are directional estimates. Bukie will give you the real number on a call.</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Card 1 — Monthly leak
    st.markdown(f"""
    <div class="result-card">
      <div class="label">Estimated Monthly Pricing Gap</div>
      <div class="number">{fmt_gbp(r['monthly_leak'])}<span style="font-size:1rem;font-weight:400;color:#7a5c9a"> / month</span></div>
      <div class="insight">
        You've been in business {inputs['years']} and you're earning {fmt_gbp(r['monthly_current'])}/month.
        Based on where service businesses at your stage typically sit in the market, a {r['uplift_pct']}% uplift puts
        your estimated fair rate at {fmt_gbp(r['monthly_current'] + r['monthly_leak'])}/month.
        That's <strong style="color:#721496">{fmt_gbp(r['monthly_leak'])} a month</strong> sitting on the table.
        Your actual gap may be higher or lower depending on your market and positioning. That's what the call is for.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Card 2 — Retention risk
    can_lose_pct = round(r['clients_can_lose'] / inputs['volume'] * 100) if r['clients_can_lose'] > 0 else 0
    st.markdown(f"""
    <div class="result-card">
      <div class="label">The Retention Risk Reality</div>
      <div class="number">{r['clients_can_lose']}<span style="font-size:1rem;font-weight:400;color:#7a5c9a"> {volume_unit} to spare</span></div>
      <div class="insight">
        Here's the maths. You currently have <strong style="color:#721496">{inputs['volume']} {retention_noun}</strong> at
        {fmt_gbp(inputs['current_rate'])}/{unit_singular}, earning {fmt_gbp(r['monthly_current'])}/month.
        At a fair rate of <strong style="color:#721496">{fmt_gbp(r['rate_raised'])}/{unit_singular}</strong>,
        you'd only need <strong style="color:#721496">{r['units_needed']} {retention_noun}</strong> to earn the same amount.
        {"That means you could lose " + str(r['clients_can_lose']) + " " + retention_noun + " (" + str(can_lose_pct) + "% of your current volume) and still break even." if can_lose_pct > 0 else "At that rate, you would need to keep all your current volume to break even."}
        The fear of losing clients almost always outweighs the actual risk.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Card 3 — 3-year projection
    st.markdown(f"""
    <div class="result-card">
      <div class="label">3-Year Projection at Current Pricing</div>
      <div class="number">{fmt_gbp(r['three_year_leak'])}</div>
      <div class="insight">
        If the gap is real and nothing changes, that's an estimated {fmt_gbp(r['three_year_leak'])} left on the table
        over the next three years. Not because your clients won't pay more.
        Because you haven't asked them to.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # AI reframe
    st.markdown(f"_{r['reframe']}_")

    st.markdown("---")

    # CTA
    st.markdown(f"""
    <div class="cta-box">
      <h3>You've just seen your number.</h3>
      <p>Now the question is what you do with it. Bukie works with established founders to raise prices 30 to 50% without losing clients or starting from scratch. Most close the gap within 8 weeks.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("Book a call with Bukie →", BOOKING_LINK, use_container_width=True)

    st.markdown("---")
    st.caption("Bukie Signature Consulting Ltd · bukiesignature.com · inquiry@bukiesignature.com")

    if st.button("← Recalculate", use_container_width=False):
        for k in ["step", "results", "inputs", "name", "email"]:
            st.session_state.pop(k, None)
        st.rerun()
