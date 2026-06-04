import argparse
import csv
import html
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


FIELD_SEPARATOR = "\x1f"
DEFAULT_MODEL_PATTERN = "ChineseIsEasy Model (ChineseIsEasy::Dictionary)"
FALLBACK_FIELDS = [
    "Word",
    "Traditional",
    "Pinyin",
    "Meaning",
    "Explanation",
    "Examples",
    "Category",
    "Frequency",
    "Image",
    "Audio",
]


def default_anki2_dir():
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Anki2"
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Anki2"
    return Path.home() / ".local/share/Anki2"


def discover_collections(anki2_dir=None):
    root = Path(anki2_dir or default_anki2_dir()).expanduser()
    if not root.exists():
        return []
    return sorted(root.glob("*/collection.anki2"))


def default_collection_path():
    collections = discover_collections()
    preferred = [path for path in collections if path.parent.name == "ChineseIsEasy"]
    if preferred:
        return preferred[0]
    user_one = [path for path in collections if path.parent.name == "User 1"]
    if user_one:
        return user_one[0]
    if len(collections) == 1:
        return collections[0]
    return default_anki2_dir() / "User 1/collection.anki2"


def default_output_dir():
    return Path(__file__).resolve().parents[1] / "MyLists"


def stable_id(text):
    import hashlib

    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:10], 16)


def stable_guid(text):
    import hashlib

    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def parse_csv_line(line):
    return next(csv.reader([line], delimiter=";", quotechar='"'))


def normalize_csv_row(row):
    normalized = {field: row.get(field, "").strip() for field in FALLBACK_FIELDS}
    if not normalized["Word"]:
        raise ValueError("CSV row is missing required Word field")
    if not normalized["Traditional"]:
        normalized["Traditional"] = normalized["Word"]
    normalized["Examples"] = format_fallback_examples(normalized["Examples"])
    return normalized


def format_fallback_examples(examples):
    parsed_examples = parse_fallback_examples(examples)
    if not parsed_examples:
        return examples

    blocks = []
    for example in parsed_examples:
        chinese = html.escape(example.get("ch", "").strip())
        pinyin = html.escape(example.get("py", "").strip())
        french = html.escape(example.get("fr", "").strip())
        if not chinese:
            continue
        blocks.append(
            '<div class="sentence-container">'
            '<div class="sentence-left" onclick="toggleReveal(this)">'
            f'<div class="sentence-ch">{chinese}</div>'
            '<div class="reveal-container">'
            f'<div class="reveal-py">{pinyin}</div>'
            f'<div class="reveal-fr">{french}</div>'
            "</div>"
            "</div>"
            "</div>"
        )
    return "".join(blocks)


def parse_fallback_examples(examples):
    if not examples:
        return []

    parsed_json = parse_json_examples(examples)
    if parsed_json:
        return parsed_json

    if "sentence-container" in examples:
        return parse_html_examples(examples)

    return []


def parse_json_examples(examples):
    try:
        data = json.loads(examples)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    parsed = []
    for item in data:
        if not isinstance(item, dict):
            continue
        parsed.append(
            {
                "ch": str(item.get("ch", "")),
                "py": str(item.get("py", "")),
                "fr": str(item.get("fr", "")),
            }
        )
    return parsed


def parse_html_examples(examples):
    pattern = re.compile(
        r'<div class="sentence-ch">(?P<ch>.*?)'
        r'<div class="reveal-container">.*?'
        r'<div class="reveal-py">(?P<py>.*?)'
        r'<div class="reveal-fr">(?P<fr>.*?)(?=<div class="sentence-container">|$)',
        re.DOTALL,
    )
    parsed = []
    for match in pattern.finditer(examples):
        parsed.append(
            {
                "ch": strip_tags(match.group("ch")),
                "py": strip_tags(match.group("py")),
                "fr": strip_tags(match.group("fr")),
            }
        )
    return parsed


def strip_tags(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def read_csv_rows(csv_path):
    path = Path(csv_path).expanduser()
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter=";", quotechar='"')
        if not reader.fieldnames:
            return rows
        missing_columns = [field for field in FALLBACK_FIELDS if field not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"{path} is missing CSV columns: {', '.join(missing_columns)}")
        for row in reader:
            if row and any(value for value in row.values() if value):
                rows.append(normalize_csv_row(row))
    return rows


