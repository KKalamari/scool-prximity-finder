# =====================================================================
# ΕΥΡΕΣΗ ΠΛΗΣΙΕΣΤΕΡΟΥ ΣΧΟΛΕΙΟΥ - Web εφαρμογή (Streamlit)
# =====================================================================
import re
import time
import difflib

import requests
import streamlit as st
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium

# ---------------------------------------------------------------------
geolocator = Nominatim(user_agent="teacher-closest-school-finder-webapp (contact: example@example.com)")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ATTICA_BBOX = (37.75, 23.45, 38.25, 24.05)  # south, west, north, east


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def geocode_address(address, tries=3):
    addr = address.strip()
    if not re.search(r"ελλ[αά]δα|greece", addr, re.IGNORECASE):
        addr = addr + ", Ελλάδα"
    for _ in range(tries):
        try:
            loc = geolocator.geocode(addr, timeout=10)
            if loc:
                return (loc.latitude, loc.longitude)
        except Exception:
            time.sleep(1)
    return None


def clean_school_name(raw_line):
    line = raw_line.strip()
    line = re.sub(r"\(.*?\)", "", line)
    line = re.sub(r"^\d+[\.\)]\s*", "", line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


def looks_like_school_line(line):
    keywords = ["ΔΗΜΟΤΙΚ", "ΝΗΠΙΑΓΩΓ", "ΣΧΟΛΕΙ", "Δ.Σ", "Ν/Γ", "ΟΛΟΗΜΕΡ"]
    upper = line.upper()
    return any(k in upper for k in keywords)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def query_overpass(name):
    escaped = re.escape(name)
    s, w, n, e = ATTICA_BBOX
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"school|kindergarten"]["name"~"{escaped}",i]({s},{w},{n},{e});
      way["amenity"~"school|kindergarten"]["name"~"{escaped}",i]({s},{w},{n},{e});
      relation["amenity"~"school|kindergarten"]["name"~"{escaped}",i]({s},{w},{n},{e});
    );
    out center tags;
    """
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception:
        return []


def best_match(name, elements):
    target = normalize(name)
    best, best_score = None, 0.0
    for el in elements:
        cand_name = el.get("tags", {}).get("name", "")
        score = difflib.SequenceMatcher(None, target, normalize(cand_name)).ratio()
        if score > best_score:
            best_score, best = score, el
    return best, best_score


def get_coords(el):
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    center = el.get("center")
    if center:
        return center["lat"], center["lon"]
    return None


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def locate_school(name):
    elements = query_overpass(name)
    if elements:
        el, score = best_match(name, elements)
        if el and score > 0.45:
            coords = get_coords(el)
            if coords:
                tags = el.get("tags", {})
                addr_parts = [tags.get("addr:street", ""), tags.get("addr:housenumber", ""), tags.get("addr:city", "")]
                address = " ".join(p for p in addr_parts if p).strip()
                if not address:
                    address = "Διεύθυνση μη διαθέσιμη στο OpenStreetMap"
                return coords[0], coords[1], address, "OpenStreetMap"

    for attempt_query in (f"{name}, Αθήνα, Ελλάδα", f"{name}, Αττική, Ελλάδα"):
        for _ in range(2):
            try:
                loc = geolocator.geocode(attempt_query, timeout=10)
                if loc:
                    return loc.latitude, loc.longitude, loc.address, "Nominatim (κατά προσέγγιση)"
            except Exception:
                time.sleep(1)
    return None


# =======================================================================
# UI
# =======================================================================
st.set_page_config(page_title="Πλησιέστερο Σχολείο", page_icon="🏫", layout="wide")
st.title("🏫 Εύρεση πλησιέστερου σχολείου")
st.caption("Πρωτοβάθμια Εκπαίδευση (Δημοτικά/Νηπιαγωγεία) - Αθήνα")

col1, col2 = st.columns([1, 1])

with col1:
    home_address = st.text_input(
        "Διεύθυνση κατοικίας σου",
        placeholder="π.χ. Πατησίων 100, Αθήνα",
    )

with col2:
    schools_raw = st.text_area(
        "Λίστα σχολείων (ένα σχολείο ανά γραμμή)",
        height=150,
        placeholder="25ο Δημοτικό Σχολείο Αθηνών\n3ο Νηπιαγωγείο Νέας Φιλαδέλφειας\n1ο Δημοτικό Σχολείο Ψυχικού",
    )

run = st.button("🔎 Βρες αποστάσεις & χάρτη", type="primary")

if run:
    if not home_address.strip():
        st.error("Συμπλήρωσε πρώτα τη διεύθυνση κατοικίας σου.")
        st.stop()
    if not schools_raw.strip():
        st.error("Επικόλλησε τη λίστα σχολείων.")
        st.stop()

    with st.spinner("Εντοπισμός διεύθυνσης κατοικίας..."):
        home_coords = geocode_address(home_address)

    if not home_coords:
        st.error(
            "Δεν μπόρεσα να εντοπίσω αυτή τη διεύθυνση. Δοκίμασε πιο συγκεκριμένη μορφή "
            "(οδός, αριθμός, περιοχή)."
        )
        st.stop()

    st.success(f"Το σπίτι εντοπίστηκε στις συντεταγμένες: {home_coords}")

    raw_lines = [l for l in schools_raw.splitlines() if l.strip()]
    school_names = []
    for line in raw_lines:
        cleaned = clean_school_name(line)
        if cleaned and looks_like_school_line(cleaned):
            school_names.append(cleaned)
    school_names = list(dict.fromkeys(school_names))

    if not school_names:
        st.warning("Δεν αναγνωρίστηκε κανένα όνομα σχολείου στη λίστα.")
        st.stop()

    st.write(f"Βρέθηκαν **{len(school_names)}** πιθανά σχολεία. Αναζήτηση σε εξέλιξη...")
    progress = st.progress(0.0)
    status = st.empty()

    results = []
    not_found = []
    for i, name in enumerate(school_names):
        status.write(f"Αναζήτηση: {name}")
        found = locate_school(name)
        if found:
            lat, lon, address, method = found
            dist_km = geodesic(home_coords, (lat, lon)).km
            results.append({
                "Σχολείο": name, "Απόσταση (χλμ)": round(dist_km, 2),
                "Διεύθυνση": address, "Πηγή": method,
                "_lat": lat, "_lon": lon,
            })
        else:
            not_found.append(name)
        progress.progress((i + 1) / len(school_names))
        time.sleep(0.3)

    status.empty()
    progress.empty()
    results.sort(key=lambda r: r["Απόσταση (χλμ)"])

    st.subheader("Αποτελέσματα (ταξινομημένα κατά απόσταση)")
    st.dataframe(
        [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
        use_container_width=True,
        hide_index=True,
    )

    if not_found:
        with st.expander(f"⚠ {len(not_found)} σχολεία δεν βρέθηκαν αυτόματα"):
            for n in not_found:
                st.write(f"- {n}")

    st.subheader("Διαδραστικός χάρτης")
    m = folium.Map(location=home_coords, zoom_start=12)
    folium.Marker(
        home_coords, popup="Το σπίτι μου", tooltip="Σπίτι",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)
    for r in results:
        folium.Marker(
            [r["_lat"], r["_lon"]],
            popup=folium.Popup(
                f"<b>{r['Σχολείο']}</b><br>{r['Απόσταση (χλμ)']} χλμ<br>{r['Διεύθυνση']}",
                max_width=300,
            ),
            tooltip=f"{r['Σχολείο']} ({r['Απόσταση (χλμ)']} χλμ)",
            icon=folium.Icon(color="blue", icon="graduation-cap", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=520, scrolling=True)
else:
    st.info("Συμπλήρωσε τη διεύθυνση και τη λίστα σχολείων, μετά πάτα το κουμπί.")
