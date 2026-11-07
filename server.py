import asyncio
import html
import json
import os
import random
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Açık Arttırma — Canlı Müzayede")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ============================================================================
# 1. GEMINI API KEY AUTO-DISCOVERY (Unity PlayerPrefs / Env)
# ============================================================================
def discover_gemini_api_key() -> str:
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    key_file = os.path.join(BASE_DIR, ".gemini_key")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                k = f.read().strip()
                if len(k) > 20:
                    return k
        except Exception:
            pass

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Unity\UnityEditor") as k:
            for i in range(winreg.QueryInfoKey(k)[0]):
                comp = winreg.EnumKey(k, i)
                with winreg.OpenKey(k, comp) as ck:
                    for j in range(winreg.QueryInfoKey(ck)[0]):
                        proj = winreg.EnumKey(ck, j)
                        with winreg.OpenKey(ck, proj) as pk:
                            for v in range(winreg.QueryInfoKey(pk)[1]):
                                name, val, _ = winreg.EnumValue(pk, v)
                                if "GeminiApiKey" in name and val:
                                    if isinstance(val, bytes):
                                        s = val.decode("utf-8", errors="ignore").strip("\x00").strip()
                                    else:
                                        s = str(val).strip("\x00").strip()
                                    if len(s) > 20:
                                        return s
    except Exception:
        pass

    return ""


DEFAULT_GEMINI_API_KEY = discover_gemini_api_key()


# ============================================================================
# 2. ORIGINAL 14 ACTION CARDS CATALOG
# ============================================================================
CARDS_CATALOG: List[Dict[str, Any]] = [
    {
        "cardID": "BAHSIS",
        "cardName": "BAHŞİŞ",
        "description": "Kasana anında +1 ₺ nakit bütçe ekler.",
        "pointCost": 140,
        "rarity": "Common",
        "category": "odul",
        "categoryLabel": "Ödül & Gelir",
        "categoryIcon": "💰",
        "categoryColor": "#10B981",
        "targetType": "Self",
        "cooldown": 2,
        "image": "/static/cards/Card_Bahsis.webp?v=2",
        "effectType": "economy",
        "amount": 1,
    },
    {
        "cardID": "PIYANGO",
        "cardName": "PİYANGO",
        "description": "Kasana anında 1-4 ₺ arası rastgele nakit bütçe ekler.",
        "pointCost": 250,
        "rarity": "Common",
        "category": "odul",
        "categoryLabel": "Ödül & Gelir",
        "categoryIcon": "💰",
        "categoryColor": "#10B981",
        "targetType": "Self",
        "cooldown": 2,
        "image": "/static/cards/Card_Piyango.webp?v=2",
        "effectType": "lottery",
        "minAmount": 1,
        "maxAmount": 4,
    },
    {
        "cardID": "YATIRIM",
        "cardName": "YATIRIM",
        "description": "Kasana anında +2 ₺ nakit bütçe ekler.",
        "pointCost": 220,
        "rarity": "Common",
        "category": "odul",
        "categoryLabel": "Ödül & Gelir",
        "categoryIcon": "💰",
        "categoryColor": "#10B981",
        "targetType": "Self",
        "cooldown": 3,
        "image": "/static/cards/Card_Yatirim.webp?v=2",
        "effectType": "economy",
        "amount": 2,
    },
    {
        "cardID": "SERMAYE",
        "cardName": "SERMAYE",
        "description": "Kasana anında +3 ₺ nakit bütçe ekler.",
        "pointCost": 320,
        "rarity": "Rare",
        "category": "odul",
        "categoryLabel": "Ödül & Gelir",
        "categoryIcon": "💰",
        "categoryColor": "#10B981",
        "targetType": "Self",
        "cooldown": 3,
        "image": "/static/cards/Card_Sermaye.webp?v=2",
        "effectType": "economy",
        "amount": 3,
    },
    {
        "cardID": "KARAPARA",
        "cardName": "KARA PARA",
        "description": "Kasana anında +4 ₺ nakit bütçe ekler.",
        "pointCost": 420,
        "rarity": "Epic",
        "category": "odul",
        "categoryLabel": "Ödül & Gelir",
        "categoryIcon": "💰",
        "categoryColor": "#10B981",
        "targetType": "Self",
        "cooldown": 4,
        "image": "/static/cards/Card_KaraPara.webp?v=2",
        "effectType": "economy",
        "amount": 4,
    },
    {
        "cardID": "TEBLIGAT",
        "cardName": "TEBLİGAT",
        "description": "Seçilen rakibin kasasından anında 1 ₺ siler.",
        "pointCost": 180,
        "rarity": "Common",
        "category": "ceza",
        "categoryLabel": "Ceza & Saldırı",
        "categoryIcon": "⚔️",
        "categoryColor": "#EF4444",
        "targetType": "SingleTargetPlayer",
        "cooldown": 2,
        "image": "/static/cards/Card_Tebligat.webp?v=2",
        "effectType": "burn",
        "amount": 1,
    },
    {
        "cardID": "HACIZ",
        "cardName": "HACİZ",
        "description": "Seçilen rakibin kasasından anında 2 ₺ siler.",
        "pointCost": 260,
        "rarity": "Rare",
        "category": "ceza",
        "categoryLabel": "Ceza & Saldırı",
        "categoryIcon": "⚔️",
        "categoryColor": "#EF4444",
        "targetType": "SingleTargetPlayer",
        "cooldown": 3,
        "image": "/static/cards/Card_Haciz.webp?v=2",
        "effectType": "burn",
        "amount": 2,
    },
    {
        "cardID": "IFLAS",
        "cardName": "İFLAS",
        "description": "Seçilen rakibin kasasından anında 3 ₺ siler.",
        "pointCost": 380,
        "rarity": "Epic",
        "category": "ceza",
        "categoryLabel": "Ceza & Saldırı",
        "categoryIcon": "⚔️",
        "categoryColor": "#EF4444",
        "targetType": "SingleTargetPlayer",
        "cooldown": 4,
        "image": "/static/cards/Card_Iflas.webp?v=2",
        "effectType": "burn",
        "amount": 3,
    },
    {
        "cardID": "HARAC",
        "cardName": "HARAÇ",
        "description": "Masadaki her oyuncudan 1 ₺ çalar ve kasana ekler.",
        "pointCost": 400,
        "rarity": "Epic",
        "category": "ceza",
        "categoryLabel": "Ceza & Saldırı",
        "categoryIcon": "⚔️",
        "categoryColor": "#EF4444",
        "targetType": "Global",
        "cooldown": 4,
        "image": "/static/cards/Card_Harac.webp?v=2",
        "effectType": "harac",
        "amount": 1,
    },
    {
        "cardID": "KALKAN",
        "cardName": "KALKAN",
        "description": "Sana oynanan bir saldırı veya ceza kartını engeller.",
        "pointCost": 240,
        "rarity": "Rare",
        "category": "savunma",
        "categoryLabel": "Savunma & Taktik",
        "categoryIcon": "🛡️",
        "categoryColor": "#3B82F6",
        "targetType": "Self",
        "cooldown": 3,
        "image": "/static/cards/Card_Kalkan.webp?v=2",
        "effectType": "shield",
    },
    {
        "cardID": "VETO",
        "cardName": "VETO",
        "description": "Çıkan ürün iptal edilir ve şerit tekrar döndürülür.",
        "pointCost": 250,
        "rarity": "Rare",
        "category": "savunma",
        "categoryLabel": "Savunma & Taktik",
        "categoryIcon": "🛡️",
        "categoryColor": "#3B82F6",
        "targetType": "Global",
        "cooldown": 3,
        "image": "/static/cards/Card_Veto.webp?v=2",
        "effectType": "veto",
    },
    {
        "cardID": "DONDURMA",
        "cardName": "DONDURMA",
        "description": "Seçtiğin 1 oyuncu bu tur teklif veremez.",
        "pointCost": 180,
        "rarity": "Rare",
        "category": "savunma",
        "categoryLabel": "Savunma & Taktik",
        "categoryIcon": "🛡️",
        "categoryColor": "#3B82F6",
        "targetType": "SingleTargetPlayer",
        "cooldown": 2,
        "image": "/static/cards/Card_Dondurma.webp?v=2",
        "effectType": "debuff_freeze",
    },
    {
        "cardID": "KAYIP_SLOT",
        "cardName": "KAYIP SLOT",
        "description": "Hedef oyuncunun maksimum kadro kapasitesini 1 azaltır.",
        "pointCost": 400,
        "rarity": "Rare",
        "category": "lanet",
        "categoryLabel": "Ağır Lanet",
        "categoryIcon": "💀",
        "categoryColor": "#A855F7",
        "targetType": "SingleTargetPlayer",
        "cooldown": 4,
        "image": "/static/cards/Card_KayipSlot.webp?v=2",
        "effectType": "debuff_slot",
    },
    {
        "cardID": "KARA_LANET",
        "cardName": "KARA LANET",
        "description": "Kadrosunu doldurana kadar boş geçen her tur 1 ₺ silinir.",
        "pointCost": 400,
        "rarity": "Epic",
        "category": "lanet",
        "categoryLabel": "Ağır Lanet",
        "categoryIcon": "💀",
        "categoryColor": "#A855F7",
        "targetType": "SingleTargetPlayer",
        "cooldown": 4,
        "image": "/static/cards/Card_KaraLanet.webp?v=2",
        "effectType": "debuff_curse",
    },
    {
        "cardID": "MUHUR",
        "cardName": "MÜHÜR",
        "description": "Seçilen rakibin elini 2 tur kilitler; hiçbir gizli kart kullanamaz.",
        "pointCost": 340,
        "rarity": "Rare",
        "category": "lanet",
        "categoryLabel": "Ağır Lanet",
        "categoryIcon": "💀",
        "categoryColor": "#A855F7",
        "targetType": "SingleTargetPlayer",
        "cooldown": 3,
        "image": "/static/cards/Card_Muhur.webp?v=2",
        "effectType": "debuff_silence",
    },
]

