import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, os, re, sys, zipfile, subprocess, json, time, hashlib
import urllib.request, urllib.error, urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
try:
    from bs4 import BeautifulSoup
    BS4 = True
except ImportError:
    BS4 = False
# ─── Renkler ──────────────────────────────────────────────
BG      = "#0D1B2A"
PANEL   = "#152030"
CARD    = "#1A2A3D"
ACCENT  = "#E8212A"
GREEN   = "#27AE60"
BLUE    = "#2980B9"
GOLD    = "#F5A623"
SILVER  = "#95A5A6"
BRONZE  = "#CA6F1E"
TEAL    = "#16A085"
YELLOW  = "#F39C12"
ORANGE  = "#E67E22"
TEXT    = "#ECF0F1"
DIM     = "#7F8C9A"
BORDER  = "#1E3050"
RED     = "#E74C3C"
LINE_C = [ACCENT,GREEN,BLUE,GOLD,TEAL,ORANGE,"#9B59B6","#1ABC9C","#E67E22","#2ECC71"]
F_H  = ("Segoe UI", 14, "bold")   # heading
F_M  = ("Segoe UI", 10, "bold")   # medium
F_N  = ("Segoe UI", 9)            # normal
F_S  = ("Segoe UI", 9,  "bold")   # small bold
F_XS = ("Segoe UI", 8)            # tiny
APP_DIR     = os.path.dirname(os.path.abspath(sys.argv[0]))
POPPLER_DIR = os.path.join(APP_DIR, "poppler_bin")
TESS_URL = ("https://github.com/UB-Mannheim/tesseract/releases/download/"
            "v5.5.0.20241111/tesseract-ocr-w64-setup-5.5.0.20241111.exe")
POP_URL  = ("https://github.com/oschwartz10612/poppler-windows/releases/download/"
            "v24.08.0-0/Release-24.08.0-0.zip")
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/131.0.0.0 Safari/537.36"),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Ch-Ua-Platform": '"Windows"',
}
VERSION = "v15.0 PRO"
CACHE_DIR = os.path.join(APP_DIR, ".cache_at")
SEHIRLER = [
    "istanbul","ankara","izmir","bursa","adana",
    "kocaeli","diyarbakir","elazig","sanliurfa","konya","antalya","balikesir",
]
TAKI_ACIKLAMA = {
    "SKG":"Göz Koruyucu","SK":"Sun Koruyucu","DB":"Dil Bağı",
    "YP":"Yan Perde","KG":"Kör Gözlük","BP":"Burniye",
    "KBK":"Kör Başlık","T":"Tırnak","ÇR":"Çekildi",
}
TJK_SEHIR_ID = {
    "adana": 1, "izmir": 2, "istanbul": 3, "bursa": 4, "ankara": 5,
    "sanliurfa": 6, "elazig": 7, "diyarbakir": 8, "kocaeli": 9,
    "antalya": 10, "konya": 42, "balikesir": 43,
}
TJK_SEHIR_AD = {
    "adana":"Adana", "izmir":"İzmir", "istanbul":"İstanbul", "bursa":"Bursa",
    "ankara":"Ankara", "sanliurfa":"Şanlıurfa", "elazig":"Elazığ",
    "diyarbakir":"Diyarbakır", "kocaeli":"Kocaeli", "antalya":"Antalya",
    "konya":"Konya", "balikesir":"Balıkesir",
}

_tess = None
_pop  = None
# ─── Kurulum ──────────────────────────────────────────────
def find_tess():
    import shutil
    for p in [
        os.path.join(APP_DIR,"tesseract_bin","tesseract.exe"),
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""),
                     "Programs","Tesseract-OCR","tesseract.exe"),
    ]:
        if p and os.path.exists(p): return p
    return None
def ensure_tess(cb):
    t = find_tess()
    if t: return t
    cb("Tesseract indiriliyor (~50MB)…")
    inst = os.path.join(APP_DIR,"tess_setup.exe")
    try:
        urllib.request.urlretrieve(TESS_URL, inst)
        cb("Tesseract kuruluyor…")
        subprocess.run([inst,"/S"], check=True, timeout=180)
    except Exception: pass
    finally:
        if os.path.exists(inst): os.remove(inst)
    return find_tess()
def ensure_pop(cb):
    import shutil
    if shutil.which("pdftoppm"): return ""
    if os.path.exists(os.path.join(POPPLER_DIR,"pdftoppm.exe")): return POPPLER_DIR
    cb("Poppler indiriliyor…")
    zp = os.path.join(APP_DIR,"pop.zip")
    try:
        urllib.request.urlretrieve(POP_URL, zp)
        with zipfile.ZipFile(zp) as z:
            os.makedirs(POPPLER_DIR, exist_ok=True)
            for m in z.namelist():
                if "/bin/" in m and not m.endswith("/"):
                    with z.open(m) as s, open(
                            os.path.join(POPPLER_DIR,os.path.basename(m)),"wb") as d:
                        d.write(s.read())
        return POPPLER_DIR
    except Exception: return None
    finally:
        if os.path.exists(zp): os.remove(zp)
def ensure_bs4(cb):
    global BS4
    if BS4: return True
    cb("beautifulsoup4 kuruluyor…")
    try:
        subprocess.run([sys.executable,"-m","pip","install",
                        "beautifulsoup4","--quiet"], check=True, timeout=60)
        from bs4 import BeautifulSoup
        BS4 = True
        return True
    except Exception: return False
# ─── Yardımcı ─────────────────────────────────────────────
def fetch(url: str, timeout: int = 15, retries: int = 3) -> str:
    """HTTP GET with retry + exponential backoff."""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last_err or Exception(f"Bağlantı hatası: {url}")

# ─── Profil Önbelleği ───────────────────────────────────
def _cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def cache_get(url: str, max_age_hours: int = 6) -> dict | None:
    """Önbellekten profil verisi oku (max_age_hours saat geçerli)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, _cache_key(url) + ".json")
    if not os.path.exists(path):
        return None
    try:
        age = (time.time() - os.path.getmtime(path)) / 3600
        if age > max_age_hours:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def cache_put(url: str, data: dict):
    """Profil verisini önbelleğe yaz."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, _cache_key(url) + ".json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass
def sehir_url(s: str) -> str:
    return (s.lower()
             .replace("ı","i").replace("ş","s").replace("ç","c")
             .replace("ğ","g").replace("ö","o").replace("ü","u")
             .replace(" ","-"))
def tarih_url(t: str) -> str:
    """GG.AA.YYYY → GG-AA-YYYY"""
    return t.replace(".","-")
def parse_date_key(d: str) -> str:
    try: p=d.split("."); return f"{p[2]}-{p[1]}-{p[0]}"
    except: return "0000-00-00"
def gun_farki(tarih: str) -> int | None:
    try:
        dt = datetime.strptime(tarih, "%d.%m.%Y")
        return (datetime.now() - dt).days
    except: return None
def bugun() -> str:
    return datetime.now().strftime("%d.%m.%Y")
# ─── Yenibeygir Scraper ───────────────────────────────────
def scrape_bulten(tarih: str, sehir: str) -> dict:
    """
    Günlük bülteni çek.
    Yenibeygir yapısı: koşu meta verisi tablo öncesi düz metin olarak gelir,
    her tablo bir koşunun at listesidir.
    """
    from bs4 import BeautifulSoup
    url  = f"https://yenibeygir.com/{tarih_url(tarih)}/{sehir_url(sehir)}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    # ── At tablosu olan tabloları bul ─────────────────────
    # Her tablo AGF | No | At İsmi | ... başlığı taşır
    at_tablolari = []
    for table in soup.find_all("table"):
        header_txt = table.get_text(" ")
        if "AGF" in header_txt and "At" in header_txt:
            at_tablolari.append(table)
    if not at_tablolari:
        raise Exception(
            f"Bülten tablosu bulunamadı.\n"
            f"URL: {url}\n\n"
            f"Olası nedenler:\n"
            f"• Bugün bu şehirde yarış yok\n"
            f"• Tarih formatı yanlış (GG.AA.YYYY olmalı)\n"
            f"• Şehir adı yanlış"
        )
    # ── Her tablo için koşu meta verisini önceki elementlerden çıkar ──
    kosular = []
    for kosu_no, table in enumerate(at_tablolari, start=1):
        # Tablo öncesindeki text node'lardan saat + cins + mesafe çıkar
        meta_txt = ""
        for sib in table.find_all_previous(limit=25):
            t = sib.get_text(" ", strip=True)
            if not t: continue
            # Önceki tabloya gelinirse dur
            if sib.name == "table": break
            meta_txt = t + " " + meta_txt
        saat_m  = re.search(r"(\d{2}:\d{2})", meta_txt)
        saat    = saat_m.group(1) if saat_m else ""
        para_m  = re.search(r"₺\s*([\d\.\,]+)", meta_txt)
        para    = "₺" + para_m.group(1) if para_m else ""
        # Mesafe + pist: "1400 Kum" veya "1400 Çim"
        msf_m   = re.search(r"(\d{3,5})\s*(Kum|Çim|Sentetik|Toprak|Sulu)?", meta_txt)
        mesafe  = msf_m.group(1) if msf_m else ""
        pist_t  = msf_m.group(2) if msf_m and msf_m.group(2) else ""
        # Koşu cinsi: "Maiden", "Handikap", "Şartlı" vb.
        cins_m  = re.search(
            r"(Maiden|Handikap|Hnd\.?|Şartlı|ŞARTLI|Satış|SATIŞ|Grup|Deneme|Açık)",
            meta_txt, re.I)
        cins    = cins_m.group(1) if cins_m else ""
        # Koşu no'yu metinden almaya çalış: tablo öncesi rakam
        no_m = re.search(r"\b(\d{1,2})\s*\.\s*(?:\d{2}:\d{2}|Koşu)", meta_txt)
        if no_m:
            kosu_no = int(no_m.group(1))
        kosu = {
            "no":     kosu_no,
            "saat":   saat,
            "cins":   cins,
            "mesafe": mesafe,
            "pist":   pist_t,
            "para":   para,
            "atlar":  [],
        }
        # ── Tablodan atları çıkar ─────────────────────────
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) < 5: continue
            cells = [td.get_text(" ", strip=True) for td in tds]
            # AGF: sayı veya "-" veya "0"
            agf = cells[0].strip()
            if not agf or not re.match(r"^[\d\.\,\-]+$", agf):
                continue
            # At linki ve ID
            at_id  = ""
            at_url = ""
            for a in tr.select("a[href*='/at/']"):
                m = re.match(r".*/at/(\d+)/([^\s\"'?#]+)", a.get("href",""))
                if m:
                    at_id  = m.group(1)
                    at_url = f"https://yenibeygir.com/at/{at_id}/{m.group(2)}"
                    break
            # At hücresi (genellikle index 2)
            at_cell = tds[2].get_text(" ", strip=True) if len(tds) > 2 else ""
            # Takı kodlarını çıkar
            takiler = re.findall(
                r"\b(SKG|SK|DB|YP|KG|BP|KBK|ÇR)\b", at_cell)
            taki = " ".join(dict.fromkeys(takiler))
            # At adı: büyük harf kelimeler, pedigri ve takıdan önce
            at_adi = ""
            if at_url:
                # URL slug'undan at adını al (en güvenilir)
                slug  = at_url.rstrip("/").split("/")[-1]
                at_adi= slug.replace("-"," ").upper()
            if not at_adi:
                # at_cell'den ilk büyük harf bloğu
                m = re.match(r"([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s\(\)]{1,35}?)(?:\s+(?:SKG|SK|DB|KG|YP|K\s|[A-Z]{2,3}\s)|$)",
                             at_cell)
                at_adi = m.group(1).strip() if m else at_cell[:25].strip()
            if not at_adi: continue
            # Son 10 bağlantılı sayılar
            son10 = []
            son10_td = tds[9] if len(tds) > 9 else (tds[8] if len(tds) > 8 else None)
            if son10_td:
                for a in son10_td.find_all("a"):
                    t2 = a.get_text(strip=True)
                    if t2.isdigit():
                        son10.append(int(t2))
            kosu["atlar"].append({
                "agf":      agf,
                "no":       cells[1].strip() if len(cells) > 1 else "",
                "at":       at_adi,
                "at_id":    at_id,
                "at_url":   at_url,
                "yas":      cells[3].strip() if len(cells) > 3 else "",
                "kilo":     cells[4].strip() if len(cells) > 4 else "",
                "jokey":    cells[5].strip() if len(cells) > 5 else "",
                "klv":      cells[7].strip() if len(cells) > 7 else "",
                "son10":    son10,
                "son10_str":"-".join(str(s) for s in son10) if son10 else "—",
                "hnd":      cells[10].strip() if len(cells) > 10 else "",
                "taki":     taki,
                "s":        cells[12].strip() if len(cells) > 12 else "",
            })
        if kosu["atlar"]:
            kosular.append(kosu)
    return {"tarih": tarih, "sehir": sehir, "kosular": kosular}
def scrape_galoplar(tarih: str, sehir: str, kosu_no: int) -> list:
    """Koşunun galop sayfasını çek."""
    from bs4 import BeautifulSoup
    url = f"https://yenibeygir.com/{tarih_url(tarih)}/{sehir_url(sehir)}/{kosu_no}/galoplar"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        raise Exception(f"Galop tablosu bulunamadı: {url}")
    rows = []
    cur_at = ""
    cur_no = ""
    cur_url= ""
    # At URL haritası
    horse_urls = {}
    for a in soup.select("a[href*='/at/']"):
        href = a.get("href","")
        m = re.match(r".*/at/(\d+)/([^\s\"']+)", href)
        if m:
            at_txt = a.get_text(strip=True).upper()
            if at_txt:
                horse_urls[at_txt] = f"https://yenibeygir.com/at/{m.group(1)}/{m.group(2)}"
    col_keys = ["400","600","800","1000","1200","1400"]
    for tr in tables[0].find_all("tr"):
        tds = tr.find_all(["td","th"])
        if not tds: continue
        text0 = tds[0].get_text(" ", strip=True)
        # At başlık satırı
        if len(tds) <= 4 and re.search(r"[A-ZÇĞİÖŞÜ]{3,}", text0):
            m = re.match(r"(\d+)\s+([A-ZÇĞİÖŞÜ\s\(\)]+)", text0)
            if m:
                cur_no  = m.group(1).strip()
                cur_at  = m.group(2).strip()
                cur_url = horse_urls.get(cur_at, "")
            continue
        # Galop veri satırı
        if len(tds) >= 8:
            cells = [td.get_text(" ", strip=True) for td in tds]
            if not re.match(r"\d{2}\.\d{2}\.\d{4}", cells[0]): continue
            row = {
                "kosu_no": kosu_no,
                "no":      cur_no,
                "at":      cur_at,
                "at_url":  cur_url,
                "g_tarih": cells[0],
                "g_sehir": cells[1] if len(cells)>1 else "",
                "kg":      cells[2] if len(cells)>2 else "",
                "jokey":   cells[3] if len(cells)>3 else "",
                "cikis":   cells[-2] if len(cells)>=2 else "",
                "pist":    cells[-1],
            }
            for i, k in enumerate(col_keys):
                v = cells[4+i] if (4+i) < len(cells) else ""
                row[k] = v if v not in ("-","","Kenter","ÇR") else ""
            rows.append(row)
    return rows
def scrape_profil(url: str, use_cache: bool = True) -> dict:
    """At profil sayfasını çek — yarış geçmişi + pist stats (önbellekli)."""
    if use_cache:
        cached = cache_get(url)
        if cached:
            return cached
    from bs4 import BeautifulSoup
    html  = fetch(url)
    soup  = BeautifulSoup(html, "html.parser")
    h2    = soup.find("h2")
    at_adi= h2.get_text(strip=True) if h2 else ""
    # Meta
    hnd = dozaj = ""
    for line in soup.get_text("\n").splitlines():
        line = line.strip()
        m = re.search(r"Handikap P[:\s]+(\d+)", line)
        if m: hnd = m.group(1)
        m = re.search(r"Dozaj P[:\s]+([\d\-]+)", line)
        if m: dozaj = m.group(1)
    # Yarış geçmişi tablosu
    races = []
    for table in soup.find_all("table"):
        trs   = table.find_all("tr")
        hmap  = {}
        htr   = None
        for tr in trs:
            cells = [td.get_text(strip=True) for td in tr.find_all(["th","td"])]
            if "Tarih" in cells and ("S" in cells or "Derece" in cells):
                hmap = {v:i for i,v in enumerate(cells)}
                htr  = tr
                break
        if not hmap: continue
        def gc(cells, *keys):
            for k in keys:
                i = hmap.get(k)
                if i is not None and i < len(cells): return cells[i]
            return ""
        for tr in trs:
            if tr is htr: continue
            tds   = tr.find_all("td")
            cells = [td.get_text(" ", strip=True) for td in tds]
            if not cells: continue
            tarih = gc(cells,"Tarih")
            if not tarih or not re.match(r"\d{2}\.\d{2}\.\d{4}", tarih): continue
            msf_raw = gc(cells,"Msf/Pist","Msf","Mesafe")
            msf_m   = re.search(r"(\d{3,5})", msf_raw)
            pist_m  = re.sub(r"[\d\s]","",msf_raw).strip()
            races.append({
                "tarih":  tarih,
                "sehir":  gc(cells,"Şehir","Sehir"),
                "kcins":  gc(cells,"K. Cinsi","KCins"),
                "msf":    msf_m.group(1) if msf_m else "",
                "pist":   pist_m,
                "sira":   gc(cells,"S","Sıra"),
                "derece": gc(cells,"Derece"),
                "hiz":    gc(cells,"Hız","Hiz"),
                "jokey":  gc(cells,"Jokey"),
                "kilo":   gc(cells,"Kilo"),
                "taki":   gc(cells,"Takı","Taki"),
            })
        if races: break
    # Pist istatistikleri
    pist_stats = {}
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells and cells[0] in ("Kum","Çim","Sentetik","Toplam"):
                try:
                    pist_stats[cells[0]] = {
                        "kosu": int(cells[1]) if len(cells)>1 else 0,
                        "1":    int(cells[2]) if len(cells)>2 else 0,
                        "2":    int(cells[3]) if len(cells)>3 else 0,
                        "3":    int(cells[4]) if len(cells)>4 else 0,
                        "hiz":  int(cells[7]) if len(cells)>7 else 0,
                    }
                except: pass
    result = {"at": at_adi, "hnd": hnd, "dozaj": dozaj,
              "races": races, "pist_stats": pist_stats}
    cache_put(url, result)
    return result
# ─── Jokey Analizi ────────────────────────────────────────
def analiz_jokey(profiller: dict) -> dict:
    """Tüm profillerden jokey kazanma oranı çıkar."""
    jokey_stats = defaultdict(lambda: {"kosu": 0, "birinci": 0, "ilk3": 0})
    for at_adi, profil in profiller.items():
        for r in profil.get("races", []):
            jokey = r.get("jokey", "").strip()
            if not jokey:
                continue
            jokey_stats[jokey]["kosu"] += 1
            try:
                sira = int(re.sub(r"[^\d]", "", str(r.get("sira", "") or "")))
                if sira == 1:
                    jokey_stats[jokey]["birinci"] += 1
                if sira <= 3:
                    jokey_stats[jokey]["ilk3"] += 1
            except (ValueError, TypeError):
                pass
    result = {}
    for jokey, s in jokey_stats.items():
        if s["kosu"] >= 2:
            result[jokey] = {
                "kosu": s["kosu"],
                "birinci": s["birinci"],
                "ilk3": s["ilk3"],
                "win_pct": round(s["birinci"] / s["kosu"] * 100, 1),
                "ilk3_pct": round(s["ilk3"] / s["kosu"] * 100, 1),
            }
    return result
# ─── Analiz ───────────────────────────────────────────────
def galop_to_sec(t: str) -> float | None:
    if not t or str(t).strip() in ("","-","Kenter","ÇR","R"): return None
    t = str(t).strip().replace(",",".")
    parts = t.split(".")
    try:
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/10
        elif len(parts) == 2: return float(t)
    except: pass
    return None
def derece_to_sec(t: str) -> float | None:
    if not t or t in ("-","0"): return None
    t = re.sub(r"[^\d.]","",str(t))
    parts = t.split(".")
    try:
        if len(parts)==3: return int(parts[0])*60+int(parts[1])+int(parts[2])/100
        elif len(parts)==2: return float(t)
    except: pass
    return None
def sec_fmt(s: float | None) -> str:
    if s is None: return "—"
    if s >= 60: m=int(s)//60; return f"{m}:{s-m*60:05.2f}"
    return f"{s:.2f}"
