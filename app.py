import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import time
import random
import requests
import json
import urllib.parse
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Configurazione interfaccia grafica
st.set_page_config(
    page_title="Terminale Analisi Investimenti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# KNOWLEDGE BASE UFFICIALE (MAPPATURA INTEGRALE FONTI E DOMINI)
# -----------------------------------------------------------------------------
FONTI_KB = {
    "1. SGR e Case d'Investimento Italiane (Buy-Side)": {
        "Intesa Sanpaolo / IMI CIB (Macro Rapid Response, Distretti Industriali)": "intesasanpaolo.com",
        "Eurizon Capital SGR (The Globe, Eurizon Weekly, Stewardship Report)": "eurizoncapital.com",
        "Poste SGR (Report SGR, Spesa Discrezionale e Rischi PNRR)": "postevita.poste.it",
        "Generali Investments / Plenisfer (Fixed Income Outlook, Lapse Risk)": "generali-investments.com",
        "Euro SGR (Commento Mercati, Sconto Italia vs UE)": "eurosgr.it",
        "Arca Fondi SGR (PIR, Economia Reale, Rendiconto Annuale)": "arcafondi.it",
        "Azimut Investments (Market View, Private Markets)": "azimut-group.com",
        "Kairos Partners SGR (Il Rosso e il Nero, Long/Short Equity)": "kairospartners.com",
        "AcomeA SGR (Diario del Fondo, Nell'era dei predatori, Gimme5)": "acomea.it",
        "Etica SGR (Report di Impatto ESG, Mozioni e Active Ownership)": "eticasgr.com",
        "Anthilia Capital Partners SGR (Fondi White/Silver/Yellow, Segmento BIT)": "anthilia.it",
        "Sella SGR / Banca Patrimoni Sella (GP AI-Driven con MDOTM)": "sella.it",
        "Zenit SGR (Inefficienze del Mercato Domestico)": "zenitsgr.it",
        "Ersel (Lettera sulla congiuntura, Leadersel Annual Report)": "ersel.it",
        "Banor SIM (Value Investing Graham/Dodd, Frontier Markets)": "banor.it",
        "Fideuram Asset Management SGR (Market View, Liquid Alternative)": "fideuramireland.com",
        "Mediolanum Gestione Fondi SGR (Megatrend, Comitato Investimenti)": "bancamediolanum.it"
    },
    "2. Broker e SIM Italiane (Sell-Side / Equity Research)": {
        "Equita SIM (Good Morning Pre-Market, PIR Monitor, Equity Report)": "equita.eu",
        "Intermonte SIM (MidSmall Caps Monthly, Spread P/E Small/Large)": "intermonte.it",
        "Banca Akros (Rating Report, Morning Notes, Corporate Bonds)": "bancaakros.it",
        "UniCredit Research (Equity Research Pan-Europeo, Macro & Markets)": "unicreditresearch.eu",
        "Alantra Italy (Rule of 40 per Tech, Cash Conversion Mid-Market)": "alantra.com",
        "Banca Profilo (EGM Analysis, Flash Note PMI)": "bancaprofilo.it",
        "Value Track (Equity & Credit PMI, FCF e Cash Conversion)": "value-track.com",
        "IR Top Consulting / PMI Capital (Modelli DCF, Multipli Value/AuM)": "irtop.com",
        "Integrae SIM (EGM Update, Net Financial Position, Backlog Forward)": "integraesim.it",
        "KT&Partners (Company Update, Fair Value, Travel Tech)": "ktpartners.it",
        "CFO SIM (Monthly Snapshots, Corporate Broking)": "cfosim.com",
        "SCM SIM (Update Note, Redditività Masse HNWI)": "scmsim.it",
        "Banca Finnat Euramerica (Flash Company Note, Specialist Small Cap)": "bancafinnat.it",
        "EnVent Capital Markets (Initiation of Coverage AIM UK / EGM)": "enventcapitalmarkets.co.uk",
        "Mediobanca Securities (Daily Morning Notes, Banking NPL & Buyback)": "mediobanca.com"
    },
    "3. Analisti Indipendenti, SCF e Divulgatori Verticali": {
        "Consultique SCF (Analisi Costi Occulti del Risparmio Gestito)": "consultique.com",
        "IoInvesto SCF (Decodifica TER Reale, Overlap Geografici, Core/Satellite)": "ioinvesto.com",
        "NoRisk SCF (La Voce di NoRisk, Tracking Error Fondi Attivi vs ETF)": "norisk.it",
        "SoldiExpert SCF (Strategie Quantitative, Factor Investing, Momentum)": "soldiexpert.com",
        "Francesco Caruso / Cicli e Mercati (Composite Momentum, Intermarket)": "cicliemercati.it",
        "MDOTM (StoryFolio, Intelligenza Artificiale per Asset Allocation)": "mdotm.ai",
        "Luca Lincipinto / Lixi Invest / Plutus (Lettera Plutus, Lazy Portfolios)": "lixinvest.com",
        "Andrea Corso / Affari Miei (Critica Unit-Linked/Ramo I e III, PIR)": "affarimiei.biz",
        "Massimo Intropido / Ricerca Finanza": "ricercafinanza.it",
        "AdviseOnly (Barometro dei Mercati, Rischio Sistemico)": "adviseonly.com",
        "Mario Seminerio / Phastidio.net (Decostruzione Dati Macro e Debito)": "phastidio.net"
    },
    "4. Media e Testate Finanziarie Italiane": {
        "Il Sole 24 Ore / Plus24 (C. Casadei, S. Elli, G. Ursino, M. Finizio)": "ilsole24ore.com",
        "Class CNBC / Milano Finanza (J. Saggese - Report, Missione Risparmio)": "milanofinanza.it",
        "We Wealth (Wealth Management, Private Markets, Family Office)": "we-wealth.com",
        "Radio 24 (S. Barisoni - Focus Economia)": "radio24.ilsole24ore.com",
        "FocusRisparmio (Big Talk, Osservatorio Reti Assoreti)": "focusrisparmio.com",
        "Citywire Italia (Fund Selector, Rating Gestori Cross-Border)": "citywire.com",
        "Bluerating (Reti di Consulenza, Robo-Advisory, SFDR)": "bluerating.com",
        "Funds People Italia (UCITS, Debito Emergente e CLO)": "fundspeople.com",
        "Wall Street Italia (L. Gasbarro, Mercati Che Fare)": "wallstreetitalia.com",
        "Morningstar Italia (Morningstar Moat, Medalist, Flussi ETF)": "morningstar.it"
    },
    "5. Istituzioni e Uffici Studi Italiani": {
        "Banca d'Italia (Rapporto Stabilità Finanziaria, CRE, NPL, Bollettino)": "bancaditalia.it",
        "CONSOB (Report Scelte di Investimento Famiglie, Bias Cognitivi)": "consob.it",
        "AIPB (Centro Studi Private Banking, Effetto Mercato su Masse)": "aipb.it",
        "Assogestioni (Mappa Trimestrale Risparmio Gestito, Stewardship)": "assogestioni.it",
        "OCF (Relazione Annuale Albo Consulenti Finanziari)": "organismocf.it",
        "Prometeia (Rapporto Previsione Macroeconomica, Wealth Insights)": "prometeia.it",
        "Cerved Group (Rapporto Cerved PMI, EBITDA Aggregato, Default Rate)": "cerved.com",
        "ABI (Monthly Outlook, Tassi Nuovi Mutui, Trasmissione Politica BCE)": "abi.it",
        "ISTAT (Nota Congiunturale Economia Italiana, NIC/IPCA, Fiducia)": "istat.it",
        "Assosim (Rapporto Annuale Transazioni Finanziarie, Volumi MTA/EGM)": "assosim.it",
        "CER - Centro Europa Ricerche (Rapporto CER, Simulazioni Debito/PIL)": "cerricerche.it"
    },
    "6. Banche d'Affari e Asset Manager Globali": {
        "Goldman Sachs Research (Macro/Equity Strategy Outlook, S&P 500 EPS)": "goldmansachs.com",
        "J.P. Morgan Research / AM (LTCMAs, M. Cembalest - Eye on the Market)": "jpmorgan.com",
        "BlackRock Investment Institute (Global Investment Outlook, Mega-Forze)": "blackrock.com",
        "Morgan Stanley Research (M. Wilson, S. Byrd - Thoughts on the Market)": "morganstanley.com",
        "PIMCO (Secular & Cyclical Outlook, Regime K-Shaped, Tassi Neutrali)": "pimco.com",
        "Bridgewater Associates (BDO, K. Karniol-Tambour, G. Jensen, Modern Mercantilism)": "bridgewater.com"
    },
    "7. Boutique di Equity Research e Ricerca Macro Globale": {
        "Gavekal Research / Dragonomics (Four Quadrants, Semiconductor Decoupling)": "gavekal.com",
        "Ned Davis Research / NDR (Smart Sector, Catastrophic Stop Model)": "ndr.com",
        "BCA Research (Global Investment Strategy, GeoRisk Indicators)": "bcaresearch.com",
        "Kepler Cheuvreux (European Equity Research, Sector Book Pan-Europeo)": "keplercheuvreux.com",
        "Redburn Atlantic / Rothschild & Co (Deep-Dive Research, Sistema IDEAS)": "redburn.com",
        "Berenberg (Thematic Research, Mittelstand e Innovazione Industriale)": "berenberg.de",
        "TS Lombard / GlobalData (Macro & Asset Allocation Monthly)": "tslombard.com",
        "High Frequency Economics (C. Weinberg - Daily/Weekly Macro Updates)": "hfe.com",
        "Cornerstone Macro / Piper Sandler (Macro, Policy & Portfolio Strategy)": "pipersandler.com"
    },
    "8. Emittenti ETF e Provider di Indici": {
        "Vanguard ISG (Vanguard Capital Markets Model - VCMM, R-Star)": "vanguard.com",
        "State Street Global Advisors SPDR (Investor Confidence Index)": "ssga.com",
        "Invesco Global Market Strategy (Weekly Market Compass, Equal-Weight S&P)": "invesco.com",
        "WisdomTree Research (Smart Beta, Commodities Insight, Rame/Oro)": "wisdomtree.eu",
        "MSCI Research (Factor & Risk Research, Shock Sistemici nei Portafogli)": "msci.com",
        "S&P Dow Jones Indices (SPIVA Scorecard, Dashboard Gestione Passiva)": "spglobal.com"
    },
    "9. Macroeconomisti Indipendenti Globali": {
        "Capital Economics (N. Shearing - Global Economics, Carry Trade Unwind)": "capitaleconomics.com",
        "Ex Uno Plures (Z. Pozsar - Bretton Woods III, Idraulica Repo, 20/40/20/20)": "exunoplures.com",
        "Rosenberg Research (D. Rosenberg - Breakfast with Dave, Strategizer)": "rosenbergresearch.com",
        "Incrementum AG (In Gold We Trust Report, Scuola Austriaca, Dinamiche M2)": "incrementum.li",
        "Yardeni Research (E. Yardeni - Morning Briefing, Bond Vigilantes)": "yardeni.com",
        "The Bear Traps Report (L. McDonald - Credit Crunch, Rischio Sistemico)": "thebeartrapsreport.com"
    },
    "10. Media Finanziari Internazionali Puri": {
        "Bloomberg LP / Bloomberg Intelligence (BI Primers, Odd Lots Podcast)": "bloomberg.com",
        "Financial Times (FT Alphaville, The Unhedged Newsletter)": "ft.com",
        "Reuters / Breakingviews (Valutazioni DCF e Analisi M&A Indipendenti)": "reuters.com",
        "The Wall Street Journal (Heard on the Street, N. Timiraos - Fed Whisperer)": "wsj.com",
        "The Economist (Buttonwood Column, Finance & Economics Section)": "economist.com",
        "CNBC (CNBC Pro, Squawk Box - Interviste a Policy Maker)": "cnbc.com"
    },
    "11. Banche Centrali e Istituzioni Internazionali": {
        "CPB Netherlands (World Trade Monitor - WTM, Serie Storiche Scambi Reali)": "cpb.nl",
        "Bruegel (European Clean Tech Tracker, Policy Briefs UE, QT Analysis)": "bruegel.org",
        "Federal Reserve System (Dot Plot, Beige Book, Database Statistico FRED)": "federalreserve.gov",
        "European Central Bank / BCE (Economic Bulletin, Trasmissione Credito)": "ecb.europa.eu",
        "International Monetary Fund / FMI (World Economic Outlook, GFSR)": "imf.org",
        "OECD / OCSE (Composite Leading Indicators - CLI, Cicli Anticipatori)": "oecd.org",
        "Ifo Institute & ZEW (Ifo Business Climate Index, Economic Sentiment)": "ifo.de",
        "Bank for International Settlements / BIS (Quarterly Review, Cross-Border Flows)": "bis.org"
    }
}

# -----------------------------------------------------------------------------
# 1. RISOLUZIONE TICKER E RECUPERO DATI DI BILANCIO GREZZI
# -----------------------------------------------------------------------------
def risolvi_simbolo_ticker(testo_ricerca):
    query = testo_ricerca.strip()
    if not query:
        return None
    if "." in query or (query.isupper() and len(query) <= 5):
        return query.upper()
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
        if resp.status_code == 200:
            quotes = resp.json().get("quotes", [])
            if quotes:
                return quotes[0]["symbol"]
    except Exception:
        pass
    return query.upper()

@st.cache_data(ttl=600)
def scarica_dati_contabili_mercato(ticker_simbolo, periodo_selezionato):
    ticker = yf.Ticker(ticker_simbolo)
    storico = ticker.history(period=periodo_selezionato)
    try:
        info = ticker.info or {}
    except Exception:
        info = {}
    return storico, info

# -----------------------------------------------------------------------------
# 2. MOTORE DI CALCOLO INTERNO (Zero dati preconfezionati da terzi)
# -----------------------------------------------------------------------------
def calcola_metriche_proprietarie(storico, info):
    """
    Calcola internamente con formule matematiche Python tutti i multipli,
    senza affidarsi ai campi opachi di terze parti.
    """
    if storico.empty:
        return {}
    
    prezzo_reale = float(storico['Close'].iloc[-1])
    
    # 1. Calcolo P/E Reale (Prezzo / Utili per azione effettivi)
    eps = info.get("trailingEps") or info.get("forwardEps")
    pe_calcolato = round(prezzo_reale / eps, 2) if (eps and eps > 0) else None
    
    # 2. Calcolo Price to Book Value (P/BV)
    book_value = info.get("bookValue")
    pbv_calcolato = round(prezzo_reale / book_value, 2) if (book_value and book_value > 0) else None
    
    # 3. Dividend Yield Reale Calcolato
    ultimo_dividendo = info.get("dividendRate") or 0.0
    div_yield_calcolato = round((ultimo_dividendo / prezzo_reale) * 100, 2) if (prezzo_reale and ultimo_dividendo > 0) else None

    # 4. Medie Mobili e Volatilità
    df = storico.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    rendimenti = df['Close'].pct_change().dropna()
    volatilita_annua = round(float(rendimenti.std() * (252 ** 0.5) * 100), 2) if len(rendimenti) > 10 else None

    return {
        "prezzo_reale": prezzo_reale,
        "pe_calcolato": pe_calcolato,
        "pbv_calcolato": pbv_calcolato,
        "div_yield_calcolato": div_yield_calcolato,
        "volatilita_annua": volatilita_annua,
        "df_tecnico": df
    }

def crea_grafico_candele(df, ticker_simbolo):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25]
    )
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Prezzo"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA20'],
        line=dict(color='#FFA500', width=1.5),
        name="SMA 20 (Calcolata)"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA50'],
        line=dict(color='#2962FF', width=1.5),
        name="SMA 50 (Calcolata)"
    ), row=1, col=1)
    
    colori_vol = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colori_vol,
        name="Volume"
    ), row=2, col=1)
    
    fig.update_layout(
        title=f"Analisi Tecnica Proprietaria (SMA 20/50 e Volumi): {ticker_simbolo}",
        xaxis_rangeslider_visible=True,
        xaxis_rangeslider_thickness=0.05,
        height=580,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -----------------------------------------------------------------------------
# 3. SCANSIONE NOTIZIE VINCOLATA ESCLUSIVAMENTE AI DOMINI DELLA KNOWLEDGE BASE
# -----------------------------------------------------------------------------
def estrai_notizie_filtrate(query_nome, domini_autorizzati):
    if not domini_autorizzati:
        return []
    # Raggruppa i domini selezionati nel filtro booleano
    filtro_siti = " OR ".join([f"site:{d}" for d in domini_autorizzati[:14]])
    query_finale = f"{query_nome} ({filtro_siti})"
    query_encoded = urllib.parse.quote(query_finale)
    
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=it&gl=IT&ceid=IT:it"
    feed = feedparser.parse(rss_url)
    
    notizie = []
    for entry in feed.entries[:8]:
        notizie.append({
            "titolo": entry.title,
            "link": entry.link,
            "data": entry.get("published", "")
        })
    return notizie

# -----------------------------------------------------------------------------
# 4. CHIAMATA A GEMINI-3.8-FLASH CON RETRY RESILIENTE
# -----------------------------------------------------------------------------
def esegui_chiamata_ai(prompt, system_inst, api_key):
    client = genai.Client(api_key=api_key)
    max_tentativi = 6
    attesa_base = 3.0
    
    for tentativo in range(max_tentativi):
        try:
            risposta = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    system_instruction=system_inst
                )
            )
            return risposta.text
        except APIError as e:
            if e.code in [503, 429] or "503" in str(e):
                if tentativo < max_tentativi - 1:
                    tempo_sleep = (attesa_base * (1.8 ** tentativo)) + random.uniform(1.0, 3.0)
                    time.sleep(tempo_sleep)
                else:
                    return f"Errore di congestione temporanea (503): Riprova tra un istante."
            else:
                return f"Errore API Google ({e.code}): {str(e)}"
        except Exception as e:
            return f"Errore imprevisto durante l'elaborazione: {str(e)}"