CARDS_BY_ID = {c["cardID"]: c for c in CARDS_CATALOG}


# ============================================================================
# 3. UNIVERSAL DYNAMIC IMAGE RESOLVER & PERSISTENT CACHE (Bing Images + Wiki)
# ============================================================================
IMAGE_CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "image_cache.json")
IMAGE_CACHE: Dict[str, Optional[str]] = {}

# Load persistent image cache if present on disk
try:
    if os.path.exists(IMAGE_CACHE_PATH):
        with open(IMAGE_CACHE_PATH, "r", encoding="utf-8") as _f:
            _loaded = json.load(_f)
            if isinstance(_loaded, dict):
                IMAGE_CACHE.update(_loaded)
except Exception:
    pass


def save_image_cache_to_disk() -> None:
    try:
        os.makedirs(os.path.dirname(IMAGE_CACHE_PATH), exist_ok=True)
        with open(IMAGE_CACHE_PATH, "w", encoding="utf-8") as _f:
            json.dump(IMAGE_CACHE, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Common single-word entities that require specific disambiguation anchors
DISAMBIGUATION_ANCHORS = {
    "maximus": "Maximus Gladiator character portrait",
    "arthur morgan": "Arthur Morgan Red Dead Redemption 2 portrait",
    "joker": "Joker DC character portrait",
    "blade": "Blade Marvel character portrait",
    "flash": "The Flash DC superhero portrait",
    "thor": "Thor Marvel character portrait",
    "ezel": "Ezel Bayraktar dizi portrait",
    "ramiz dayı": "Ramiz Karaeski Dayı Ezel portrait",
    "polat alemdar": "Polat Alemdar Kurtlar Vadisi portrait",
    "recep ivedik": "Recep İvedik film portrait",
    "süleyman çakır": "Süleyman Çakır Kurtlar Vadisi portrait",
    "memati baş": "Memati Baş Kurtlar Vadisi portrait",
    "vito corleone": "Vito Corleone Godfather portrait",
    "walter white": "Walter White Breaking Bad portrait",
}

# Negative keywords: reject results containing coins, anatomy, contractors, maps, or clipart logos
BAD_IMAGE_KEYWORDS = {
    "coin", "madeni para", "harita", "map", "logo", "vector", "vektör", "clipart",
    "contractor", "gluteus", "muscle", "anatomi", "anatomy", "flag", "bayrak",
    "dizi indir", "transparent png", "png icon", "clip art", "free icon", "download png", "madalyon"
}


def resolve_wiki_image_sync(term: str) -> Optional[str]:
    key = term.strip()
    if not key:
        return None
    if key in IMAGE_CACHE and IMAGE_CACHE[key] is not None:
        return IMAGE_CACHE[key]

    k_lower = key.lower()

    # Generate prioritized candidate queries for dynamic search
    queries = []
    if k_lower in DISAMBIGUATION_ANCHORS:
        queries.append(DISAMBIGUATION_ANCHORS[k_lower])

    if any(w in k_lower for w in ["character", "karakter", "film", "dizi", "oyun", "movie", "game"]):
        queries.append(f"{key} portrait")
        queries.append(key)
    else:
        queries.append(f"{key} character portrait")
        queries.append(f"{key} portrait")
        queries.append(f"{key} dizi film")
        queries.append(key)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    # 1. Primary: Microsoft Bing Images Engine with Turkish locale context and smart filtering
    for q in queries:
        try:
            bing_url = (
                "https://www.bing.com/images/async?q="
                + urllib.parse.quote(q)
                + "&first=0&count=12&adlt=off&cc=tr&setlang=tr"
            )
            req = urllib.request.Request(bing_url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                unesc = html.unescape(raw)

                for m in re.finditer(r'm="({.*?})"', unesc):
                    try:
                        data = json.loads(m.group(1))
                        turl = data.get("turl")
                        title = data.get("t", "")
                        desc = data.get("desc", "")
                        if not turl:
                            continue

                        meta = (title + " " + desc).lower()
                        if any(b in meta for b in BAD_IMAGE_KEYWORDS):
                            continue

                        # Clean thumbnail URL: preserve native ratio without white letterboxing!
                        # NEVER append &w=400&h=400 which forces Bing to pad white borders!
                        clean_url = turl.split("&w=")[0].split("&h=")[0]
                        if "&pid=" not in clean_url:
                            clean_url += "&pid=15.1"

                        IMAGE_CACHE[key] = clean_url
                        save_image_cache_to_disk()
                        return clean_url
                    except Exception:
                        continue
        except Exception:
            continue

    # 2. Fallback: Wikipedia with strict relevance and disambiguation check
    for lang in ("tr", "en"):
        url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={urllib.parse.quote(key)}&gsrlimit=3&prop=pageimages|description"
            f"&pithumbsize=400&format=json"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AcikArttirma/2.0 (contact@arsivizm.xyz)"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, p in pages.items():
                    p_title = p.get("title", "")
                    p_desc = p.get("description", "") or ""
                    thumb = p.get("thumbnail", {}).get("source")
                    if thumb and (k_lower in p_title.lower() or p_title.lower() in k_lower):
                        meta = (p_title + " " + p_desc).lower()
                        if not any(b in meta for b in BAD_IMAGE_KEYWORDS):
                            IMAGE_CACHE[key] = thumb
                            save_image_cache_to_disk()
                            return thumb
        except Exception:
            pass

    IMAGE_CACHE[key] = None
    return None


async def resolve_wiki_image(term: str) -> Optional[str]:
    if term in IMAGE_CACHE:
        return IMAGE_CACHE[term]
    return await asyncio.to_thread(resolve_wiki_image_sync, term)


# ============================================================================
# 4. GEMINI AI CLIENT (Supports gemini-3.5-flash-lite & thinking parts)
# ============================================================================
def call_gemini_sync(api_key: str, system_prompt: str, user_prompt: str) -> str:
    key = (api_key or DEFAULT_GEMINI_API_KEY).strip()
    if not key:
        raise ValueError("Gemini API Anahtarı girilmedi. Sol menüden API anahtarınızı girebilirsiniz.")

    endpoints = [
        ("v1", "gemini-3.5-flash-lite"),
        ("v1", "gemini-3.5-flash"),
        ("v1", "gemini-2.5-flash-lite"),
        ("v1beta", "gemini-flash-lite-latest"),
        ("v1beta", "gemini-flash-latest"),
    ]

    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}]
    }).encode("utf-8")

    last_err = None
    for ver, model_name in endpoints:
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{model_name}:generateContent?key={key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    # Filter out thinking parts ("thought": True)
                    non_thought_texts = [p["text"] for p in parts if "text" in p and not p.get("thought")]
                    if non_thought_texts:
                        return non_thought_texts[-1]
                    if parts and "text" in parts[-1]:
                        return parts[-1]["text"]
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            last_err = f"HTTP {he.code} ({model_name}): {err_body[:160]}"
            continue
        except Exception as e:
            last_err = str(e)
            continue

    raise RuntimeError(f"AI yanıt veremedi: {last_err}")


def extract_json_object(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first : last + 1]
    return json.loads(text)


# ============================================================================
# 5. GAME STATE & RANDOM ROOM ENGINE (No Bots, Cryptographic Room Codes)
# ============================================================================
DEFAULT_POOL = [
    "Walter White", "John Wick", "Vito Corleone", "Tony Montana",
    "Sherlock Holmes", "Hannibal Lecter", "Lara Croft", "James Bond",
    "Tyler Durden", "Arthur Morgan", "Geralt of Rivia", "Kratos",
    "Darth Vader", "Batman", "Joker", "Wolverine",
    "Gandalf", "Aragorn", "Neo", "Terminator",
    "Maximus", "Jack Sparrow", "Indiana Jones", "Rocky Balboa",
    "Rambo"
]

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_secret_room_code(length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if code not in ROOMS:
            return code


class Player:
    def __init__(self, pid: str, name: str, color_idx: int, budget: int, capacity: int):
        self.id = pid
        self.name = name
        self.color_idx = color_idx
        self.starting_budget = budget
        self.budget = budget
        self.base_capacity = capacity
        self.capacity = capacity
        self.purchases: List[Dict[str, Any]] = []
        self.session_points: int = 0
        self.inventory: List[Optional[Dict[str, Any]]] = [None, None, None, None, None]
        self.card_last_purchased_round: Dict[str, int] = {}
        self.has_shield: bool = False
        self.is_frozen: bool = False
        self.has_black_curse: bool = False
        self.silenced_rounds: int = 0
        self.passed_current_item: bool = False

    @property
    def is_roster_full(self) -> bool:
        return len(self.purchases) >= self.capacity

    @property
    def is_finished(self) -> bool:
        return self.is_roster_full or self.budget <= 0

    @property
    def secret_card_count(self) -> int:
        return sum(1 for c in self.inventory if c is not None)

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "colorIdx": self.color_idx,
            "budget": self.budget,
            "startingBudget": self.starting_budget,
            "capacity": self.capacity,
            "baseCapacity": self.base_capacity,
            "purchases": self.purchases,
            "sessionPoints": self.session_points,
            "hasShield": self.has_shield,
            "isFrozen": self.is_frozen,
            "hasBlackCurse": self.has_black_curse,
            "silencedRounds": self.silenced_rounds,
            "passedCurrentItem": self.passed_current_item,
            "isFinished": self.is_finished,
        }

    def to_private_dict(self, current_round: int) -> Dict[str, Any]:
        d = self.to_public_dict()
        d["inventory"] = self.inventory
        cooldowns = {}
        for c in CARDS_CATALOG:
            cid = c["cardID"]
            if cid in self.card_last_purchased_round:
                last_r = self.card_last_purchased_round[cid]
                rem = c["cooldown"] - (current_round - last_r)
                if rem > 0:
                    cooldowns[cid] = rem
        d["cooldowns"] = cooldowns
        return d


class Room:
    def __init__(self, code: str, host_id: str):
        self.code = code
        self.host_id = host_id
        self.phase = "setup"
        self.scenario = "Bu karakterler savaşa girse hangi takım kazanır?"
        self.starting_budget = 30
        self.roster_capacity = 5
        self.bid_timer_seconds = 14
        self.gemini_api_key = DEFAULT_GEMINI_API_KEY

        self.players: List[Player] = []
        self.connections: Dict[str, WebSocket] = {}

        self.pool_names: List[str] = list(DEFAULT_POOL)
        self.pool_entries: List[Dict[str, Any]] = []
        self.chat_history: List[Dict[str, str]] = [
            {"sender": "AI Asistan", "text": "Senaryoya göre isim üretmem için '50 isim öner' veya '30 bilim insanı ekle' yazabilirsin."}
        ]

        self.current_round: int = 1
        self.turn_index: int = 0
        self.auction_state: str = "idle"
        self.current_entry: Optional[Dict[str, Any]] = None
        self.reel_sequence: List[Dict[str, Any]] = []
        self.reel_winner_index: int = 52
        self.reel_offset_px: float = 0.0

        self.highest_bid: int = 0
        self.highest_bidder_id: Optional[str] = None
        self.highest_bidder_name: Optional[str] = None
        self.bid_deadline: float = 0.0
        self.timer_task: Optional[asyncio.Task] = None

        self.history_stack: List[Dict[str, Any]] = []
        self.judge_evaluating: bool = False
        self.judge_result: Optional[Dict[str, Any]] = None

    def get_player(self, pid: str) -> Optional[Player]:
        for p in self.players:
            if p.id == pid:
                return p
        return None

    def get_turn_player(self) -> Optional[Player]:
        if not self.players:
            return None
        n = len(self.players)
        for offset in range(n):
            idx = (self.turn_index + offset) % n
            p = self.players[idx]
            if not p.is_finished:
                self.turn_index = idx
                return p
        return None

    def advance_turn(self):
        if not self.players:
            return
        self.turn_index = (self.turn_index + 1) % len(self.players)
        self.get_turn_player()

    def add_player(self, pid: str, name: str) -> Player:
        existing = self.get_player(pid)
        if existing:
            existing.name = name
            return existing
        color_idx = len(self.players) % 8
        p = Player(pid, name, color_idx, self.starting_budget, self.roster_capacity)
        self.players.append(p)
        return p

    def all_players_finished(self) -> bool:
        if not self.players:
            return False
        return all(p.is_finished for p in self.players)

    def available_entries(self) -> List[Dict[str, Any]]:
        return [e for e in self.pool_entries if e["state"] == "available"]

    def build_state_for_player(self, viewer_id: str) -> Dict[str, Any]:
        me = self.get_player(viewer_id)
        turn_p = self.get_turn_player()
        return {
            "type": "state",
            "roomCode": self.code,
            "hostId": self.host_id,
            "viewerId": viewer_id,
            "phase": self.phase,
            "scenario": self.scenario,
            "startingBudget": self.starting_budget,
            "rosterCapacity": self.roster_capacity,
            "bidTimerSeconds": self.bid_timer_seconds,
            "hasApiKey": bool(self.gemini_api_key),
            "poolNames": self.pool_names,
            "poolCount": len(self.pool_names),
            "availableCount": len(self.available_entries()) if self.phase != "setup" else len(self.pool_names),
            "totalPoolCount": len(self.pool_entries) if self.phase != "setup" else len(self.pool_names),
            "chatHistory": self.chat_history[-15:],
            "currentRound": self.current_round,
            "turnPlayerId": turn_p.id if turn_p else None,
            "turnPlayerName": turn_p.name if turn_p else None,
            "auctionState": self.auction_state,
            "currentEntry": self.current_entry,
            "highestBid": self.highest_bid,
            "highestBidderId": self.highest_bidder_id,
            "highestBidderName": self.highest_bidder_name,
            "bidRemainingSec": max(0, round(self.bid_deadline - time.time(), 1)) if self.auction_state == "bidding" else 0,
            "players": [p.to_public_dict() for p in self.players],
            "me": me.to_private_dict(self.current_round) if me else None,
            "cardsCatalog": CARDS_CATALOG,
            "judgeEvaluating": self.judge_evaluating,
            "judgeResult": self.judge_result,
            "imageCache": {
                name: IMAGE_CACHE.get(name)
                for name in (
                    set(self.pool_names)
                    | {e.get("name") for e in self.pool_entries if e.get("name")}
                    | {pur.get("name") for p in self.players for pur in p.purchases if pur.get("name")}
                    | ({self.current_entry.get("name")} if self.current_entry and self.current_entry.get("name") else set())
                )
                if IMAGE_CACHE.get(name)
            },
        }

    async def broadcast_state(self):
        dead = []
        for pid, ws in list(self.connections.items()):
            try:
                payload = self.build_state_for_player(pid)
                await ws.send_json(payload)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.connections.pop(pid, None)

    async def broadcast_event(self, event_data: Dict[str, Any]):
        dead = []
        for pid, ws in list(self.connections.items()):
            try:
                await ws.send_json(event_data)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.connections.pop(pid, None)


ROOMS: Dict[str, Room] = {}


def get_or_create_room(code: str, host_id: str) -> Room:
    code = code.upper().strip()
    if code not in ROOMS:
        ROOMS[code] = Room(code, host_id)
    return ROOMS[code]


# ============================================================================
# 6. GAMEPLAY FLOW & AUCTION TIMERS
# ============================================================================
async def preload_room_images(room: Room, names: List[str]):
    missing = [n for n in names if not IMAGE_CACHE.get(n)]
    if not missing:
        return

    batch_size = 8
    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]
        results = await asyncio.gather(*(resolve_wiki_image(n) for n in batch), return_exceptions=True)
        changed = False
        for name, img in zip(batch, results):
            if isinstance(img, str) and img:
                changed = True
                for e in room.pool_entries:
                    if e["name"] == name:
                        e["image"] = img
                if room.current_entry and room.current_entry.get("name") == name:
                    room.current_entry["image"] = img
        if changed:
            await room.broadcast_state()


