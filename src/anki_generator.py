import pandas as pd
import genanki
import hashlib
import json
import os
import shutil
import re
import ast
from pathlib import Path
from datasets import load_dataset, Audio, Image
from pypinyin import lazy_pinyin, Style
import argparse
from display import GeneratorDisplay

DEFAULT_CONFIG = {
  "base-example": {
    "deck_root": "ChineseIsEasy::Dictionary",
    "dataset_filter": {
      "field": "SetsItBelongsTo",
      "value": "SUBTLEX-CH",
      "sort_by": "WCount",
      "limit": 2000
    },
    "grouping": {
      "strategy": "field",
      "field": "Catégorie",
      "default_group": "Divers"
    },
    "metadata_badges": ["Frequency", "Category"],
    "fields_mapping": {
      "Word": "Word",
      "Traditional": "Traditionnel",
      "Pinyin": "Pinyin",
      "Meaning": "Signification",
      "Explanation": "Explication",
      "Image": "hf_img_optim",
      "Audio": "hf_audio_word",
      "Examples": "hf_examples_json"
    }
  },
  "tone-practice": {
    "deck_root": "ChineseIsEasy::TonePairs",
    "dataset_filter": {
      "field": "SetsItBelongsTo",
      "value": "SUBTLEX-CH",
      "limit": 500
    },
    "grouping": {
      "strategy": "field",
      "field": "Computed_AtonalPinyin",
      "default_group": "Unknown"
    },
    "metadata_badges": ["Computed_AtonalPinyin"],
    "fields_mapping": {
      "Word": "Word",
      "Traditional": "Traditionnel",  
      "Pinyin": "Pinyin",
      "Meaning": "Signification",
      "Explanation": "Explication", 
      "Audio": "hf_audio_word",
      "Image": "hf_img_optim",
      "Examples": "hf_examples_json", 
      "AtonalPinyin": "Computed_AtonalPinyin"
    }
  },
  "poetry": {
    "deck_root": "ChineseIsEasy::Poetry",
    "dataset_filter": {
      "field": "SetsItBelongsTo",
      "value": "Poems"
    },
    "grouping": {
      "strategy": "field",
      "field": "Computed_Author",
      "default_group": "Anonyme"
    },
    "metadata_badges": ["Computed_Author", "Category"],
    "fields_mapping": {
      "Word": "Word",
      "Traditional": "Traditionnel", 
      "Pinyin": "Pinyin",
      "Meaning": "Signification",
      "Explanation": "Explication",
      "Image": "hf_img_optim",
      "Audio": "hf_audio_word",
      "Author": "Computed_Author",
      "Examples": "hf_examples_json"
    }
  },
  "chengyu-block": {
    "deck_root": "ChineseIsEasy::Chengyu",
    "dataset_filter": {
      "field": "SetsItBelongsTo",
      "value": "Chengyu",
      "limit": 1000
    },
    "grouping": {
      "strategy": "chunk",
      "size": 50,
      "prefix": "Bloc"
    },
    "metadata_badges": ["Category"],
    "fields_mapping": {
      "Word": "Word",
      "Traditional": "Traditionnel",
      "Pinyin": "Pinyin",
      "Meaning": "Signification",
      "Explanation": "Explication",
      "Image": "hf_img_optim",
      "Audio": "hf_audio_word",
      "Examples": "hf_examples_json"
    }
  }
}

class DataEnricher:
    @staticmethod
    def get_atonal_pinyin(text):
        if not text or not isinstance(text, str): return ""
        return "".join(lazy_pinyin(text, style=Style.NORMAL))

    @staticmethod
    def extract_author(infos_val):
        if pd.isna(infos_val) or infos_val is None or infos_val == "":
            return "Unknown"
        data = None
        if isinstance(infos_val, dict):
            data = infos_val
        elif isinstance(infos_val, str):
            try:
                data = ast.literal_eval(infos_val)
            except Exception:
                return "Unknown"

        if data and isinstance(data, dict):
            sens_list = data.get("sens", [])
            if isinstance(sens_list, list):
                for item in sens_list:
                    if isinstance(item, str) and "Poème de" in item:
                        return item.replace("Poème de", "").strip()
            if "Auteur" in data:
                return data["Auteur"]
        return "Unknown"

    @classmethod
    def process(cls, df, ui):
        ui.info("Enriching data (Preprocessing)...")
        df['Computed_AtonalPinyin'] = df['Word'].apply(cls.get_atonal_pinyin)
        if 'infos' in df.columns:
            df['Computed_Author'] = df['infos'].apply(cls.extract_author)
        else:
            df['Computed_Author'] = "Unknown"
        if 'WCount' in df.columns: df['Frequency'] = df['WCount']
        if 'Catégorie' in df.columns: df['Category'] = df['Catégorie']
        return df