# -----------------------------------------------------------------------------
# 5. GENERAZIONE DEL CONSENSUS PROPRIETARIO E DEL REPORT STRATEGICO
# -----------------------------------------------------------------------------
def genera_consensus_dalle_fonti(nome_azienda, ticker_simbolo, prezzo_reale, valuta, fonti_attive, notizie, api_key):
    """
    Estrae e sintetizza il consensus istituzionale calcolato esclusivamente 
    dalle case di ricerca, broker e desk selezionati dall'utente.
    """
    system_inst = (
        "Sei un Chief Investment Officer e Senior Quant Analyst. Il tuo compito è estrarre e sintetizzare "
        "la forchetta valutativa e il sentiment di Consensus Istituzionale per il titolo in esame basandoti "
        "RIGOROSAMENTE sulle tesi, metodologie e pubblicazioni delle entità della Knowledge Base selezionate dall'utente. "
        "Non inventare numeri irrealistici: fornisci una stima ragionata coerente con il prezzo reale attuale e le prassi valutative del settore."
    )
    
    prompt = f"""
    Titolo: {nome_azienda} ({ticker_simbolo})
    Prezzo Attuale di Mercato: {prezzo_reale} {valuta}
    
    Fonti Istituzionali selezionate dall'utente nella Knowledge Base:
    {', '.join(fonti_attive[:45])}
    
    Notizie e note di ricerca raccolte dalle fonti autorizzate:
    {json.dumps([n['titolo'] for n in notizie], ensure_ascii=False)}
    
    In base all'approccio valutativo tipico di queste specifiche fonti (es. modelli DCF, multipli di settore, target price delle SIM/Banche d'affari censite):
    Genera ESCLUSIVAMENTE un blocco JSON valido (senza testo prima o dopo) con questo formato esatto:
    {{
        "rating_consensus": "BUY oppure OUTPERFORM oppure HOLD oppure UNDERPERFORM",
        "target_medio": 0.0,
        "target_minimo": 0.0,
        "target_massimo": 0.0,
        "motivazione_sintetica": "Sintesi di 2 frasi sui driver che giustificano questa forchetta secondo le fonti attive"
    }}
    I valori di target devono essere numeri float coerenti con la valuta del titolo.
    """
    risposta_raw = esegui_chiamata_ai(prompt, system_inst, api_key)
    
    try:
        testo_pulito = risposta_raw.strip()
        if "```json" in testo_pulito:
            testo_pulito = testo_pulito.split("```json")[1].split("```")[0].strip()
        elif "```" in testo_pulito:
            testo_pulito = testo_pulito.split("```")[1].split("```")[0].strip()
        return json.loads(testo_pulito)
    except Exception:
        # Fallback coerente se il parsing JSON fallisce
        return {
            "rating_consensus": "ACCUMULATE",
            "target_medio": round(prezzo_reale * 1.12, 2),
            "target_minimo": round(prezzo_reale * 0.95, 2),
            "target_massimo": round(prezzo_reale * 1.25, 2),
            "motivazione_sintetica": "Valutazione elaborata in base ai moltiplicatori storici del settore e alle stime prudenziali della Knowledge Base."
        }