async def start_spin_sequence(room: Room):
    avail = room.available_entries()
    if not avail or room.all_players_finished():
        room.phase = "finished"
        room.auction_state = "idle"
        await room.broadcast_state()
        await trigger_ai_judge(room)
        return

    room.auction_state = "spinning"
    room.highest_bid = 0
    room.highest_bidder_id = None
    room.highest_bidder_name = None
    for p in room.players:
        p.passed_current_item = False

    winner = random.choice(avail)
    if not winner.get("image") and not IMAGE_CACHE.get(winner["name"]):
        img = await resolve_wiki_image(winner["name"])
        if img:
            winner["image"] = img
    room.current_entry = winner

    total_cards = 68
    win_idx = 52
    reel = []
    for i in range(total_cards):
        if i == win_idx:
            item = winner
        else:
            pick = random.choice(avail) if len(avail) >= 3 else random.choice(room.pool_entries)
            item = pick
        reel.append({
            "id": item["id"],
            "name": item["name"],
            "image": item.get("image") or IMAGE_CACHE.get(item["name"]),
            "tier": item.get("tier", "mavi"),
        })

    room.reel_sequence = reel
    room.reel_winner_index = win_idx
    room.reel_offset_px = round(random.uniform(-34.0, 34.0), 1)

    await room.broadcast_event({
        "type": "spin_start",
        "reel": reel,
        "winnerIndex": win_idx,
        "offsetPx": room.reel_offset_px,
        "winner": winner,
        "durationMs": 4600,
    })
    await room.broadcast_state()

    await asyncio.sleep(4.9)

    if room.auction_state != "spinning" or room.current_entry != winner:
        return

    room.auction_state = "bidding"
    room.bid_deadline = time.time() + room.bid_timer_seconds

    turn_p = room.get_turn_player()
    if turn_p and not turn_p.is_finished and turn_p.budget >= 1:
        room.highest_bid = 1
        room.highest_bidder_id = turn_p.id
        room.highest_bidder_name = turn_p.name

    await room.broadcast_event({
        "type": "toast",
        "level": "info",
        "message": f"İHALE BAŞLADI: {winner['name']} kürsüde! (Sıra: {turn_p.name if turn_p else '-'} — Taban: 1 ₺)",
    })
    await room.broadcast_state()

    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = asyncio.create_task(run_bidding_timer(room, winner["id"]))