def analiz_galop(galop_rows: list, n: int = 4) -> dict:
    """At bazında son N galop analizi."""
    if not galop_rows: return {}
    df = pd.DataFrame(galop_rows)
    df["_date"] = df["g_tarih"].apply(parse_date_key)
    df["_400s"] = df["400"].apply(galop_to_sec)
    result = {}
    for at, grp in df.groupby("at"):
        grp   = grp.sort_values("_date", ascending=False)
        son_n = grp.head(n)
        vals  = son_n["_400s"].dropna()
        result[at] = {
            "at":          at,
            "galop_sayisi":len(grp),
            "son_n":       n,
            "en_iyi_400":  round(vals.min(),2) if not vals.empty else None,
            "ort_400":     round(vals.mean(),2) if not vals.empty else None,
            "son_tarih":   grp["g_tarih"].iloc[0],
            "gun_fark":    gun_farki(grp["g_tarih"].iloc[0]),
            "rows":        son_n.to_dict("records"),
        }
    return result
def analiz_stil(profil: dict) -> dict:
    """Koşu stili + pist/mesafe tercihi."""
    races = profil.get("races", [])
    if not races:
        return {"stil": "❓ Veri Yok", "stil_skor": 0}
    races = sorted(races, key=lambda r: parse_date_key(r.get("tarih","")), reverse=True)
    siralar, hizlar = [], []
    for r in races:
        try:
            s = int(re.sub(r"[^\d]","",r.get("sira","") or ""))
            if 0 < s <= 30: siralar.append(s)
        except: pass
        m = re.search(r"\(?([+-]?\d+)\)?", str(r.get("hiz","") or ""))
        if m:
            try: hizlar.append(int(m.group(1)))
            except: pass
    ort_s = round(sum(siralar)/len(siralar),1) if siralar else 99
    ort_h = round(sum(hizlar)/len(hizlar),1)   if hizlar  else 0
    ilk3  = round(sum(1 for s in siralar if s<=3)/len(siralar)*100,1) if siralar else 0
    if ort_s <= 3.0:   stil = "🟢 ÖNDEN / LİDER"
    elif ort_s <= 5.5: stil = "🟡 ORTADAN"
    elif ort_h > 25:   stil = "🟡 ORTADAN / YÜKSELİCİ"
    else:              stil = "🔵 GERİDEN / KAPICI"
    # Pist tercihi
    ps = profil.get("pist_stats",{})
    best_pist = max(
        [(p,v) for p,v in ps.items() if p!="Toplam" and v.get("kosu",0)>=2],
        key=lambda x: x[1].get("hiz",0), default=(None,{})
    )
    pist_pref = ""
    if best_pist[0]:
        v = best_pist[1]
        pist_pref = f"{best_pist[0]} ({v.get('kosu',0)} koşu, hız={v.get('hiz',0)})"
    # Takı
    taki_c = {}
    for r in races:
        for t in str(r.get("taki","")).split():
            t = t.strip().upper()
            if t in TAKI_ACIKLAMA: taki_c[t] = taki_c.get(t,0)+1
    taki_str = " | ".join(
        f"{k}×{v}" for k,v in sorted(taki_c.items(),key=lambda x:-x[1])[:4]
    ) if taki_c else "—"
    son5 = "-".join(str(s) for s in siralar[:5]) if siralar else "—"
    return {
        "stil":       stil,
        "ort_sira":   ort_s,
        "ort_hiz":    ort_h,
        "ilk3_pct":   ilk3,
        "son5":       son5,
        "pist_pref":  pist_pref,
        "taki":       taki_str,
        "toplam_kosu":len(siralar),
    }
def analiz_perform(profil: dict, n: int = 5) -> dict:
    """Son N koşunun hız trendi."""
    races = sorted(profil.get("races",[]),
                   key=lambda r: parse_date_key(r.get("tarih","")), reverse=True)
    races = races[:n]
    hizlar = []
    for r in races:
        d = derece_to_sec(r.get("derece",""))
        try:
            msf = int(re.sub(r"[^\d]","",str(r.get("msf","") or "")))
            h   = msf/d if d and d>0 else None
            if h: hizlar.append(h)
        except: pass
    trend_skor = 0.0
    if len(hizlar) >= 2:
        trend_skor = round(hizlar[0]-hizlar[-1], 3)
    if trend_skor > 0.15:   trend = "🟢 YÜKSELİYOR"
    elif trend_skor < -0.15: trend = "🔴 DÜŞÜYOR"
    else:                    trend = "🟡 STABİL"
    return {
        "trend":      trend,
        "trend_skor": trend_skor,
        "en_iyi_hiz": round(max(hizlar),3) if hizlar else None,
        "ort_hiz_ms": round(sum(hizlar)/len(hizlar),3) if hizlar else None,
    }
# ─── TJK Scraper ──────────────────────────────────────────

def scrape_tjk_sonuclar(tarih: str, sehir: str) -> list:
    """
    TJK.org'dan yarış sonuçlarını çek.
    Önce CSV endpoint dener, başarısız olursa HTML sayfasını parse eder.
    tarih: GG.AA.YYYY  sehir: küçük harf (istanbul, ankara, ...)
    Returns: list of dict per horse result
    """
    from bs4 import BeautifulSoup

    sehir_id = TJK_SEHIR_ID.get(sehir.lower(), 3)
    sehir_ad = TJK_SEHIR_AD.get(sehir.lower(), sehir.title())

    # Tarih format: GG.AA.YYYY → GG/AA/YYYY
    parts = tarih.split(".")
    if len(parts) != 3:
        raise Exception(f"Geçersiz tarih formatı: {tarih}")
    tjk_tarih = f"{parts[0]}/{parts[1]}/{parts[2]}"

    rows = []

    # ── Yöntem 1: CSV endpoint ──
    csv_url = (
        f"https://www.tjk.org/TR/YarisSever/Info/GetCSV/GunlukYarisSonuclari"
        f"?SehirId={sehir_id}&QueryParameter_Tarih={tjk_tarih}"
        f"&Era=past&Sehir={urllib.parse.quote(sehir_ad)}"
    )
    try:
        csv_text = fetch(csv_url, timeout=20, retries=2)
        if csv_text and len(csv_text) > 100 and (";" in csv_text or "," in csv_text):
            rows = _parse_tjk_csv(csv_text, sehir)
            if rows:
                return rows
    except Exception:
        pass

    # ── Yöntem 2: HTML sayfası ──
    html_url = (
        f"https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisSonuclari"
        f"?QueryParameter_Tarih={tjk_tarih}&SehirAdi={urllib.parse.quote(sehir_ad)}"
    )
    try:
        html = fetch(html_url, timeout=25, retries=2)
        rows = _parse_tjk_html(html, sehir)
        if rows:
            return rows
    except Exception:
        pass

    # ── Yöntem 3: Alternatif URL pattern ──
    alt_url = (
        f"https://www.tjk.org/TR/Kurumsal/Info/Page/GunlukYarisSonuclari"
        f"?QueryParameter_Tarih={tjk_tarih}&SehirAdi={urllib.parse.quote(sehir_ad)}"
    )
    try:
        html = fetch(alt_url, timeout=25, retries=2)
        rows = _parse_tjk_html(html, sehir)
        if rows:
            return rows
    except Exception:
        pass

    raise Exception(
        f"TJK sonuçları çekilemedi.\n"
        f"Tarih: {tarih}  Şehir: {sehir_ad}\n\n"
        f"Olası nedenler:\n"
        f"• TJK sunucusu erişime izin vermiyor\n"
        f"• Tarihte bu şehirde yarış yok\n"
        f"• İnternet bağlantı sorunu"
    )


def _parse_tjk_csv(csv_text: str, sehir: str) -> list:
    """TJK CSV formatını parse et (noktalı virgül ayraçlı)."""
    rows = []
    lines = csv_text.strip().split("\n")
    if len(lines) < 2:
        return rows

    # Ayraç tespit
    sep = ";" if ";" in lines[0] else ","
    header = [h.strip().strip('"') for h in lines[0].split(sep)]

    # Sütun isimlerini normalize et
    col_map = {}
    for i, h in enumerate(header):
        hl = h.lower().replace("ı","i").replace("ş","s").replace("ç","c").replace("ğ","g").replace("ö","o").replace("ü","u")
        if "kosu" in hl and "no" in hl: col_map["kosu_no"] = i
        elif hl in ("s","sira","siralama"): col_map["sira"] = i
        elif "at" in hl and ("adi" in hl or "ismi" in hl or "ad" in hl): col_map["at"] = i
        elif hl in ("at","horse","name") and "at" not in col_map: col_map["at"] = i
        elif "jokey" in hl or "jockey" in hl: col_map["jokey"] = i
        elif "kilo" in hl or "weight" in hl: col_map["kilo"] = i
        elif "derece" in hl or "time" in hl or "sure" in hl: col_map["derece"] = i
        elif "mesafe" in hl or "distance" in hl or "msf" in hl: col_map["mesafe"] = i
        elif "pist" in hl or "track" in hl: col_map["pist"] = i
        elif "ganyan" in hl or "odds" in hl: col_map["ganyan"] = i
        elif "agf" in hl: col_map["agf"] = i
        elif "gny" in hl or "gany" in hl: col_map["gny"] = i
        elif "fark" in hl or "margin" in hl: col_map["fark"] = i
        elif "hp" in hl or "handikap" in hl: col_map["hp"] = i
        elif "yas" in hl or "age" in hl: col_map["yas"] = i
        elif "antrenor" in hl or "trainer" in hl: col_map["antrenor"] = i

    def gc(cells, key, default=""):
        i = col_map.get(key)
        if i is not None and i < len(cells):
            return cells[i].strip().strip('"')
        return default

    kosu_no = 0
    for line in lines[1:]:
        cells = [c.strip().strip('"') for c in line.split(sep)]
        if len(cells) < 4:
            continue

        kn = gc(cells, "kosu_no", "")
        if kn and kn.isdigit():
            kosu_no = int(kn)
        elif kosu_no == 0:
            kosu_no = 1

        sira_txt = gc(cells, "sira", "")
        if not sira_txt or not re.match(r"^\d+$", sira_txt):
            continue
        sira = int(sira_txt)

        at_adi = gc(cells, "at", "").upper()
        if not at_adi:
            continue

        derece = gc(cells, "derece", "")
        mesafe = gc(cells, "mesafe", "")
        msf_num = 0
        m = re.search(r"(\d{3,5})", mesafe)
        if m:
            msf_num = int(m.group(1))

        hiz_ms = None
        d_sec = derece_to_sec(derece)
        if d_sec and msf_num:
            hiz_ms = round(msf_num / d_sec, 3)

        rows.append({
            "kosu_no":  kosu_no,
            "sira":     sira,
            "at":       at_adi,
            "jokey":    gc(cells, "jokey"),
            "kilo":     gc(cells, "kilo"),
            "yas":      gc(cells, "yas"),
            "derece":   derece,
            "msf":      str(msf_num) if msf_num else "",
            "pist":     gc(cells, "pist"),
            "ganyan":   gc(cells, "ganyan"),
            "agf":      gc(cells, "agf"),
            "gny":      gc(cells, "gny"),
            "fark":     gc(cells, "fark"),
            "hp":       gc(cells, "hp"),
            "antrenor": gc(cells, "antrenor"),
            "hiz_ms":   hiz_ms,
            "kaynak":   "TJK-CSV",
        })

    return rows