def sibling_csv_path(list_file):
    if not list_file:
        return None
    return Path(list_file).expanduser().with_suffix(".csv")


def read_words_and_fallbacks(raw_items, list_file, fallback_csv):
    words = []
    fallback_rows = []
    if list_file:
        list_path = Path(list_file).expanduser()
        if not list_path.exists():
            raise FileNotFoundError(
                f"Word list not found: {list_path}\n"
                "If the path contains spaces, quote it. Example: --file 'mylists/3-05-2026-青神'"
            )
        for line_number, line in enumerate(list_path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if ";" in stripped:
                values = parse_csv_line(stripped)
                if values and values[0] == "Word":
                    continue
                if len(values) != len(FALLBACK_FIELDS):
                    raise ValueError(
                        f"{list_path}:{line_number} has {len(values)} CSV fields, expected {len(FALLBACK_FIELDS)}"
                    )
                row = normalize_csv_row(dict(zip(FALLBACK_FIELDS, values)))
                fallback_rows.append(row)
                words.append(row["Word"])
            else:
                words.append(stripped)
    for item in raw_items:
        words.extend(re.split(r"[\s,;]+", item))

    csv_path = Path(fallback_csv).expanduser() if fallback_csv else sibling_csv_path(list_file)
    if csv_path:
        for row in read_csv_rows(csv_path):
            fallback_rows.append(row)
            words.append(row["Word"])

    clean_words = []
    seen = set()
    for word in words:
        word = word.strip()
        if word and word not in seen:
            clean_words.append(word)
            seen.add(word)
    return clean_words, fallback_rows


def infer_list_name(name, list_file):
    if name:
        return name
    if not list_file:
        raise ValueError("provide a list name or use --file so the name can be inferred")
    return Path(list_file).expanduser().name


def split_fields(fields_blob):
    return fields_blob.split(FIELD_SEPARATOR)


def collection_error_message(path):
    discovered = discover_collections()
    if discovered:
        options = "\n".join(f"- {item}" for item in discovered)
        return f"Anki collection not found: {path}\nAvailable collections:\n{options}"
    return f"Anki collection not found: {path}"


def open_collection(collection_path):
    path = Path(collection_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(collection_error_message(path))
    return sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)


def read_varint(buffer, index):
    shift = 0
    value = 0
    while index < len(buffer):
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
    raise ValueError("truncated protobuf varint")


def protobuf_strings(buffer):
    strings = {}
    index = 0
    while index < len(buffer):
        key, index = read_varint(buffer, index)
        field_number = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            _, index = read_varint(buffer, index)
        elif wire_type == 2:
            length, index = read_varint(buffer, index)
            data = buffer[index : index + length]
            index += length
            try:
                strings[field_number] = data.decode("utf-8")
            except UnicodeDecodeError:
                pass
        else:
            break
    return strings


@contextmanager
def collection_connection(collection_path):
    path = Path(collection_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(collection_error_message(path))
    try:
        with open_collection(path) as connection:
            yield connection
            return
    except sqlite3.OperationalError as error:
        if "locked" not in str(error).lower():
            raise

    print(f"Collection is locked, retrying from a temporary snapshot: {path}", file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="cie-anki-") as temp_dir:
        snapshot_path = Path(temp_dir) / "collection.anki2"
        shutil.copy2(path, snapshot_path)
        with sqlite3.connect(f"file:{snapshot_path}?mode=ro&immutable=1", uri=True) as connection:
            yield connection


def load_models(connection, model_pattern):
    models_json = connection.execute("select models from col").fetchone()[0]
    if models_json.strip():
        all_models = json.loads(models_json)
        matches = []
        for model_id, model in all_models.items():
            if model_pattern.lower() in model.get("name", "").lower():
                matches.append((int(model_id), model))
        return sort_models_by_preference(matches)

    return sort_models_by_preference(load_models_from_normalized_schema(connection, model_pattern))


def sort_models_by_preference(models):
    return sorted(models, key=lambda item: model_preference_score(item[1]), reverse=True)


def model_preference_score(model):
    templates = model.get("tmpls", [])
    template_text = "\n".join(
        f"{template.get('qfmt', '')}\n{template.get('afmt', '')}" for template in templates
    )
    score = 0
    if "_styles_v5.css" in template_text:
        score += 1000
    if "_shared_hanzi_v3.js" in template_text:
        score += 500
    if "_hanzi-writer.min.js" in template_text:
        score += 100
    score += len(model.get("name", ""))
    return score


def load_models_from_normalized_schema(connection, model_pattern):
    matches = []
    notetypes = connection.execute("select id, name from notetypes").fetchall()
    for model_id, name in notetypes:
        if model_pattern.lower() not in name.lower():
            continue

        fields = []
        field_rows = connection.execute("select ord, name from fields where ntid = ? order by ord", (model_id,))
        for ordinal, field_name in field_rows:
            fields.append({"ord": ordinal, "name": field_name})

        templates = []
        template_rows = connection.execute(
            "select ord, name, config from templates where ntid = ? order by ord",
            (model_id,),
        )
        for ordinal, template_name, config in template_rows:
            template_strings = protobuf_strings(config)
            templates.append(
                {
                    "ord": ordinal,
                    "name": template_name,
                    "qfmt": template_strings.get(1, ""),
                    "afmt": template_strings.get(2, ""),
                }
            )

        matches.append(
            (
                int(model_id),
                {
                    "id": int(model_id),
                    "name": name,
                    "flds": fields,
                    "tmpls": templates,
                    "css": "",
                },
            )
        )
    return matches


def model_to_genanki(model):
    import genanki

    fields = [{"name": field["name"]} for field in sorted(model["flds"], key=lambda item: item["ord"])]
    templates = []
    for template in sorted(model["tmpls"], key=lambda item: item["ord"]):
        templates.append(
            {
                "name": template["name"],
                "qfmt": template["qfmt"],
                "afmt": template["afmt"],
            }
        )
    return genanki.Model(
        int(model["id"]),
        model["name"],
        fields=fields,
        templates=templates,
        css=model.get("css", ""),
    )


def find_word_field_index(model):
    fields = sorted(model["flds"], key=lambda item: item["ord"])
    for field in fields:
        if field["name"] == "Word":
            return field["ord"]
    return 0


def model_field_names(model):
    return [field["name"] for field in sorted(model["flds"], key=lambda item: item["ord"])]


def select_fallback_model_id(models):
    return models[0][0]


def fallback_row_to_note_data(row, model):
    fields = []
    for field_name in model_field_names(model):
        fields.append(row.get(field_name, ""))
    return {
        "note_id": None,
        "guid": None,
        "fields": fields,
        "model_id": int(model["id"]),
    }


def load_notes_by_word(connection, models):
    notes_by_word = {}
    for model_id, model in models:
        word_index = find_word_field_index(model)
        rows = connection.execute(
            "select id, guid, flds from notes where mid = ?",
            (model_id,),
        )
        for note_id, guid, fields_blob in rows:
            fields = split_fields(fields_blob)
            if word_index >= len(fields):
                continue
            word = fields[word_index].strip()
            if word and word not in notes_by_word:
                notes_by_word[word] = {
                    "note_id": note_id,
                    "guid": guid,
                    "fields": fields,
                    "model_id": model_id,
                }
    return notes_by_word


def build_package(list_name, words, models, notes_by_word, fallback_rows, preserve_guids):
    models_by_id = {model_id: model for model_id, model in models}
    fallback_model_id = select_fallback_model_id(models)
    fallback_rows_by_word = {row["Word"]: row for row in fallback_rows}
    missing = []
    note_payloads = []

    for word in words:
        fallback_row = fallback_rows_by_word.get(word)
        if fallback_row:
            note_data = fallback_row_to_note_data(fallback_row, models_by_id[fallback_model_id])
        else:
            note_data = notes_by_word.get(word)
            if not note_data:
                missing.append(word)
                continue

        guid = note_data["guid"] if preserve_guids and note_data["guid"] else stable_guid(f"ChineseIsEasy::MyLists::{list_name}::{word}")
        note_payloads.append((note_data, guid))

    if not note_payloads:
        return None, 0, missing

    try:
        import genanki
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Missing dependency: genanki. Install the repository dependencies first:\n"
            "python -m pip install -r requirements.txt"
        ) from error

    deck_name = f"ChineseIsEasy::MyLists::{list_name}"
    deck = genanki.Deck(stable_id(deck_name), deck_name)
    genanki_models = {model_id: model_to_genanki(model) for model_id, model in models}

    for note_data, guid in note_payloads:
        deck.add_note(
            genanki.Note(
                model=genanki_models[note_data["model_id"]],
                fields=note_data["fields"],
                guid=guid,
                tags=["ChineseIsEasy", "MyLists", list_name],
            )
        )

    package = genanki.Package(deck)
    package.media_files = []
    return package, len(note_payloads), missing


def print_missing(missing):
    print("Missing words:")
    for word in missing:
        print(f"- {word}")


def output_path_for_list(output_dir, list_name):
    base_path = Path(output_dir) / list_name
    if base_path.exists() and base_path.is_file():
        return base_path.with_suffix(".apkg")
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / f"{list_name}.apkg"


def main():
    parser = argparse.ArgumentParser(
        description="Build a small media-free ChineseIsEasy MyLists APKG from an existing local Anki collection."
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="MyLists deck name. If omitted with --file, the file name is used.",
    )
    parser.add_argument("words", nargs="*", help="Chinese words, separated by spaces or commas")
    parser.add_argument("--file", help="UTF-8 text file containing one word per line")
    parser.add_argument(
        "--fallback-csv",
        help="Optional semicolon CSV with AI-filled fallback card rows. Defaults to the --file path with .csv extension.",
    )
    parser.add_argument("--collection", default=str(default_collection_path()), help="Path to collection.anki2")
    parser.add_argument(
        "--model-pattern",
        default=DEFAULT_MODEL_PATTERN,
        help="Case-insensitive substring used to select the source Anki note model",
    )
    parser.add_argument(
        "--preserve-guids",
        action="store_true",
        help="Reuse original note GUIDs. This is useful for updating existing notes, not for creating a separate duplicate deck.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Check which words would be found without writing an APKG")
    parser.add_argument("--output-dir", default=str(default_output_dir()), help="Directory where the list folder will be created")
    args = parser.parse_args()

    try:
        list_name = infer_list_name(args.name, args.file)
    except ValueError as error:
        parser.error(str(error))

    try:
        words, fallback_rows = read_words_and_fallbacks(args.words, args.file, args.fallback_csv)
    except FileNotFoundError as error:
        raise SystemExit(str(error))
    except ValueError as error:
        raise SystemExit(str(error))
    if not words:
        parser.error("provide words as arguments or with --file")

    with collection_connection(args.collection) as connection:
        models = load_models(connection, args.model_pattern)
        if not models:
            raise SystemExit(f"No source models matched: {args.model_pattern}")
        notes_by_word = load_notes_by_word(connection, models)

    fallback_words = {row["Word"] for row in fallback_rows}
    found = [word for word in words if word in notes_by_word and word not in fallback_words]
    fallback_found = [word for word in words if word in fallback_words]
    missing = [word for word in words if word not in notes_by_word and word not in fallback_words]
    if args.dry_run:
        print(f"List name: {list_name}")
        print(f"Found in Anki collection: {len(found)}")
        print(f"Found in fallback CSV: {len(fallback_found)}")
        print(f"Missing: {len(missing)}")
        if missing:
            print_missing(missing)
            raise SystemExit(2)
        return

    package, added, missing = build_package(list_name, words, models, notes_by_word, fallback_rows, args.preserve_guids)
    if added == 0:
        print_missing(missing)
        raise SystemExit("No requested words were found in the source Anki collection. No APKG was written.")

    output_path = output_path_for_list(args.output_dir, list_name)
    package.write_to_file(str(output_path))

    print(f"Exported {added} notes to {output_path}")
    if missing:
        print_missing(missing)


if __name__ == "__main__":
    main()