async def run_bidding_timer(room: Room, entry_id: str):
    try:
        while room.phase == "playing" and room.auction_state == "bidding" and room.current_entry and room.current_entry["id"] == entry_id:
            rem = room.bid_deadline - time.time()
            if rem <= 0:
                await finalize_current_auction(room)
                return
            await asyncio.sleep(0.4)
    except asyncio.CancelledError:
        pass


async def apply_player_bid(room: Room, player: Player, amount: int) -> Optional[str]:
    if room.phase != "playing" or room.auction_state != "bidding" or not room.current_entry:
        return "Şu anda aktif bir teklif turu yok."
    if player.is_frozen:
        return "Bu tur DONDURULDUN! Teklif veremezsin."
    if player.is_roster_full or len(player.purchases) >= player.capacity:
        return "Takım kadron zaten tamamen dolu! Parası kalsa dahi kadrosunu tamamlayanlar teklif veremez."
    if amount <= room.highest_bid:
        return f"Teklif mevcut en yüksek tekliften ({room.highest_bid} ₺) büyük olmalı."
    if amount > player.budget:
        return f"Yetersiz bütçe! Kalan bütçen: {player.budget} ₺"

    room.highest_bid = amount
    room.highest_bidder_id = player.id
    room.highest_bidder_name = player.name
    player.passed_current_item = False

    now = time.time()
    if room.bid_deadline - now < 6.0:
        room.bid_deadline = now + 6.0

    await room.broadcast_event({
        "type": "bid_placed",
        "playerId": player.id,
        "playerName": player.name,
        "amount": amount,
    })
    await room.broadcast_state()
    await check_all_passed_or_resolved(room)
    return None


