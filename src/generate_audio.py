""" 
This script uses [`voxcpm`](https://huggingface.co/openbmb/VoxCPM-0.5B) model from OpenBMB for the audio generation. 

Since the python environment setup can be tricky, here are the steps I used to get it working : 

```bash
conda create -n naturalaudio python=3.10 -y
conda activate naturalaudio

pip install voxcpm
pip install torchcodec
conda install "ffmpeg<8" -c conda-forge
pip install soundfile pandas huggingface_hub modelscope
```

And then download the required models :

```python
from huggingface_hub import snapshot_download
snapshot_download("openbmb/VoxCPM-0.5B")
from modelscope import snapshot_download
snapshot_download('iic/speech_zipenhancer_ans_multiloss_16k_base')
snapshot_download('iic/SenseVoiceSmall')
```
"""

import hashlib
import subprocess
from pathlib import Path
import soundfile as sf
from gtts import gTTS
from voxcpm import VoxCPM
import pandas as pd
from display import GeneratorDisplay

class AudioGenerator:
    def __init__(self, display_handler, mode="gtts", output_dir="audio_output", references_dir="audio_references"):
        """
        Initializes the audio generator.
        :param mode: "natural" (VoxCPM) or "gtts" (Google TTS)
        :param output_dir: Directory where audio files will be saved
        :param references_dir: Directory containing reference audio and metadata for natural mode
        """
        self.ui = display_handler
        self.mode = mode.lower()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.model = None
        self.df_ref = None
        self.ref_dir = Path(references_dir)

        if self.mode == "natural":
            self._init_natural_engine()
            self.ui.info("Using [bold magenta]VoxCPM[/] engine (Local & High Quality).")
        else:
            self.ui.info("Using [bold cyan]gTTS[/] engine (Fast & Cloud-based), it can reach rate limits.")

    def _init_natural_engine(self):
        """Lazy loading of the heavy VoxCPM model."""
        self.model = VoxCPM.from_pretrained("openbmb/VoxCPM-0.5B")
        
        metadata_path = self.ref_dir / "metadata.csv"
        if metadata_path.exists():
            self.df_ref = pd.read_csv(metadata_path)
            self.df_ref['text'] = self.df_ref['ID'].apply(
                lambda x: (self.ref_dir / f"{x}.txt").read_text(encoding="utf-8").strip()
            )
        else:
            self.ui.error("Metadata for natural voice cloning not found.")

    def _get_hash(self, text):
        """Stable filename based on text hash to avoid duplicates."""
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        return f"{h}"

    def _compress_to_mp3(self, wav_path, bitrate="48k"):
        """Converts local WAV to MP3 using ffmpeg."""
        mp3_path = wav_path.with_suffix(".mp3")
        if mp3_path.exists(): return mp3_path
        
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", bitrate, str(mp3_path)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if wav_path.exists(): wav_path.unlink()
        return mp3_path

    def generate(self, text):
        """
        Generates audio for the given text based on the selected mode.
        Returns the path to the .mp3 file.
        """
        filename = self._get_hash(text) + ".mp3"
        final_path = self.output_dir / filename

        if final_path.exists():
            return final_path

        try:
            if self.mode == "natural" and self.model:
                ref = self.df_ref.sample(n=1).iloc[0] # Randomly select a reference
                wav_temp = final_path.with_suffix(".wav")
                
                wav_data = self.model.generate(
                    text=text,
                    prompt_wav_path=str(self.ref_dir / f"{ref['ID']}.wav"),
                    prompt_text=ref['text'],
                    cfg_value=2.0,            
                    inference_timesteps=10,   
                    normalize=True,          
                    denoise=True,             
                    retry_badcase=True,        
                    retry_badcase_max_times=3,  
                    retry_badcase_ratio_threshold=6.0, 
                )
                sf.write(wav_temp, wav_data, 16000)
                return self._compress_to_mp3(wav_temp)

            else:
                tts = gTTS(text=text, lang="zh")
                tts.save(str(final_path))
                return final_path

        except Exception as e:
            self.ui.error(f"Generation failed: {e}")
            return None

    def process_batch(self, text_list):
        """Processes a list of strings with a progress bar."""
        results = {}
        with self.ui.get_progress() as progress:
            task = progress.add_task(f"[yellow]Audio ({self.mode})...", total=len(text_list))
            for text in text_list:
                path = self.generate(text)
                results[text] = path
                progress.update(task, advance=1, description=f"[cyan]Audio: {text[:10]}...")
        return results

if __name__ == "__main__":
    ui = GeneratorDisplay(app_name="Audio Test Suite", version="1.1")
    ui.print_banner()

    # TEST_MODE = "gtts" 
    TEST_MODE = "natural"
    
    phrases_test = [
        "你好，很高兴认识你。",
        "学中文很有趣，但也有一点难。"
    ]

    try:
        audio_gen = AudioGenerator(
            display_handler=ui, 
            mode=TEST_MODE,
            output_dir="test_results",
            references_dir="../ChineseIsEasy/audio_references"
        )
        results = audio_gen.process_batch(phrases_test)

        ui.console.print("\n[bold green]Results of Audio Generation:[/]\n")
        for text, path in results.items():
            if path:
                ui.success(f"Sentence : {text}")
                ui.console.print(f"   └── File : [blue]{path}[/]")
            else:
                ui.error(f"Failed for : {text}")

    except Exception as e:
        ui.error(f"Unexpected error: {e}")