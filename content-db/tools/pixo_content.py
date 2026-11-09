"""Pixo content tool: checks the content library and publishes the delivered session files.

Usage (from the repository root):
    uv run --with jsonschema python content-db/tools/pixo_content.py check
    uv run --with jsonschema python content-db/tools/pixo_content.py publish            # test publish
    uv run --with jsonschema python content-db/tools/pixo_content.py publish --release  # real children: strict media rules
    uv run --with jsonschema python content-db/tools/pixo_content.py sql                # db/seed.sql for Supabase

Every message has a code (S01, R03, P02...). Each code is explained in content-db/docs/07-verifications.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    sys.exit("jsonschema is missing: run with  uv run --with jsonschema python ...")

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library"
SCHEMAS = ROOT / "schemas"
PUBLISHED = ROOT / "published"
MEDIA_DIR = ROOT / "media"
CURRICULUM = ROOT / "reference" / "curriculum-pre-a1.csv"

FOLDERS = {"objectives": "objective", "words": "word", "media": "media", "sessions": "session"}
MAX_WORDS_PER_SENTENCE = 5
MIN_NAME_COUNT = 3
FORBIDDEN = {"no", "wrong"}  # never said as feedback; allowed only when "no" is the word being taught


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, code: str, where: str, msg: str) -> None:
        self.errors.append(f"[{code}] {where}: {msg}")

    def warn(self, code: str, where: str, msg: str) -> None:
        self.warnings.append(f"[{code}] {where}: {msg}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name: str):
    schema = load_json(SCHEMAS / f"{name}.schema.json")
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def load_library(rep: Report) -> dict[str, dict[str, dict]]:
    """Returns {type: {id: document}} and checks schema, file names and unique ids (S01-S03)."""
    lib: dict[str, dict[str, dict]] = {t: {} for t in ["program", *FOLDERS.values()]}
    seen: dict[str, str] = {}
    files = [(LIB / "program.json", "program")]
    for folder, typ in FOLDERS.items():
        files += [(p, typ) for p in sorted((LIB / folder).glob("*.json"))]
    validators = {t: validator(t) for t in lib}
    for path, typ in files:
        where = str(path.relative_to(ROOT))
        try:
            doc = load_json(path)
        except json.JSONDecodeError as e:
            rep.error("S01", where, f"JSON invalide ({e})")
            continue
        for err in sorted(validators[typ].iter_errors(doc), key=lambda e: list(e.absolute_path)):
            loc = "/".join(str(x) for x in err.absolute_path) or "(racine)"
            rep.error("S01", where, f"schéma {typ} : {loc} : {err.message[:200]}")
        did = doc.get("id", "?")
        if typ != "program" and path.stem != did:
            rep.error("S02", where, f"le nom du fichier doit être l'id ({did}.json)")
        if did in seen:
            rep.error("S03", where, f"id {did} déjà utilisé dans {seen[did]}")
        seen[did] = where
        lib[typ][did] = doc
    return lib


def curriculum_items() -> set[str]:
    """All words/chunks of the Pre-A1 curriculum, lowercase, without quotes, stars or ellipses."""
    items: set[str] = set()
    if not CURRICULUM.exists():
        return items
    with CURRICULUM.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for raw in row["new_items"].split(","):
                t = raw.strip().strip('"').rstrip("*").replace("…", "").strip().lower()
                if t and not t.startswith("("):
                    items.add(t)
    return items


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def word_count(sentence: str) -> int:
    return len(re.findall(r"\{name\}|[A-Za-z0-9']+", sentence.replace(":", " ")))


# ---------------------------------------------------------------- checks
def check_references(lib, rep: Report) -> None:
    words, media, objs, sessions = lib["word"], lib["media"], lib["objective"], lib["session"]
    for wid, w in words.items():
        if w["image_media"] and w["image_media"] not in media:
            rep.error("R01", wid, f"image_media {w['image_media']} n'existe pas")
        if w["taught_in"] not in sessions:
            rep.warn("R06", wid, f"taught_in {w['taught_in']} : séance pas encore écrite")
    for mid, m in media.items():
        for w in m.get("words", []):
            if w not in words:
                rep.error("R02", mid, f"mot {w} inconnu")
    program_sessions = {s for lvl in lib["program"].get("pixo-english", {}).get("levels", [])
                        for mod in lvl["modules"] for u in mod["units"] for s in u["sessions"]}
    for sid, s in sessions.items():
        if sid not in program_sessions:
            rep.error("R03", sid, "la séance n'est pas dans la carte du programme (program.json)")
        for o in s["objectives"]:
            if o not in objs:
                rep.error("R04", sid, f"objectif {o} inconnu")
        for w in s["new_words"]:
            if w not in words:
                rep.error("R05", sid, f"mot nouveau {w} inconnu")
        for a in s["activities"]:
            refs = [a.get("word_id"), a.get("correct_word_id"), a.get("expected_word_id"),
                    *[i["word_id"] for i in a.get("images", [])]]
            for r in filter(None, refs):
                if r not in words:
                    rep.error("R05", f"{sid}/{a['id']}", f"mot {r} inconnu")
            for r in filter(None, [a.get("media_id"), a.get("image_media")]):
                if r not in media:
                    rep.error("R01", f"{sid}/{a['id']}", f"média {r} inconnu")


def check_variants(lib, rep: Report) -> None:
    """V01: a variant must never be another program word. V02: lowercase, no duplicates across words."""
    words = lib["word"]
    program = curriculum_items()
    owner: dict[str, str] = {}
    for wid, w in words.items():
        own = w["text"].lower().replace("…", "").strip().rstrip("!?").strip()
        for v in w["accepted_variants"]:
            if v != v.lower():
                rep.error("V02", wid, f"variante « {v} » doit être en minuscules")
            if v in owner and owner[v] != wid:
                rep.error("V02", wid, f"variante « {v} » déjà acceptée pour {owner[v]}")
            owner[v] = wid
            if v != own and v in program:
                rep.error("V01", wid, f"variante « {v} » est un autre mot du programme")
        others = {o["text"].lower().rstrip("!?…").strip() for o in words.values() if o is not w}
        for v in w["accepted_variants"]:
            if v in others:
                rep.error("V01", wid, f"variante « {v} » est le mot d'un autre document")


def check_session(sid: str, s: dict, lib, rep: Report, earlier_words: set[str]) -> None:
    acts = s["activities"]
    by_id = {a["id"]: a for a in acts}
    if len(by_id) != len(acts):
        rep.error("A01", sid, "deux activités ont le même id")
    positions = sorted(a["position"] for a in acts)
    if positions != list(range(1, len(acts) + 1)):
        rep.error("A02", sid, f"les positions doivent aller de 1 à {len(acts)} sans trou ni doublon")
    ordered = sorted(acts, key=lambda a: a["position"])
    if ordered[0]["type"] != "greeting" or ordered[0].get("moment") != "hello":
        rep.error("A03", sid, "la première activité doit être le bonjour (greeting, moment hello)")
    if ordered[-1]["type"] != "greeting" or ordered[-1].get("moment") != "bye":
        rep.error("A03", sid, "la dernière activité doit être l'au revoir (greeting, moment bye), après les rattrapages")
    # retries
    for a in acts:
        where = f"{sid}/{a['id']}"
        for r in a.get("retry_activity_ids", []):
            if r not in by_id:
                rep.error("A04", where, f"rattrapage {r} introuvable")
            elif by_id[r]["execution_mode"] != "retry_only":
                rep.error("A05", where, f"le rattrapage {r} doit être en retry_only")
            elif by_id[r]["position"] < a["position"]:
                rep.error("A06", where, f"le rattrapage {r} doit être placé après l'exercice")
        if a["execution_mode"] == "retry_only" and a.get("retry_activity_ids"):
            rep.error("A07", where, "un rattrapage n'a pas lui-même de rattrapage")
        if a["category"] == "reward" and a.get("retry_activity_ids"):
            rep.error("A07", where, "une récompense n'a pas de rattrapage")
    used_as_retry = {r for a in acts for r in a.get("retry_activity_ids", [])}
    for a in acts:
        if a["execution_mode"] == "retry_only" and a["id"] not in used_as_retry:
            rep.warn("A08", f"{sid}/{a['id']}", "rattrapage jamais appelé")
    # pedagogy
    name_count = 0
    for a in acts:
        where = f"{sid}/{a['id']}"
        text = a["instruction"]
        name_count += text.count("{name}")
        for sent in sentences(text):
            n = word_count(sent)
            if n > MAX_WORDS_PER_SENTENCE:
                rep.error("P01", where, f"« {sent} » : {n} mots (maximum {MAX_WORDS_PER_SENTENCE} par phrase)")
        teaching_no = a.get("word_id") == "w_no" or a.get("correct_word_id") == "w_no"
        for tok in re.findall(r"[A-Za-z']+", text):
            if tok.lower() in FORBIDDEN and not (tok.lower() == "no" and teaching_no):
                rep.error("P02", where, f"« {tok} » interdit dans une consigne (on encourage, on ne dit jamais No / Wrong)")
    if name_count < MIN_NAME_COUNT:
        rep.error("P03", sid, f"prénom {name_count} fois (minimum {MIN_NAME_COUNT})")
    # show before ask
    presented: set[str] = set()
    new = set(s["new_words"])
    for a in ordered:
        if a["type"] == "present":
            presented.add(a["word_id"])
        asked = a.get("word_id") if a["type"] in ("repeat",) else a.get("correct_word_id") or a.get("expected_word_id")
        if asked and asked in new and asked not in presented:
            rep.error("P04", f"{sid}/{a['id']}", f"{asked} est demandé avant d'avoir été montré (present)")
        for img in a.get("images", []):
            w = img["word_id"]
            if w not in new and w not in earlier_words:
                rep.error("P05", f"{sid}/{a['id']}", f"image {w} : mot ni nouveau ni déjà appris")
    for w in new:
        types = {a["type"] for a in acts if a.get("word_id") == w}
        if not {"present", "repeat"} <= types:
            rep.error("P06", sid, f"le mot nouveau {w} doit avoir un present et un repeat")
    has_review = any(a["type"] == "review" for a in acts)
    if has_review and not earlier_words:
        rep.error("P07", sid, "révision dans la première séance : il n'y a encore rien à réviser")
    if not has_review and earlier_words:
        rep.warn("P07", sid, "pas de révision alors que des mots ont déjà été appris")


def ordered_sessions(lib) -> list[str]:
    order = []
    for lvl in lib["program"].get("pixo-english", {}).get("levels", []):
        for mod in lvl["modules"]:
            for u in mod["units"]:
                order += u["sessions"]
    return [s for s in order if s in lib["session"]]


def check_media_files(lib, rep: Report, release: bool) -> None:
    for mid, m in lib["media"].items():
        lic = m["licence"]
        used = media_in_use(lib, mid)
        if not used:
            continue
        if release and not (lic["cleared_for_children"] and lic["terms"] == "cleared"):
            rep.error("M01", mid, f"licence « {lic['terms']} » : interdit pour une publication avec de vrais enfants")
        elif not lic["cleared_for_children"]:
            rep.warn("M01", mid, f"licence « {lic['terms']} » : tests internes seulement")
        if m["production"] == "todo":
            (rep.error if release else rep.warn)("M02", mid, f"média à produire ({m['storage_path']})")
        elif not (MEDIA_DIR / Path(m["storage_path"]).relative_to("media")).exists():
            rep.warn("M03", mid, f"fichier absent en local : content-db/{m['storage_path']}")


def media_in_use(lib, mid: str) -> bool:
    for s in lib["session"].values():
        for a in s["activities"]:
            if a.get("media_id") == mid or a.get("image_media") == mid:
                return True
            ws = [a.get("word_id"), a.get("correct_word_id"), *[i["word_id"] for i in a.get("images", [])]]
            if any(w and lib["word"].get(w, {}).get("image_media") == mid for w in ws):
                return True
    return False


def run_checks(rep: Report, release: bool = False):
    lib = load_library(rep)
    if rep.errors:
        return lib
    check_references(lib, rep)
    check_variants(lib, rep)
    learned: set[str] = set()
    for sid in ordered_sessions(lib):
        s = lib["session"][sid]
        check_session(sid, s, lib, rep, set(learned))
        learned |= set(s["new_words"])
    check_media_files(lib, rep, release)
    return lib


# ---------------------------------------------------------------- publish
def build_delivered(sid: str, lib) -> dict:
    s = lib["session"][sid]
    words, media, objs = lib["word"], lib["media"], lib["objective"]

    def uri(mid):
        return media[mid]["storage_path"] if mid else None

    used: list[str] = list(s["new_words"])
    for a in sorted(s["activities"], key=lambda a: a["position"]):
        for w in [a.get("word_id"), a.get("correct_word_id"), a.get("expected_word_id"), *[i["word_id"] for i in a.get("images", [])]]:
            if w and w not in used:
                used.append(w)
    out_words = []
    for w in used:
        d = words[w]
        item = {"id": w, "word": d["text"], "uri": uri(d["image_media"]), "type": d["kind"], "accepted_variants": d["accepted_variants"]}
        if d["match"] != "exact":
            item["match"] = d["match"]
        out_words.append(item)

    acts = []
    for a in sorted(s["activities"], key=lambda a: a["position"]):
        b = {k: v for k, v in a.items() if k not in ("media_id", "images", "correct_word_id", "image_media")}
        if a["type"] == "sing_with_me":
            m = media[a["media_id"]]
            b["media_uri"] = m["storage_path"]
            b["lyrics"] = " ".join(line["text"] for line in m["lyrics"])
            b["timestamps"] = m["lyrics"]
        elif a["type"] == "watch_video":
            b["media_uri"] = media[a["media_id"]]["storage_path"]
        elif a["type"] == "visual_description":
            b["uri"] = uri(a["image_media"])
        if "images" in a:
            b["images"] = [{"label": words[i["word_id"]]["text"], "uri": uri(words[i["word_id"]]["image_media"])} for i in a["images"]]
            b["correct_label"] = words[a["correct_word_id"]]["text"]
        acts.append(b)

    return {
        "id": sid, "version": s["version"], "position": s["position"], "title": s["title"],
        "program_id": s["program_id"], "module_id": s["module_id"], "unit_id": s["unit_id"],
        "objectives": [{"id": o, "title": objs[o]["title_fr"], "framework": objs[o]["framework"],
                        "gse_value": objs[o]["gse_value"], "skill": objs[o]["skill"]} for o in s["objectives"]],
        "words": out_words,
        "activities": acts,
    }


def build_index(lib, published: dict[str, int]) -> dict:
    taught: dict[str, list[str]] = {}
    in_images: dict[str, list[str]] = {}
    obj_map: dict[str, list[str]] = {}
    media_map: dict[str, list[str]] = {}
    for sid in ordered_sessions(lib):
        s = lib["session"][sid]
        for w in s["new_words"]:
            taught.setdefault(w, []).append(sid)
        for a in s["activities"]:
            for i in a.get("images", []):
                if i["word_id"] not in s["new_words"]:
                    in_images.setdefault(i["word_id"], []).append(sid)
            if a.get("media_id"):
                media_map.setdefault(a["media_id"], [])
                if sid not in media_map[a["media_id"]]:
                    media_map[a["media_id"]].append(sid)
        for o in s["objectives"]:
            obj_map.setdefault(o, []).append(sid)
    for wid, w in lib["word"].items():
        if w["image_media"]:
            media_map.setdefault(w["image_media"], []).append(wid)
    all_items = curriculum_items()
    taught_texts = {lib["word"][w]["text"].lower().replace("…", "").rstrip("!?").strip() for w in taught}
    return {
        "type": "index",
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "program": f"pixo-english@{lib['program']['pixo-english']['version']}",
        "sessions": published,
        "word_taught_in": taught,
        "word_used_again_in": in_images,
        "objective_to_sessions": obj_map,
        "media_to_documents": media_map,
        "coverage": {"curriculum_items": len(all_items), "items_written": len(taught_texts & all_items),
                     "objectives_covered": sorted(obj_map)},
    }


def publish(rep: Report, release: bool) -> None:
    lib = run_checks(rep, release)
    if rep.errors:
        return
    delivered_validator = validator("delivered-session")
    PUBLISHED.mkdir(exist_ok=True)
    published: dict[str, int] = {}
    for sid in ordered_sessions(lib):
        out = build_delivered(sid, lib)
        for err in delivered_validator.iter_errors(out):
            rep.error("S04", sid, f"fichier livré non conforme : {err.message[:200]}")
        target = PUBLISHED / f"{sid}.v{out['version']}.json"
        text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") != text:
            rep.error("F01", sid, f"{target.name} est déjà publié et figé : le contenu a changé, passe la séance en version {out['version'] + 1}")
            continue
        if not rep.errors:
            target.write_text(text, encoding="utf-8")
        published[sid] = out["version"]
    if not rep.errors:
        (PUBLISHED / "index.json").write_text(json.dumps(build_index(lib, published), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sql_literal(obj) -> str:
    return "'" + json.dumps(obj, ensure_ascii=False).replace("'", "''") + "'::jsonb"


def export_sql(rep: Report) -> None:
    """Writes db/seed.sql: schemas + library documents + published sessions, ready for the Supabase SQL editor."""
    lib = run_checks(rep)
    if rep.errors:
        return
    lines = ["-- Généré par pixo_content.py sql : NE PAS MODIFIER À LA MAIN.",
             "-- Charge les schémas, les documents de la bibliothèque et les séances publiées.", "begin;"]
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        t = path.name.removesuffix(".schema.json")
        lines.append(f"insert into content_schema (doc_type, schema) values ('{t}', {sql_literal(load_json(path))})"
                     " on conflict (doc_type) do update set schema = excluded.schema, updated_at = now();")
    for typ, docs in lib.items():
        for did, d in docs.items():
            lines.append("insert into content_document (id, doc_type, version, status, body, updated_by) values "
                         f"('{did}', '{typ}', {d['version']}, '{d['status']}', {sql_literal(d)}, '{d['updated_by']}')"
                         " on conflict (id) do update set version = excluded.version, status = excluded.status,"
                         " body = excluded.body, updated_by = excluded.updated_by;")
    for path in sorted(PUBLISHED.glob("*.v*.json")):
        d = load_json(path)
        lines.append("insert into published_session (session_id, version, delivered) values "
                     f"('{d['id']}', {d['version']}, {sql_literal(d)}) on conflict do nothing;")
    lines.append("commit;")
    (ROOT / "db" / "seed.sql").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pixo content: check and publish")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="vérifie toute la bibliothèque")
    c.add_argument("--release", action="store_true", help="règles strictes (vrais enfants)")
    p = sub.add_parser("publish", help="vérifie puis fabrique published/<séance>.v<version>.json + index.json")
    p.add_argument("--release", action="store_true", help="règles strictes (vrais enfants)")
    sub.add_parser("sql", help="fabrique db/seed.sql pour charger la bibliothèque dans Supabase")
    args = ap.parse_args(argv)
    rep = Report()
    if args.cmd == "check":
        run_checks(rep, args.release)
    elif args.cmd == "publish":
        publish(rep, args.release)
    else:
        export_sql(rep)
    for w in rep.warnings:
        print("ATTENTION", w)
    for e in rep.errors:
        print("ERREUR   ", e)
    status = "OK" if not rep.errors else "ÉCHEC"
    print(f"\n{status} : {len(rep.errors)} erreur(s), {len(rep.warnings)} avertissement(s)")
    if args.cmd == "publish" and not rep.errors:
        print(f"Fichiers livrés dans {PUBLISHED.relative_to(ROOT.parent)}")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