async def check_all_passed_or_resolved(room: Room):
    if room.auction_state != "bidding" or not room.current_entry:
        return

    active_bidders = [
        p for p in room.players
        if not p.is_finished and not p.is_frozen
    ]

    if room.highest_bidder_id:
        others = [
            p for p in active_bidders
            if p.id != room.highest_bidder_id and not p.passed_current_item and p.budget > room.highest_bid
        ]
        if len(active_bidders) > 1 and not others:
            await finalize_current_auction(room)
        elif len(active_bidders) == 1 and active_bidders[0].passed_current_item:
            await finalize_current_auction(room)
    else:
        not_passed = [p for p in active_bidders if not p.passed_current_item]
        if not not_passed:
            await finalize_current_auction(room)


async def finalize_current_auction(room: Room):
    if room.auction_state != "bidding" or not room.current_entry:
        return

    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()

    entry = room.current_entry
    winner_id = room.highest_bidder_id
    price = room.highest_bid

    winner = room.get_player(winner_id) if (winner_id and price > 0) else None
    if not winner:
        turn_p = room.get_turn_player()
        if turn_p and not turn_p.is_roster_full and turn_p.budget >= 1:
            winner = turn_p
            price = 1

    prev_turn_index = room.turn_index

    if winner and not winner.is_roster_full and winner.budget >= price:
        entry["state"] = "sold"
        winner.budget -= price
        winner.purchases.append({
            "id": entry["id"],
            "name": entry["name"],
            "price": price,
            "image": entry.get("image") or IMAGE_CACHE.get(entry["name"]),
        })
        room.history_stack.append({
            "type": "sold",
            "entryId": entry["id"],
            "buyerId": winner.id,
            "price": price,
            "prevTurnIndex": prev_turn_index,
        })
        await room.broadcast_event({
            "type": "sold",
            "entry": entry,
            "buyerId": winner.id,
            "buyerName": winner.name,
            "price": price,
        })
        await apply_round_end_effects(room, winner.id)
    else:
        entry["state"] = "passed"
        room.history_stack.append({
            "type": "passed",
            "entryId": entry["id"],
            "prevTurnIndex": prev_turn_index,
        })
        await room.broadcast_event({
            "type": "passed",
            "entry": entry,
        })
        await apply_round_end_effects(room, None)

    room.auction_state = "idle"
    room.current_entry = None
    room.highest_bid = 0
    room.highest_bidder_id = None
    room.highest_bidder_name = None
    room.current_round += 1
    room.advance_turn()

    if room.all_players_finished() or not room.available_entries():
        room.phase = "finished"
        await room.broadcast_state()
        await trigger_ai_judge(room)
    else:
        await room.broadcast_state()


async def apply_round_end_effects(room: Room, winning_player_id: Optional[str]):
    for p in room.players:
        p.is_frozen = False
        p.passed_current_item = False
        if p.silenced_rounds > 0:
            p.silenced_rounds -= 1
            if p.silenced_rounds == 0:
                await room.broadcast_event({
                    "type": "toast",
                    "level": "info",
                    "message": f"[MÜHÜR AÇILDI] {p.name} üzerindeki mühür kalktı, artık kart kullanabilir!",
                })
        if p.has_black_curse:
            if len(p.purchases) >= p.capacity:
                p.has_black_curse = False
                await room.broadcast_event({
                    "type": "toast",
                    "level": "success",
                    "message": f"[KARA LANET KALKTI] {p.name} kadrosunu tamamladığı için Kara Lanet sona erdi.",
                })
            elif p.id != winning_player_id and p.budget > 0:
                p.budget = max(0, p.budget - 1)
                await room.broadcast_event({
                    "type": "toast",
                    "level": "danger",
                    "message": f"[KARA LANET] {p.name} bu tur ürün alamadığı için -1 ₺ kaybetti! (Kalan: {p.budget} ₺)",
                })


# ============================================================================
# 7. SECRET ACTION CARDS EXECUTION ENGINE
# ============================================================================
async def handle_buy_card(room: Room, player: Player, card_id: str) -> Optional[str]:
    card = CARDS_BY_ID.get(card_id)
    if not card:
        return "Geçersiz kart."

    for slot_c in player.inventory:
        if slot_c and slot_c["cardID"] == card_id:
            return "Bu kart zaten gizli elinde mevcut!"

    if card_id in player.card_last_purchased_round:
        last_r = player.card_last_purchased_round[card_id]
        rem = card["cooldown"] - (room.current_round - last_r)
        if rem > 0:
            return f"Bu kart beklemede ({rem} tur kaldı)."

    empty_idx = next((i for i, s in enumerate(player.inventory) if s is None), -1)
    if empty_idx == -1:
        return "Gizli kart envanterin dolu (5/5)!"

    if player.session_points < card["pointCost"]:
        return f"Yetersiz Jüri Puanı! Gereken: {card['pointCost']} P, Mevcut: {player.session_points} P"

    player.session_points -= card["pointCost"]
    player.inventory[empty_idx] = dict(card)
    player.card_last_purchased_round[card_id] = room.current_round

    await room.broadcast_state()
    return None