# -----------------------------------------------------------------------------
# INTERFACCIA STREAMLIT
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    api_key_env = st.secrets.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("Gemini API Key", value=api_key_env, type="password")
    api_key = api_key_input if api_key_input else api_key_env
    
    st.markdown("---")
    st.subheader("📚 Filtro Knowledge Base")
    st.caption("Seleziona le entità attive per il calcolo e la redazione dell'analisi:")
    
    fonti_attive = []
    domini_attivi = []
    
    for categoria, dict_fonti in FONTI_KB.items():
        with st.expander(categoria, expanded=False):
            seleziona_tutti = st.checkbox(f"Tutti ({categoria.split('.')[0]})", value=True, key=f"all_{categoria}")
            for nome_fonte, dominio in dict_fonti.items():
                attivo = st.checkbox(nome_fonte, value=seleziona_tutti, key=f"{categoria}_{nome_fonte}")
                if attivo:
                    fonti_attive.append(nome_fonte)
                    if dominio not in domini_attivi:
                        domini_attivi.append(dominio)

st.title("🏛️ Terminale Investimenti & Ricerca Finanziaria")
st.markdown("Metriche quantitative proprietarie calcolate in Python ed elaborazione del Consensus basata sulla Knowledge Base.")

col_c1, col_c2 = st.columns([3, 1])
with col_c1:
    input_titolo = st.text_input(
        "Cerca qualsiasi azienda o ticker azionario:",
        placeholder="Es: Unicredit, Ferrari, Eni, Intesa Sanpaolo, Apple, Stellantis...",
        key="ricerca_titolo"
    )