def _parse_tjk_html(html: str, sehir: str) -> list:
    """TJK HTML yarış sonuçları sayfasını parse et."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    kosu_no = 0

    for table in soup.find_all("table"):
        header_txt = table.get_text(" ")
        has_sira = any(k in header_txt for k in ("Sıra", "S.", "ira"))
        has_derece = "Derece" in header_txt or "erece" in header_txt
        if not (has_sira or has_derece):
            continue

        # Koşu no tespiti — tablo öncesi elementlerden
        for sib in table.find_all_previous(limit=15):
            t = sib.get_text(" ", strip=True)
            nm = re.search(r"(\d{1,2})\s*\.\s*(?:Koşu|koşu|\d{2}:\d{2})", t)
            if nm:
                kosu_no = int(nm.group(1))
                break
        if kosu_no == 0:
            kosu_no += 1

        # Mesafe + pist tespiti
        mesafe_kosu = ""
        pist_kosu = ""
        for sib in table.find_all_previous(limit=20):
            t = sib.get_text(" ", strip=True)
            mm = re.search(r"(\d{3,5})\s*(Kum|Çim|Sentetik|Toprak)?", t)
            if mm:
                mesafe_kosu = mm.group(1)
                pist_kosu = mm.group(2) or ""
                break

        # Header mapping
        hdr_row = None
        hdr_map = {}
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["th","td"])]
            if any(k in cells for k in ("S","Sıra","S.")) and any(k in " ".join(cells) for k in ("At","Derece","erece")):
                hdr_map = {v: i for i, v in enumerate(cells)}
                hdr_row = tr
                break

        def hc(cells, *keys):
            for k in keys:
                i = hdr_map.get(k)
                if i is not None and i < len(cells):
                    return cells[i]
            return ""

        for tr in table.find_all("tr"):
            if tr is hdr_row:
                continue
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]

            sira_txt = hc(cells, "S", "Sıra", "S.") or cells[0]
            if not sira_txt or not re.match(r"^\d+$", sira_txt.strip()):
                continue
            sira = int(sira_txt.strip())

            at_adi = hc(cells, "At Adı", "At", "At İsmi") or ""
            at_adi = re.sub(r"\s*(SKG|SK|DB|YP|KG|BP|KBK)\s*", " ", at_adi).strip().upper()
            if not at_adi:
                continue

            derece = hc(cells, "Derece", "D.")
            msf_val = mesafe_kosu
            hiz_ms = None
            d_sec = derece_to_sec(derece)
            if d_sec and msf_val:
                try:
                    hiz_ms = round(int(msf_val) / d_sec, 3)
                except:
                    pass

            rows.append({
                "kosu_no":  kosu_no,
                "sira":     sira,
                "at":       at_adi,
                "jokey":    hc(cells, "Jokey", "J."),
                "kilo":     hc(cells, "Kilo", "Kg"),
                "yas":      hc(cells, "Yaş", "Y"),
                "derece":   derece,
                "msf":      msf_val,
                "pist":     pist_kosu,
                "ganyan":   hc(cells, "Ganyan", "G."),
                "agf":      hc(cells, "AGF"),
                "gny":      hc(cells, "GNY"),
                "fark":     hc(cells, "Fark", "F."),
                "hp":       hc(cells, "HP", "Hnd"),
                "antrenor": hc(cells, "Antrenör", "Ant."),
                "hiz_ms":   hiz_ms,
                "kaynak":   "TJK-HTML",
            })

    return rows


# ─── Tempo & Hız Analizi ─────────────────────────────────

def analiz_tempo(sonuc_rows: list) -> dict:
    """
    Yarış sonuçlarından detaylı tempo analizi yap.
    Her koşu ve her at için:
    - Hız (m/s)
    - Tempo rating (koşu ortalamasına göre)
    - Sektör tahmini (galop verisinden)
    - Pace figür (normalize edilmiş hız puanı)
    """
    if not sonuc_rows:
        return {"kosular": {}, "atlar": {}, "yildizlar": []}

    from collections import defaultdict

    kosu_data = defaultdict(list)
    for r in sonuc_rows:
        kosu_data[r["kosu_no"]].append(r)

    kosu_analiz = {}
    at_analiz = defaultdict(list)
    tum_hizlar = []

    for kno, atlar in kosu_data.items():
        hizlar = [r["hiz_ms"] for r in atlar if r.get("hiz_ms")]
        if not hizlar:
            continue

        ort_hiz = sum(hizlar) / len(hizlar)
        en_iyi = max(hizlar)
        en_kotu = min(hizlar)
        std = (sum((h - ort_hiz) ** 2 for h in hizlar) / max(len(hizlar), 1)) ** 0.5

        # Tempo: hızlı mı yavaş mı koşuldu?
        # Genel standart: 1000m kum ~16.0 m/s, çim ~16.5 m/s
        msf = 0
        for r in atlar:
            try:
                msf = int(re.sub(r"[^\d]", "", str(r.get("msf", "") or "")))
                break
            except:
                pass

        if msf <= 1200:
            tempo_tip = "Sprint"
        elif msf <= 1600:
            tempo_tip = "Orta"
        elif msf <= 2000:
            tempo_tip = "Uzun-Orta"
        else:
            tempo_tip = "Uzun"

        # Tempo hız kategorisi
        if ort_hiz >= 16.5:
            tempo_kat = "🔥 ÇOK HIZLI"
        elif ort_hiz >= 15.8:
            tempo_kat = "⚡ HIZLI"
        elif ort_hiz >= 15.0:
            tempo_kat = "🟢 NORMAL"
        elif ort_hiz >= 14.2:
            tempo_kat = "🟡 YAVAŞ"
        else:
            tempo_kat = "🐌 ÇOK YAVAŞ"

        kosu_analiz[kno] = {
            "kosu_no":   kno,
            "at_sayisi": len(atlar),
            "msf":       msf,
            "pist":      atlar[0].get("pist", ""),
            "tempo_tip": tempo_tip,
            "tempo_kat": tempo_kat,
            "ort_hiz":   round(ort_hiz, 3),
            "en_iyi":    round(en_iyi, 3),
            "en_kotu":   round(en_kotu, 3),
            "std":       round(std, 3),
        }

        # Her at için pace figür hesapla
        for r in atlar:
            hiz = r.get("hiz_ms")
            if not hiz:
                continue

            # Pace figür: 100 × (at_hız / koşu_ort_hız)
            pace_fig = round(hiz / ort_hiz * 100, 1) if ort_hiz > 0 else 0

            # Tempo rating: koşu std sapmasına göre kaç sigma üstünde
            tempo_rtg = round((hiz - ort_hiz) / max(std, 0.01), 2)

            # Hız yüzdelik dilim (koşu içinde)
            hiz_rank = sum(1 for h in hizlar if h >= hiz)
            hiz_pct = round(hiz_rank / len(hizlar) * 100, 1)

            # Tahmini sektör hızları (uniform dağılım varsayımı)
            d_sec = derece_to_sec(r.get("derece", ""))
            sektorler = {}
            if d_sec and msf:
                # 200m'lik sektörler
                n_sektor = msf // 200
                if n_sektor >= 2:
                    sektor_sure = d_sec / n_sektor
                    # Başlangıç yavaş, orta stabil, son değişken
                    for si in range(n_sektor):
                        pct = si / max(n_sektor - 1, 1)
                        # Basit model: ilk %10 yavaş, son %10 sprinter bonus
                        mod = 1.02 if si == 0 else (0.97 if si == n_sektor - 1 else 1.0)
                        s_sure = sektor_sure * mod
                        s_hiz = round(200 / s_sure, 2) if s_sure > 0 else 0
                        sektorler[f"{(si + 1) * 200}m"] = {
                            "sure": round(s_sure, 2),
                            "hiz": s_hiz,
                        }

            entry = {
                "kosu_no":    r["kosu_no"],
                "sira":       r["sira"],
                "at":         r["at"],
                "derece":     r.get("derece", ""),
                "hiz_ms":     hiz,
                "pace_fig":   pace_fig,
                "tempo_rtg":  tempo_rtg,
                "hiz_pct":    hiz_pct,
                "sektorler":  sektorler,
                "msf":        msf,
                "pist":       r.get("pist", ""),
                "kilo":       r.get("kilo", ""),
                "jokey":      r.get("jokey", ""),
                "fark":       r.get("fark", ""),
                "ganyan":     r.get("ganyan", ""),
                "antrenor":   r.get("antrenor", ""),
                "kaynak":     r.get("kaynak", ""),
            }
            at_analiz[r["at"]].append(entry)
            tum_hizlar.append(entry)

    # Yıldız atları bul (pace figür >= 103 veya tempo rating >= 1.5)
    yildizlar = []
    for entry in tum_hizlar:
        yildiz = ""
        pf = entry["pace_fig"]
        tr = entry["tempo_rtg"]
        sira = entry["sira"]

        if pf >= 108 and sira == 1:
            yildiz = "★★★🔥"
        elif pf >= 105 and sira <= 2:
            yildiz = "★★★"
        elif pf >= 103 and sira <= 3:
            yildiz = "★★"
        elif pf >= 101 and sira <= 3:
            yildiz = "★"
        elif tr >= 2.0:
            yildiz = "★★🌟"
        elif tr >= 1.5:
            yildiz = "★🌟"
        elif tr >= 1.0:
            yildiz = "✨"

        if yildiz:
            entry["yildiz"] = yildiz
            yildizlar.append(entry)

    yildizlar.sort(key=lambda x: x["pace_fig"], reverse=True)

    return {
        "kosular": kosu_analiz,
        "atlar": dict(at_analiz),
        "yildizlar": yildizlar,
        "tum": tum_hizlar,
    }


# ─── Ana Uygulama ─────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"🏇  At Yarışı Pro Analiz  {VERSION}")
        self.geometry("1700x960")
        self.minsize(1200,720)
        self.configure(bg=BG)
        # State
        self.bulten     = None    # scrape_bulten sonucu
        self.sel_kosu   = None    # seçili koşu dict
        self.galoplar   = []      # scrape_galoplar sonucu
        self.galop_an   = {}      # analiz_galop sonucu
        self.profiller  = {}      # {at: scrape_profil}
        self.stiller    = {}      # {at: analiz_stil}
        self.performlar = {}      # {at: analiz_perform}
        self.jokey_stats= {}      # {jokey: stats}
        self.tjk_rows   = []      # TJK sonuç satırları
        self.tjk_analiz = {}      # analiz_tempo sonucu
        self._ready     = False
        self._conn_ok   = True    # bağlantı durumu
        self._build_ui()
        self._bind_shortcuts()
        threading.Thread(target=self._setup, daemon=True).start()
    def _bind_shortcuts(self):
        """Klavye kısayolları."""
        self.bind("<F5>", lambda e: self.cek_bulten())
        self.bind("<F6>", lambda e: self.analiz_kosu())
        self.bind("<Control-e>", lambda e: self.export_excel())
        self.bind("<Left>", lambda e: self._onceki_gun())
        self.bind("<Right>", lambda e: self._sonraki_gun())
    # ── Setup ─────────────────────────────────────────────
    def _setup(self):
        global _tess, _pop
        self._st("Sistem kontrol ediliyor…")
        p = ensure_pop(self._st)
        if p is not None: _pop = p or None
        t = ensure_tess(self._st)
        if t: _tess = t
        ensure_bs4(self._st)
        self._ready = True
        self._check_conn()
        self._st("Hazır  —  Tarih ve şehir seçip Bülten Çek butonuna basın.")
    # ── UI ────────────────────────────────────────────────
    def _build_ui(self):
        self._style()
        self._topbar()
        self._toolbar()
        self._main_area()
        self._statusbar()
    def _style(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("Treeview", background=PANEL, foreground=TEXT,
                    fieldbackground=PANEL, rowheight=24, font=F_N, borderwidth=0)
        s.configure("Treeview.Heading", background=CARD, foreground=TEXT,
                    font=F_S, relief="flat")
        s.map("Treeview",
              background=[("selected","#1A4A8A")],
              foreground=[("selected",TEXT)])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=DIM,
                    font=F_S, padding=(12,6))
        s.map("TNotebook.Tab",
              background=[("selected",ACCENT)],
              foreground=[("selected",TEXT)])
        s.configure("Horizontal.TProgressbar",
                    background=ACCENT, troughcolor=PANEL)
    def _topbar(self):
        tb = tk.Frame(self, bg="#0A1520", height=48)
        tb.pack(fill="x"); tb.pack_propagate(False)
        tk.Label(tb, text=f"🏇  AT YARIŞI PRO ANALİZ  {VERSION}",
                 font=("Segoe UI",14,"bold"), bg="#0A1520", fg=GOLD).pack(side="left", padx=16)
        tk.Label(tb, text="Yenibeygir  •  TJK Tempo  •  Pace Figür  •  Accurace",
                 font=F_XS, bg="#0A1520", fg=DIM).pack(side="left", padx=8)
        # Bağlantı durumu
        self.conn_var = tk.StringVar(value="⏳")
        self.conn_lbl = tk.Label(tb, textvariable=self.conn_var,
                 font=F_XS, bg="#0A1520", fg=GREEN)
        self.conn_lbl.pack(side="right", padx=8)
        # Önbellek temizle
        tk.Button(tb, text="🗑 Önbellek", command=self._clear_cache,
                  bg="#0A1520", fg=DIM, font=F_XS, relief="flat",
                  cursor="hand2", activebackground="#0A1520", activeforeground=TEXT
                  ).pack(side="right", padx=4)
        # Saat
        self.clock_var = tk.StringVar()
        tk.Label(tb, textvariable=self.clock_var,
                 font=F_N, bg="#0A1520", fg=DIM).pack(side="right", padx=16)
        self._tick()
    def _tick(self):
        self.clock_var.set(datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))
        self.after(1000, self._tick)
    def _clear_cache(self):
        """Önbellek klasörünü temizle."""
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR, ignore_errors=True)
            self._st("✓ Önbellek temizlendi")
        else:
            self._st("Önbellek zaten boş")
    def _check_conn(self):
        """Arka planda bağlantı kontrolü."""
        def worker():
            try:
                fetch("https://yenibeygir.com", timeout=8, retries=1)
                self._conn_ok = True
                self.after(0, lambda: self.conn_var.set("🟢 Bağlı"))
                self.after(0, lambda: self.conn_lbl.config(fg=GREEN))
            except Exception:
                self._conn_ok = False
                self.after(0, lambda: self.conn_var.set("🔴 Bağlantı Yok"))
                self.after(0, lambda: self.conn_lbl.config(fg=RED))
        threading.Thread(target=worker, daemon=True).start()
    def _toolbar(self):
        bar = tk.Frame(self, bg=CARD, height=46)
        bar.pack(fill="x"); bar.pack_propagate(False)
        def lbl(t):
            tk.Label(bar, text=t, font=F_XS, bg=CARD, fg=DIM).pack(side="left", padx=(12,2))
        def entry(w=12, default=""):
            e = tk.Entry(bar, bg=BG, fg=TEXT, insertbackground=TEXT,
                         font=F_N, relief="flat", width=w,
                         highlightthickness=1, highlightbackground=BORDER)
            if default: e.insert(0, default)
            e.pack(side="left", padx=(0,6), ipady=4)
            return e
        def btn(t, cmd, bg=ACCENT, w=None):
            kw = {"width": w} if w else {}
            b = tk.Button(bar, text=t, command=cmd, bg=bg, fg=TEXT,
                          font=F_S, relief="flat", cursor="hand2",
                          activebackground=bg, activeforeground=TEXT,
                          padx=10, pady=6, **kw)
            b.pack(side="left", padx=3)
            return b
        lbl("Tarih:")
        self.e_tarih = entry(12, bugun())
        lbl("Şehir:")
        self.sehir_var = tk.StringVar(value="istanbul")
        cb = ttk.Combobox(bar, textvariable=self.sehir_var,
                          values=SEHIRLER, state="readonly",
                          font=F_N, width=12)
        cb.pack(side="left", padx=(0,6))
        btn("📥  BÜLTENİ ÇEK [F5]", self.cek_bulten, bg="#1A5276")
        # Önceki / Sonraki gün
        btn("◀", self._onceki_gun, bg="#243040", w=3)
        btn("▶", self._sonraki_gun, bg="#243040", w=3)
        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)
        lbl("Koşu:")
        self.kosu_var = tk.StringVar()
        self.kosu_cb  = ttk.Combobox(bar, textvariable=self.kosu_var,
                                      state="readonly", font=F_N, width=40)
        self.kosu_cb.pack(side="left", padx=(0,6))
        self.kosu_cb.bind("<<ComboboxSelected>>", lambda e: self._sec_kosu())
        btn("🐎  KOŞUYU ANALİZ ET [F6]", self.analiz_kosu, bg="#1A5C2A")
        btn("⚡ Tüm Koşuları Analiz", self._analiz_tum_kosular, bg="#6C3483")
        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)
        self.prog = ttk.Progressbar(bar, mode="indeterminate", length=120)
        self.prog.pack(side="left", padx=4)
        # Export
        btn("💾 Excel", self.export_excel, bg="#145A32")
        btn("📄 CSV",   self.export_csv,   bg="#1A4F6E")
    def _main_area(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=6, pady=4)
        # Sol: koşu atları listesi (250px)
        self._build_left(main)
        # Sağ: sekmeler
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_tabs(right)
    def _statusbar(self):
        self.st_var = tk.StringVar(value="Hazırlanıyor…")
        bar = tk.Frame(self, bg="#0A1520", height=24)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.st_var,
                 font=F_XS, bg="#0A1520", fg=DIM).pack(side="left", padx=10)
        # Kısayol ipuçları
        tk.Label(bar, text="F5: Bülten  |  F6: Analiz  |  ◀▶: Gün  |  Ctrl+E: Excel",
                 font=F_XS, bg="#0A1520", fg="#3A4A5A").pack(side="right", padx=10)
    def _build_left(self, parent):
        lf = tk.Frame(parent, bg=PANEL, width=260,
                      highlightthickness=1, highlightbackground=BORDER)
        lf.pack(side="left", fill="y", padx=(0,6))
        lf.pack_propagate(False)
        tk.Label(lf, text="KOŞU ATLARI", font=F_S, bg=PANEL, fg=DIM
                 ).pack(anchor="w", padx=8, pady=(8,4))
        # Koşu özet kartı
        self.kosu_info = tk.Label(lf, text="—", font=F_XS,
                                   bg=CARD, fg=GOLD, wraplength=240,
                                   justify="left", padx=8, pady=6)
        self.kosu_info.pack(fill="x", padx=6, pady=(0,4))
        # At listesi
        lf2 = tk.Frame(lf, bg=BG,
                        highlightthickness=1, highlightbackground=BORDER)
        lf2.pack(fill="both", expand=True, padx=6, pady=(0,4))
        vsb = ttk.Scrollbar(lf2, orient="vertical")
        self.at_tree = ttk.Treeview(lf2, columns=("no","at","agf","son10","hnd","taki"),
                                     show="headings", yscrollcommand=vsb.set,
                                     selectmode="browse")
        vsb.config(command=self.at_tree.yview)
        vsb.pack(side="right", fill="y")
        self.at_tree.pack(fill="both", expand=True)
        for col, w, txt in [
            ("no",   30, "#"),
            ("at",  120, "At Adı"),
            ("agf",  35, "AGF"),
            ("son10",80, "Son 10"),
            ("hnd",  35, "Hnd"),
            ("taki", 60, "Takı"),
        ]:
            self.at_tree.heading(col, text=txt)
            self.at_tree.column(col, width=w, anchor="center", minwidth=w)
        self.at_tree.tag_configure("good", background="#1A3020", foreground=GREEN)
        self.at_tree.tag_configure("mid",  background="#2A2A10", foreground=YELLOW)
        self.at_tree.tag_configure("odd",  background="#162030")
        self.at_tree.tag_configure("ev",   background=PANEL)
        # Filtre
        ff = tk.Frame(lf, bg=PANEL)
        ff.pack(fill="x", padx=6, pady=(0,4))
        tk.Label(ff, text="Filtre:", font=F_XS, bg=PANEL, fg=DIM).pack(side="left")
        self.at_filter = tk.Entry(ff, bg=BG, fg=TEXT, insertbackground=TEXT,
                                   font=F_XS, relief="flat", width=14,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.at_filter.pack(side="left", padx=4, ipady=2)
        self.at_filter.bind("<KeyRelease>", lambda e: self._filter_atlar())
    def _build_tabs(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill="both", expand=True)
        tabs = [
            ("  📊  Genel Analiz  ",    self._build_genel_tab),
            ("  🐎  Galop Detay  ",     self._build_galop_tab),
            ("  🎨  Koşu Stili  ",      self._build_stil_tab),
            ("  📈  Performans Trendi  ",self._build_trend_tab),
            ("  📋  Yarış Sonuçları  ",  self._build_sonuc_tab),
            ("  🔄  Karşılaştırma  ",   self._build_karsi_tab),
            ("  ⚡  Son 2 Yarış Hız  ",  self._build_son2hiz_tab),
            ("  👁  Takip Atları  ",     self._build_takip_tab),
            ("  🎬  Yarış Senaryosu  ", self._build_senaryo_tab),
            ("  🏁  TJK Tempo Analizi  ", self._build_tjk_tab),
        ]
        self.tab_frames = {}
        for name, builder in tabs:
            f = tk.Frame(self.nb, bg=BG)
            self.nb.add(f, text=name)
            builder(f)
            self.tab_frames[name] = f
    # ── Tab: Genel Analiz ────────────────────────────────
    def _build_genel_tab(self, parent):
        # Podium
        self.pod = tk.Frame(parent, bg=BG)
        self.pod.pack(fill="x", padx=8, pady=(8,4))
        tk.Label(parent, text="Tüm Atlar — Birleşik Skor (Galop + Stil + Performans + TJK Pace)",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", padx=8, pady=(0,4))
        self.tree_genel = self._make_tree(parent)
    # ── Tab: Galop Detay ─────────────────────────────────
    def _build_galop_tab(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=8, pady=(6,4))
        tk.Label(top, text="At:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.g_horse_var = tk.StringVar(value="Tümü")
        self.g_horse_cb  = ttk.Combobox(top, textvariable=self.g_horse_var,
                                         state="readonly", width=26, font=F_N)
        self.g_horse_cb.pack(side="left", padx=6)
        self.g_horse_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_galop_detail())
        tk.Label(top, text="Son N galop:", font=F_XS, bg=BG, fg=DIM).pack(side="left", padx=(12,0))
        self.g_n_var = tk.StringVar(value="4")
        ttk.Combobox(top, textvariable=self.g_n_var,
                     values=["4","5","8","10","Tümü"],
                     state="readonly", width=6, font=F_N
                     ).pack(side="left", padx=4)
        tk.Button(top, text="Göster", command=self._refresh_galop_detail,
                  bg=BLUE, fg=TEXT, font=F_S, relief="flat",
                  padx=8, pady=4).pack(side="left", padx=4)
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        # Sol: tablo
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        self.tree_galop = self._make_tree(lp)
        # Sağ: bar grafik
        rp = tk.Frame(mid, bg=BG, width=380)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="En İyi 400m Karşılaştırması",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_galop = tk.Canvas(rp, bg=PANEL,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.cv_galop.pack(fill="both", expand=True)
        self.cv_galop.bind("<Configure>", lambda e: self._draw_galop_bar())
    # ── Tab: Koşu Stili ──────────────────────────────────
    def _build_stil_tab(self, parent):
        self.stil_status = tk.StringVar(value="Analiz çalıştırınca otomatik dolar…")
        tk.Label(parent, textvariable=self.stil_status,
                 font=F_S, bg=BG, fg=TEAL).pack(anchor="w", padx=8, pady=(8,4))
        self.stil_cards = tk.Frame(parent, bg=BG)
        self.stil_cards.pack(fill="x", padx=8, pady=(0,6))
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=8, pady=(0,4))
        tk.Label(top, text="At:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.stil_horse_var = tk.StringVar(value="Tümü")
        self.stil_horse_cb  = ttk.Combobox(top, textvariable=self.stil_horse_var,
                                            state="readonly", width=28, font=F_N)
        self.stil_horse_cb.pack(side="left", padx=6)
        self.stil_horse_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_stil_detail())
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(lp, text="Koşu Stili Özeti",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_stil = self._make_tree(lp)
        rp = tk.Frame(mid, bg=BG, width=420)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Yarış Geçmişi",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_stil_detail = self._make_tree(rp)
    # ── Tab: Performans Trendi ───────────────────────────
    def _build_trend_tab(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=8, pady=(6,4))
        tk.Label(top, text="At:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.trend_horse_var = tk.StringVar(value="Tümü")
        self.trend_horse_cb  = ttk.Combobox(top, textvariable=self.trend_horse_var,
                                             state="readonly", width=28, font=F_N)
        self.trend_horse_cb.pack(side="left", padx=6)
        self.trend_horse_cb.bind("<<ComboboxSelected>>", lambda e: self._draw_trend_chart())
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(lp, text="Performans Tablosu",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_trend = self._make_tree(lp)
        rp = tk.Frame(mid, bg=BG, width=450)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Hız Trend Grafiği (m/s)",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_trend = tk.Canvas(rp, bg=PANEL,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.cv_trend.pack(fill="both", expand=True)
        self.cv_trend.bind("<Configure>", lambda e: self._draw_trend_chart())
    # ── Tab: Yarış Sonuçları ─────────────────────────────
    def _build_sonuc_tab(self, parent):
        ctrl = tk.Frame(parent, bg=BG)
        ctrl.pack(fill="x", padx=8, pady=(8,4))
        tk.Button(ctrl, text="📥  SONUÇLARI ÇEK",
                  command=self._cek_sonuclar,
                  bg="#1A5276", fg=TEXT, font=F_M, relief="flat",
                  cursor="hand2", padx=14, pady=7).pack(side="left")
        tk.Label(ctrl, text="Yıldız eşiği (hız ind.):",
                 font=F_XS, bg=BG, fg=DIM).pack(side="left", padx=(16,2))
        self.yildiz_esik_var = tk.StringVar(value="30")
        ttk.Combobox(ctrl, textvariable=self.yildiz_esik_var,
                     values=["10","20","30","40","50","60"],
                     state="readonly", width=5, font=F_N).pack(side="left", padx=4)
        tk.Button(ctrl, text="⭐ Yıldızla", command=self._yildizla,
                  bg="#7D6608", fg=TEXT, font=F_S, relief="flat",
                  cursor="hand2", padx=8, pady=5).pack(side="left", padx=4)
        self.sonuc_info = tk.StringVar(value="")
        tk.Label(ctrl, textvariable=self.sonuc_info,
                 font=F_XS, bg=BG, fg=TEAL).pack(side="left", padx=12)
        kosu_row = tk.Frame(parent, bg=BG)
        kosu_row.pack(fill="x", padx=8, pady=(0,4))
        tk.Label(kosu_row, text="Koşu:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.sonuc_kosu_var = tk.StringVar(value="Tümü")
        self.sonuc_kosu_cb  = ttk.Combobox(kosu_row,
                                            textvariable=self.sonuc_kosu_var,
                                            state="readonly", width=50, font=F_N)
        self.sonuc_kosu_cb.pack(side="left", padx=6)
        self.sonuc_kosu_cb.bind("<<ComboboxSelected>>",
                                lambda e: self._filtrele_sonuclar())
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        self.tree_sonuc = self._make_tree(lp)
        rp = tk.Frame(mid, bg=BG, width=380)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Hız Dagilimi (m/s)",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_sonuc = tk.Canvas(rp, bg=PANEL,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.cv_sonuc.pack(fill="both", expand=True)
        self.cv_sonuc.bind("<Configure>", lambda e: self._draw_sonuc_chart())
    def _scrape_sonuclar(self, tarih, sehir):
        from bs4 import BeautifulSoup
        url  = f"https://yenibeygir.com/{tarih_url(tarih)}/{sehir_url(sehir)}/sonuclar"
        html = fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        tum_rows = []
        kosu_no  = 0
        kosu_meta = {}
        for elem in soup.find_all(["p","div","h2","h3","table","span"]):
            tag = elem.name
            txt = elem.get_text(" ", strip=True)
            if tag in ("p","div","span","h2","h3"):
                saat_m = re.search(r"(\d{2}:\d{2})", txt)
                msf_m  = re.search(r"(\d{3,5})\s*(Kum|Cim|Sentetik|Toprak)?", txt)
                para_m = re.search(r"[tT][lL][^\d]*(\d[\d\.\,]+)", txt)
                no_m   = re.search(r"\b(\d{1,2})\s*\.\s*(?:\d{2}:\d{2})", txt)
                if no_m and (saat_m or msf_m):
                    kosu_no = int(no_m.group(1))
                    kosu_meta[kosu_no] = {
                        "saat": saat_m.group(1) if saat_m else "",
                        "msf":  msf_m.group(1)  if msf_m  else "",
                        "pist": msf_m.group(2)  if msf_m and msf_m.group(2) else "",
                    }
                continue
            if tag == "table":
                header_txt = elem.get_text(" ")
                has_sira   = "Sıra" in header_txt or "ira" in header_txt
                has_derece = "Derece" in header_txt
                if not (has_sira and has_derece):
                    continue
                kosu_no += 1
                meta = kosu_meta.get(kosu_no, {})
                for tr in elem.find_all("tr"):
                    tds   = tr.find_all("td")
                    if len(tds) < 6: continue
                    cells = [td.get_text(" ", strip=True) for td in tds]
                    sira_txt = cells[0].strip()
                    if not sira_txt or not re.match(r"^\d+$", sira_txt): continue
                    sira = int(sira_txt)
                    at_id = at_url = ""
                    for a in tr.select("a[href*='/at/']"):
                        href = a.get("href","")
                        m2   = re.match(r".*/at/(\d+)/([^\s?#\"']+)", href)
                        if m2:
                            at_id  = m2.group(1)
                            at_url = f"https://yenibeygir.com/at/{at_id}/{m2.group(2)}"
                            break
                    at_adi = ""
                    if at_url:
                        slug   = at_url.rstrip("/").split("/")[-1]
                        at_adi = slug.replace("-"," ").upper()
                    at_cell = tds[1].get_text(" ", strip=True) if len(tds)>1 else ""
                    takiler = re.findall(r"\b(SKG|SK|DB|YP|KG|BP)\b", at_cell)
                    taki    = " ".join(dict.fromkeys(takiler))
                    derece  = cells[8]  if len(cells)>8  else ""
                    hiz_ind = cells[9]  if len(cells)>9  else ""
                    gny     = cells[10] if len(cells)>10 else ""
                    agf     = cells[11] if len(cells)>11 else ""
                    fark    = cells[12] if len(cells)>12 else ""
                    hiz_num = None
                    hm = re.search(r"\(?([+-]?\d+)\)?", str(hiz_ind))
                    if hm:
                        try: hiz_num = int(hm.group(1))
                        except: pass
                    msf_val = meta.get("msf","")
                    hiz_ms  = None
                    d_sec   = derece_to_sec(derece)
                    if d_sec and msf_val:
                        try: hiz_ms = round(int(msf_val) / d_sec, 3)
                        except: pass
                    tum_rows.append({
                        "kosu_no": kosu_no,
                        "sira":    sira,
                        "at":      at_adi,
                        "at_id":   at_id,
                        "at_url":  at_url,
                        "taki":    taki,
                        "yas":     cells[2].strip() if len(cells)>2 else "",
                        "kilo":    cells[3].strip() if len(cells)>3 else "",
                        "jokey":   cells[4].strip() if len(cells)>4 else "",
                        "klv":     cells[7].strip() if len(cells)>7 else "",
                        "derece":  derece,
                        "hiz_ind": hiz_num,
                        "gny":     gny,
                        "agf":     agf,
                        "fark":    fark,
                        "msf":     msf_val,
                        "pist":    meta.get("pist",""),
                        "hiz_ms":  hiz_ms,
                        "yildiz":  "",
                    })
        return tum_rows
    def _cek_sonuclar(self):
        if not BS4:
            messagebox.showerror("Hata","beautifulsoup4 gerekli."); return
        tarih = self.e_tarih.get().strip()
        sehir = self.sehir_var.get().strip()
        if not tarih or not sehir:
            messagebox.showwarning("Uyari","Tarih ve sehir secin."); return
        threading.Thread(target=self._sonuc_worker, args=(tarih,sehir), daemon=True).start()
    def _sonuc_worker(self, tarih, sehir):
        self.prog.start(10)
        self._st(f"Sonuclar cekiliyor: {tarih} {sehir}...")
        try:
            rows = self._scrape_sonuclar(tarih, sehir)
            if not rows:
                self.after(0, lambda: messagebox.showwarning("Sonuc Yok",
                    "Sonuc bulunamadi.\n• Kosu bitti mi?\n• Tarih/sehir dogru mu?"))
                return
            self._sonuc_rows = rows
            self.after(0, lambda: self._on_sonuclar(rows))
            self._st(f"OK {len(rows)} at sonucu")
        except Exception as e:
            self.after(0, lambda e2=str(e): messagebox.showerror("Hata", f"Sonuc:\n{e2}"))
            self._st(f"HATA: {e}")
        finally:
            self.prog.stop()
    def _on_sonuclar(self, rows):
        kosular = sorted(set(r["kosu_no"] for r in rows))
        vals    = ["Tumu"] + [f"{k}. Kosu" for k in kosular]
        self.sonuc_kosu_cb["values"] = vals
        self.sonuc_kosu_var.set("Tumu")
        self._yildizla()
        self._filtrele_sonuclar()
        self.sonuc_info.set(f"{len(rows)} at  |  {len(kosular)} kosu")
    def _yildizla(self):
        if not hasattr(self,"_sonuc_rows"): return
        try: esik = int(self.yildiz_esik_var.get())
        except: esik = 30
        kosu_hizlar = defaultdict(list)
        for r in self._sonuc_rows:
            if r["hiz_ms"]: kosu_hizlar[r["kosu_no"]].append(r["hiz_ms"])
        kosu_stats = {}
        for k, vals in kosu_hizlar.items():
            ort = sum(vals)/len(vals)
            std = (sum((v-ort)**2 for v in vals)/max(len(vals),1))**0.5
            kosu_stats[k] = {"ort": ort, "std": max(std, 0.01)}
        for r in self._sonuc_rows:
            yildiz = ""
            hiz    = r.get("hiz_ind")
            hiz_ms = r.get("hiz_ms")
            sira   = r.get("sira", 99)
            kno    = r["kosu_no"]
            stats  = kosu_stats.get(kno, {})
            if isinstance(hiz, int):
                if hiz >= esik + 20:  yildiz += "YYYYY"
                elif hiz >= esik + 10: yildiz += "YYYY"
                elif hiz >= esik:      yildiz += "YYY"
            if hiz_ms and stats:
                ort = stats["ort"]; std = stats["std"]
                if hiz_ms >= ort + std and sira <= 3:
                    yildiz += "S"
                elif hiz_ms >= ort + std*0.5:
                    yildiz += "P"
            # Emoji donusum
            yildiz = (yildiz
                .replace("YYYYYS","★★★🌟")
                .replace("YYYYP","★★★✨")
                .replace("YYYYY","★★★")
                .replace("YYYYS","★★🌟")
                .replace("YYYYP","★★✨")
                .replace("YYYY","★★")
                .replace("YYYS","★🌟")
                .replace("YYYP","★✨")
                .replace("YYY","★")
                .replace("S","🌟").replace("P","✨"))
            r["yildiz"] = yildiz
        self._filtrele_sonuclar()
        n_star = sum(1 for r in self._sonuc_rows if r.get("yildiz"))
        self.sonuc_info.set(f"{len(self._sonuc_rows)} at  |  {n_star} yildizli  |  esik: hiz>={esik}")
    def _filtrele_sonuclar(self):
        if not hasattr(self,"_sonuc_rows"): return
        secim = self.sonuc_kosu_var.get()
        rows  = self._sonuc_rows
        if secim and secim not in ("Tumu","Tümü"):
            m = re.search(r"(\d+)", secim)
            if m: rows = [r for r in rows if r["kosu_no"] == int(m.group(1))]
        df = pd.DataFrame(rows)
        if df.empty: return
        show = ["yildiz","kosu_no","sira","at","taki","derece",
                "hiz_ms","hiz_ind","kilo","jokey","msf","pist","gny","agf","fark"]
        show = [c for c in show if c in df.columns]
        df   = df.sort_values(["kosu_no","sira"]).reset_index(drop=True)
        def tag_fn(row, idx):
            y = str(row.get("yildiz",""))
            s = row.get("sira",99)
            try: s = int(s)
            except: s = 99
            if "★★★" in y or "🌟" in y: return "g1"
            if "★★" in y:  return "g2"
            if "★" in y:   return "g3"
            if s == 1:  return "up"
            if s <= 3:  return "st"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_sonuc, df[show], tag_fn=tag_fn)
        self._draw_sonuc_chart()
    def _draw_sonuc_chart(self):
        cv = self.cv_sonuc; cv.delete("all")
        W  = cv.winfo_width() or 380; H = cv.winfo_height() or 420
        if not hasattr(self,"_sonuc_rows") or W < 80: return
        secim = self.sonuc_kosu_var.get()
        rows  = self._sonuc_rows
        if secim and secim not in ("Tumu","Tümü"):
            m = re.search(r"(\d+)", secim)
            if m: rows = [r for r in rows if r["kosu_no"] == int(m.group(1))]
        data = [(r["at"], r["hiz_ms"], r.get("yildiz",""), r["sira"])
                for r in rows if r.get("hiz_ms")]
        if not data: return
        data.sort(key=lambda x: x[1], reverse=True)
        data = data[:14]
        PL,PR,PT,PB = 52,14,40,68
        vals = [v for _,v,_,_ in data]
        mn = max(0, min(vals)-0.2); mx = max(vals)+0.2; rng = max(mx-mn,0.1)
        n  = len(data); bw = max(10, int((W-PL-PR)/n)-4); xs=(W-PL-PR)/n
        cv.create_text(W//2,20,text="Hiz m/s — En Hizlidan Yavasa",fill=TEXT,font=F_S)
        for frac in [0,0.25,0.5,0.75,1.0]:
            val = mn+frac*rng; y = PT+(1-frac)*(H-PT-PB)
            cv.create_line(PL,y,W-PR,y,fill=BORDER,dash=(2,5))
            cv.create_text(PL-5,y,text=f"{val:.2f}",fill=DIM,font=F_XS,anchor="e")
        for i,(at,hiz,yildiz,sira) in enumerate(data):
            frac = (hiz-mn)/rng; bh = max(4,int(frac*(H-PT-PB)))
            x0 = PL+i*xs+(xs-bw)/2; x1=x0+bw; y1=H-PB; y0=y1-bh
            col = GOLD if ("★★★" in yildiz or "🌟" in yildiz) else                   GREEN if "★★" in yildiz else TEAL if "★" in yildiz else BLUE
            cv.create_rectangle(x0,y0,x1,y1,fill=col,outline=BG)
            cv.create_text((x0+x1)/2,y0-5,text=f"{hiz:.2f}",fill=col,font=F_XS)
            sc = GOLD if sira==1 else SILVER if sira==2 else BRONZE if sira==3 else DIM
            cv.create_text((x0+x1)/2,y1+4,text=f"{sira}.",fill=sc,font=F_XS)
            if yildiz:
                cv.create_text((x0+x1)/2,y0-15,text=yildiz[:4],fill=GOLD,font=F_XS)
            cv.create_text((x0+x1)/2,H-PB+14,text=at[:9],
                           fill=TEXT,font=F_XS,angle=40,anchor="nw")
        cv.create_line(PL,PT,PL,H-PB,fill=DIM)
        cv.create_line(PL,H-PB,W-PR,H-PB,fill=DIM)
    # ── Tab: Karşılaştırma ───────────────────────────────
    def _build_karsi_tab(self, parent):
        tk.Label(parent,
                 text="Galop hızı + koşu stili + performans trendi birleşik karşılaştırma",
                 font=F_XS, bg=BG, fg=DIM).pack(anchor="w", padx=8, pady=(8,4))
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        self.tree_karsi = self._make_tree(lp)
        rp = tk.Frame(mid, bg=BG, width=460)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Karşılaştırma Radar",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_karsi = tk.Canvas(rp, bg=PANEL,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.cv_karsi.pack(fill="both", expand=True)
        self.cv_karsi.bind("<Configure>", lambda e: self._draw_karsi_chart())
    # ── Yardımcılar ──────────────────────────────────────
    def _make_tree(self, parent):
        f = tk.Frame(parent, bg=PANEL,
                     highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="both", expand=True, pady=(0,4))
        vsb = ttk.Scrollbar(f, orient="vertical")
        hsb = ttk.Scrollbar(f, orient="horizontal")
        tree = ttk.Treeview(f, show="headings",
                             yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("g1",  background="#1F3A12", foreground=GOLD)
        tree.tag_configure("g2",  background="#112233", foreground=SILVER)
        tree.tag_configure("g3",  background="#2A1A08", foreground=BRONZE)
        tree.tag_configure("up",  background="#0F2A18", foreground=GREEN)
        tree.tag_configure("dn",  background="#2A0F0F", foreground=RED)
        tree.tag_configure("st",  background="#1A1A0A", foreground=YELLOW)
        tree.tag_configure("odd", background="#162030")
        tree.tag_configure("ev",  background=PANEL)
        return tree
    def _fill_tree(self, tree, df, tag_fn=None):
        tree.delete(*tree.get_children())
        if df is None or df.empty: return
        cols = list(df.columns)
        tree["columns"] = cols
        for c in cols:
            w = 130 if c in ("At","at","Jokey","KosuAdi") else 90
            tree.heading(c, text=c.replace("_"," "),
                         command=lambda _c=c, _t=tree: self._sort(_t,_c))
            tree.column(c, width=w, anchor="center", minwidth=55)
        for idx, row in df.iterrows():
            tag = "odd" if idx%2==0 else "ev"
            if tag_fn: tag = tag_fn(row, idx) or tag
            vals = []
            for c in cols:
                v = row.get(c, "")
                if isinstance(v, float):
                    v = f"{v:+.3f}" if abs(v) < 10 else f"{v:.1f}"
                vals.append(str(v) if v is not None else "")
            tree.insert("","end", values=vals, tags=(tag,))
    def _sort(self, tree, col):
        items = [(tree.set(c,col),c) for c in tree.get_children("")]
        try:    items.sort(key=lambda x: float(re.sub(r"[^\d.\-]","",x[0]) or "0"))
        except: items.sort(key=lambda x: x[0])
        for i,(_,c) in enumerate(items): tree.move(c,"",i)
    def _st(self, msg):
        self.st_var.set(msg); self.update_idletasks()
    def _onceki_gun(self):
        try:
            d = datetime.strptime(self.e_tarih.get(),"%d.%m.%Y") - timedelta(days=1)
            self.e_tarih.delete(0,"end"); self.e_tarih.insert(0,d.strftime("%d.%m.%Y"))
        except: pass
    def _sonraki_gun(self):
        try:
            d = datetime.strptime(self.e_tarih.get(),"%d.%m.%Y") + timedelta(days=1)
            self.e_tarih.delete(0,"end"); self.e_tarih.insert(0,d.strftime("%d.%m.%Y"))
        except: pass
    # ── Bülten çekimi ────────────────────────────────────
    def cek_bulten(self):
        if not self._ready:
            messagebox.showwarning("Bekle","Sistem hazırlanıyor."); return
        if not BS4:
            messagebox.showerror("Hata","beautifulsoup4 gerekli. pip install beautifulsoup4"); return
        tarih = self.e_tarih.get().strip()
        sehir = self.sehir_var.get().strip()
        if not tarih or not sehir:
            messagebox.showwarning("Uyarı","Tarih ve şehir seçin."); return
        threading.Thread(target=self._cek_bulten_worker,
                         args=(tarih,sehir), daemon=True).start()
    def _cek_bulten_worker(self, tarih, sehir):
        self.prog.start(10)
        self._st(f"Bülten çekiliyor: {tarih} {sehir}…")
        t0 = time.time()
        try:
            b = scrape_bulten(tarih, sehir)
            self.bulten = b
            self._conn_ok = True
            self.after(0, lambda: self.conn_var.set("🟢 Bağlı"))
            elapsed = round(time.time() - t0, 1)
            self.after(0, lambda: self._on_bulten(b))
            self._st(f"✓ {len(b['kosular'])} koşu bulundu  —  {sehir.title()} {tarih}  ({elapsed}s)")
        except Exception as e:
            err_msg = str(e)
            if "403" in err_msg or "HTTP Error" in err_msg:
                hint = "\n\nİpucu: VPN kullanmayı deneyin veya birkaç dakika bekleyin."
            elif "timed out" in err_msg.lower() or "urlopen" in err_msg.lower():
                hint = "\n\nİpucu: İnternet bağlantınızı kontrol edin."
                self._conn_ok = False
                self.after(0, lambda: self.conn_var.set("🔴 Bağlantı Yok"))
            else:
                hint = ""
            self.after(0, lambda e2=err_msg, h=hint:
                       messagebox.showerror("Hata", f"Bülten çekilemedi:\n{e2}{h}"))
            self._st(f"HATA: {e}")
        finally: self.prog.stop()
    def _on_bulten(self, b):
        kosular = b.get("kosular", [])
        if not kosular:
            messagebox.showwarning("Sonuç Yok","Koşu bulunamadı."); return
        vals = []
        for k in kosular:
            n_at = len(k.get("atlar",[]))
            label = (f"{k['no']}. Koşu  {k['saat']}  |  "
                     f"{k['cins']}  {k['mesafe']}m {k['pist']}  |  "
                     f"{n_at} at")
            vals.append(label)
        self.kosu_cb["values"] = vals
        if vals:
            self.kosu_cb.current(0)
            self._sec_kosu()
    def _sec_kosu(self):
        """Seçili koşunun atlarını sol panele doldur."""
        idx = self.kosu_cb.current()
        if idx < 0 or not self.bulten: return
        kosular = self.bulten.get("kosular",[])
        if idx >= len(kosular): return
        self.sel_kosu = kosular[idx]
        self._fill_at_listesi(self.sel_kosu)
    def _fill_at_listesi(self, kosu):
        self.at_tree.delete(*self.at_tree.get_children())
        atlar = kosu.get("atlar",[])
        # Koşu özet
        self.kosu_info.config(
            text=f"{'  '.join(filter(None,[kosu.get('cins',''),kosu.get('mesafe','')+'m',kosu.get('pist',''),kosu.get('para','₺')]))}"
        )
        for i, at in enumerate(atlar):
            son10_str = at.get("son10_str","—")
            # Son 10'dan form skoru: küçük sayı iyi
            son10 = at.get("son10",[])
            form_skor = sum(1 for s in son10[-3:] if s<=3) if son10 else 0
            if form_skor >= 2:   tag = "good"
            elif form_skor == 1: tag = "mid"
            else:                tag = "odd" if i%2==0 else "ev"
            self.at_tree.insert("","end",
                values=(at.get("no",""), at.get("at",""),
                        at.get("agf",""), son10_str,
                        at.get("hnd",""), at.get("taki","")),
                tags=(tag,))
    def _filter_atlar(self):
        """Filtre kutusuna göre at listesini filtrele."""
        q = self.at_filter.get().lower().strip()
        if not self.sel_kosu: return
        self.at_tree.delete(*self.at_tree.get_children())
        for i, at in enumerate(self.sel_kosu.get("atlar",[])):
            if q and q not in at.get("at","").lower(): continue
            tag = "odd" if i%2==0 else "ev"
            self.at_tree.insert("","end",
                values=(at.get("no",""), at.get("at",""),
                        at.get("agf",""), at.get("son10_str","—"),
                        at.get("hnd",""), at.get("taki","")),
                tags=(tag,))
    # ── Tüm Koşuları Sırayla Analiz Et ──────────────────
    def _analiz_tum_kosular(self):
        """Bültendeki tüm koşuları sırayla analiz et, sonuçları topla."""
        if not self._ready:
            messagebox.showwarning("Bekle","Sistem hazırlanıyor."); return
        if not self.bulten or not self.bulten.get("kosular"):
            messagebox.showwarning("Uyarı","Önce bülten çekin."); return
        threading.Thread(target=self._tum_kosular_worker, daemon=True).start()
    def _tum_kosular_worker(self):
        self.prog.start(10)
        kosular = self.bulten.get("kosular",[])
        tarih   = self.bulten["tarih"]
        sehir   = self.bulten["sehir"]
        tum_profil = {}
        tum_galop  = {}
        tum_stil   = {}
        tum_perf   = {}
        for ki, kosu in enumerate(kosular):
            kosu_no = kosu["no"]
            self._st(f"[{ki+1}/{len(kosular)}] {kosu_no}. koşu analiz ediliyor…")
            # Galopları çek
            try:
                g_rows = scrape_galoplar(tarih, sehir, kosu_no)
                ga = analiz_galop(g_rows)
                tum_galop[kosu_no] = ga
            except Exception:
                tum_galop[kosu_no] = {}
            # Profilleri çek
            for at in kosu.get("atlar",[]):
                url = at.get("at_url","")
                adi = at.get("at","")
                if not url or adi in tum_profil:
                    continue
                try:
                    profil = scrape_profil(url)
                    tum_profil[adi] = profil
                    tum_stil[adi]   = analiz_stil(profil)
                    tum_perf[adi]   = analiz_perform(profil)
                except Exception:
                    pass
        # Son seçili koşunun verilerini güncelle
        self.profiller.update(tum_profil)
        self.stiller.update(tum_stil)
        self.performlar.update(tum_perf)
        self.jokey_stats = analiz_jokey(self.profiller)
        if self.sel_kosu:
            kno = self.sel_kosu["no"]
            if kno in tum_galop:
                self.galop_an = tum_galop[kno]
        self.prog.stop()
        self.after(0, self._guncelle_tum_tablolar)
        self._st(f"✓ {len(kosular)} koşu analiz edildi  |  {len(tum_profil)} at profili yüklendi")
    # ── Analiz çalıştır ──────────────────────────────────
    def analiz_kosu(self):
        if not self._ready:
            messagebox.showwarning("Bekle","Sistem hazırlanıyor."); return
        if not self.sel_kosu:
            messagebox.showwarning("Uyarı","Önce bülten çekip koşu seçin."); return
        threading.Thread(target=self._analiz_worker, daemon=True).start()
    def _analiz_worker(self):
        self.prog.start(10)
        kosu   = self.sel_kosu
        tarih  = self.bulten["tarih"]
        sehir  = self.bulten["sehir"]
        kosu_no= kosu["no"]
        # 1. Galopları çek
        self._st(f"Galoplar çekiliyor: {kosu_no}. koşu…")
        try:
            g_rows = scrape_galoplar(tarih, sehir, kosu_no)
            self.galoplar = g_rows
            self.galop_an = analiz_galop(g_rows)
            self._st(f"✓ {len(g_rows)} galop kaydı")
        except Exception as e:
            self._st(f"Galop hatası: {e}")
            self.galoplar = []
            self.galop_an = {}
        # 2. Her at için profil çek
        atlar = kosu.get("atlar",[])
        total = sum(1 for a in atlar if a.get("at_url"))
        done  = 0
        self.profiller.clear(); self.stiller.clear(); self.performlar.clear()
        cache_hit = 0
        for at in atlar:
            url = at.get("at_url","")
            if not url: continue
            at_adi = at.get("at","")
            done += 1
            # Önbellekte var mı kontrol et
            cached = cache_get(url)
            src = "önbellek" if cached else "web"
            self._st(f"Profil [{done}/{total}] ({src}): {at_adi}…")
            try:
                profil = scrape_profil(url)
                if cached:
                    cache_hit += 1
                self.profiller[at_adi] = profil
                self.stiller[at_adi]   = analiz_stil(profil)
                self.performlar[at_adi]= analiz_perform(profil)
            except Exception as e:
                self._st(f"Profil hatası ({at_adi}): {e}")
        # Jokey analizi
        self.jokey_stats = analiz_jokey(self.profiller)
        self.prog.stop()
        self.after(0, self._guncelle_tum_tablolar)
        cache_msg = f"  ({cache_hit} önbellekten)" if cache_hit else ""
        self._st(f"✓ Analiz tamamlandı  —  {len(self.stiller)} at profil{cache_msg}  |  {len(self.jokey_stats)} jokey analiz edildi")
    def _guncelle_tum_tablolar(self):
        self._update_genel()
        self._update_galop_tab()
        self._update_stil_tab()
        self._update_trend_tab()
        self._update_karsi_tab()
        self._update_son2hiz()
        self._update_takip()
        self._update_senaryo()
    # ── Genel Analiz ─────────────────────────────────────
    def _update_genel(self):
        if not self.sel_kosu: return
        atlar = self.sel_kosu.get("atlar",[])
        rows  = []
        for at in atlar:
            adi = at.get("at","")
            g   = self.galop_an.get(adi,{})
            s   = self.stiller.get(adi,{})
            p   = self.performlar.get(adi,{})
            # Birleşik skor (PRO v14 — ağırlıklı bileşenler)
            skor = 0.0
            # 1. Galop hızı (max 40 puan)
            if g.get("en_iyi_400"):
                skor += max(0, min(40, (27-g["en_iyi_400"])*5))
            # 2. Galop tazeliği (max 15 puan)
            if g.get("gun_fark") is not None:
                skor += max(0, 15-g["gun_fark"]*0.8)
            # 3. İlk 3 yüzdesi (max 20 puan)
            if s.get("ilk3_pct"):
                skor += min(20, s["ilk3_pct"]*0.3)
            # 4. Performans trendi (max 15 puan)
            if p.get("trend_skor"):
                skor += min(15, max(-15, p["trend_skor"]*30))
            # 5. Jokey başarısı (max 10 puan)
            jokey_adi = at.get("jokey","").strip()
            j_stat = self.jokey_stats.get(jokey_adi, {})
            jokey_win = j_stat.get("win_pct", 0)
            jokey_ilk3 = j_stat.get("ilk3_pct", 0)
            skor += min(10, jokey_win * 0.3 + jokey_ilk3 * 0.1)
            # 6. TJK Tempo/Pace bonus (max 15 puan) — v15 YENİ
            tjk_pace = ""
            tjk_hiz  = ""
            tjk_at_data = self.tjk_analiz.get("atlar", {}).get(adi, [])
            if tjk_at_data:
                best = max(tjk_at_data, key=lambda x: x.get("pace_fig", 0))
                pf = best.get("pace_fig", 100)
                tjk_pace = pf
                tjk_hiz  = best.get("hiz_ms", "")
                # Pace > 100 → bonus, < 100 → ceza
                skor += min(15, max(-10, (pf - 100) * 2.5))
            skor = round(skor, 1)
            rows.append({
                "No":          at.get("no",""),
                "At":          adi,
                "AGF":         at.get("agf",""),
                "Hnd":         at.get("hnd",""),
                "Jokey":       jokey_adi,
                "J_Win%":      jokey_win if jokey_win else "",
                "Son5_Form":   s.get("son5","—"),
                "Kosu_Stili":  s.get("stil","—"),
                "Ilk3_%":      s.get("ilk3_pct",""),
                "En_Iyi_400":  g.get("en_iyi_400",""),
                "Son_Galop":   g.get("gun_fark",""),
                "Trend":       p.get("trend","—"),
                "Pace":        tjk_pace if tjk_pace else "—",
                "TJK_Hız":     tjk_hiz if tjk_hiz else "—",
                "Taki":        at.get("taki",""),
                "Skor":        skor,
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Skor",
                key=lambda x: pd.to_numeric(x,errors="coerce").fillna(0),
                ascending=False).reset_index(drop=True)
        def tag_fn(row, idx):
            if idx == 0: return "g1"
            if idx == 1: return "g2"
            if idx == 2: return "g3"
            t = str(row.get("Trend",""))
            if "YÜKSELİYOR" in t: return "up"
            if "DÜŞÜYOR"    in t: return "dn"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_genel, df, tag_fn=tag_fn)
        # Podium
        self._draw_podium(df.head(3).to_dict("records") if not df.empty else [])
    def _draw_podium(self, top3):
        for w in self.pod.winfo_children(): w.destroy()
        tk.Label(self.pod, text="🏆  En Güçlü Adaylar",
                 font=F_M, bg=BG, fg=TEXT).pack(side="left", padx=(0,16))
        medals = ["🥇","🥈","🥉"]; colors = [GOLD,SILVER,BRONZE]
        for i, row in enumerate(top3):
            c = tk.Frame(self.pod, bg=CARD,
                         highlightthickness=2, highlightbackground=colors[i],
                         padx=14, pady=8)
            c.pack(side="left", padx=(0,10))
            tk.Label(c, text=f"{medals[i]} {row.get('At','')}",
                     font=F_M, bg=CARD, fg=TEXT).pack()
            tk.Label(c, text=f"Skor: {row.get('Skor','—')}",
                     font=("Segoe UI",12,"bold"), bg=CARD, fg=colors[i]).pack()
            details = f"{row.get('Kosu_Stili','—')}  |  Form: {row.get('Son5_Form','—')}"
            tk.Label(c, text=details, font=F_XS, bg=CARD, fg=DIM).pack(pady=(2,0))
            jokey_info = row.get('Jokey','')
            j_win = row.get('J_Win%','')
            if jokey_info:
                j_txt = f"🏇 {jokey_info}" + (f"  (Win: %{j_win})" if j_win else "")
                tk.Label(c, text=j_txt, font=F_XS, bg=CARD, fg=TEAL).pack()
    # ── Galop Tab ─────────────────────────────────────────
    def _update_galop_tab(self):
        if not self.galop_an: return
        horses = ["Tümü"] + sorted(self.galop_an.keys())
        self.g_horse_cb["values"] = horses
        self.g_horse_var.set("Tümü")   # hep Tümü ile aç
        self._refresh_galop_detail()
        # Galop sekmesine geç (sekme index 1)
        self.nb.select(1)
    def _refresh_galop_detail(self):
        horse = self.g_horse_var.get()
        n_str = self.g_n_var.get()
        # Tümü = hepsi, seçili = sadece o at
        rows = [r for r in self.galoplar
                if horse == "Tümü" or r.get("at","") == horse]
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        if not df.empty:
            df["_date"] = df["g_tarih"].apply(parse_date_key)
            df["_400s"] = df["400"].apply(galop_to_sec)
            df["_gun"]  = df["g_tarih"].apply(gun_farki)
            # Her at için son N galop al (tarihe göre)
            def son_n(grp):
                g2 = grp.sort_values("_date", ascending=False)
                if n_str != "Tümü":
                    try: g2 = g2.head(int(n_str))
                    except: pass
                return g2
            df = df.groupby("at", group_keys=False).apply(son_n).reset_index(drop=True)
            # Ağırlıklı skor: hız (büyük = iyi) + tazelik bonusu
            MAX_SEC = 35.0
            df["_hiz_skor"] = df["_400s"].apply(
                lambda s: (MAX_SEC - s) * 3 if s and s > 0 else -999
            )
            df["_taze"] = df["_gun"].apply(
                lambda g: 8 if g is not None and g <= 3
                     else 5 if g is not None and g <= 7
                     else 2 if g is not None and g <= 14
                     else 0
            )
            df["_skor"] = df["_hiz_skor"] + df["_taze"]
            # ── Düz liste: tüm atlar, en iyiden en kötüye ──────
            df = df.sort_values("_skor", ascending=False,
                                na_position="last").reset_index(drop=True)
            # Görsel sütunlar
            df["Tazelik"] = df["_gun"].apply(
                lambda g: "🟢 Bugün" if g == 0
                     else f"🟢 {g}g"  if g is not None and g <= 3
                     else f"🟡 {g}g"  if g is not None and g <= 7
                     else f"🟠 {g}g"  if g is not None and g <= 14
                     else f"⚫ {g}g"  if g is not None
                     else "—"
            )
            df["Skor"] = df["_skor"].round(1)
            df = df.drop(columns=["_date","_400s","_gun","_hiz_skor","_taze","_skor"],
                         errors="ignore")
        show = ["Skor","no","at","Tazelik","g_tarih",
                "400","600","800","1000","g_sehir","kg","jokey","pist"]
        show = [c for c in show if not df.empty and c in df.columns]
        def tag_fn(row, idx):
            if idx == 0: return "g1"
            if idx == 1: return "g2"
            if idx == 2: return "g3"
            taze = str(row.get("Tazelik",""))
            if "🟢" in taze: return "up"
            if "🟡" in taze: return "st"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_galop,
                        df[show] if show and not df.empty else df,
                        tag_fn=tag_fn)
        self.after(80, self._draw_galop_bar)
    def _draw_galop_bar(self):
        cv = self.cv_galop; cv.delete("all")
        W  = cv.winfo_width() or 380; H = cv.winfo_height() or 400
        if not self.galop_an or W < 80: return
        items = []
        for at, d in self.galop_an.items():
            v = d.get("en_iyi_400")
            if v: items.append((at, v))
        if not items: return
        items.sort(key=lambda x: x[1])
        PL,PR,PT,PB = 50,12,36,60
        mn = items[0][1]; mx = items[-1][1]; rng = max(mx-mn,0.5)
        n  = len(items); bw = max(12, int((W-PL-PR)/n)-4); xs=(W-PL-PR)/n
        cv.create_text(W//2,18,
                       text="En İyi 400m  (küçük = hızlı)",
                       fill=TEXT, font=F_S)
        for frac in [0,0.25,0.5,0.75,1.0]:
            val = mn+frac*rng; y = PT+(1-frac)*(H-PT-PB)
            cv.create_line(PL,y,W-PR,y,fill=BORDER,dash=(2,5))
            cv.create_text(PL-5,y,text=f"{val:.1f}",fill=DIM,font=F_XS,anchor="e")
        for i,(at,val) in enumerate(items):
            frac = (val-mn)/rng if rng>0 else 0.5
            bh   = max(4, int(frac*(H-PT-PB)))
            x0   = PL+i*xs+(xs-bw)/2; x1=x0+bw
            y1   = H-PB; y0=y1-bh
            gun  = self.galop_an.get(at,{}).get("gun_fark",99) or 99
            col  = GREEN if gun<=7 else (YELLOW if gun<=14 else BLUE)
            cv.create_rectangle(x0,y0,x1,y1,fill=col,outline=BG,width=1)
            cv.create_text((x0+x1)/2,y0-5,text=f"{val:.1f}",fill=col,font=F_XS)
            cv.create_text((x0+x1)/2,H-PB+14,
                           text=at[:10],fill=DIM,font=F_XS,angle=42,anchor="nw")
        cv.create_line(PL,PT,PL,H-PB,fill=DIM)
        cv.create_line(PL,H-PB,W-PR,H-PB,fill=DIM)
        # Legend
        for col,lbl,x in [(GREEN,"≤7 gün",PL),(YELLOW,"≤14 gün",PL+70),(BLUE,">14 gün",PL+145)]:
            cv.create_rectangle(x,H-PB+48,x+10,H-PB+58,fill=col,outline="")
            cv.create_text(x+13,H-PB+53,text=lbl,fill=col,font=F_XS,anchor="w")
    # ── Stil Tab ─────────────────────────────────────────
    def _update_stil_tab(self):
        if not self.stiller: return
        self.stil_status.set(f"✓ {len(self.stiller)} at analiz edildi")
        rows = []
        for at, s in self.stiller.items():
            rows.append({
                "At":          at,
                "Stil":        s.get("stil",""),
                "Ort_Sira":    s.get("ort_sira",""),
                "Ort_Hiz":     s.get("ort_hiz",""),
                "Ilk3_%":      s.get("ilk3_pct",""),
                "Son5":        s.get("son5",""),
                "Pist_Pref":   s.get("pist_pref","")[:35] if s.get("pist_pref") else "",
                "Taki":        s.get("taki","")[:45] if s.get("taki") else "",
                "Kosu_Sayisi": s.get("toplam_kosu",""),
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Ilk3_%",
                key=lambda x: pd.to_numeric(x,errors="coerce").fillna(0),
                ascending=False).reset_index(drop=True)
        def tag_fn(row, idx):
            s = str(row.get("Stil",""))
            if "ÖNDEN" in s:  return "g1"
            if "ORTADAN" in s: return "g2"
            if "GERİDEN" in s or "KAPICI" in s: return "g3"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_stil, df, tag_fn=tag_fn)
        # Kartlar
        for w in self.stil_cards.winfo_children(): w.destroy()
        onderr  = sum(1 for s in self.stiller.values() if "ÖNDEN" in s.get("stil",""))
        ortadan = sum(1 for s in self.stiller.values() if "ORTADAN" in s.get("stil",""))
        geriden = sum(1 for s in self.stiller.values()
                      if "GERİDEN" in s.get("stil","") or "KAPICI" in s.get("stil",""))
        for lbl,val,col in [
            ("🟢 Önden",   onderr,  GREEN),
            ("🟡 Ortadan", ortadan, YELLOW),
            ("🔵 Geriden", geriden, BLUE),
            ("Toplam",     len(self.stiller), DIM),
        ]:
            c = tk.Frame(self.stil_cards, bg=CARD,
                         highlightthickness=2, highlightbackground=col,
                         padx=12, pady=6)
            c.pack(side="left", padx=(0,8))
            tk.Label(c,text=str(val),font=("Segoe UI",18,"bold"),bg=CARD,fg=col).pack()
            tk.Label(c,text=lbl,font=F_XS,bg=CARD,fg=DIM).pack()
        horses = ["Tümü"]+sorted(self.stiller.keys())
        self.stil_horse_cb["values"] = horses
        if len(horses)>1:
            self.stil_horse_var.set(horses[1])
            self._refresh_stil_detail()
    def _refresh_stil_detail(self):
        horse = self.stil_horse_var.get()
        if not horse or horse=="Tümü" or horse not in self.profiller: return
        races = self.profiller[horse].get("races",[])
        if not races: return
        df = pd.DataFrame(races)
        show = ["tarih","sehir","kcins","msf","pist","sira","derece","hiz","jokey","kilo","taki"]
        show = [c for c in show if c in df.columns]
        def tag_fn(row, idx):
            try:
                s = int(re.sub(r"[^\d]","",str(row.get("sira","") or "")))
                if s==1: return "g1"
                if s==2: return "g2"
                if s==3: return "g3"
            except: pass
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_stil_detail,
                        df[show] if show else df, tag_fn=tag_fn)
    # ── Trend Tab ─────────────────────────────────────────
    def _update_trend_tab(self):
        if not self.performlar: return
        rows = []
        for at, p in self.performlar.items():
            rows.append({
                "At":          at,
                "Trend":       p.get("trend",""),
                "Trend_Skor":  p.get("trend_skor",""),
                "En_Iyi_Hiz":  p.get("en_iyi_hiz",""),
                "Ort_Hiz_ms":  p.get("ort_hiz_ms",""),
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Trend_Skor",
                key=lambda x: pd.to_numeric(x,errors="coerce").fillna(-999),
                ascending=False).reset_index(drop=True)
        def tag_fn(row, idx):
            t = str(row.get("Trend",""))
            if "YÜKSELİYOR" in t: return "up"
            if "DÜŞÜYOR"    in t: return "dn"
            return "st"
        self._fill_tree(self.tree_trend, df, tag_fn=tag_fn)
        horses = ["Tümü"]+sorted(self.performlar.keys())
        self.trend_horse_cb["values"] = horses
        if len(horses)>1:
            self.trend_horse_var.set(horses[1])
            self._draw_trend_chart()
    def _draw_trend_chart(self):
        horse = self.trend_horse_var.get()
        cv    = self.cv_trend; cv.delete("all")
        if not horse or horse=="Tümü" or horse not in self.profiller: return
        races = sorted(self.profiller[horse].get("races",[]),
                       key=lambda r: parse_date_key(r.get("tarih","")))[-10:]
        data  = []
        for r in races:
            d = derece_to_sec(r.get("derece",""))
            try:
                msf = int(re.sub(r"[^\d]","",str(r.get("msf","") or "")))
                h   = msf/d if d and d>0 else None
                if h: data.append((r.get("tarih",""), round(h,3)))
            except: pass
        W = cv.winfo_width() or 450; H = cv.winfo_height() or 380
        if len(data) < 2:
            cv.create_text(W//2,H//2,text="Yeterli veri yok",fill=DIM,font=F_M); return
        PL,PR,PT,PB = 55,20,36,40
        vals = [v for _,v in data]
        mn,mx = min(vals),max(vals); rng = max(mx-mn,0.05)
        xs = (W-PL-PR)/max(len(data)-1,1)
        cv.create_text(W//2,18,
                       text=f"{horse}  —  Koşu Hız Trendi (m/s)",
                       fill=TEXT, font=F_S)
        for frac in [0,0.25,0.5,0.75,1.0]:
            val = mn+frac*rng; y = PT+(1-frac)*(H-PT-PB)
            cv.create_line(PL,y,W-PR,y,fill=BORDER,dash=(2,5))
            cv.create_text(PL-5,y,text=f"{val:.2f}",fill=DIM,font=F_XS,anchor="e")
        pts = []
        for i,(tarih,v) in enumerate(data):
            x = PL+i*xs; y = PT+(1-(v-mn)/rng)*(H-PT-PB)
            pts.append((x,y,v,tarih))
        for i in range(len(pts)-1):
            col = GREEN if pts[i+1][2]>pts[i][2] else RED
            cv.create_line(pts[i][0],pts[i][1],
                           pts[i+1][0],pts[i+1][1],
                           fill=col, width=2, smooth=True)
        for x,y,v,t in pts:
            cv.create_oval(x-4,y-4,x+4,y+4,fill=BLUE,outline=BG)
            cv.create_text(x,H-PB+12,text=t[-5:],
                           fill=DIM,font=F_XS,angle=30,anchor="nw")
            cv.create_text(x,y-10,text=f"{v:.2f}",
                           fill=TEXT,font=F_XS)
        cv.create_line(PL,PT,PL,H-PB,fill=DIM)
        cv.create_line(PL,H-PB,W-PR,H-PB,fill=DIM)
    # ── Karşılaştırma Tab ────────────────────────────────
    def _update_karsi_tab(self):
        if not self.sel_kosu: return
        atlar = self.sel_kosu.get("atlar",[])
        rows  = []
        for at in atlar:
            adi = at.get("at","")
            g   = self.galop_an.get(adi,{})
            s   = self.stiller.get(adi,{})
            p   = self.performlar.get(adi,{})
            rows.append({
                "No":         at.get("no",""),
                "At":         adi,
                "En_Iyi_400": g.get("en_iyi_400","—"),
                "Son_Galop":  str(g.get("gun_fark","—"))+"g" if g.get("gun_fark") is not None else "—",
                "Stil":       s.get("stil","—"),
                "Ilk3_%":     s.get("ilk3_pct","—"),
                "Son5":       s.get("son5","—"),
                "Trend":      p.get("trend","—"),
                "Trend_Skor": p.get("trend_skor","—"),
                "Taki":       at.get("taki",""),
                "AGF":        at.get("agf",""),
            })
        df = pd.DataFrame(rows)
        def tag_fn(row, idx):
            t = str(row.get("Trend",""))
            if "YÜKSELİYOR" in t: return "up"
            if "DÜŞÜYOR"    in t: return "dn"
            s = str(row.get("Stil",""))
            if "ÖNDEN" in s: return "g1"
            if "ORTADAN" in s: return "g2"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_karsi, df, tag_fn=tag_fn)
        self.after(100, self._draw_karsi_chart)
    def _draw_karsi_chart(self):
        """Basit çizgi karşılaştırma grafiği — ilk 8 at."""
        cv = self.cv_karsi; cv.delete("all")
        W  = cv.winfo_width() or 460; H = cv.winfo_height() or 380
        if not self.galop_an or W < 80: return
        items = sorted(
            [(at, d.get("en_iyi_400")) for at,d in self.galop_an.items()
             if d.get("en_iyi_400")],
            key=lambda x: x[1]
        )[:8]
        if not items: return
        PL,PR,PT,PB = 50,150,36,40
        vals = [v for _,v in items]
        mn,mx = min(vals),max(vals); rng=max(mx-mn,0.5)
        ys = (H-PT-PB)/max(len(items)-1,1)
        cv.create_text(W//2,18,text="400m Sıralama (en hızlı üstte)",
                       fill=TEXT,font=F_S)
        for i,(at,val) in enumerate(items):
            y    = PT + i*ys
            frac = (val-mn)/rng if rng>0 else 0.5
            bar_w= int(frac*(W-PL-PR-10))
            col  = LINE_C[i%len(LINE_C)]
            cv.create_rectangle(PL, y-10, PL+max(bar_w,4), y+10,
                                 fill=col, outline=BG)
            cv.create_text(PL+max(bar_w,4)+5, y,
                           text=f"{val:.2f}s", fill=col, font=F_XS, anchor="w")
            # İsim
            gun = self.galop_an.get(at,{}).get("gun_fark","")
            gun_txt = f" ({gun}g)" if gun is not None else ""
            cv.create_text(PL-5, y,
                           text=at[:14]+gun_txt, fill=TEXT, font=F_XS, anchor="e")
        cv.create_line(PL,PT-15,PL,H-PB,fill=DIM)
    # ── Tab: Takip Atları ─────────────────────────────────
    def _build_takip_tab(self, parent):
        # Üst filtreler
        flt = tk.Frame(parent, bg=BG)
        flt.pack(fill="x", padx=8, pady=(8,4))
        tk.Label(flt, text="Min Hız İndeksi:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.takip_hiz_var = tk.StringVar(value="10")
        ttk.Combobox(flt, textvariable=self.takip_hiz_var,
                     values=["0","5","10","20","30","50"],
                     state="readonly", width=5, font=F_N).pack(side="left", padx=4)
        tk.Label(flt, text="Max Bitiş Sırası:", font=F_S, bg=BG, fg=DIM
                 ).pack(side="left", padx=(16,0))
        self.takip_sira_var = tk.StringVar(value="5")
        ttk.Combobox(flt, textvariable=self.takip_sira_var,
                     values=["3","4","5","6","8","Tümü"],
                     state="readonly", width=5, font=F_N).pack(side="left", padx=4)
        tk.Label(flt, text="Min Katılımcı:", font=F_S, bg=BG, fg=DIM
                 ).pack(side="left", padx=(16,0))
        self.takip_kati_var = tk.StringVar(value="6")
        ttk.Combobox(flt, textvariable=self.takip_kati_var,
                     values=["4","5","6","7","8","10"],
                     state="readonly", width=5, font=F_N).pack(side="left", padx=4)
        tk.Button(flt, text="🔍 Filtrele", command=self._update_takip,
                  bg=BLUE, fg=TEXT, font=F_S, relief="flat",
                  padx=10, pady=5).pack(side="left", padx=12)
        tk.Label(flt,
                 text="İyi koşup kazanamayan, form oluşturan, takip edilmesi gereken atlar",
                 font=F_XS, bg=BG, fg=TEAL).pack(side="left")
        # Podium kartları
        self.takip_cards = tk.Frame(parent, bg=BG)
        self.takip_cards.pack(fill="x", padx=8, pady=(0,6))
        # Orta: tablo + grafik
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(lp, text="Takip Listesi — En Güçlü Performans Üstte",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_takip = self._make_tree(lp)
        rp = tk.Frame(mid, bg=BG, width=380)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Takip Skoru Grafiği",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_takip = tk.Canvas(rp, bg=PANEL,
                                   highlightthickness=1, highlightbackground=BORDER)
        self.cv_takip.pack(fill="both", expand=True)
        self.cv_takip.bind("<Configure>", lambda e: self._draw_takip_chart())
    def _compute_takip_skor(self, at_adi: str, profil: dict) -> dict | None:
        """
        Bir atın 'takip edilmesi gereken at' skorunu hesapla.
        
        Kriter:
        1. Son N koşuda iyi hız ama düşük ödül (handikap yükü yüksek veya şanssız)
        2. Koşu stili oturmuş (stabil)
        3. Pozitif veya stabil trend
        4. Son koşuda belirli sıra içinde bitirmiş (ama 1. olmamış)
        5. Hız indeksi pozitif (galop derecesi iyi)
        
        Returns: None if not worth tracking
        """
        races = sorted(
            profil.get("races", []),
            key=lambda r: parse_date_key(r.get("tarih","")),
            reverse=True
        )[:5]  # son 5 koşu
        if not races:
            return None
        # --- Hız skorları ---
        hiz_skorlari = []
        for r in races:
            m = re.search(r"\(?([+-]?\d+)\)?", str(r.get("hiz","") or ""))
            if m:
                try: hiz_skorlari.append(int(m.group(1)))
                except: pass
        if not hiz_skorlari:
            return None
        ort_hiz = sum(hiz_skorlari) / len(hiz_skorlari)
        # Minimum hız filtresi
        try:
            min_hiz = int(self.takip_hiz_var.get())
        except:
            min_hiz = 10
        if ort_hiz < min_hiz:
            return None
        # --- Bitiş sıraları ---
        siralar = []
        for r in races:
            try:
                s = int(re.sub(r"[^\d]","", str(r.get("sira","") or "")))
                if 0 < s <= 30: siralar.append(s)
            except: pass
        if not siralar:
            return None
        ort_sira = sum(siralar) / len(siralar)
        son_sira = siralar[0]
        # Max bitiş sırası filtresi
        try:
            max_sira = int(self.takip_sira_var.get()) if self.takip_sira_var.get() != "Tümü" else 99
        except:
            max_sira = 5
        if son_sira > max_sira:
            return None
        # 1. olmamışsa daha değerli (henüz kazanmamış form atı)
        hic_birinci = any(s == 1 for s in siralar)
        # --- Trend ---
        trend = self.performlar.get(at_adi, {}).get("trend_skor", 0) or 0
        # --- Galop tazeliği ---
        galop = self.galop_an.get(at_adi, {})
        gun_fark = galop.get("gun_fark")
        taze_bonus = 0
        if gun_fark is not None:
            if gun_fark <= 7:  taze_bonus = 15
            elif gun_fark <= 14: taze_bonus = 8
        # --- Takip Skoru ---
        # Hız yüksek + sıra makul + trend pozitif + taze = yüksek skor
        skor = (
            ort_hiz * 0.5           +   # hız indeksi
            max(0, (6 - ort_sira) * 8) + # ortalama sıra (iyi sıra bonus)
            trend * 20              +   # yükseliş trendi
            taze_bonus              +   # galop tazeliği
            (10 if not hic_birinci else -5)  # henüz kazanmamış = form birikimi
        )
        # Neden takip edilmeli açıklaması
        nedenler = []
        if ort_hiz >= 30: nedenler.append(f"Yüksek hız ({ort_hiz:.0f})")
        if trend > 0.1:   nedenler.append("Yükselen trend")
        if taze_bonus > 0: nedenler.append(f"Taze galop ({gun_fark}g)")
        if not hic_birinci and son_sira <= 3:
            nedenler.append("İlk 3 formda, henüz 1. olmadı")
        if ort_sira <= 3:  nedenler.append(f"Ort.sıra {ort_sira:.1f}")
        # Son koşu özeti
        son_kosu = races[0]
        return {
            "At":           at_adi,
            "Takip_Skor":   round(skor, 1),
            "Son_Sira":     son_sira,
            "Ort_Sira":     round(ort_sira, 1),
            "Son_Hiz_Ind":  hiz_skorlari[0] if hiz_skorlari else "—",
            "Ort_Hiz_Ind":  round(ort_hiz, 1),
            "Trend":        self.performlar.get(at_adi, {}).get("trend", "—"),
            "Son_Galop":    f"{gun_fark}g" if gun_fark is not None else "—",
            "Son_Tarih":    son_kosu.get("tarih",""),
            "Son_Msf":      son_kosu.get("msf",""),
            "Son_Pist":     son_kosu.get("pist",""),
            "Kazandimi":    "✗ Hayır" if not hic_birinci else "✓ Evet",
            "Neden":        "  •  ".join(nedenler) if nedenler else "—",
            "_skor_raw":    skor,
        }
    def _update_takip(self):
        """Takip atlarını hesapla ve tabloyu güncelle."""
        if not self.profiller:
            return
        sonuclar = []
        for at_adi, profil in self.profiller.items():
            r = self._compute_takip_skor(at_adi, profil)
            if r:
                sonuclar.append(r)
        if not sonuclar:
            self._st("Filtre kriterlerine uyan takip atı bulunamadı.")
            return
        # Skora göre sırala
        sonuclar.sort(key=lambda x: x["_skor_raw"], reverse=True)
        # Podium
        self._draw_takip_podium(sonuclar[:3])
        # Tablo
        show_cols = ["At","Takip_Skor","Son_Sira","Ort_Sira",
                     "Son_Hiz_Ind","Ort_Hiz_Ind","Trend","Son_Galop",
                     "Son_Tarih","Son_Msf","Kazandimi","Neden"]
        df = pd.DataFrame([{k:v for k,v in r.items() if not k.startswith("_")}
                           for r in sonuclar])
        def tag_fn(row, idx):
            if idx == 0: return "g1"
            if idx == 1: return "g2"
            if idx == 2: return "g3"
            t = str(row.get("Trend",""))
            if "YÜKSELİYOR" in t: return "up"
            if "DÜŞÜYOR"    in t: return "dn"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_takip,
                        df[[c for c in show_cols if c in df.columns]],
                        tag_fn=tag_fn)
        self._takip_data = sonuclar
        self.after(100, self._draw_takip_chart)
        self._st(f"✓ {len(sonuclar)} takip atı bulundu")
    def _draw_takip_podium(self, top3):
        for w in self.takip_cards.winfo_children():
            w.destroy()
        if not top3: return
        tk.Label(self.takip_cards, text="⭐ En Güçlü Takip Atları",
                 font=F_M, bg=BG, fg=TEXT).pack(side="left", padx=(0,16))
        colors  = [GOLD, SILVER, BRONZE]
        medals  = ["🥇","🥈","🥉"]
        for i, r in enumerate(top3):
            c = tk.Frame(self.takip_cards, bg=CARD,
                         highlightthickness=2, highlightbackground=colors[i],
                         padx=14, pady=8)
            c.pack(side="left", padx=(0,10))
            tk.Label(c, text=f"{medals[i]} {r['At']}",
                     font=F_M, bg=CARD, fg=TEXT).pack()
            tk.Label(c, text=f"Skor: {r['Takip_Skor']}",
                     font=("Segoe UI",12,"bold"), bg=CARD, fg=colors[i]).pack()
            tk.Label(c, text=f"Son: {r['Son_Sira']}. | Ort: {r['Ort_Sira']} | Hız: {r['Son_Hiz_Ind']}",
                     font=F_XS, bg=CARD, fg=DIM).pack(pady=(2,0))
            neden = str(r.get("Neden",""))[:45]
            tk.Label(c, text=neden,
                     font=F_XS, bg=CARD, fg=TEAL).pack(pady=(1,0))
    def _draw_takip_chart(self):
        cv = self.cv_takip; cv.delete("all")
        W  = cv.winfo_width() or 380; H = cv.winfo_height() or 420
        if not hasattr(self,"_takip_data") or not self._takip_data or W < 80:
            return
        data = self._takip_data[:12]  # en fazla 12 at
        PL,PR,PT,PB = 50,12,40,65
        skorlar = [r["_skor_raw"] for r in data]
        mn = max(0, min(skorlar) - 5)
        mx = max(skorlar) + 5
        rng= max(mx - mn, 1)
        n  = len(data)
        bw = max(14, int((W-PL-PR)/n) - 4)
        xs = (W-PL-PR) / n
        cv.create_text(W//2, 20,
                       text="Takip Skoru (yüksek = öncelikli izle)",
                       fill=TEXT, font=F_S)
        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            val = mn + frac * rng
            y   = PT + (1-frac) * (H-PT-PB)
            cv.create_line(PL, y, W-PR, y, fill=BORDER, dash=(2,5))
            cv.create_text(PL-5, y, text=f"{val:.0f}",
                           fill=DIM, font=F_XS, anchor="e")
        for i, r in enumerate(data):
            skor = r["_skor_raw"]
            frac = (skor - mn) / rng
            bh   = max(4, int(frac * (H-PT-PB)))
            x0   = PL + i*xs + (xs-bw)/2
            x1   = x0 + bw
            y1   = H - PB; y0 = y1 - bh
            # Renk: kazanmamış + yüksek skor = altın
            if i == 0:               col = GOLD
            elif i == 1:             col = SILVER
            elif i == 2:             col = BRONZE
            elif r["Kazandimi"] == "✗ Hayır": col = TEAL
            else:                    col = BLUE
            cv.create_rectangle(x0, y0, x1, y1, fill=col, outline=BG)
            cv.create_text((x0+x1)/2, y0-5,
                           text=f"{skor:.0f}", fill=col, font=F_XS)
            # Son sıra küçük etiket
            cv.create_text((x0+x1)/2, y1+4,
                           text=f"{r['Son_Sira']}.", fill=DIM, font=F_XS)
            # At adı
            cv.create_text((x0+x1)/2, H-PB+14,
                           text=r["At"][:9],
                           fill=TEXT, font=F_XS, angle=40, anchor="nw")
        cv.create_line(PL, PT, PL, H-PB, fill=DIM)
        cv.create_line(PL, H-PB, W-PR, H-PB, fill=DIM)
        # Legend
        for col, lbl, x in [(TEAL,"Henüz kazanmadı",PL),
                             (BLUE,"Kazandı",        PL+110)]:
            cv.create_rectangle(x, H-PB+48, x+10, H-PB+58, fill=col, outline="")
            cv.create_text(x+13, H-PB+53, text=lbl, fill=col,
                           font=F_XS, anchor="w")
    # ── Tab: Son 2 Yarış Hız ─────────────────────────────
    def _build_son2hiz_tab(self, parent):
        tk.Label(parent,
                 text=("Hız = Mesafe ÷ Derece (m/s)  •  Son 2 koşu karşılaştırması  "
                       "•  Yeşil = hızlandı  •  Kırmızı = yavaşladı"),
                 font=F_XS, bg=BG, fg=DIM).pack(anchor="w", padx=8, pady=(8,4))
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)
        # Sol: tablo
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(lp, text="At Bazında Son 2 Yarış Hız Analizi",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_s2h = self._make_tree(lp)
        # Sağ: bar karşılaştırma grafiği
        rp = tk.Frame(mid, bg=BG, width=400)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)
        tk.Label(rp, text="Hız Karşılaştırması (m/s)",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_s2h = tk.Canvas(rp, bg=PANEL,
                                 highlightthickness=1, highlightbackground=BORDER)
        self.cv_s2h.pack(fill="both", expand=True)
        self.cv_s2h.bind("<Configure>", lambda e: self._draw_s2h_chart())
    def _update_son2hiz(self):
        """Her at için son 2 yarışın hız analizini hesapla ve göster."""
        if not self.profiller: return
        rows = []
        for at_adi, profil in self.profiller.items():
            races = sorted(
                profil.get("races", []),
                key=lambda r: parse_date_key(r.get("tarih","")),
                reverse=True
            )
            # Derece ve mesafesi olan ilk 2 yarışı al
            valid = []
            for r in races:
                d = derece_to_sec(r.get("derece",""))
                try:
                    m = int(re.sub(r"[^\d]","", str(r.get("msf","") or "")))
                except: m = 0
                if d and m > 0:
                    h = round(m / d, 3)
                    valid.append({
                        "tarih":  r.get("tarih",""),
                        "msf":    m,
                        "pist":   r.get("pist",""),
                        "sira":   r.get("sira",""),
                        "derece": r.get("derece",""),
                        "hiz":    h,
                        "jokey":  r.get("jokey",""),
                    })
                if len(valid) == 2:
                    break
            if not valid:
                continue
            son1 = valid[0]  # en yeni
            son2 = valid[1] if len(valid) > 1 else None
            fark     = round(son1["hiz"] - son2["hiz"], 3) if son2 else None
            fark_pct = round(fark / son2["hiz"] * 100, 1)  if son2 and son2["hiz"] else None
            if fark is not None:
                if fark > 0.05:    trend = "🟢 HIZLANDI"
                elif fark < -0.05: trend = "🔴 YAVAŞLADI"
                else:              trend = "🟡 STABİL"
            else:
                trend = "—"
            row = {
                "At":            at_adi,
                "Trend":         trend,
                "Son1_Tarih":    son1["tarih"],
                "Son1_Msf":      son1["msf"],
                "Son1_Pist":     son1["pist"],
                "Son1_Sira":     son1["sira"],
                "Son1_Derece":   son1["derece"],
                "Son1_Hiz(m/s)": son1["hiz"],
                "Son2_Tarih":    son2["tarih"] if son2 else "—",
                "Son2_Msf":      son2["msf"]   if son2 else "—",
                "Son2_Pist":     son2["pist"]  if son2 else "—",
                "Son2_Sira":     son2["sira"]  if son2 else "—",
                "Son2_Derece":   son2["derece"]if son2 else "—",
                "Son2_Hiz(m/s)": son2["hiz"]  if son2 else "—",
                "Fark(m/s)":     fark          if fark is not None else "—",
                "Fark_%":        fark_pct      if fark_pct is not None else "—",
            }
            rows.append(row)
        if not rows: return
        df = pd.DataFrame(rows)
        # En çok hızlanan üstte
        df = df.sort_values(
            "Fark(m/s)",
            key=lambda x: pd.to_numeric(x, errors="coerce").fillna(-999),
            ascending=False
        ).reset_index(drop=True)
        def tag_fn(row, idx):
            t = str(row.get("Trend",""))
            if "HIZLANDI" in t: return "up"
            if "YAVAŞLADI" in t: return "dn"
            if "STABİL"   in t: return "st"
            return "odd" if idx%2==0 else "ev"
        self._fill_tree(self.tree_s2h, df, tag_fn=tag_fn)
        # Grafik için cache
        self._s2h_data = rows
        self.after(100, self._draw_s2h_chart)
    def _draw_s2h_chart(self):
        """Son 2 yarış hız çift bar grafiği."""
        cv = self.cv_s2h; cv.delete("all")
        W  = cv.winfo_width() or 400; H = cv.winfo_height() or 420
        if not hasattr(self,"_s2h_data") or not self._s2h_data or W < 80: return
        data = [r for r in self._s2h_data
                if isinstance(r.get("Son1_Hiz(m/s)"), float)]
        if not data: return
        # Hız değerlerini topla — ölçek için
        all_hiz = []
        for r in data:
            all_hiz.append(r["Son1_Hiz(m/s)"])
            if isinstance(r.get("Son2_Hiz(m/s)"), float):
                all_hiz.append(r["Son2_Hiz(m/s)"])
        if not all_hiz: return
        PL,PR,PT,PB = 52,16,48,50
        mn = min(all_hiz) - 0.2
        mx = max(all_hiz) + 0.2
        rng= max(mx - mn, 0.1)
        n  = len(data)
        grp_w = (W - PL - PR) / n
        bar_w = max(8, int(grp_w * 0.35))
        cv.create_text(W//2, 20,
                       text="Son 2 Yarış Hız Karşılaştırması (m/s)",
                       fill=TEXT, font=F_S)
        # Grid
        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            val = mn + frac * rng
            y   = PT + (1-frac) * (H-PT-PB)
            cv.create_line(PL, y, W-PR, y, fill=BORDER, dash=(2,5))
            cv.create_text(PL-5, y, text=f"{val:.2f}",
                           fill=DIM, font=F_XS, anchor="e")
        for i, row in enumerate(data):
            cx   = PL + (i + 0.5) * grp_w
            h1   = row["Son1_Hiz(m/s)"]
            h2   = row.get("Son2_Hiz(m/s)")
            fark = row.get("Fark(m/s)")
            # Renk: hızlandıysa yeşil, yavaşladıysa kırmızı
            if isinstance(fark, float):
                col1 = GREEN if fark >= 0 else RED
            else:
                col1 = BLUE
            col2 = SILVER
            # Bar 1 (son yarış)
            y1_top = PT + (1 - (h1-mn)/rng) * (H-PT-PB)
            y_bot  = PT + (H-PT-PB)
            cv.create_rectangle(cx - bar_w - 2, y1_top,
                                 cx - 2, y_bot,
                                 fill=col1, outline=BG)
            cv.create_text(cx - bar_w//2 - 2, y1_top - 4,
                           text=f"{h1:.2f}", fill=col1, font=F_XS)
            # Bar 2 (önceki yarış)
            if isinstance(h2, float):
                y2_top = PT + (1 - (h2-mn)/rng) * (H-PT-PB)
                cv.create_rectangle(cx + 2, y2_top,
                                     cx + bar_w + 2, y_bot,
                                     fill=col2, outline=BG)
                cv.create_text(cx + bar_w//2 + 2, y2_top - 4,
                               text=f"{h2:.2f}", fill=col2, font=F_XS)
            # Fark oku
            if isinstance(fark, float) and isinstance(h2, float):
                ok = "▲" if fark > 0 else "▼"
                col_ok = GREEN if fark > 0 else RED
                cv.create_text(cx, y_bot - 4,
                               text=f"{ok}{abs(fark):.3f}",
                               fill=col_ok, font=F_XS)
            # At adı
            cv.create_text(cx, H-PB+14,
                           text=row["At"][:9],
                           fill=TEXT, font=F_XS, angle=38, anchor="nw")
        # Eksen
        cv.create_line(PL, PT, PL, H-PB, fill=DIM)
        cv.create_line(PL, H-PB, W-PR, H-PB, fill=DIM)
        # Legend
        for col, lbl, x in [(GREEN,"Son Yarış (hızlandı)", PL),
                             (RED,  "Son Yarış (yavaşladı)", PL+120),
                             (SILVER,"Önceki Yarış",         PL+240)]:
            cv.create_rectangle(x, H-PB+38, x+10, H-PB+48, fill=col, outline="")
            cv.create_text(x+13, H-PB+43, text=lbl, fill=col, font=F_XS, anchor="w")
    # ── Tab: Senaryo ─────────────────────────────────────
    def _build_senaryo_tab(self, parent):
        # ── Üst kontrol ──────────────────────────────────
        ctrl = tk.Frame(parent, bg=BG)
        ctrl.pack(fill="x", padx=8, pady=(8,4))
        tk.Button(ctrl, text="▶  OYNAT",
                  command=self._oynat_senaryo,
                  bg=ACCENT, fg=TEXT, font=F_M, relief="flat",
                  cursor="hand2", padx=14, pady=7
                  ).pack(side="left")
        tk.Button(ctrl, text="⏹",
                  command=self._durdur_senaryo,
                  bg="#2A2A2A", fg=TEXT, font=F_S, relief="flat",
                  cursor="hand2", padx=8, pady=7
                  ).pack(side="left", padx=4)
        tk.Button(ctrl, text="↺  Başa Al",
                  command=lambda: self._render_frame(0.0),
                  bg="#1E3048", fg=TEXT, font=F_S, relief="flat",
                  cursor="hand2", padx=8, pady=7
                  ).pack(side="left", padx=4)
        tk.Label(ctrl, text="Hız:", font=F_XS, bg=BG, fg=DIM).pack(side="left", padx=(16,2))
        self.anim_hiz = tk.IntVar(value=50)
        ttk.Scale(ctrl, from_=10, to=120, variable=self.anim_hiz,
                  orient="horizontal", length=90).pack(side="left")
        self.sn_info = tk.StringVar(value="Analiz çalıştırınca senaryo oluşur.")
        tk.Label(ctrl, textvariable=self.sn_info,
                 font=F_XS, bg=BG, fg=TEAL).pack(side="left", padx=16)
        # ── Orta alan: animasyon (sol) + pozisyon tablosu (sağ) ──
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8, pady=(4,4))
        # Sol: pist animasyonu
        left = tk.Frame(mid, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(left, text="Yarış Pisti — Animasyon",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_sen = tk.Canvas(left, bg="#0A1A0A",
                                highlightthickness=1, highlightbackground=BORDER)
        self.cv_sen.pack(fill="both", expand=True)
        self.cv_sen.bind("<Configure>", lambda e: self._draw_senaryo_static())
        # Sağ: split pozisyon tablosu
        right = tk.Frame(mid, bg=BG, width=420)
        right.pack(side="left", fill="both")
        right.pack_propagate(False)
        tk.Label(right, text="📍 Split Bazlı Pozisyon Tahmini",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        # Treeview — sütunlar: At, 200m, 400m, 600m, Son200m, Bitiş
        tf = tk.Frame(right, bg=PANEL,
                      highlightthickness=1, highlightbackground=BORDER)
        tf.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(tf, orient="vertical")
        self.tree_sen = ttk.Treeview(tf, show="headings",
                                      yscrollcommand=vsb.set)
        vsb.config(command=self.tree_sen.yview)
        vsb.pack(side="right", fill="y")
        self.tree_sen.pack(fill="both", expand=True)
        split_cols = [
            ("No",     30),
            ("At",    110),
            ("Start",  45),
            ("200m",   45),
            ("400m",   45),
            ("600m",   45),
            ("800m",   45),
            ("Son200", 50),
            ("Bitiş",  45),
            ("Güç",    45),
        ]
        self.tree_sen["columns"] = [c for c,_ in split_cols]
        for col, w in split_cols:
            self.tree_sen.heading(col, text=col)
            self.tree_sen.column(col, width=w, anchor="center", minwidth=w)
        self.tree_sen.tag_configure("g1",  background="#1F3A12", foreground=GOLD)
        self.tree_sen.tag_configure("g2",  background="#112233", foreground=SILVER)
        self.tree_sen.tag_configure("g3",  background="#2A1A08", foreground=BRONZE)
        self.tree_sen.tag_configure("ond", background="#0F2210", foreground=GREEN)
        self.tree_sen.tag_configure("ger", background="#0F1A2A", foreground=BLUE)
        self.tree_sen.tag_configure("odd", background="#162030")
        self.tree_sen.tag_configure("ev",  background=PANEL)
        # ── Alt: yarış yorumu (ince) ──────────────────────
        yt = tk.Frame(parent, bg=BG)
        yt.pack(fill="x", padx=8, pady=(0,6))
        tk.Label(yt, text="Yarış Yorumu:", font=F_S, bg=BG, fg=DIM).pack(side="left")
        self.txt_sen = tk.Text(yt, bg=PANEL, fg=TEXT, font=F_XS,
                               height=5, relief="flat",
                               highlightthickness=1, highlightbackground=BORDER,
                               state="disabled", wrap="word")
        self.txt_sen.pack(fill="x", expand=True, padx=(6,0))
        # Animasyon state
        self._anim_running = False
        self._anim_frame   = 0
    # ── Senaryo Hesaplama ─────────────────────────────────
    def _compute_senaryo(self):
        """
        Her at için koşu boyunca tahmini pozisyonu hesapla.
        Splitler: start, 200m, 400m, 600m, (800m), son200m, finish
        Returns list of {at, stil, renkler, pozlar, yorum}
        """
        if not self.sel_kosu: return []
        atlar = self.sel_kosu.get("atlar", [])
        if not atlar: return []
        mesafe = 0
        try: mesafe = int(re.sub(r"[^\d]","",self.sel_kosu.get("mesafe","") or ""))
        except: pass
        result = []
        n_at   = len(atlar)
        for i, at in enumerate(atlar):
            adi   = at.get("at","")
            stil  = self.stiller.get(adi, {})
            galop = self.galop_an.get(adi, {})
            perf  = self.performlar.get(adi, {})
            son10 = at.get("son10", [])
            # ── Temel parametreler ──
            # Stil skoru: önden=1, orta=0, geriden=-1
            stil_txt = stil.get("stil","")
            if "ÖNDEN" in stil_txt:       stil_skor = 1.0
            elif "ORTADAN" in stil_txt:   stil_skor = 0.0
            else:                          stil_skor = -1.0
            # Hız kapasitesi (galop + performans)
            hiz_kap = 0.5
            en_iyi  = galop.get("en_iyi_400")
            if en_iyi:
                hiz_kap = max(0, min(1, (28.0 - en_iyi) / 6.0))
            gun_fark = galop.get("gun_fark")
            taze_mod = 1.0 if gun_fark is not None and gun_fark <= 7 else \
                       0.85 if gun_fark is not None and gun_fark <= 14 else 0.7
            trend_skor = perf.get("trend_skor", 0) or 0
            trend_mod  = 1.0 + min(0.15, max(-0.15, trend_skor * 0.1))
            # Son 3 form
            son3 = [s for s in son10[:3] if isinstance(s,int) and s>0]
            form_mod = 1.0
            if son3:
                ort = sum(son3)/len(son3)
                form_mod = max(0.7, min(1.2, 1.5 - ort*0.1))
            # Genel güç = hız × tazelik × trend × form
            guc = hiz_kap * taze_mod * trend_mod * form_mod
            # ── Pozisyon simülasyonu ──
            # Her split noktasında sıra tahmini (1=başta)
            # start_pos: önden koşanlar küçük sayı, kapıcılar büyük
            noise_seed = hash(adi) % 100 / 100.0  # at başına sabit gürültü
            start_pos = 1 + (1 - stil_skor) * (n_at/2 - 1) + noise_seed * 1.5
            start_pos = max(1, min(n_at, start_pos))
            # Koşunun ilerleyişinde güçlü at öne geçer
            # split_pct: 0=start, 0.3=erken, 0.6=orta, 1.0=bitiş
            def pos_at(pct):
                # Önden: erken iyi, sonda yorulabilir
                if stil_skor > 0.5:
                    early_bonus = -1.5 * guc
                    late_fade   = pct * 1.5 * (1 - guc)
                    p = start_pos + early_bonus + late_fade
                # Geriden: başta geride, sonda yükselir
                elif stil_skor < -0.3:
                    late_gain = -pct * 3.0 * guc
                    p = start_pos + late_gain
                # Ortadan
                else:
                    mid_gain = -pct * 1.5 * guc
                    p = start_pos + mid_gain
                return max(1.0, min(float(n_at), p))
            splits = [0.0, 0.15, 0.35, 0.55, 0.75, 0.90, 1.0]
            pozlar = [round(pos_at(s), 2) for s in splits]
            # Bitiş sırası
            finish = round(pozlar[-1])
            finish = max(1, min(n_at, finish))
            result.append({
                "at":      adi,
                "no":      at.get("no",""),
                "stil":    stil_txt or "?",
                "stil_skor": stil_skor,
                "guc":     round(guc, 3),
                "pozlar":  pozlar,
                "finish":  finish,
                "renk":    LINE_C[i % len(LINE_C)],
                "taki":    at.get("taki",""),
                "agf":     at.get("agf",""),
                "en_iyi_400": en_iyi,
                "gun_fark":   gun_fark,
                "trend":   perf.get("trend",""),
            })
        # Bitiş sıralarını normalize et (1..n eşsiz)
        result.sort(key=lambda x: x["pozlar"][-1])
        for rank, r in enumerate(result, 1):
            r["finish_rank"] = rank
        return result
    def _yorum_uret(self, senaryo: list, mesafe: int) -> str:
        """Senaryo verisiyle Türkçe yarış yorumu oluştur."""
        if not senaryo: return "Yeterli veri yok."
        lideri  = [r for r in senaryo if "ÖNDEN" in r["stil"]]
        kapici  = [r for r in senaryo if "GERİDEN" in r["stil"] or "KAPICI" in r["stil"]]
        tahmini = senaryo[0]  # bitiş sıralaması 1. tahmin
        lines = []
        # Pist yorumu
        if mesafe and mesafe <= 1200:
            lines.append(f"⚡ {mesafe}m sprint mesafesi — start hızı kritik, önden koşanlar avantajlı.")
        elif mesafe and mesafe >= 2000:
            lines.append(f"🏃 {mesafe}m uzun mesafe — geriden gelenler ve dayanıklılık ön plana çıkar.")
        else:
            lines.append(f"🎯 {mesafe}m orta mesafe — her stilden at şansına sahip.")
        # Lider tahmini
        lider_adlari = ", ".join(r["at"] for r in sorted(lideri, key=lambda x: x["guc"], reverse=True)[:3])
        if lider_adlari:
            lines.append(f"\n🟢 ÖNDEN KOŞACAKLAR: {lider_adlari}")
            lines.append("   Bu atlar start bandından ilk pozisyonu almaya çalışacak.")
        # Kapıcılar
        kap_adlari = ", ".join(r["at"] for r in sorted(kapici, key=lambda x: x["guc"], reverse=True)[:3])
        if kap_adlari:
            lines.append(f"\n🔵 GERİDEN YÜKSELECEKLER: {kap_adlari}")
            lines.append("   Son 400m'de pozisyon kazanımı bekleniyor.")
        # Tehlikeli atlar
        tehlikeli = [r for r in senaryo
                     if r["guc"] > 0.6 and r.get("gun_fark") is not None and r["gun_fark"] <= 7]
        if tehlikeli:
            t_adi = ", ".join(r["at"] for r in tehlikeli[:2])
            lines.append(f"\n⚠️  TEHLİKELİ ADAYLAR: {t_adi}")
            lines.append("   Hem taze hem güçlü galop — formda görünüyor.")
        # Sürpriz adaylar
        surpriz = [r for r in senaryo
                   if r.get("trend","") == "🟢 YÜKSELİYOR" and r["finish_rank"] <= 4]
        if surpriz:
            s_adi = ", ".join(r["at"] for r in surpriz[:2])
            lines.append(f"\n🚀 YÜKSELİŞ TRENDİ: {s_adi}")
            lines.append("   Son koşularda hız arttı — sürpriz yapabilir.")
        # Tahmini finalist
        top3 = [r["at"] for r in senaryo[:3]]
        lines.append(f"\n🏆 TAHMİNİ İLK 3: {' — '.join(top3)}")
        # Riskler
        riskler = []
        for r in senaryo:
            if r.get("gun_fark") is not None and r["gun_fark"] > 21:
                riskler.append(f"{r['at']} (son galop {r['gun_fark']}g önce)")
        if riskler:
            lines.append(f"\n⚫ HAZIRLIK SORUSU: {', '.join(riskler[:2])}")
        return "\n".join(lines)
    def _update_senaryo(self):
        """Analiz bittikten sonra senaryoyu hesapla, tabloyu ve yorumu doldur."""
        self._senaryo_data = self._compute_senaryo()
        mesafe = 0
        try: mesafe = int(re.sub(r"[^\d]","",self.sel_kosu.get("mesafe","") or ""))
        except: pass
        # ── Split pozisyon tablosu ────────────────────────
        self._fill_split_table()
        # ── Yarış yorumu ─────────────────────────────────
        yorum = self._yorum_uret(self._senaryo_data, mesafe)
        self.txt_sen.config(state="normal")
        self.txt_sen.delete("1.0","end")
        self.txt_sen.insert("end", yorum)
        self.txt_sen.config(state="disabled")
        # Statik çizim
        self._draw_senaryo_static()
        n = len(self._senaryo_data)
        self.sn_info.set(f"{n} at  —  ▶ Oynat  |  Sağda split pozisyon tablosu")
        # Sekmeye geç
        self.nb.select(7)
    def _fill_split_table(self):
        """Split bazlı pozisyon tahmin tablosunu doldur — bitiş sırasına göre sırala."""
        tree = self.tree_sen
        tree.delete(*tree.get_children())
        if not hasattr(self,"_senaryo_data") or not self._senaryo_data:
            return
        # Nokta etiketleri: [Start, 200m, 400m, 600m, 800m, Son200, Bitiş]
        split_pcts = [0.0, 0.15, 0.35, 0.55, 0.75, 0.90, 1.0]
        def interp(pozlar, pct):
            for i in range(len(split_pcts)-1):
                if split_pcts[i] <= pct <= split_pcts[i+1]:
                    t = (pct-split_pcts[i])/(split_pcts[i+1]-split_pcts[i])
                    return pozlar[i] + t*(pozlar[i+1]-pozlar[i])
            return pozlar[-1]
        # Bitiş sırasına göre sırala
        sorted_data = sorted(self._senaryo_data, key=lambda r: r["finish_rank"])
        for idx, r in enumerate(sorted_data):
            finish = r["finish_rank"]
            # Her split için tahmini pozisyon (1..n, yuvarlanmış)
            def pos(pct):
                v = interp(r["pozlar"], pct)
                return str(int(round(v)))
            guc_pct = f"%{int(r['guc']*100)}"
            vals = (
                r["no"],
                r["at"],
                pos(0.0),    # Start
                pos(0.15),   # 200m
                pos(0.35),   # 400m
                pos(0.55),   # 600m
                pos(0.75),   # 800m
                pos(0.90),   # Son 200m
                str(finish), # Bitiş
                guc_pct,
            )
            # Tag
            if finish == 1:   tag = "g1"
            elif finish == 2: tag = "g2"
            elif finish == 3: tag = "g3"
            elif "ÖNDEN" in r["stil"]:  tag = "ond"
            elif "GERİDEN" in r["stil"] or "KAPICI" in r["stil"]: tag = "ger"
            else: tag = "odd" if idx%2==0 else "ev"
            tree.insert("","end", values=vals, tags=(tag,))
    def _draw_senaryo_static(self):
        """Statik son durum çizimi (animasyon olmadan)."""
        if not hasattr(self,"_senaryo_data") or not self._senaryo_data:
            return
        self._render_frame(1.0)
    def _render_frame(self, pct: float):
        """
        pct: 0.0 (start) → 1.0 (finish)
        Her at için pct'ye göre interpolasyon yap ve pisti çiz.
        """
        cv = self.cv_sen
        cv.delete("all")
        W = cv.winfo_width()  or 900
        H = cv.winfo_height() or 400
        if W < 100 or H < 100: return
        data = self._senaryo_data
        n_at = len(data)
        # Pist arka planı
        PIST_TOP    = 60
        PIST_BOT    = H - 80
        LANE_H      = (PIST_BOT - PIST_TOP) / max(n_at, 1)
        PIST_LEFT   = 120
        PIST_RIGHT  = W - 160
        # Zemin
        cv.create_rectangle(PIST_LEFT, PIST_TOP,
                             PIST_RIGHT, PIST_BOT,
                             fill="#1A2A0A", outline=BORDER)
        # Şerit çizgileri
        for i in range(n_at + 1):
            y = PIST_TOP + i * LANE_H
            cv.create_line(PIST_LEFT, y, PIST_RIGHT, y,
                           fill="#2A3A1A", width=1)
        # Start + bitiş çizgisi
        cv.create_line(PIST_LEFT, PIST_TOP-5,
                       PIST_LEFT, PIST_BOT+5, fill=SILVER, width=2)
        cv.create_line(PIST_RIGHT, PIST_TOP-5,
                       PIST_RIGHT, PIST_BOT+5, fill=GOLD, width=3, dash=(5,3))
        # Mesafe etiketleri
        splits_pct  = [0.0, 0.15, 0.35, 0.55, 0.75, 0.90, 1.0]
        splits_lbl  = ["Start","200m","400m","600m","800m","Son200m","Bitiş"]
        mesafe = 0
        try: mesafe = int(re.sub(r"[^\d]","",self.sel_kosu.get("mesafe","") or ""))
        except: pass
        for sp, lbl in zip(splits_pct, splits_lbl):
            x = PIST_LEFT + sp * (PIST_RIGHT - PIST_LEFT)
            if sp > 0 and sp < 1:
                cv.create_line(x, PIST_TOP, x, PIST_BOT,
                               fill="#2A4A1A", dash=(3,6))
            cv.create_text(x, PIST_TOP - 12, text=lbl,
                           fill=DIM, font=F_XS, anchor="s")
        # Başlık
        sn_pct_txt = f"{int(pct*100)}%"
        kosu_txt = (f"{self.sel_kosu.get('no','')}. Koşu  "
                    f"{self.sel_kosu.get('mesafe','')}m {self.sel_kosu.get('pist','')}  "
                    f"— Senaryo  {sn_pct_txt}")
        cv.create_text(W//2, 20, text=kosu_txt,
                       fill=GOLD, font=F_M, anchor="center")
        # Splits indeksi için pct→pozisyon interpolasyonu
        def interp_pos(pozlar, pct):
            """7 noktalı pozisyon listesinden pct anındaki değeri interpole et."""
            n = len(splits_pct) - 1
            for i in range(n):
                if splits_pct[i] <= pct <= splits_pct[i+1]:
                    t = (pct - splits_pct[i]) / (splits_pct[i+1] - splits_pct[i])
                    return pozlar[i] + t * (pozlar[i+1] - pozlar[i])
            return pozlar[-1]
        # Her at çiz
        for r in data:
            pos  = interp_pos(r["pozlar"], pct)   # 1..n arası float
            col  = r["renk"]
            at   = r["at"]
            # Şerit y koordinatı (pos büyüdükçe aşağı → 1=en üst)
            lane_y = PIST_TOP + (pos - 0.5) * LANE_H
            # x koordinatı: pct → pist üzerinde konum
            x = PIST_LEFT + pct * (PIST_RIGHT - PIST_LEFT)
            # At simgesi (oval)
            R = max(8, int(LANE_H * 0.32))
            cv.create_oval(x-R*2, lane_y-R,
                           x+R*0.5, lane_y+R,
                           fill=col, outline=BG, width=1)
            # At adı sol tarafta (start öncesi)
            if pct < 0.05:
                cv.create_text(PIST_LEFT - 5, lane_y,
                               text=f"{r['no']}. {at[:12]}",
                               fill=col, font=F_XS, anchor="e")
            # İsim etiketi atın üzerinde
            cv.create_text(x - R*0.8, lane_y - R - 4,
                           text=at[:8],
                           fill=col, font=F_XS, anchor="s")
        # Sağda bitiş sıralaması (pct > 0.85 iken)
        if pct > 0.85:
            sorted_now = sorted(data, key=lambda r: interp_pos(r["pozlar"], pct))
            for rank, r in enumerate(sorted_now, 1):
                y_rank = PIST_BOT + 18 + (rank-1) * 0 # sıralamayı sağda yaz
                x_rank = PIST_RIGHT + 10
                col    = [GOLD, SILVER, BRONZE][rank-1] if rank <= 3 else DIM
                cv.create_text(x_rank, PIST_TOP + (rank-0.5) * LANE_H,
                               text=f"{rank}. {r['at'][:12]}",
                               fill=col, font=F_XS, anchor="w")
    # ── Animasyon ─────────────────────────────────────────
    def _oynat_senaryo(self):
        if not hasattr(self,"_senaryo_data") or not self._senaryo_data:
            messagebox.showwarning("Uyarı","Önce koşuyu analiz edin.")
            return
        self._anim_running = True
        self._anim_frame   = 0
        self._anim_step()
    def _durdur_senaryo(self):
        self._anim_running = False
    def _anim_step(self):
        if not self._anim_running: return
        TOTAL_FRAMES = 120
        pct = self._anim_frame / TOTAL_FRAMES
        self._render_frame(min(pct, 1.0))
        self._anim_frame += 1
        if self._anim_frame > TOTAL_FRAMES:
            self._anim_running = False
            self._render_frame(1.0)
            return
        delay = max(8, 130 - self.anim_hiz.get())
        self.after(delay, self._anim_step)
    # ── Tab: TJK Tempo Analizi ────────────────────────────

    def _build_tjk_tab(self, parent):
        # Üst kontrol paneli
        ctrl = tk.Frame(parent, bg=BG)
        ctrl.pack(fill="x", padx=8, pady=(8,4))

        tk.Button(ctrl, text="🏁  TJK SONUÇLARI ÇEK",
                  command=self._cek_tjk_sonuclar,
                  bg="#8E1A1A", fg=TEXT, font=F_M, relief="flat",
                  cursor="hand2", padx=14, pady=7).pack(side="left")

        tk.Label(ctrl, text="Koşu:", font=F_S, bg=BG, fg=DIM).pack(side="left", padx=(16,2))
        self.tjk_kosu_var = tk.StringVar(value="Tümü")
        self.tjk_kosu_cb = ttk.Combobox(ctrl, textvariable=self.tjk_kosu_var,
                                         state="readonly", width=12, font=F_N)
        self.tjk_kosu_cb.pack(side="left", padx=4)
        self.tjk_kosu_cb.bind("<<ComboboxSelected>>",
                              lambda e: self._filtrele_tjk())

        tk.Label(ctrl, text="Min Pace:", font=F_S, bg=BG, fg=DIM).pack(side="left", padx=(12,2))
        self.tjk_min_pace = tk.StringVar(value="98")
        ttk.Combobox(ctrl, textvariable=self.tjk_min_pace,
                     values=["95","97","98","100","102","103","105"],
                     state="readonly", width=5, font=F_N).pack(side="left", padx=4)

        tk.Button(ctrl, text="⭐ Yıldızları Bul", command=self._filtrele_tjk,
                  bg="#7D6608", fg=TEXT, font=F_S, relief="flat",
                  cursor="hand2", padx=8, pady=5).pack(side="left", padx=4)

        self.tjk_info = tk.StringVar(value="TJK sonuçlarını çekmek için butona basın.")
        tk.Label(ctrl, textvariable=self.tjk_info,
                 font=F_XS, bg=BG, fg=TEAL).pack(side="left", padx=12)

        # Koşu tempo kartları
        self.tjk_cards = tk.Frame(parent, bg=BG)
        self.tjk_cards.pack(fill="x", padx=8, pady=(0,4))

        # Yıldız atlar özet
        self.tjk_stars_frame = tk.Frame(parent, bg=BG)
        self.tjk_stars_frame.pack(fill="x", padx=8, pady=(0,4))

        # Ana alan: tablo (sol) + grafikler (sağ)
        mid = tk.Frame(parent, bg=BG)
        mid.pack(fill="both", expand=True, padx=8)

        # Sol: sonuç tablosu
        lp = tk.Frame(mid, bg=BG)
        lp.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(lp, text="TJK Yarış Sonuçları — Tempo & Pace Figür Analizi",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.tree_tjk = self._make_tree(lp)

        # Sağ: grafikler (üst: tempo bar, alt: pace dağılım)
        rp = tk.Frame(mid, bg=BG, width=440)
        rp.pack(side="left", fill="both")
        rp.pack_propagate(False)

        tk.Label(rp, text="Koşu Tempo Karşılaştırması",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_tjk_tempo = tk.Canvas(rp, bg=PANEL, height=180,
                                       highlightthickness=1,
                                       highlightbackground=BORDER)
        self.cv_tjk_tempo.pack(fill="x", padx=0, pady=(0,6))
        self.cv_tjk_tempo.bind("<Configure>", lambda e: self._draw_tjk_tempo())

        tk.Label(rp, text="Pace Figür Dağılımı (at bazlı)",
                 font=F_M, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        self.cv_tjk_pace = tk.Canvas(rp, bg=PANEL,
                                      highlightthickness=1,
                                      highlightbackground=BORDER)
        self.cv_tjk_pace.pack(fill="both", expand=True)
        self.cv_tjk_pace.bind("<Configure>", lambda e: self._draw_tjk_pace())

    def _cek_tjk_sonuclar(self):
        if not self._ready:
            messagebox.showwarning("Bekle", "Sistem hazırlanıyor."); return
        if not BS4:
            messagebox.showerror("Hata", "beautifulsoup4 gerekli."); return
        tarih = self.e_tarih.get().strip()
        sehir = self.sehir_var.get().strip()
        if not tarih or not sehir:
            messagebox.showwarning("Uyarı", "Tarih ve şehir seçin."); return
        threading.Thread(target=self._tjk_worker, args=(tarih, sehir), daemon=True).start()

    def _tjk_worker(self, tarih, sehir):
        self.prog.start(10)
        self._st(f"TJK sonuçları çekiliyor: {tarih} {sehir}…")
        try:
            rows = scrape_tjk_sonuclar(tarih, sehir)
            if not rows:
                self.after(0, lambda: messagebox.showwarning("Sonuç Yok",
                    "TJK sonucu bulunamadı.\n• Koşu bitti mi?\n• Tarih/şehir doğru mu?"))
                return
            self.tjk_rows = rows
            self.tjk_analiz = analiz_tempo(rows)
            self.after(0, lambda: self._on_tjk_sonuclar())
            self._st(f"✓ TJK: {len(rows)} at sonucu  |  "
                     f"{len(self.tjk_analiz.get('yildizlar', []))} yıldız at  |  "
                     f"Kaynak: {rows[0].get('kaynak', '?')}")
        except Exception as e:
            self.after(0, lambda e2=str(e): messagebox.showerror("TJK Hata", f"TJK sonuçları:\n{e2}"))
            self._st(f"TJK HATA: {e}")
        finally:
            self.prog.stop()

    def _on_tjk_sonuclar(self):
        kosular = sorted(self.tjk_analiz.get("kosular", {}).keys())
        vals = ["Tümü"] + [f"{k}. Koşu" for k in kosular]
        self.tjk_kosu_cb["values"] = vals
        self.tjk_kosu_var.set("Tümü")
        self._draw_tjk_cards()
        self._draw_tjk_stars()
        self._filtrele_tjk()
        n_rows = len(self.tjk_rows)
        n_star = len(self.tjk_analiz.get("yildizlar", []))
        n_kosu = len(kosular)
        self.tjk_info.set(f"{n_rows} at  |  {n_kosu} koşu  |  {n_star} yıldız performans")

    def _draw_tjk_cards(self):
        """Koşu bazında tempo kartları."""
        for w in self.tjk_cards.winfo_children():
            w.destroy()
        if not self.tjk_analiz:
            return

        tk.Label(self.tjk_cards, text="📊 Koşu Tempoları",
                 font=F_M, bg=BG, fg=TEXT).pack(side="left", padx=(0,12))

        for kno, ka in sorted(self.tjk_analiz.get("kosular", {}).items()):
            col = GOLD if "HIZLI" in ka["tempo_kat"] else GREEN if "NORMAL" in ka["tempo_kat"] else BLUE
            c = tk.Frame(self.tjk_cards, bg=CARD,
                         highlightthickness=2, highlightbackground=col,
                         padx=10, pady=5)
            c.pack(side="left", padx=(0,6))
            tk.Label(c, text=f"{kno}. Koşu", font=F_S, bg=CARD, fg=TEXT).pack()
            tk.Label(c, text=f"{ka['ort_hiz']:.2f} m/s",
                     font=("Segoe UI", 11, "bold"), bg=CARD, fg=col).pack()
            tk.Label(c, text=f"{ka['tempo_kat']}  {ka['msf']}m {ka['pist']}",
                     font=F_XS, bg=CARD, fg=DIM).pack()
            tk.Label(c, text=f"{ka['at_sayisi']} at  |  σ={ka['std']:.3f}",
                     font=F_XS, bg=CARD, fg=DIM).pack()

    def _draw_tjk_stars(self):
        """Yıldız atlar özet kartları."""
        for w in self.tjk_stars_frame.winfo_children():
            w.destroy()
        yildizlar = self.tjk_analiz.get("yildizlar", [])
        if not yildizlar:
            return

        tk.Label(self.tjk_stars_frame, text="⭐ Yıldız Performanslar",
                 font=F_M, bg=BG, fg=GOLD).pack(side="left", padx=(0,12))

        colors = [GOLD, SILVER, BRONZE, TEAL, GREEN]
        for i, y in enumerate(yildizlar[:5]):
            col = colors[i] if i < len(colors) else DIM
            c = tk.Frame(self.tjk_stars_frame, bg=CARD,
                         highlightthickness=2, highlightbackground=col,
                         padx=10, pady=4)
            c.pack(side="left", padx=(0,6))
            tk.Label(c, text=f"{y.get('yildiz','')} {y['at'][:14]}",
                     font=F_S, bg=CARD, fg=TEXT).pack()
            tk.Label(c, text=f"Pace: {y['pace_fig']}  |  {y['hiz_ms']:.2f} m/s",
                     font=("Segoe UI", 10, "bold"), bg=CARD, fg=col).pack()
            tk.Label(c, text=f"{y['sira']}. sıra  |  {y['kosu_no']}. koşu  |  {y['msf']}m",
                     font=F_XS, bg=CARD, fg=DIM).pack()

    def _filtrele_tjk(self):
        """TJK sonuç tablosunu filtrele ve doldur."""
        if not self.tjk_analiz:
            return

        tum = self.tjk_analiz.get("tum", [])
        secim = self.tjk_kosu_var.get()
        if secim and secim not in ("Tümü",):
            m = re.search(r"(\d+)", secim)
            if m:
                tum = [r for r in tum if r["kosu_no"] == int(m.group(1))]

        try:
            min_pace = float(self.tjk_min_pace.get())
        except:
            min_pace = 98

        rows = []
        for r in tum:
            yildiz = ""
            pf = r["pace_fig"]
            tr = r["tempo_rtg"]
            sira = r["sira"]

            if pf >= 108 and sira == 1:
                yildiz = "★★★🔥"
            elif pf >= 105 and sira <= 2:
                yildiz = "★★★"
            elif pf >= 103 and sira <= 3:
                yildiz = "★★"
            elif pf >= 101 and sira <= 3:
                yildiz = "★"
            elif tr >= 2.0:
                yildiz = "★★🌟"
            elif tr >= 1.5:
                yildiz = "★🌟"
            elif tr >= 1.0:
                yildiz = "✨"

            rows.append({
                "Yıldız":     yildiz,
                "Koşu":       r["kosu_no"],
                "Sıra":       sira,
                "At":         r["at"],
                "Derece":     r["derece"],
                "Hız(m/s)":   r["hiz_ms"],
                "Pace":       r["pace_fig"],
                "TmpRtg":     r["tempo_rtg"],
                "Mesafe":     r["msf"],
                "Pist":       r["pist"],
                "Kilo":       r["kilo"],
                "Jokey":      r["jokey"],
                "Fark":       r["fark"],
                "Ganyan":     r["ganyan"],
                "Antrenör":   r["antrenor"],
            })

        df = pd.DataFrame(rows)
        if df.empty:
            return

        df = df.sort_values(["Koşu", "Sıra"]).reset_index(drop=True)

        def tag_fn(row, idx):
            y = str(row.get("Yıldız", ""))
            s = row.get("Sıra", 99)
            try:
                s = int(s)
            except:
                s = 99
            if "★★★" in y or "🔥" in y:
                return "g1"
            if "★★" in y:
                return "g2"
            if "★" in y or "🌟" in y:
                return "g3"
            if s == 1:
                return "up"
            if s <= 3:
                return "st"
            return "odd" if idx % 2 == 0 else "ev"

        self._fill_tree(self.tree_tjk, df, tag_fn=tag_fn)
        self.after(80, self._draw_tjk_tempo)
        self.after(100, self._draw_tjk_pace)

    def _draw_tjk_tempo(self):
        """Koşu bazında ortalama hız bar grafiği."""
        cv = self.cv_tjk_tempo
        cv.delete("all")
        W = cv.winfo_width() or 440
        H = cv.winfo_height() or 180
        kosular = self.tjk_analiz.get("kosular", {})
        if not kosular or W < 80:
            return

        items = sorted(kosular.values(), key=lambda x: x["kosu_no"])
        PL, PR, PT, PB = 48, 12, 28, 36
        vals = [k["ort_hiz"] for k in items]
        mn = max(0, min(vals) - 0.5)
        mx = max(vals) + 0.5
        rng = max(mx - mn, 0.1)
        n = len(items)
        bw = max(20, int((W - PL - PR) / n) - 6)
        xs = (W - PL - PR) / n

        cv.create_text(W // 2, 14, text="Koşu Ortalama Tempo (m/s)",
                       fill=TEXT, font=F_S)

        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            val = mn + frac * rng
            y = PT + (1 - frac) * (H - PT - PB)
            cv.create_line(PL, y, W - PR, y, fill=BORDER, dash=(2, 5))
            cv.create_text(PL - 5, y, text=f"{val:.1f}", fill=DIM, font=F_XS, anchor="e")

        for i, k in enumerate(items):
            frac = (k["ort_hiz"] - mn) / rng
            bh = max(4, int(frac * (H - PT - PB)))
            x0 = PL + i * xs + (xs - bw) / 2
            x1 = x0 + bw
            y1 = H - PB
            y0 = y1 - bh

            if "HIZLI" in k["tempo_kat"]:
                col = GOLD if "ÇOK" in k["tempo_kat"] else GREEN
            elif "NORMAL" in k["tempo_kat"]:
                col = TEAL
            elif "YAVAŞ" in k["tempo_kat"]:
                col = ORANGE if "ÇOK" in k["tempo_kat"] else YELLOW
            else:
                col = BLUE

            cv.create_rectangle(x0, y0, x1, y1, fill=col, outline=BG)
            cv.create_text((x0 + x1) / 2, y0 - 5,
                           text=f"{k['ort_hiz']:.2f}", fill=col, font=F_XS)
            cv.create_text((x0 + x1) / 2, y1 + 6,
                           text=f"{k['kosu_no']}. ({k['msf']}m)",
                           fill=DIM, font=F_XS)

        cv.create_line(PL, PT, PL, H - PB, fill=DIM)
        cv.create_line(PL, H - PB, W - PR, H - PB, fill=DIM)

    def _draw_tjk_pace(self):
        """At bazında pace figür bar grafiği — en iyiler üstte."""
        cv = self.cv_tjk_pace
        cv.delete("all")
        W = cv.winfo_width() or 440
        H = cv.winfo_height() or 300
        tum = self.tjk_analiz.get("tum", [])
        if not tum or W < 80:
            return

        # Seçili koşuya filtrele
        secim = self.tjk_kosu_var.get()
        data = tum
        if secim and secim not in ("Tümü",):
            m = re.search(r"(\d+)", secim)
            if m:
                data = [r for r in data if r["kosu_no"] == int(m.group(1))]

        if not data:
            return

        # Pace'e göre sırala, en iyi üstte
        data = sorted(data, key=lambda x: x["pace_fig"], reverse=True)[:16]

        PL, PR, PT, PB = 100, 16, 28, 12
        vals = [d["pace_fig"] for d in data]
        mn = min(90, min(vals) - 2)
        mx = max(vals) + 2
        rng = max(mx - mn, 1)
        n = len(data)
        bh = max(10, int((H - PT - PB) / n) - 3)
        ys = (H - PT - PB) / n

        cv.create_text(W // 2, 14, text="Pace Figür (100 = koşu ortalaması)",
                       fill=TEXT, font=F_S)

        # 100 çizgisi (ortalama)
        x100 = PL + (100 - mn) / rng * (W - PL - PR)
        cv.create_line(x100, PT, x100, H - PB, fill=SILVER, width=2, dash=(4, 3))
        cv.create_text(x100, PT - 4, text="100", fill=SILVER, font=F_XS)

        for i, d in enumerate(data):
            y_center = PT + (i + 0.5) * ys
            pace = d["pace_fig"]
            bar_w = max(4, int((pace - mn) / rng * (W - PL - PR)))
            x0 = PL
            x1 = PL + bar_w

            # Renk: pace > 103 altın, > 100 yeşil, < 98 kırmızı
            if pace >= 105:
                col = GOLD
            elif pace >= 103:
                col = GREEN
            elif pace >= 100:
                col = TEAL
            elif pace >= 98:
                col = YELLOW
            else:
                col = RED

            cv.create_rectangle(x0, y_center - bh / 2,
                                x1, y_center + bh / 2,
                                fill=col, outline=BG)
            cv.create_text(x1 + 4, y_center,
                           text=f"{pace:.0f}",
                           fill=col, font=F_XS, anchor="w")

            # İsim + sıra
            sira_col = GOLD if d["sira"] == 1 else SILVER if d["sira"] == 2 else BRONZE if d["sira"] == 3 else DIM
            cv.create_text(PL - 4, y_center,
                           text=f"{d['sira']}. {d['at'][:12]}",
                           fill=sira_col, font=F_XS, anchor="e")

    # ── Export ───────────────────────────────────────────
    def export_excel(self):
        if not self.sel_kosu:
            messagebox.showwarning("Uyarı","Veri yok."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")],
            initialfile=f"analiz_{self.bulten['sehir']}_{self.bulten['tarih'].replace('.','')}.xlsx")
        if not path: return
        atlar = self.sel_kosu.get("atlar",[])
        rows  = []
        for at in atlar:
            adi = at.get("at","")
            g   = self.galop_an.get(adi,{})
            s   = self.stiller.get(adi,{})
            p   = self.performlar.get(adi,{})
            rows.append({
                "No":at.get("no",""),"At":adi,"AGF":at.get("agf",""),
                "Hnd":at.get("hnd",""),"Kilo":at.get("kilo",""),
                "Jokey":at.get("jokey",""),"Taki":at.get("taki",""),
                "Son10":at.get("son10_str",""),
                "En_Iyi_400":g.get("en_iyi_400",""),"Ort_400":g.get("ort_400",""),
                "Son_Galop_Gun":g.get("gun_fark",""),
                "Kosu_Stili":s.get("stil",""),"Ort_Sira":s.get("ort_sira",""),
                "Ilk3_%":s.get("ilk3_pct",""),"Son5":s.get("son5",""),
                "Pist_Pref":s.get("pist_pref",""),
                "Trend":p.get("trend",""),"Trend_Skor":p.get("trend_skor",""),
            })
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            pd.DataFrame(rows).to_excel(w, index=False, sheet_name="Analiz")
            if self.galoplar:
                pd.DataFrame(self.galoplar).to_excel(w, index=False, sheet_name="Galoplar")
            if self.jokey_stats:
                j_rows = [{"Jokey": k, **v} for k, v in
                          sorted(self.jokey_stats.items(), key=lambda x: -x[1].get("win_pct",0))]
                pd.DataFrame(j_rows).to_excel(w, index=False, sheet_name="Jokeyler")
            if self.tjk_rows:
                pd.DataFrame(self.tjk_rows).to_excel(w, index=False, sheet_name="TJK_Sonuc")
            if self.tjk_analiz.get("yildizlar"):
                yld = [{k: v for k, v in y.items() if k != "sektorler"}
                       for y in self.tjk_analiz["yildizlar"]]
                pd.DataFrame(yld).to_excel(w, index=False, sheet_name="TJK_Yildiz")
            for sheet in w.sheets.values():
                for col in sheet.columns:
                    mx = max(len(str(c.value or "")) for c in col)
                    sheet.column_dimensions[col[0].column_letter].width = min(mx+2,35)
        messagebox.showinfo("✓ Kaydedildi", path)
    def export_csv(self):
        if not self.galoplar:
            messagebox.showwarning("Uyarı","Galop verisi yok."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV","*.csv")],
            initialfile="galoplar.csv")
        if not path: return
        pd.DataFrame(self.galoplar).to_csv(path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("✓ Kaydedildi", path)
if __name__ == "__main__":
    App().mainloop()