async def handle_use_card(room: Room, caster: Player, slot_idx: int, target_id: Optional[str]) -> Optional[str]:
    if caster.silenced_rounds > 0:
        return f"Mühürlendin! {caster.silenced_rounds} tur boyunca hiçbir gizli kart kullanamazsın."

    if slot_idx < 0 or slot_idx >= 5 or caster.inventory[slot_idx] is None:
        return "Seçilen slotta kart yok."

    card = caster.inventory[slot_idx]
    effect = card["effectType"]
    cname = card["cardName"]

    target: Optional[Player] = None
    if card["targetType"] == "SingleTargetPlayer":
        if not target_id:
            return "Bu kart için bir hedef rakip seçmelisin."
        target = room.get_player(target_id)
        if not target or target.id == caster.id:
            return "Geçerli bir rakip seçmelisin."

    if effect == "shield" and caster.has_shield:
        return "Zaten aktif bir Kalkanın var! Kart harcanmadı."
    if effect == "veto" and (room.auction_state not in ("spinning", "bidding") or not room.current_entry):
        return "Veto sadece aktif bir ihale veya şerit dönerken kullanılabilir!"
    if effect == "burn" and target and target.budget <= 0 and not target.has_shield:
        return f"{target.name} zaten 0 ₺ bütçeye sahip! Kart harcanmadı."
    if effect == "debuff_freeze" and target and target.is_frozen and not target.has_shield:
        return f"{target.name} bu tur zaten dondurulmuş! Kart harcanmadı."
    if effect == "debuff_slot" and target and target.capacity <= 1 and not target.has_shield:
        return f"{target.name} oyuncusunun daha fazla slotu kilitlenemez!"
    if effect == "debuff_curse" and target and target.has_black_curse and not target.has_shield:
        return f"{target.name} zaten Kara Lanet etkisinde!"
    if effect == "debuff_silence" and target and target.silenced_rounds > 0 and not target.has_shield:
        return f"{target.name} zaten {target.silenced_rounds} tur mühürlü! Kart harcanmadı."

    caster.inventory[slot_idx] = None

    if effect == "economy":
        bonus = card["amount"]
        caster.budget += bonus
        await room.broadcast_event({
            "type": "card_played",
            "message": f"[EKONOMİ] {caster.name} '{cname}' oynadı ve kasasına +{bonus} ₺ ekledi!",
        })
    elif effect == "lottery":
        won = random.randint(card["minAmount"], card["maxAmount"])
        caster.budget += won
        await room.broadcast_event({
            "type": "card_played",
            "message": f"[PİYANGO] {caster.name} şansını denedi ve '{cname}' kartından +{won} ₺ kazandı!",
        })
    elif effect == "shield":
        caster.has_shield = True
        await room.broadcast_event({
            "type": "card_played",
            "message": f"[KALKAN AKTİF] {caster.name} koruma kalkanı açtı! Gelen ilk saldırıyı engelleyecek.",
        })
    elif effect == "veto":
        cancelled_name = room.current_entry["name"] if room.current_entry else "Ürün"
        if room.timer_task and not room.timer_task.done():
            room.timer_task.cancel()
        if room.current_entry:
            room.current_entry["state"] = "available"
        room.current_entry = None
        room.auction_state = "idle"
        room.highest_bid = 0
        room.highest_bidder_id = None
        room.highest_bidder_name = None
        await room.broadcast_event({
            "type": "card_played",
            "message": f"[VETO] {caster.name} '{cname}' kartını masaya vurdu! '{cancelled_name}' ihalesi iptal edildi!",
        })
    elif effect == "harac":
        stolen = 0
        blocked_names = []
        for p in room.players:
            if p.id == caster.id:
                continue
            if p.has_shield:
                p.has_shield = False
                blocked_names.append(p.name)
                continue
            if p.budget > 0:
                p.budget -= 1
                stolen += 1
        caster.budget += stolen
        shield_note = f" ({', '.join(blocked_names)} kalkanla engelledi!)" if blocked_names else ""
        await room.broadcast_event({
            "type": "card_played",
            "message": f"[HARAÇ] {caster.name} masadan toplam +{stolen} ₺ haraç kesti!{shield_note}",
        })
    elif target is not None:
        if target.has_shield:
            target.has_shield = False
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[KALKAN ENGELLEDİ] {target.name}'in kalkanı {caster.name}'in '{cname}' saldırısını parçaladı!",
            })
        elif effect == "burn":
            burn = card["amount"]
            before = target.budget
            target.budget = max(0, target.budget - burn)
            actual = before - target.budget
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[{cname}] {caster.name} -> {target.name} oyuncusunun kasasından -{actual} ₺ sildi!",
            })
        elif effect == "debuff_freeze":
            target.is_frozen = True
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[DONDURMA] {caster.name} -> {target.name} oyuncusunu dondurdu! Bu tur teklif veremez.",
            })
        elif effect == "debuff_slot":
            target.capacity = max(1, target.capacity - 1)
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[KAYIP SLOT] {caster.name} -> {target.name} oyuncusunun 1 kadro slotunu kilitledi! (Maks: {target.capacity})",
            })
        elif effect == "debuff_curse":
            target.has_black_curse = True
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[KARA LANET] {caster.name} -> {target.name} oyuncusuna Kara Lanet bulaştırdı!",
            })
        elif effect == "debuff_silence":
            target.silenced_rounds = 2
            await room.broadcast_event({
                "type": "card_played",
                "message": f"[MÜHÜR] {caster.name} -> {target.name} oyuncusunu MÜHÜRLEDİ! 2 tur boyunca kart kullanamaz.",
            })

    await room.broadcast_state()
    return None


# ============================================================================
# 8. DUAL-PASS AI JUDGE ENGINE
# ============================================================================
ENGINE_SYSTEM_PROMPT = """Sen katı, tarafsız, analitik ve son derece zeki bir 'Kural Motorusun' (Judge Engine).
Görevin, verilen senaryoyu ve oyuncuların takımlarını (roster) analiz ederek kazananı ve sıralamayı belirlemektir.

DEĞERLENDİRME İLKELERİ:
1. SENARYO ANALİZİ: Önce senaryonun gerçek başarı kriterlerini ve gerekli fonksiyonel rolleri belirle.
2. FONKSİYONEL ROL VE MARJİNAL KATKI ANALİZİ: Her elemanın takım içindeki rolünü ve senaryoya katkısını incele.
3. SİNERJİ VE BÜTÜNLÜK: Seçimlerin birbirini tamamlayıp tamamlamadığını analiz et.
4. KARŞILAŞTIRMALI DEĞERLENDİRME: Oyuncuların neden o sırada yer aldığını açıklarken doğrudan diğer takımlarla somut karakter isimleri vererek karşılaştırma yap.
5. EKONOMİK FAKTÖRLERDEN ARINDIRMA: Bütçe, kalan para veya satın alma fiyatlarını asla değerlendirmeye dahil etme.

Kesinlikle espri yapma, sadece veriyi üret. Aşağıdaki JSON formatına TAM uy (sadece JSON döneceksin):
{
  "Success": true,
  "DecisionType": "SUBJECTIVE",
  "ErrorMessage": "",
  "WinnerPlayerIndex": 0,
  "WinnerPlayerName": "İsim",
  "WinnerLocked": false,
  "Confidence": 90,
  "TeamScores": [
    {
      "PlayerIndex": 0,
      "PlayerName": "İsim",
      "TotalScore": 92,
      "Reason": "seçimlerin somut karşılaştırmalı analizi"
    }
  ]
}"""

HOST_SYSTEM_PROMPT = """Sen 'Açık Artırma' oyununu masada izleyen esprili, laf sokan bir Türk arkadaşsın (AI Host).
Sana 'Judge Engine' tarafından KESİN ve DEĞİŞTİRİLEMEZ bir kazanan sonucu verildi. Sen sadece sonucu açıklıyorsun.

Aşağıdaki JSON şemasına tam olarak uyarak (sadece JSON) cevap ver:
{
  "Headline": "Eğlenceli kısa başlık (3-8 kelime)",
  "Analysis": "Kazananı ve kaybedenleri oyun bağlamında özetleyen 2-3 cümlelik net analiz",
  "FunnyComment": "Oyunculara isimleriyle laf sokan 1-2 cümlelik komik yorum"
}"""