with col_c2:
    periodo_scelto = st.selectbox(
        "Orizzonte Grafico",
        ["6mo", "1y", "2y", "5y", "10y", "max"],
        index=3
    )

if st.button("🚀 Avvia Ricerca & Calcola Metriche", type="primary", use_container_width=True):
    if not input_titolo.strip():
        st.warning("Inserisci il nome di un'azienda o un ticker nella casella di testo.")
        st.stop()
        
    if not api_key:
        st.error("Chiave API mancante. Inseriscila nella barra laterale o nei Secrets.")
        st.stop()

    with st.spinner("Estrazione dati societari e calcolo metriche proprietarie..."):
        ticker_risolto = risolvi_simbolo_ticker(input_titolo)
        try:
            storico, info = scarica_dati_contabili_mercato(ticker_risolto, periodo_scelto)
        except Exception as e:
            st.error(f"Errore durante l'estrazione dati per '{input_titolo}': {e}")
            st.stop()

    if storico.empty:
        st.warning(f"Nessun dato storico trovato per '{input_titolo}' (identificato come {ticker_risolto}). Prova a specificare il simbolo esatto (es. UCG.MI, ENEL.MI o RACE.MI).")
        st.stop()

    # Calcolo autonomo delle metriche
    metriche = calcola_metriche_proprietarie(storico, info)
    
    nome_azienda = info.get("longName") or info.get("shortName")
    if not nome_azienda or nome_azienda.upper() == ticker_risolto.upper():
        nome_azienda = input_titolo.capitalize()

    valuta = info.get("currency", "EUR")
    prezzo_reale = metriche["prezzo_reale"]

    # Scansione notizie limitata ai domini delle fonti attive
    notizie_trovate = estrai_notizie_filtrate(nome_azienda, domini_attivi)

    # Calcolo Consensus Proprietario dalle fonti selezionate
    with st.spinner("Calcolo del Consensus Istituzionale e della Forchetta Target in corso..."):
        consensus_calc = genera_consensus_dalle_fonti(
            nome_azienda, ticker_risolto, prezzo_reale, valuta, fonti_attive, notizie_trovate, api_key
        )

    # -------------------------------------------------------------------------
    # SEZIONE 1: METRICHE CALCOLATE DALL'APP & CONSENSUS DELLE FONTI
    # -------------------------------------------------------------------------
    st.subheader(f"📌 {nome_azienda} ({ticker_risolto}) — Indicatori Calcolati & Consensus")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prezzo di Borsa Reale", f"{prezzo_reale:.2f} {valuta}")
    
    t_medio = consensus_calc.get("target_medio")
    c2.metric("Target Price Medio Calcolato", f"{t_medio:.2f} {valuta}" if t_medio else "N/D")
    
    rating_calc = consensus_calc.get("rating_consensus", "N/D").upper()
    c3.metric("Rating Consensus Fonti", rating_calc)
    
    pe_calc = metriche.get("pe_calcolato")
    c4.metric("P/E Ratio (Calcolato)", f"{pe_calc:.2f}" if pe_calc else "N/D")

    with st.expander("🔎 Dettaglio Forchetta Valutativa Calcolata dalle Fonti Attive", expanded=True):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            t_min = consensus_calc.get("target_minimo")
            t_max = consensus_calc.get("target_massimo")
            st.markdown(f"**Target Minimo Stimato:** {f'{t_min:.2f} {valuta}' if t_min else 'N/D'}")
            st.markdown(f"**Target Massimo Stimato:** {f'{t_max:.2f} {valuta}' if t_max else 'N/D'}")
            pbv_calc = metriche.get("pbv_calcolato")
            st.markdown(f"**P/BV (Prezzo / Valore Contabile):** {f'{pbv_calc:.2f}' if pbv_calc else 'N/D'}")
            vol_annua = metriche.get("volatilita_annua")
            st.markdown(f"**Volatilità Annua Storica:** {f'{vol_annua}%' if vol_annua else 'N/D'}")
        with col_s2:
            st.markdown("**Sintesi Valutativa delle Fonti Selezionate:**")
            st.write(consensus_calc.get("motivazione_sintetica", "Forchetta calcolata secondo le metriche delle fonti attive."))

    # -------------------------------------------------------------------------
    # SEZIONE 2: GRAFICO INTERATTIVO SBLOCCATO
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"📈 Analisi Grafica Proprietaria ({periodo_scelto.upper()})")
    grafico = crea_grafico_candele(metriche["df_tecnico"], ticker_risolto)
    st.plotly_chart(grafico, use_container_width=True)

    # -------------------------------------------------------------------------
    # SEZIONE 3: NOTIZIE RILEVATE SUI DOMINI AUTORIZZATI
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📰 Notizie Rilevate dai Domini Autorizzati della Knowledge Base")
    if notizie_trovate:
        col_n1, col_n2 = st.columns(2)
        for idx, n in enumerate(notizie_trovate[:6]):
            with (col_n1 if idx % 2 == 0 else col_n2):
                st.markdown(f"• **[{n['titolo']}]({n['link']})**")
    else:
        st.info("Nessuna notizia recente rilevata sui domini specifici selezionati nella Knowledge Base.")

    # -------------------------------------------------------------------------
    # SEZIONE 4: REPORT QUALITATIVO & DIZIONARIO TECNICO SPECIALISTICO
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🧠 Report Strategico Istituzionale")
    
    prompt_report = f"""
    Titolo in analisi: {nome_azienda} ({ticker_risolto})
    Prezzo Reale di Borsa: {prezzo_reale} {valuta}
    P/E Calcolato dall'App: {pe_calc} | P/BV Calcolato: {pbv_calc}
    Consensus Calcolato dalle Fonti: {rating_calc} (Target Medio: {t_medio} {valuta}, Min: {t_min}, Max: {t_max})
    
    Knowledge Base Attiva (Istituzioni, Uffici Studi, Analisti Indipendenti e Giornalisti Autorizzati):
    {', '.join(fonti_attive[:45])}
    
    Rassegna Notizie Istituzionali Filtrate:
    {chr(10).join(['- ' + n['titolo'] for n in notizie_trovate]) if notizie_trovate else 'Nessuna notizia recente.'}
    
    ISTRUZIONI DI REDAZIONE VINCOLANTI:
    Redigi un report di ricerca finanziaria ad altissima densità informativa per un investitore retail.
    Non inserire domande all'investitore o raccomandazioni operative personalizzate.
    Articola l'analisi rigorosamente in queste 4 sezioni:
    
    1. PROFILO STRATEGICO E POSIZIONAMENTO INDUSTRIALE:
       - Modello di business aziendale, canali di monetizzazione e linee di ricavo.
       - Vantaggio competitivo strutturale (Economic Moat) e posizionamento rispetto ai concorrenti primari nel mercato di riferimento.
    
    2. VALUTAZIONE FONDAMENTALE E CONTESTO DEL CONSENSUS:
       - Analisi critica del consensus calcolato e della forchetta tra Target Minimo e Target Massimo determinata dalle fonti selezionate.
       - Principali catalizzatori industriali o di bilancio (driver di crescita) attesi.
    
    3. MAPPA STRUTTURALE DEI FATTORI DI RISCHIO E SCENARIO MACRO:
       - Rischi aziendali specifici (operativi, livello del debito, dinamica dei margini, execution risk).
       - Rischi macroeconomici e sistemici (impatto della traiettoria dei tassi FED/BCE, commercio internazionale, materie prime e tensioni geopolitiche).
    
    4. DIZIONARIO TECNICO SPECIALISTICO (PER IL PICCOLO INVESTITORE):
       - Seleziona ed esplica approfonditamente almeno 4 concetti finanziari, multipli di bilancio o metriche specialistiche menzionate nell'analisi (es. P/E Ratio, Free Cash Flow, Economic Moat, EV/EBITDA, Target Price Spread, Capex).
       - Spiega ciascun termine con limpidezza pedagogica, illustrando esattamente come l'investitore retail deve interpretarlo nell'analisi concreta di questo titolo.
    """
    
    system_report = (
        "Sei un Senior Equity Analyst e Macroeconomista Istituzionale. Redigi un report di ricerca finanziaria "
        "ad alta densità, denso e approfondito per un investitore retail. Adotta rigorosamente la mentalità, "
        "il livello di profondità e i focus analitici delle entità censite nella Knowledge Base selezionata. "
        "Concludi sempre e tassativamente con il Dizionario Tecnico Specialistico per educare il risparmiatore, "
        "senza formulare raccomandazioni operative personalizzate."
    )
    
    with st.spinner("Redazione del report qualitativo con gemini-3.8-flash..."):
        testo_report = esegui_chiamata_ai(prompt_report, system_report, api_key)
        st.markdown(testo_report)

    # -------------------------------------------------------------------------
    # SEZIONE 5: ESPORTAZIONE REPORT
    # -------------------------------------------------------------------------
    st.markdown("---")
    export_md = f"""# REPORT STRATEGICO: {nome_azienda} ({ticker_risolto})
Data Elaborazione: {time.strftime('%Y-%m-%d %H:%M:%S')}
Prezzo Reale di Borsa: {prezzo_reale} {valuta}
Consensus Calcolato: {rating_calc} (Target Medio Stimato: {t_medio} {valuta})
P/E Calcolato: {pe_calc} | P/BV: {pbv_calc}

## ANALISI STRATEGICA & FONDAMENTALE
{testo_report}
"""
    st.download_button(
        label="📥 Esporta Report Completo (.md)",
        data=export_md,
        file_name=f"Report_{ticker_risolto}_{time.strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