class AnkiFactory:
    def __init__(self, ui, examples_map=None, media_dir="../ChineseIsEasy", config_path="config.json"):
        self.ui = ui
        self.examples_map = examples_map if examples_map else {}
        self.root_path = Path(media_dir)
        self.export_dir = Path("build_media_tmp")
        if os.path.exists(config_path):
            self.ui.log(f"Loading configuration from: {config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
        else:
            self.ui.info("Config file not found. Using internal DEFAULT_CONFIG.")
            self.config_data = DEFAULT_CONFIG
        if self.export_dir.exists(): shutil.rmtree(self.export_dir)
        self.export_dir.mkdir(exist_ok=True)

    def _get_svg(self, key):
        svgs = {
            "Audio": """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="svg-icon"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>""",
            "Writer": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="svg-icon"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>""",
            "Analysis": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="svg-icon"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-10.6 8.5 8.5 0 0 1 4.6 1.3L21 3.5V11.5z"></path></svg>""",
            "Frequency": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>""",
            "Category": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>""",
            "Computed_Author": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>""",
            "Computed_AtonalPinyin": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>"""
        }
        return svgs.get(key, "")

    def get_id(self, key):
        return int(hashlib.sha1(key.encode("utf-8")).hexdigest()[:10], 16)

    def wrap_hanzi(self, text):
        if not text: return ""
        pattern = r'([\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+)'
        return re.sub(pattern, r'<span class="hanzi-text">\1</span>', str(text))

    def get_model(self, deck_config):
        metadata_badges_html = ""
        requested_badges = deck_config.get("metadata_badges", [])
        
        badge_styles = {
            "Frequency": "color:#90CAF9; border-color:rgba(144, 202, 249, 0.3)",
            "Category": "color:#A5D6A7; border-color:rgba(165, 214, 167, 0.3)",
            "Computed_Author": "color:#CE93D8; border-color:rgba(206, 147, 216, 0.3)",
            "Computed_AtonalPinyin": "color:#FFCC80; border-color:rgba(255, 204, 128, 0.3)"
        }
        default_style = "color:#B0BEC5; border-color:rgba(176, 190, 197, 0.3)"

        for meta in requested_badges:
            display_name = meta.replace("Computed_", "")
            style = badge_styles.get(meta, default_style)
            svg = self._get_svg(meta)
            metadata_badges_html += f"""
            {{{{#{meta}}}}}
            <div class="meta-tag" style="{style}">
                {svg} &nbsp;{display_name}: {{{{{meta}}}}}
            </div>
            {{{{/{meta}}}}}
            """

        js_script = """
        <script>
        (function() {
            function initExamples() {
                var triggers = document.querySelectorAll('.toggle-trigger');
                triggers.forEach(function(trigger) {
                    // On retire les anciens listeners pour éviter les doublons si Anki recharge
                    var newTrigger = trigger.cloneNode(true);
                    trigger.parentNode.replaceChild(newTrigger, trigger);
                    
                    newTrigger.addEventListener('click', function(e) {
                        var targetId = this.getAttribute('data-target');
                        var target = document.getElementById(targetId);
                        if (target) {
                            target.classList.toggle('active');
                        }
                    });
                });
            }
            // On lance le script immédiatement et aussi après un petit délai pour AnkiDroid
            initExamples();
            setTimeout(initExamples, 500);
        })();
        </script>
        """

        qfmt = f"""
        <link rel="stylesheet" href="_styles_v5.css">
        <div class="char-grid">
            <div class="char-item"><span class="char-zi f-simp">{{{{Word}}}}</span><span class="char-label">Simplifié</span></div>
            <div class="char-item"><span class="char-zi f-trad">{{{{Traditional}}}}</span><span class="char-label">Traditionnel</span></div>
            <div class="char-item"><span class="char-zi f-long">{{{{Word}}}}</span><span class="char-label">Long Cang</span></div>
            <div class="char-item"><span class="char-zi f-zhi">{{{{Word}}}}</span><span class="char-label">Zhi Mang</span></div>
        </div>
        <div id="writer-container"></div>
        <div class="main-btns">
             <button class="btn-ctrl" id="replay-btn">{self._get_svg("Writer")} Rejouer</button>
             <button class="btn-ctrl btn-audio-main" id="audio-btn">{self._get_svg("Audio")} Audio</button>
        </div>
        <div class="img-box">{{{{Image}}}}</div>
        <div class="meta-bar">{metadata_badges_html}</div>
        <div class="hidden-audio" id="hidden-audio-word">{{{{Audio}}}}</div>
        <script src="_hanzi-writer.min.js"></script>
        <script src="_shared_hanzi_v3.js"></script>
        <script>if(typeof initCardLogic === "function") {{ initCardLogic("{{{{Word}}}}", "audio-btn", "hidden-audio-word"); }}</script>
        """

        afmt = f"""
        <link rel="stylesheet" href="_styles_v5.css">
        {{{{FrontSide}}}}<hr class="sep">
        <div class="pinyin-box">{{{{Pinyin}}}}</div>
        <div class="meaning-box">{{{{Meaning}}}}</div>
        {{{{#Explanation}}}}
        <div class="grammar-container">
            <div class="grammar-header">{self._get_svg("Analysis")} Analyse & Nuances</div>
            <div class="grammar-content">{{{{Explanation}}}}</div>
        </div>
        {{{{/Explanation}}}}
        <div class="examples-header">Exemples en contexte</div>
        <div class="examples-wrapper">{{{{Examples}}}}</div>
        {js_script}
        """

        base_fields = ["Word", "Traditional", "Pinyin", "Meaning", "Explanation", "Image", "Audio", "Examples"]
        all_field_names = list(set(base_fields + requested_badges))
        
        return genanki.Model(
            self.get_id(f"CIE_Model_{deck_config.get('deck_root')}"),
            f"ChineseIsEasy Model ({deck_config.get('deck_root')})",
            fields=[{"name": f} for f in all_field_names],
            templates=[{"name": "Recognition", "qfmt": qfmt, "afmt": afmt}]
        )

    def export_media_file(self, data, ext=".mp3", specific_filename=None):
        if not data: return None
        content = data.get('bytes') if isinstance(data, dict) else None
        path_src = data.get('path') if isinstance(data, dict) else data
        if not content and (not path_src or not os.path.exists(str(path_src))): return None
        
        if specific_filename:
            filename = specific_filename
        elif isinstance(data, dict) and data.get('path'):
             filename = os.path.basename(data['path'])
        else:
             file_hash = hashlib.md5(content if content else str(path_src).encode()).hexdigest()[:10]
             filename = f"{file_hash}{ext}"
             
        dest_path = self.export_dir / filename
        if not dest_path.exists():
            if content:
                with open(dest_path, "wb") as f: f.write(content)
            else:
                shutil.copy2(path_src, dest_path)
        return filename

    def format_examples_with_audio(self, examples_json):
        """Generates HTML for split-box examples with Inline OnClick (Mobile Fix)."""
        if not examples_json: return ""
        try:
            exs = json.loads(examples_json) if isinstance(examples_json, str) else examples_json
            out_visible, out_hidden = [], []
            for i, ex in enumerate(exs):
                ex_hash = ex.get('hash')
                audio_data = self.examples_map.get(ex_hash)
                filename = self.export_media_file(audio_data, ".mp3", specific_filename=f"{ex_hash}.mp3") if audio_data else None
                
                audio_div_id = f"sent_aud_{i}_{ex_hash if ex_hash else i}"
                
                html = f"""
                <div class="sentence-container">
                    <div class="sentence-left" onclick="toggleReveal(this)">
                        <div class="sentence-ch">{ex['ch']}</div>
                        <div class="reveal-container">
                            <div class="reveal-py">{ex['py']}</div>
                            <div class="reveal-fr">{ex['fr']}</div>
                        </div>
                    </div>
                    <div class="sentence-right" onclick="event.stopPropagation(); playExAudio('{audio_div_id}')">
                        {self._get_svg("Audio")}
                    </div>
                </div>"""
                
                audio_div = f'<div id="{audio_div_id}" class="hidden-audio">[sound:{filename}]</div>' if filename else ""
                out_visible.append(html)
                out_hidden.append(audio_div)
            return "".join(out_visible + out_hidden)
        except Exception: return ""

    def _get_fallback_audio_from_examples(self, examples_json):
        if not examples_json: return None
        try:
            exs = json.loads(examples_json) if isinstance(examples_json, str) else examples_json
            if exs and len(exs) > 0:
                first_ex_hash = exs[0].get('hash')
                if first_ex_hash:
                    return self.examples_map.get(first_ex_hash)
        except: return None
        return None

    def _get_subdeck_name(self, row, index, deck_config):
        root = deck_config["deck_root"] 
        grouping = deck_config.get("grouping", {"strategy": "none"})
        strategy = grouping.get("strategy", "none")

        if strategy == "dynamic" and "tonepairs" in root.lower():
            atonal = str(row.get("Computed_AtonalPinyin", "")).lower().strip()
            
            if not atonal:
                return f"{root}::Divers"
            
            level1 = atonal[0].upper()
            level2 = atonal[:2].capitalize() if len(atonal) > 1 else level1
            level3 = atonal[:3].capitalize() if len(atonal) > 2 else level2
            level4 = atonal[:4].capitalize() if len(atonal) > 3 else level3
            return f"{root}::{level1}::{level2}::{level3}::{level4}::{atonal}"

        if strategy == "field":
            field = grouping.get("field")
            val = row.get(field)
            if not val: val = grouping.get("default_group", "Divers")
            return f"{root}::{str(val).capitalize()}"
        
        elif strategy == "chunk":
            size = grouping.get("size", 50)
            prefix = grouping.get("prefix", "Part")
            chunk_num = (index // size) + 1
            return f"{root}::{prefix} {chunk_num:02d}"
            
        return root

    def run_all(self, full_df):
        self.ui.log(f"Starting generation for {len(self.config_data)} deck configurations...")
        with self.ui.get_progress() as progress:
            total_task = progress.add_task("[bold green]Total Progress", total=len(self.config_data))
            for config_name, deck_config in self.config_data.items():
                self._generate_single_config(config_name, deck_config, full_df, progress)
                progress.advance(total_task)

    def _generate_single_config(self, config_name, deck_config, full_df, progress):
        self.ui.log(f"Processing config: [bold cyan]{config_name}[/bold cyan]")
        filter_cfg = deck_config.get("dataset_filter", {})
        filtered_df = full_df.copy()
        
        if "field" in filter_cfg and "value" in filter_cfg:
             filtered_df = filtered_df[filtered_df[filter_cfg["field"]] == filter_cfg["value"]]
        if "sort_by" in filter_cfg and filter_cfg["sort_by"] in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=filter_cfg["sort_by"], ascending=False)
        if "limit" in filter_cfg:
            filtered_df = filtered_df.head(filter_cfg["limit"])

        self.ui.log(f"  -> {len(filtered_df)} cards selected.")
        
        model = self.get_model(deck_config)
        fields_map = deck_config["fields_mapping"]
        requested_badges = deck_config.get("metadata_badges", [])
        deck_instances = {}

        deck_task = progress.add_task(f"  Building {config_name}", total=len(filtered_df))
        
        for i, (index, row) in enumerate(filtered_df.iterrows()):
            deck_name = self._get_subdeck_name(row, i, deck_config)
            if deck_name not in deck_instances:
                deck_instances[deck_name] = genanki.Deck(self.get_id(deck_name), deck_name)

            note_fields = []
            model_field_names = [f["name"] for f in model.fields]
            audio_source = row.get(fields_map.get("Audio"))
            examples_source = row.get(fields_map.get("Examples"))
            
            for field_name in model_field_names:
                val = None
                if field_name in fields_map:
                    val = row.get(fields_map[field_name])
                elif field_name in requested_badges:
                    val = row.get(field_name)

                if field_name == "Traditional" and (pd.isna(val) or val == ""):
                    val = row.get(fields_map.get("Word", "Word"))
                
                if field_name == "Audio":
                    is_empty = (pd.isna(val) or val is None)
                    if is_empty: 
                        fallback_audio = self._get_fallback_audio_from_examples(examples_source)
                        if fallback_audio:
                            val = f"[sound:{self.export_media_file(fallback_audio, '.mp3')}]"
                        else:
                            val = "" 
                    else:
                        val = f"[sound:{self.export_media_file(val, '.mp3')}]"

                if field_name == "Frequency" and val:
                     try: val = f"{int(val):,}".replace(",", " ")
                     except: pass
                
                if field_name in ["Explanation", "Meaning"]:
                     val = self.wrap_hanzi(val)
                     if val: val = str(val).replace("\n", "<br>")
                
                elif field_name == "Image":
                     val = f'<img src="{self.export_media_file(val, ".jpg")}">' if val else ""
                
                elif field_name == "Examples":
                     val = self.format_examples_with_audio(val)

                note_fields.append(str(val) if val is not None and not pd.isna(val) else "")

            deck_instances[deck_name].add_note(genanki.Note(model=model, fields=note_fields))
            progress.advance(deck_task)

        progress.remove_task(deck_task)

        assets_files = [
            (self.root_path/"fonts/FZ_Kai/_FZKai.ttf", "_FZKai.ttf"),
            (self.root_path/"fonts/Long_Cang/_LongCang.ttf", "_LongCang.ttf"),
            (self.root_path/"fonts/Zhi_Mang_Xing/_ZhiMangXing.ttf", "_ZhiMangXing.ttf"),
            (self.root_path/"scripts/_hanzi-writer.min.js", "_hanzi-writer.min.js"),
            (self.root_path/"scripts/_shared_hanzi_v3.js", "_shared_hanzi_v3.js"),
            (self.root_path/"styles/_styles_v5.css", "_styles_v5.css")
        ]
        
        for src, name in assets_files:
            if src.exists(): shutil.copy2(src, self.export_dir / name)
            
        package = genanki.Package(list(deck_instances.values()))
        package.media_files = [str(p) for p in self.export_dir.iterdir() if p.is_file()]
        
        strokes_dir = self.root_path / "graphics/strokes"
        if strokes_dir.exists():
            package.media_files += [str(p) for p in strokes_dir.glob("*.json")]
            
        safe_name = deck_config['deck_root'].replace("::", "_")
        out_name = f"ChineseIsEasy_{safe_name}.apkg"
        package.write_to_file(out_name)
        self.ui.success(f"Deck exported: {out_name}")

if __name__ == "__main__":
    ui = GeneratorDisplay(app_name="Anki Generator", version="2.0")
    ui.print_banner()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", type=str, default="config.json")
    args = arg_parser.parse_args()

    ui.info("Loading Datasets from Hugging Face...")
    ds_words = load_dataset('AxelDlv00/ChineseIsEasy', 'default', split='train')
    ds_words = ds_words.cast_column("hf_audio_word", Audio(decode=False))
    ds_words = ds_words.cast_column("hf_img_optim", Image(decode=False))
    
    ds_examples = load_dataset('AxelDlv00/ChineseIsEasy', 'examples', split='train')
    ds_examples = ds_examples.cast_column("audio", Audio(decode=False))

    ui.info("Indexing Example Audio...")
    examples_map = {}
    for ex in ds_examples:
        if ex.get('hash') and ex.get('audio') and ex['hash'] not in examples_map:
            examples_map[ex['hash']] = ex['audio']

    df_full = ds_words.to_pandas()
    df_full = DataEnricher.process(df_full, ui)

    factory = AnkiFactory(ui=ui, config_path=args.config, examples_map=examples_map)
    factory.run_all(df_full)