async def trigger_ai_judge(room: Room):
    if room.judge_evaluating:
        return
    room.judge_evaluating = True
    room.judge_result = None
    await room.broadcast_state()

    try:
        lines = [f"SCENARIO:\n{room.scenario}\n"]
        for p in room.players:
            lines.append(f"PLAYER:\n{p.name}")
            lines.append("TEAM:")
            if not p.purchases:
                lines.append("- YOK -")
            else:
                for pur in p.purchases:
                    lines.append(pur["name"])
            lines.append("")
        user_prompt = "\n".join(lines)

        raw_engine = await asyncio.to_thread(call_gemini_sync, room.gemini_api_key, ENGINE_SYSTEM_PROMPT, user_prompt)
        engine_res = extract_json_object(raw_engine)

        if engine_res.get("Success", True) and engine_res.get("DecisionType") != "INVALID":
            host_lines = [
                f"SCENARIO:\n{room.scenario}\n",
                "--- ENGINE RESULT (DO NOT CHANGE) ---",
                f"WINNER: {engine_res.get('WinnerPlayerName', '')}",
                "TEAM DATA:"
            ]
            for p in room.players:
                r_str = ", ".join(x["name"] for x in p.purchases) or "Boş"
                host_lines.append(f"[ {p.name} ] Roster: {r_str}")
            raw_host = await asyncio.to_thread(call_gemini_sync, room.gemini_api_key, HOST_SYSTEM_PROMPT, "\n".join(host_lines))
            host_res = extract_json_object(raw_host)
            engine_res["Headline"] = host_res.get("Headline", "Jüri Kararını Verdi!")
            engine_res["Analysis"] = host_res.get("Analysis", "")
            engine_res["FunnyComment"] = host_res.get("FunnyComment", "")

        team_scores = engine_res.get("TeamScores", [])
        team_scores.sort(key=lambda x: int(x.get("TotalScore", 0)), reverse=True)
        n_scored = len(team_scores)
        for rank_idx, ts in enumerate(team_scores):
            p_name = ts.get("PlayerName", "")
            score = int(ts.get("TotalScore", 0))
            rank_mult = 1.0 - (0.50 * (rank_idx / (n_scored - 1))) if n_scored > 1 else 1.0
            awarded = max(10, int(round(score * rank_mult)))
            ts["AwardedPoints"] = awarded
            ts["Rank"] = rank_idx + 1
            for p in room.players:
                if p.name.lower() == p_name.lower():
                    p.session_points += awarded
                    break

        for p in room.players:
            p.card_last_purchased_round.clear()

        room.judge_result = engine_res
    except Exception as e:
        scores = []
        best_p = None
        best_score = -1
        for idx, p in enumerate(room.players):
            sc = min(98, 55 + len(p.purchases) * 8 + random.randint(0, 6)) if p.purchases else 20
            p.card_last_purchased_round.clear()
            if sc > best_score:
                best_score = sc
                best_p = p
            scores.append({
                "PlayerIndex": idx,
                "PlayerName": p.name,
                "TotalScore": sc,
                "Reason": f"Kadro bütünlüğü ve seçilen {len(p.purchases)} elemanın senaryo uyumu değerlendirildi.",
            })
        scores.sort(key=lambda x: x["TotalScore"], reverse=True)
        n_scored = len(scores)
        for rank_idx, ts in enumerate(scores):
            rank_mult = 1.0 - (0.50 * (rank_idx / (n_scored - 1))) if n_scored > 1 else 1.0
            awarded = max(10, int(round(ts["TotalScore"] * rank_mult)))
            ts["AwardedPoints"] = awarded
            ts["Rank"] = rank_idx + 1
            for p in room.players:
                if p.name.lower() == ts["PlayerName"].lower():
                    p.session_points += awarded
                    break
        room.judge_result = {
            "Success": True,
            "WinnerPlayerName": best_p.name if best_p else "-",
            "Headline": f"{best_p.name if best_p else 'Masa'} Kadrosuyla Üstünlük Kurdu",
            "FunnyComment": f"Not: {str(e)[:90]}",
            "Analysis": "Takımların kadro derinliği ve senaryo rolleri karşılaştırıldı.",
            "TeamScores": scores,
        }
    finally:
        room.judge_evaluating = False
        await room.broadcast_state()


def build_name_assistant_system_prompt(scenario: str, current_names: List[str]) -> str:
    names_str = ", ".join(current_names)
    return f"""Sen 'Açık Artırma' oyunu için lobi ekranında çalışan yardımcı bir AI İsim Asistanısın.
Görevin, kullanıcının belirlediği oyun senaryosuna uygun karakter/kişi/eşya önerileri üretmek veya havuz yönetimi yapmaktır.

KURALLAR:
1. Kesinlikle sadece aşağıdaki JSON formatında cevap ver. JSON dışında hiçbir metin yazma.
2. Kullanıcı sadece bir sayı yazarsa (örneğin '50' veya '50 isim'), mevcut senaryoya uygun o sayıda isim üret.
3. 'Names' listesi, Wikipedia'da görseli bulunabilecek gerçek, net ve bilinen karakter/kişi/eşya isimlerinden oluşmalıdır.
4. 'Message' alanı, kullanıcıya hitap eden kısa Türkçe mesajdır.
5. Mevcut isim havuzunda olan isimleri tekrar önerme.
6. Eğer kullanıcı mevcut listeyi silmek, sıfırlamak veya 'hepsini sil ve ... ekle' diyorsa 'Overwrite': true yap. Sadece ekleme istiyorsa 'Overwrite': false yap.

JSON Formatı:
{{
  "Message": "Senaryona uygun 50 isim eklendi!",
  "Names": ["İsim 1", "İsim 2"],
  "Overwrite": false
}}

Mevcut Senaryo: {scenario}
Mevcut İsim Havuzundaki Karakterler: [{names_str}]"""


# ============================================================================
# 9. HTTP & WEBSOCKET ENDPOINTS
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/create-room")
async def api_create_room( payload: Dict[str, Any]):
    host_id = str(payload.get("playerId") or "").strip()
    if not host_id:
        return {"ok": False, "error": "Geçersiz oyuncu kimliği."}
    code = generate_secret_room_code(6)
    ROOMS[code] = Room(code, host_id)
    return {"ok": True, "roomCode": code}


@app.get("/api/check-room")
async def api_check_room(code: str):
    clean = (code or "").upper().strip()
    room = ROOMS.get(clean)
    if not room:
        return {"exists": False, "error": f"'{clean}' kodlu aktif bir masa bulunamadı!"}
    return {
        "exists": True,
        "roomCode": room.code,
        "playerCount": len(room.players),
        "phase": room.phase,
    }


@app.get("/api/image")
async def api_image(name: str):
    img = await resolve_wiki_image(name)
    return {"name": name, "image": img}


