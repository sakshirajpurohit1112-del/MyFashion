"""
Fashion IQ Boat — Your Personal Fashion Intelligence Platform
Single-file Streamlit application.

Run:
    pip install -r requirements.txt   (or see the package list in the README block below)
    streamlit run app.py

Environment variables (optional — the app works fully without them):
    OPENAI_API_KEY=
"""

import os
import io
import math
import random
import colorsys
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================
# 0. CONFIG / SECRETS (never hard-code real keys)
# ============================================================

def get_secret(name: str, default: str = "") -> str:
    """Fetch a secret from Streamlit secrets first, then env vars, never crash."""
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets.get(name, default)
    except Exception:
        pass
    return os.getenv(name, default)


OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")
AI_ENABLED = bool(OPENAI_API_KEY)


def mask_key(key: str) -> str:
    if not key:
        return "Not configured"
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:4]}••••••••{key[-4:]}"


# ============================================================
# 1. PAGE SETUP + CSS
# ============================================================

def setup_page():
    st.set_page_config(
        page_title="Fashion IQ Boat",
        page_icon="👗",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def load_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        :root {
            --white: #ffffff;
            --pink-pale: #ffeaf3;
            --pink-light: #ffc2dd;
            --pink: #ff3d94;
            --pink-deep: #d6006e;
            --text: #d6006e;
        }

        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #fff0f7 100%);
            color: var(--pink-deep);
        }

        /* Make every bit of default text bold and pink/white so it "highlights" */
        .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp .stMarkdown, .stApp .stCaption, .stApp .stTextInput label,
        .stApp .stSelectbox label, .stApp .stSlider label, .stApp .stRadio label {
            color: var(--pink-deep) !important;
            font-weight: 600;
        }
        .stApp h1, .stApp h2, .stApp h3 {
            color: var(--pink) !important;
            font-weight: 700;
        }

        section[data-testid="stSidebar"] {
            background: var(--white);
            border-right: 2px solid var(--pink-light);
        }
        section[data-testid="stSidebar"] * { color: var(--pink-deep) !important; }

        .fiq-hero {
            padding: 56px 40px;
            border-radius: 20px;
            background: linear-gradient(135deg, var(--pink) 0%, var(--pink-deep) 100%);
            border: 1px solid var(--pink-light);
            margin-bottom: 28px;
            animation: fadeIn 0.6s ease;
        }
        .fiq-hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: 2.6rem;
            margin-bottom: 4px;
            color: var(--white) !important;
            -webkit-text-fill-color: var(--white);
        }
        .fiq-hero p { color: var(--pink-pale) !important; font-size: 1.05rem; font-weight: 600; }

        .fiq-card {
            background: var(--white);
            backdrop-filter: blur(10px);
            border: 1.5px solid var(--pink-light);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .fiq-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(255,61,148,0.25);
            border-color: var(--pink);
        }
        .fiq-card * { color: var(--pink-deep) !important; }

        .fiq-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            background: var(--pink);
            color: var(--white) !important;
            border: 1px solid var(--pink-deep);
            margin-right: 6px;
        }

        .fiq-swatch {
            display: inline-block;
            width: 22px; height: 22px;
            border-radius: 6px;
            margin-right: 6px;
            border: 1px solid var(--pink-light);
            vertical-align: middle;
        }

        .fiq-kpi {
            text-align: center;
            padding: 18px;
            border-radius: 14px;
            background: var(--pink-pale);
            border: 1.5px solid var(--pink-light);
        }
        .fiq-kpi .val { font-size: 1.8rem; font-weight: 700; color: var(--pink) !important; }
        .fiq-kpi .lbl { font-size: 0.8rem; color: var(--pink-deep) !important; opacity: 0.9; font-weight: 600; }

        .stButton>button {
            background: linear-gradient(90deg, var(--pink), var(--pink-deep));
            color: var(--white) !important;
            border: none;
            border-radius: 10px;
            padding: 0.55em 1.4em;
            font-weight: 700;
            transition: filter 0.2s ease;
        }
        .stButton>button:hover { filter: brightness(1.1); }
        .stButton>button * { color: var(--white) !important; }

        @keyframes fadeIn { from {opacity:0; transform: translateY(8px);} to {opacity:1; transform: translateY(0);} }
        .fiq-fade { animation: fadeIn 0.5s ease; }

        .fiq-empty {
            text-align: center; padding: 40px; opacity: 0.85;
            border: 1.5px dashed var(--pink-light); border-radius: 14px;
            background: var(--pink-pale);
            color: var(--pink-deep) !important;
            font-weight: 600;
        }

        /* Inputs, sliders, dataframes, tabs — keep the pink/white theme consistent */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            background: var(--white) !important;
            border: 1.5px solid var(--pink-light) !important;
            color: var(--pink-deep) !important;
        }
        .stSlider [data-baseweb="slider"] div { background: var(--pink) !important; }
        .stProgress > div > div { background: linear-gradient(90deg, var(--pink-light), var(--pink)) !important; }
        .stAlert, .stAlert * { color: var(--pink-deep) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 2. DEMO DATA
# ============================================================

STYLE_PERSONALITIES = [
    "Minimalist", "Streetwear", "Classic", "Luxury", "Casual",
    "Athleisure", "Boho", "Smart Casual", "Y2K", "Old Money", "Indo-Western",
]

GENDERS = ["Women", "Men", "Unisex"]
OCCASIONS = ["Everyday", "Work", "Date Night", "Wedding", "Festival", "Travel", "Party", "Interview"]
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
COLORS = ["Black", "White", "Beige", "Navy", "Burgundy", "Olive", "Camel", "Pastel Pink", "Emerald", "Charcoal"]
BRANDS = ["Studio Noir", "Aara & Co", "Northline", "Velvet Room", "Ember Label", "Common Thread", "Maison Loop"]


@st.cache_data
def load_demo_data():
    random.seed(42)
    categories = ["Dress", "Blazer", "Denim", "Knitwear", "Outerwear", "Footwear", "Accessory", "Tailored Pant"]
    rows = []
    for i in range(40):
        rows.append({
            "id": i,
            "name": f"{random.choice(['Draped', 'Tailored', 'Relaxed', 'Structured', 'Fluid'])} "
                    f"{random.choice(categories)}",
            "brand": random.choice(BRANDS),
            "category": random.choice(categories),
            "color": random.choice(COLORS),
            "price": round(random.uniform(25, 320), 2),
            "rating": round(random.uniform(3.4, 5.0), 1),
            "style": random.choice(STYLE_PERSONALITIES),
        })
    products = pd.DataFrame(rows)

    trends = pd.DataFrame({
        "trend": ["Old Money Tailoring", "Boho Layering", "Y2K Revival", "Quiet Luxury", "Utility Streetwear",
                   "Coastal Grandma", "Sheer Layers", "Chunky Knits"],
        "growth_pct": [34, 12, 28, 41, 19, 9, 22, 15],
        "category": ["Formal", "Boho", "Streetwear", "Minimalist", "Streetwear", "Casual", "Evening", "Casual"],
    })

    color_trend = pd.DataFrame({
        "color": ["Burgundy", "Camel", "Sage Green", "Charcoal", "Butter Yellow", "Ivory"],
        "popularity": [78, 65, 60, 82, 44, 70],
    })

    seasonality = pd.DataFrame({
        "season": SEASONS,
        "Formal": [40, 55, 60, 70],
        "Streetwear": [65, 70, 50, 40],
        "Boho": [70, 80, 45, 20],
        "Minimalist": [55, 50, 65, 75],
    })

    return {"products": products, "trends": trends, "colors": color_trend, "seasonality": seasonality}


# ============================================================
# 3. SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "page": "Dashboard",
        "profile": {
            "style": "Minimalist", "colors": [], "brands": [], "budget": 150,
            "occasions": [], "personality": "Minimalist",
        },
        "generated_outfits": [],
        "favorites": [],
        "fashion_iq": {"color": 72, "occasion": 68, "trend": 80, "versatility": 66},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# 4. FQE — FASHION QUALITY EVALUATION
# ============================================================

def calculate_fqe(color_harmony, occasion_fit, style_consistency, trend_relevance, budget_fit, versatility):
    weights = {
        "color_harmony": 0.25, "occasion_fit": 0.20, "style_consistency": 0.20,
        "trend_relevance": 0.15, "budget_fit": 0.10, "versatility": 0.10,
    }
    values = {
        "color_harmony": color_harmony, "occasion_fit": occasion_fit, "style_consistency": style_consistency,
        "trend_relevance": trend_relevance, "budget_fit": budget_fit, "versatility": versatility,
    }
    score = sum(values[k] * weights[k] for k in weights)
    score = round(score, 1)

    if score >= 90:
        verdict = "Excellent Match"
    elif score >= 75:
        verdict = "Strong Match"
    elif score >= 60:
        verdict = "Good Match"
    else:
        verdict = "Needs Refinement"

    top_factor = max(values, key=values.get)
    explanation = (
        f"Strongest factor: **{top_factor.replace('_', ' ').title()}** ({values[top_factor]}/100). "
        f"Weighted FQE combines color harmony, occasion fit, style consistency, trend relevance, "
        f"budget fit and versatility."
    )
    return score, verdict, explanation, values


# ============================================================
# 5. RULE-BASED / AI OUTFIT GENERATION
# ============================================================

TOPS = {
    "Minimalist": ["Boxy cotton tee", "Structured white shirt", "Fine-knit turtleneck"],
    "Streetwear": ["Oversized graphic hoodie", "Cropped bomber", "Boxy tee"],
    "Classic": ["Crisp button-down", "Fitted blazer", "Cashmere sweater"],
    "Luxury": ["Silk blouse", "Tailored double-breasted jacket", "Cashmere wrap top"],
    "Casual": ["Relaxed tee", "Denim shirt", "Soft cardigan"],
    "Athleisure": ["Ribbed tank", "Zip-up track jacket", "Performance hoodie"],
    "Boho": ["Embroidered peasant blouse", "Flowy kimono", "Crochet top"],
    "Smart Casual": ["Knit polo", "Light chambray shirt", "Merino sweater"],
    "Y2K": ["Baby tee", "Low-rise cropped top", "Metallic halter"],
    "Old Money": ["Cable-knit sweater", "Oxford shirt", "Quilted vest"],
    "Indo-Western": ["Embellished kurta top", "Fusion jacket", "Bandhgala blouse"],
}
BOTTOMS = {
    "Minimalist": ["Tapered trousers", "Straight-leg denim", "Midi skirt"],
    "Streetwear": ["Cargo pants", "Wide-leg jeans", "Track pants"],
    "Classic": ["Tailored trousers", "Pencil skirt", "Wool pants"],
    "Luxury": ["Silk wide-leg pants", "Structured skirt", "Tailored trousers"],
    "Casual": ["Straight denim", "Chino shorts", "Relaxed joggers"],
    "Athleisure": ["Bike shorts", "Jogger pants", "Leggings"],
    "Boho": ["Maxi skirt", "Flared trousers", "Printed wide pants"],
    "Smart Casual": ["Chinos", "Dark denim", "Tailored shorts"],
    "Y2K": ["Low-rise jeans", "Cargo mini skirt", "Flared denim"],
    "Old Money": ["Pleated trousers", "Tweed skirt", "Chino pants"],
    "Indo-Western": ["Palazzo pants", "Dhoti pants", "Sharara"],
}
SHOES = {
    "Minimalist": "Leather loafers", "Streetwear": "Chunky sneakers", "Classic": "Oxford shoes",
    "Luxury": "Pointed heels", "Casual": "Canvas sneakers", "Athleisure": "Running shoes",
    "Boho": "Suede ankle boots", "Smart Casual": "Suede loafers", "Y2K": "Platform sneakers",
    "Old Money": "Penny loafers", "Indo-Western": "Embellished juttis",
}
ACCESSORIES = {
    "Minimalist": "Delicate gold chain", "Streetwear": "Bucket hat + chain",
    "Classic": "Leather belt + watch", "Luxury": "Statement earrings",
    "Casual": "Canvas tote", "Athleisure": "Sport cap", "Boho": "Layered beaded necklaces",
    "Smart Casual": "Slim watch", "Y2K": "Mini sunglasses", "Old Money": "Pearl studs",
    "Indo-Western": "Statement jhumkas",
}

# Menswear-specific pools (the dicts above double as the women's pools)
MEN_TOPS = {
    "Minimalist": ["Crew-neck tee", "Structured shirt", "Fine-knit sweater"],
    "Streetwear": ["Oversized graphic tee", "Bomber jacket", "Boxy hoodie"],
    "Classic": ["Oxford shirt", "Wool blazer", "Cashmere crew sweater"],
    "Luxury": ["Silk shirt", "Tailored double-breasted jacket", "Cashmere polo"],
    "Casual": ["Henley tee", "Flannel shirt", "Zip-up hoodie"],
    "Athleisure": ["Performance tee", "Track jacket", "Tech-fabric hoodie"],
    "Boho": ["Linen shirt", "Printed overshirt", "Textured henley"],
    "Smart Casual": ["Knit polo", "Chambray shirt", "Merino sweater"],
    "Y2K": ["Graphic baby tee", "Varsity jacket", "Mesh layering top"],
    "Old Money": ["Cable-knit sweater", "Oxford shirt", "Quilted gilet"],
    "Indo-Western": ["Nehru jacket over kurta", "Bandhgala jacket", "Embroidered kurta"],
}
MEN_BOTTOMS = {
    "Minimalist": ["Tapered trousers", "Straight-leg denim", "Slim chinos"],
    "Streetwear": ["Cargo pants", "Baggy jeans", "Track pants"],
    "Classic": ["Tailored trousers", "Wool dress pants", "Dark denim"],
    "Luxury": ["Wool suit trousers", "Silk-blend trousers", "Tailored chinos"],
    "Casual": ["Straight denim", "Twill shorts", "Relaxed joggers"],
    "Athleisure": ["Training shorts", "Jogger pants", "Compression tights"],
    "Boho": ["Linen drawstring pants", "Flared trousers", "Printed wide pants"],
    "Smart Casual": ["Chinos", "Dark denim", "Tailored shorts"],
    "Y2K": ["Low-rise jeans", "Cargo pants", "Flared denim"],
    "Old Money": ["Pleated trousers", "Tweed pants", "Chino pants"],
    "Indo-Western": ["Dhoti pants", "Churidar", "Straight-fit pajama pants"],
}
MEN_SHOES = {
    "Minimalist": "Leather derbies", "Streetwear": "Chunky sneakers", "Classic": "Oxford shoes",
    "Luxury": "Leather monk straps", "Casual": "Canvas sneakers", "Athleisure": "Running shoes",
    "Boho": "Suede desert boots", "Smart Casual": "Suede loafers", "Y2K": "Platform sneakers",
    "Old Money": "Penny loafers", "Indo-Western": "Embroidered mojaris",
}
MEN_ACCESSORIES = {
    "Minimalist": "Slim leather watch", "Streetwear": "Bucket hat + chain",
    "Classic": "Leather belt + watch", "Luxury": "Signet ring + watch",
    "Casual": "Canvas backpack", "Athleisure": "Sport cap", "Boho": "Woven bracelet stack",
    "Smart Casual": "Slim watch", "Y2K": "Mini sunglasses", "Old Money": "Leather belt",
    "Indo-Western": "Statement brooch",
}


def get_wardrobe_pools(gender):
    """Return (tops, bottoms, shoes, accessories) dicts for the chosen gender.
    'Women' uses the base pools defined above; 'Men' uses the MEN_* pools;
    'Unisex' merges both so items from either wardrobe can be drawn."""
    if gender == "Men":
        return MEN_TOPS, MEN_BOTTOMS, MEN_SHOES, MEN_ACCESSORIES
    if gender == "Unisex":
        merged_tops = {k: list(set(TOPS.get(k, []) + MEN_TOPS.get(k, []))) for k in STYLE_PERSONALITIES}
        merged_bottoms = {k: list(set(BOTTOMS.get(k, []) + MEN_BOTTOMS.get(k, []))) for k in STYLE_PERSONALITIES}
        merged_shoes = {k: random.choice([SHOES.get(k, "Sneakers"), MEN_SHOES.get(k, "Sneakers")])
                         for k in STYLE_PERSONALITIES}
        merged_acc = {k: random.choice([ACCESSORIES.get(k, "Simple jewelry"), MEN_ACCESSORIES.get(k, "Simple jewelry")])
                      for k in STYLE_PERSONALITIES}
        return merged_tops, merged_bottoms, merged_shoes, merged_acc
    return TOPS, BOTTOMS, SHOES, ACCESSORIES


def generate_outfit(personality, occasion, season, color, budget, gender="Unisex", n=1):
    tops_pool, bottoms_pool, shoes_pool, acc_pool = get_wardrobe_pools(gender)
    outfits = []
    for i in range(n):
        top = random.choice(tops_pool.get(personality, tops_pool.get("Casual", ["Classic top"])))
        bottom = random.choice(bottoms_pool.get(personality, bottoms_pool.get("Casual", ["Classic bottom"])))
        shoe = shoes_pool.get(personality, "Sneakers")
        acc = acc_pool.get(personality, "Simple jewelry")
        est_price = round(random.uniform(budget * 0.5, budget * 1.1), 2)

        color_harmony = random.randint(70, 98)
        occasion_fit = random.randint(65, 97)
        style_consistency = random.randint(70, 99)
        trend_relevance = random.randint(55, 95)
        budget_fit = max(30, 100 - int(abs(est_price - budget) / max(budget, 1) * 100))
        versatility = random.randint(50, 95)

        fqe, verdict, explanation, breakdown = calculate_fqe(
            color_harmony, occasion_fit, style_consistency, trend_relevance, budget_fit, versatility
        )

        gender_label = f"{gender} " if gender != "Unisex" else ""
        outfits.append({
            "name": f"{gender_label}{color} {personality} {occasion} Look",
            "gender": gender,
            "top": top, "bottom": bottom, "footwear": shoe, "accessories": acc,
            "palette": [color, random.choice(COLORS), random.choice(COLORS)],
            "tips": f"Balance proportions — pair the {top.lower()} with the {bottom.lower()} and let "
                    f"the {acc.lower()} be the focal point. Ideal for {occasion.lower()} in {season.lower()}.",
            "occasion": occasion,
            "budget": est_price,
            "fqe": fqe,
            "verdict": verdict,
            "explanation": explanation,
            "breakdown": breakdown,
        })
    return outfits


def call_ai(prompt: str) -> str:
    """Uses OpenAI if configured, otherwise falls back to a rule-based note.
    Never raises — always returns usable text."""
    if not AI_ENABLED:
        return ("*(AI styling is running in offline/rule-based mode — add an OPENAI_API_KEY "
                "to enable live AI-generated styling notes.)*")
    try:
        import requests
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return ("*(AI service unavailable right now — showing rule-based styling instead.)*")


# ============================================================
# 6. IMAGE / STYLE ANALYZER — local PIL fallback (no CV API required)
# ============================================================

def analyze_image(image_bytes):
    """
    Local, dependency-light analysis:
    - Dominant colors via downsampled pixel quantization (PIL only, no external API/model).
    - Category/style are heuristic guesses based on color palette + aspect ratio, clearly
      labeled as a demo estimate, not a trained classifier result.
    This function never raises; any failure degrades to a safe demo response.
    """
    if not PIL_AVAILABLE:
        return {
            "ok": False,
            "message": "Image processing library unavailable in this environment — showing demo analysis.",
            "dominant_colors": ["#c9a24b", "#1b1a1d", "#f7f3ec"],
            "category_guess": "Layered Ensemble (demo)",
            "style_guess": "Smart Casual (demo)",
            "styling_tips": ["Pair with a structured outer layer.", "Add one metallic accessory."],
        }
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_small = img.resize((80, 80))
        pixels = list(img_small.getdata())

        # Simple quantization bucket (no external ML dependency)
        buckets = {}
        for r, g, b in pixels:
            key = (r // 32, g // 32, b // 32)
            buckets[key] = buckets.get(key, 0) + 1
        top_buckets = sorted(buckets.items(), key=lambda x: -x[1])[:3]
        dominant_hex = []
        for (rk, gk, bk), _ in top_buckets:
            r, g, b = rk * 32 + 16, gk * 32 + 16, bk * 32 + 16
            dominant_hex.append(f"#{r:02x}{g:02x}{b:02x}")

        # Heuristic style guess from average saturation/brightness
        avg_h, avg_s, avg_v = [], [], []
        for r, g, b in pixels[::7]:
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            avg_h.append(h); avg_s.append(s); avg_v.append(v)
        mean_s = sum(avg_s) / len(avg_s)
        mean_v = sum(avg_v) / len(avg_v)

        if mean_v < 0.35:
            style_guess = "Classic / Evening"
        elif mean_s < 0.2 and mean_v > 0.6:
            style_guess = "Minimalist"
        elif mean_s > 0.55:
            style_guess = "Boho / Streetwear"
        else:
            style_guess = "Smart Casual"

        width, height = img.size
        category_guess = "Full Outfit" if height >= width else "Detail / Accessory"

        tips = [
            f"The dominant tone reads {'muted' if mean_s < 0.3 else 'vibrant'} — "
            f"{'add a soft neutral base layer.' if mean_s >= 0.3 else 'introduce one saturated accent piece.'}",
            f"Overall brightness is {'low' if mean_v < 0.4 else 'high'}, which suits "
            f"{'evening or formal settings.' if mean_v < 0.4 else 'daytime or casual settings.'}",
        ]

        return {
            "ok": True,
            "message": "Local pixel-based analysis (demo heuristic, not a trained fashion classifier).",
            "dominant_colors": dominant_hex,
            "category_guess": category_guess,
            "style_guess": style_guess,
            "styling_tips": tips,
        }
    except Exception:
        return {
            "ok": False,
            "message": "Could not analyze this image — showing demo analysis instead.",
            "dominant_colors": ["#c9a24b", "#1b1a1d", "#f7f3ec"],
            "category_guess": "Layered Ensemble (demo)",
            "style_guess": "Smart Casual (demo)",
            "styling_tips": ["Pair with a structured outer layer.", "Add one metallic accessory."],
        }


# ============================================================
# 7. UI HELPERS
# ============================================================

def swatch_html(colors):
    return "".join(f'<span class="fiq-swatch" style="background:{c}"></span>' for c in colors)


def render_outfit_card(outfit, key_prefix):
    with st.container():
        st.markdown('<div class="fiq-card fiq-fade">', unsafe_allow_html=True)
        st.markdown(f"**{outfit['name']}**")
        gender_badge = f'<span class="fiq-badge">{outfit["gender"]}</span>' if outfit.get("gender") else ""
        st.markdown(
            f'{gender_badge}'
            f'<span class="fiq-badge">{outfit["occasion"]}</span>'
            f'<span class="fiq-badge">FQE {outfit["fqe"]}</span>'
            f'<span class="fiq-badge">${outfit["budget"]:.0f}</span>',
            unsafe_allow_html=True,
        )
        st.write(f"👕 Top: {outfit['top']}")
        st.write(f"👖 Bottom: {outfit['bottom']}")
        st.write(f"👟 Footwear: {outfit['footwear']}")
        st.write(f"💍 Accessories: {outfit['accessories']}")
        st.markdown(swatch_html(outfit["palette"]), unsafe_allow_html=True)
        st.caption(outfit["tips"])
        st.progress(min(int(outfit["fqe"]), 100) / 100)
        st.caption(f"FQE Verdict: **{outfit['verdict']}**")
        if st.button("❤️ Save Look", key=f"{key_prefix}_save"):
            st.session_state.favorites.append(outfit)
            st.success("Saved to Favorites!")
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 8. SIDEBAR / NAV
# ============================================================

def render_sidebar():
    st.sidebar.markdown("### 👗 Fashion IQ Boat")
    st.sidebar.caption("Your Personal Fashion Intelligence")
    pages = [
        "🏠 Dashboard", "✨ AI Stylist", "👗 Outfit Generator", "🔥 Trend Intelligence",
        "🛍️ Fashion Finder", "📸 Style Analyzer", "❤️ Favorites", "👤 My Style Profile",
    ]
    choice = st.sidebar.radio("Navigate", pages, label_visibility="collapsed")
    st.session_state.page = choice.split(" ", 1)[1]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"AI status: {'🟢 Connected' if AI_ENABLED else '⚪ Offline (rule-based mode)'}")
    st.sidebar.caption(f"API key: {mask_key(OPENAI_API_KEY)}")
    st.sidebar.markdown("---")
    st.sidebar.caption(f"© {datetime.now().year} Fashion IQ Boat")


# ============================================================
# 9. PAGES
# ============================================================

def render_dashboard():
    st.markdown(
        """
        <div class="fiq-hero">
            <h1>Your Personal Fashion Intelligence</h1>
            <p>Discover. Style. Express.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✨ Create My Look", use_container_width=True):
            st.session_state.page = "AI Stylist"
            st.rerun()
    with c2:
        if st.button("Explore Trends", use_container_width=True):
            st.session_state.page = "Trend Intelligence"
            st.rerun()

    st.markdown("#### Snapshot")
    iq = st.session_state.fashion_iq
    overall = round(sum(iq.values()) / len(iq))
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, (label, val) in zip([k1, k2, k3, k4], iq.items()):
        with col:
            st.markdown(
                f'<div class="fiq-kpi"><div class="val">{val}</div>'
                f'<div class="lbl">{label.title()}</div></div>',
                unsafe_allow_html=True,
            )
    with k5:
        st.markdown(
            f'<div class="fiq-kpi"><div class="val">{overall}</div>'
            f'<div class="lbl">Fashion IQ</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("#### Recently Generated")
    if not st.session_state.generated_outfits:
        st.markdown(
            '<div class="fiq-empty">No looks generated yet — head to AI Stylist or Outfit Generator ✨</div>',
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(3)
        for i, outfit in enumerate(st.session_state.generated_outfits[-3:]):
            with cols[i % 3]:
                render_outfit_card(outfit, key_prefix=f"dash_{i}")


def render_ai_stylist():
    st.subheader("✨ AI Stylist")
    data = load_demo_data()
    with st.form("stylist_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            personality = st.selectbox("Style personality", STYLE_PERSONALITIES)
            occasion = st.selectbox("Occasion", OCCASIONS)
            season = st.selectbox("Season", SEASONS)
        with c2:
            pref_colors = st.multiselect("Preferred colors", COLORS)
            avoid_colors = st.multiselect("Colors to avoid", COLORS)
            formality = st.select_slider("Formality", ["Very Casual", "Casual", "Smart", "Formal", "Black Tie"])
        with c3:
            budget = st.slider("Budget ($)", 20, 1000, 150)
            brands = st.multiselect("Preferred brands", BRANDS)
            category = st.selectbox("Clothing category focus", ["Full Outfit", "Top", "Bottom", "Footwear", "Accessories"])
        submitted = st.form_submit_button("Generate My Look")

    if submitted:
        color = random.choice([c for c in pref_colors if c not in avoid_colors] or COLORS)
        outfits = generate_outfit(personality, occasion, season, color, budget, n=1)
        st.session_state.generated_outfits.extend(outfits)
        st.session_state.profile.update({
            "style": personality, "colors": pref_colors, "brands": brands,
            "budget": budget, "occasions": [occasion], "personality": personality,
        })
        st.success("Look generated!")
        outfit = outfits[0]
        render_outfit_card(outfit, key_prefix="stylist")
        with st.expander("AI styling note"):
            note = call_ai(
                f"Give a short styling tip for a {personality} {occasion} outfit in {color}, budget ${budget}."
            )
            st.write(note)
        with st.expander("Why this FQE score?"):
            st.write(outfit["explanation"])
            st.json(outfit["breakdown"])


def render_outfit_generator():
    st.subheader("👗 Outfit Generator")
    c0, c1, c2, c3, c4 = st.columns(5)
    with c0:
        gender = st.selectbox("Gender", GENDERS, key="og_gender")
    with c1:
        occasion = st.selectbox("Occasion", OCCASIONS, key="og_occasion")
    with c2:
        season = st.selectbox("Weather / Season", SEASONS, key="og_season")
    with c3:
        color = st.selectbox("Color", COLORS, key="og_color")
    with c4:
        style = st.selectbox("Style", STYLE_PERSONALITIES, key="og_style")
    budget = st.slider("Budget ($)", 20, 1000, 150, key="og_budget")
    count = st.slider("Number of outfits", 3, 6, 4)

    if st.button("Generate Outfits"):
        outfits = generate_outfit(style, occasion, season, color, budget, gender=gender, n=count)
        st.session_state.generated_outfits.extend(outfits)
        st.session_state["og_last_batch"] = outfits

    outfits = st.session_state.get("og_last_batch", [])
    if not outfits:
        st.markdown('<div class="fiq-empty">Set your preferences and generate a batch of looks.</div>',
                    unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, outfit in enumerate(outfits):
            with cols[i % 3]:
                render_outfit_card(outfit, key_prefix=f"gen_{i}")


def render_trend_intelligence():
    st.subheader("🔥 Fashion Trend Intelligence")
    data = load_demo_data()
    trends, colors_df, seasonality = data["trends"], data["colors"], data["seasonality"]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(trends.sort_values("growth_pct"), x="growth_pct", y="trend", orientation="h",
                     color="growth_pct", color_continuous_scale=["#ffc2dd", "#ff3d94"],
                     title="Trend Growth (%)")
        fig.update_layout(template="plotly_white", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.pie(colors_df, names="color", values="popularity", hole=0.55, title="Trending Colors",
                      color_discrete_sequence=["#ff3d94", "#ff8cba", "#ffc2dd", "#d6006e", "#ffeaf3", "#ff5fa2"])
        fig2.update_layout(template="plotly_white", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig3 = go.Figure()
        for col in ["Formal", "Streetwear", "Boho", "Minimalist"]:
            fig3.add_trace(go.Scatterpolar(r=seasonality[col], theta=seasonality["season"], fill="toself", name=col))
        fig3.update_layout(template="plotly_white", polar=dict(bgcolor="rgba(0,0,0,0)"),
                            paper_bgcolor="rgba(0,0,0,0)", title="Style Seasonality Radar")
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        heat = seasonality.set_index("season")[["Formal", "Streetwear", "Boho", "Minimalist"]]
        fig4 = px.imshow(heat.T, aspect="auto", color_continuous_scale="RdPu", title="Trend Heatmap")
        fig4.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Category Momentum")
    line = trends.groupby("category")["growth_pct"].mean().reset_index()
    fig5 = px.line(line, x="category", y="growth_pct", markers=True, title="Average Growth by Category")
    fig5.update_layout(template="plotly_white", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig5, use_container_width=True)


def render_fashion_finder():
    st.subheader("🛍️ Fashion Finder")
    data = load_demo_data()["products"]

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            category = st.multiselect("Category", sorted(data["category"].unique()))
            brand = st.multiselect("Brand", sorted(data["brand"].unique()))
        with c2:
            color = st.multiselect("Color", sorted(data["color"].unique()))
            style = st.multiselect("Style", sorted(data["style"].unique()))
        with c3:
            price_range = st.slider("Price range ($)", 0, 350, (0, 350))
            min_rating = st.slider("Minimum rating", 3.0, 5.0, 3.5, 0.1)

    filtered = data.copy()
    if category:
        filtered = filtered[filtered["category"].isin(category)]
    if brand:
        filtered = filtered[filtered["brand"].isin(brand)]
    if color:
        filtered = filtered[filtered["color"].isin(color)]
    if style:
        filtered = filtered[filtered["style"].isin(style)]
    filtered = filtered[
        (filtered["price"] >= price_range[0]) & (filtered["price"] <= price_range[1])
        & (filtered["rating"] >= min_rating)
    ]

    st.caption(f"{len(filtered)} products found")
    if filtered.empty:
        st.markdown('<div class="fiq-empty">No products match these filters — try widening your search.</div>',
                    unsafe_allow_html=True)
        return

    cols = st.columns(4)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 4]:
            st.markdown('<div class="fiq-card fiq-fade">', unsafe_allow_html=True)
            st.markdown(f"**{row['name']}**")
            st.caption(f"{row['brand']} · {row['category']}")
            st.markdown(
                f'<span class="fiq-badge">${row["price"]:.0f}</span>'
                f'<span class="fiq-badge">⭐ {row["rating"]}</span>'
                f'<span class="fiq-badge">{row["color"]}</span>',
                unsafe_allow_html=True,
            )
            bc1, bc2 = st.columns(2)
            with bc1:
                st.button("View Product", key=f"view_{row['id']}")
            with bc2:
                if st.button("❤️ Save", key=f"save_{row['id']}"):
                    st.session_state.favorites.append({
                        "name": row["name"], "top": row["category"], "bottom": "-",
                        "footwear": "-", "accessories": "-", "palette": [row["color"]],
                        "tips": f"From {row['brand']}", "occasion": "Shopping Find",
                        "budget": row["price"], "fqe": row["rating"] * 20,
                        "verdict": "Saved Item",
                    })
                    st.success("Saved!")
            st.markdown("</div>", unsafe_allow_html=True)


def render_style_analyzer():
    st.subheader("📸 Style Analyzer")
    st.caption("Upload a fashion photo for a color-and-style read. "
               "Analysis runs locally as a demo heuristic — no external CV API is required.")
    upload = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if upload is None:
        st.markdown('<div class="fiq-empty">Upload an image to get styling suggestions.</div>',
                    unsafe_allow_html=True)
        return

    try:
        st.image(upload, use_container_width=True, caption="Uploaded image")
    except Exception:
        st.warning("Could not preview this image, but analysis will still attempt to run.")

    with st.spinner("Analyzing..."):
        result = analyze_image(upload.getvalue())

    st.info(result["message"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Dominant colors**")
        st.markdown(swatch_html(result["dominant_colors"]), unsafe_allow_html=True)
        st.write(", ".join(result["dominant_colors"]))
    with c2:
        st.markdown(f"**Category guess:** {result['category_guess']}")
        st.markdown(f"**Style guess:** {result['style_guess']}")

    st.markdown("**Styling suggestions**")
    for tip in result["styling_tips"]:
        st.write(f"- {tip}")

    st.markdown("**Recommended matching colors**")
    st.markdown(swatch_html(random.sample(COLORS, 3)), unsafe_allow_html=True)
    st.markdown(f"**Recommended accessory:** {random.choice(list(ACCESSORIES.values()))}")


def render_favorites():
    st.subheader("❤️ Favorites")
    favs = st.session_state.favorites
    if not favs:
        st.markdown('<div class="fiq-empty">No saved looks yet — favorite an outfit or product to see it here.</div>',
                    unsafe_allow_html=True)
        return
    cols = st.columns(3)
    for i, outfit in enumerate(favs):
        with cols[i % 3]:
            st.markdown('<div class="fiq-card fiq-fade">', unsafe_allow_html=True)
            st.markdown(f"**{outfit['name']}**")
            st.markdown(swatch_html(outfit.get("palette", ["#c9a24b"])), unsafe_allow_html=True)
            st.caption(outfit.get("tips", ""))
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.favorites.pop(i)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_profile():
    st.subheader("👤 My Style Profile")
    profile = st.session_state.profile
    iq = st.session_state.fashion_iq
    overall = round(sum(iq.values()) / len(iq))

    st.markdown(f"### Your Fashion IQ: {overall}/100")
    for label, val in iq.items():
        st.write(label.title())
        st.progress(val / 100)

    st.markdown("---")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            personality = st.selectbox("Style personality", STYLE_PERSONALITIES,
                                        index=STYLE_PERSONALITIES.index(profile["personality"])
                                        if profile["personality"] in STYLE_PERSONALITIES else 0)
            colors = st.multiselect("Favorite colors", COLORS, default=profile.get("colors", []))
        with c2:
            brands = st.multiselect("Preferred brands", BRANDS, default=profile.get("brands", []))
            budget = st.slider("Typical budget ($)", 20, 1000, profile.get("budget", 150))
        occasions = st.multiselect("Favorite occasions", OCCASIONS, default=profile.get("occasions", []))
        saved = st.form_submit_button("Save Profile")

    if saved:
        st.session_state.profile.update({
            "personality": personality, "style": personality, "colors": colors,
            "brands": brands, "budget": budget, "occasions": occasions,
        })
        st.success("Profile updated!")

    st.markdown(f"**Saved looks:** {len(st.session_state.favorites)}")


# ============================================================
# 10. MAIN
# ============================================================

def main():
    setup_page()
    load_css()
    init_state()
    render_sidebar()

    page = st.session_state.page
    try:
        if page == "Dashboard":
            render_dashboard()
        elif page == "AI Stylist":
            render_ai_stylist()
        elif page == "Outfit Generator":
            render_outfit_generator()
        elif page == "Trend Intelligence":
            render_trend_intelligence()
        elif page == "Fashion Finder":
            render_fashion_finder()
        elif page == "Style Analyzer":
            render_style_analyzer()
        elif page == "Favorites":
            render_favorites()
        elif page == "My Style Profile":
            render_profile()
        else:
            render_dashboard()
    except Exception as e:
        st.error("Something went wrong rendering this page. Showing the dashboard instead.")
        st.caption(f"Details: {e}")
        render_dashboard()


if __name__ == "__main__":
    main()