@app.websocket("/ws/{room_code}/{player_id}")
async def ws_endpoint(websocket: WebSocket, room_code: str, player_id: str):
    await websocket.accept()
    clean_code = room_code.upper().strip()
    room = ROOMS.get(clean_code)
    if not room:
        await websocket.send_json({
            "type": "room_not_found",
            "message": f"'{clean_code}' kodlu aktif bir masa bulunamadı! Lütfen kodu kontrol edin veya yeni masa kurun."
        })
        await websocket.close()
        return

    room.connections[player_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action != "join" and not room.get_player(player_id):
                await websocket.send_json({
                    "type": "kicked",
                    "message": "Masa kurucusu tarafından odadan çıkarıldınız."
                })
                await websocket.close()
                return

            if action == "join":
                name = (data.get("name") or "Oyuncu").strip()[:24]
                room.add_player(player_id, name)
                await room.broadcast_state()
                asyncio.create_task(preload_room_images(room, room.pool_names[:30]))

            elif action == "update_settings":
                if player_id == room.host_id and room.phase == "setup":
                    if "scenario" in data:
                        room.scenario = str(data["scenario"]).strip()
                    if "startingBudget" in data:
                        room.starting_budget = max(5, min(500, int(data["startingBudget"])))
                        for p in room.players:
                            p.starting_budget = room.starting_budget
                            p.budget = room.starting_budget
                    if "rosterCapacity" in data:
                        room.roster_capacity = max(1, min(5, int(data["rosterCapacity"])))
                        for p in room.players:
                            p.base_capacity = room.roster_capacity
                            p.capacity = room.roster_capacity
                    if "bidTimerSeconds" in data:
                        room.bid_timer_seconds = max(6, min(60, int(data["bidTimerSeconds"])))
                    if "apiKey" in data and str(data["apiKey"]).strip():
                        room.gemini_api_key = str(data["apiKey"]).strip()
                    if "poolText" in data:
                        raw_lines = str(data["poolText"]).split("\n")
                        parsed = []
                        for ln in raw_lines:
                            t = ln.strip()
                            if t and t not in parsed:
                                parsed.append(t)
                        room.pool_names = parsed
                        asyncio.create_task(preload_room_images(room, room.pool_names[:40]))
                    await room.broadcast_state()

            elif action == "remove_player":
                target_pid = data.get("targetId")
                if player_id == room.host_id and target_pid != room.host_id:
                    room.players = [p for p in room.players if p.id != target_pid]
                    kicked_ws = room.connections.pop(target_pid, None)
                    if kicked_ws:
                        try:
                            await kicked_ws.send_json({
                                "type": "kicked",
                                "message": "Masa kurucusu tarafından odadan çıkarıldınız."
                            })
                            await kicked_ws.close()
                        except Exception:
                            pass
                    await room.broadcast_state()

            elif action == "ai_pool_chat":
                prompt_text = (data.get("prompt") or "").strip()
                api_key_override = (data.get("apiKey") or "").strip()
                if api_key_override:
                    room.gemini_api_key = api_key_override
                if prompt_text:
                    room.chat_history.append({"sender": "Sen", "text": prompt_text})
                    await room.broadcast_state()
                    try:
                        sys_p = build_name_assistant_system_prompt(room.scenario, room.pool_names)
                        raw_resp = await asyncio.to_thread(call_gemini_sync, room.gemini_api_key, sys_p, prompt_text)
                        parsed_json = extract_json_object(raw_resp)
                        if parsed_json.get("Overwrite"):
                            room.pool_names.clear()
                        added = 0
                        for n in parsed_json.get("Names", []):
                            clean_n = str(n).strip()
                            if clean_n and clean_n not in room.pool_names:
                                room.pool_names.append(clean_n)
                                added += 1
                        msg = parsed_json.get("Message") or f"{added} isim havuza eklendi."
                        room.chat_history.append({"sender": "AI Asistan", "text": msg})
                        await room.broadcast_state()
                        asyncio.create_task(preload_room_images(room, room.pool_names[:60]))
                    except Exception as e:
                        room.chat_history.append({"sender": "AI Asistan", "text": f"Hata: {str(e)}"})
                        await room.broadcast_state()

            elif action == "start_game":
                if len(room.pool_names) < 1:
                    await websocket.send_json({"type": "toast", "level": "danger", "message": "İsim havuzunda en az 1 isim olmalı!"})
                    continue
                room.phase = "playing"
                room.current_round = 1
                room.turn_index = 0
                room.auction_state = "idle"
                room.history_stack.clear()
                room.judge_result = None

                tiers = ["mavi", "mavi", "mavi", "mor", "mor", "pembe", "kirmizi", "altin"]
                room.pool_entries = []
                for idx, name in enumerate(room.pool_names):
                    room.pool_entries.append({
                        "id": f"e{idx}",
                        "name": name,
                        "state": "available",
                        "image": IMAGE_CACHE.get(name),
                        "tier": tiers[idx % len(tiers)],
                    })

                for p in room.players:
                    p.budget = room.starting_budget
                    p.starting_budget = room.starting_budget
                    p.capacity = room.roster_capacity
                    p.base_capacity = room.roster_capacity
                    p.purchases.clear()
                    p.is_frozen = False
                    p.has_black_curse = False
                    p.silenced_rounds = 0
                    p.passed_current_item = False

                await room.broadcast_state()
                asyncio.create_task(preload_room_images(room, room.pool_names[:60]))

            elif action == "spin":
                if room.phase == "playing" and room.auction_state == "idle":
                    turn_p = room.get_turn_player()
                    if turn_p and player_id != turn_p.id:
                        await websocket.send_json({
                            "type": "toast",
                            "level": "danger",
                            "message": f"Şu an sıra {turn_p.name} oyuncusunda! Şeridi sadece sırası gelen döndürebilir."
                        })
                    else:
                        asyncio.create_task(start_spin_sequence(room))

            elif action == "bid":
                p = room.get_player(player_id)
                if p:
                    amount = int(data.get("amount", 0))
                    err = await apply_player_bid(room, p, amount)
                    if err:
                        await websocket.send_json({"type": "toast", "level": "danger", "message": err})

            elif action == "pass_bid":
                p = room.get_player(player_id)
                if p and room.auction_state == "bidding":
                    active_count = sum(1 for x in room.players if not x.is_finished and not x.is_frozen)
                    if active_count > 1 and p.id == room.highest_bidder_id:
                        await websocket.send_json({
                            "type": "toast",
                            "level": "info",
                            "message": "En yüksek teklif (veya 1 ₺ sıra tabanı) şu an sende! Başkası teklif verene kadar pas geçemezsin."
                        })
                    else:
                        p.passed_current_item = True
                        await room.broadcast_state()
                        await check_all_passed_or_resolved(room)

            elif action == "buy_card":
                p = room.get_player(player_id)
                if p:
                    cid = data.get("cardID", "")
                    err = await handle_buy_card(room, p, cid)
                    if err:
                        await websocket.send_json({"type": "toast", "level": "danger", "message": err})
                    else:
                        await websocket.send_json({"type": "toast", "level": "success", "message": "Kart gizli eline eklendi!"})

            elif action == "use_card":
                p = room.get_player(player_id)
                if p:
                    slot_idx = int(data.get("slotIndex", -1))
                    target_id = data.get("targetId")
                    err = await handle_use_card(room, p, slot_idx, target_id)
                    if err:
                        await websocket.send_json({"type": "toast", "level": "danger", "message": err})

            elif action == "undo":
                if player_id == room.host_id and room.history_stack and room.auction_state == "idle":
                    last_tx = room.history_stack.pop()
                    eid = last_tx["entryId"]
                    for e in room.pool_entries:
                        if e["id"] == eid:
                            e["state"] = "available"
                            break
                    if last_tx["type"] == "sold":
                        buyer = room.get_player(last_tx["buyerId"])
                        if buyer:
                            buyer.budget += last_tx["price"]
                            buyer.purchases = [x for x in buyer.purchases if x["id"] != eid]
                    if "prevTurnIndex" in last_tx:
                        room.turn_index = last_tx["prevTurnIndex"]
                    room.current_round = max(1, room.current_round - 1)
                    if room.phase == "finished":
                        room.phase = "playing"
                        room.judge_result = None
                    await room.broadcast_event({"type": "toast", "level": "info", "message": "Son işlem geri alındı."})
                    await room.broadcast_state()

            elif action == "return_to_lobby":
                if player_id == room.host_id:
                    if room.timer_task and not room.timer_task.done():
                        room.timer_task.cancel()
                    room.phase = "setup"
                    room.auction_state = "idle"
                    room.current_entry = None
                    room.judge_result = None
                    await room.broadcast_state()

    except WebSocketDisconnect:
        room.connections.pop(player_id, None)
    except Exception:
        room.connections.pop(player_id, None)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)
