import os
from prompt_manager import PromptManager
import torch
import hashlib
from pathlib import Path
from PIL import Image
from diffusers import AutoPipelineForText2Image
from display import GeneratorDisplay

class ImageGenerator:
    def __init__(self, display_handler, output_dir="images", device=None):
        """
        Initializes the Juggernaut XL pipeline for local image generation.
        """
        self.ui = display_handler
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        os.environ["DIFFUSERS_DISABLE_PROGRESS_BARS"] = "1"
        
        self.ui.info("Loading [bold magenta]Juggernaut-XL[/] (approx. 7GB VRAM required)...")
        
        if device is None:
            if torch.cuda.is_available(): self.device = "cuda"
            elif torch.backends.mps.is_available(): self.device = "mps"
            else: self.device = "cpu"
        else:
            self.device = device

        self.pipe = AutoPipelineForText2Image.from_pretrained(
            "RunDiffusion/Juggernaut-XL-v9",
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            variant="fp16" if self.device != "cpu" else None
        ).to(self.device)

        self.neg_prompt = (
            "low quality, blurry, distorted, watermark, text, logo, signature, "
            "bad anatomy, extra limbs, deformed hands, cartoon, animated"
        )

    def _get_hash(self, text):
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]

    def generate_single(self, word, visual_prompt, size=256, quality=85):
        """
        Generates a single image, resizes it and saves it as JPEG.
        """
        filename = f"{self._get_hash(word)}.jpg"
        final_path = self.output_dir / filename

        if final_path.exists():
            return filename

        try:
            image = self.pipe(
                prompt=visual_prompt,
                negative_prompt=self.neg_prompt,
                num_inference_steps=20,
                guidations_scale=4.5,
                width=768,
                height=768
            ).images[0]

            image = image.resize((size, size), Image.LANCZOS)
            image.save(final_path, format="JPEG", quality=quality, optimize=True)
            
            return filename

        except Exception as e:
            self.ui.error(f"Image generation failed for '{word}': {e}")
            return None

    def process_batch(self, tasks, size=256):
        """
        Processes a list of tasks [(word, visual_prompt), ...]
        """
        results = {}
        total = len(tasks)
        
        with self.ui.get_progress() as progress:
            task_id = progress.add_task("[magenta]Painting images...", total=total)
            
            for word, prompt in tasks:
                filename = self.generate_single(word, prompt, size=size)
                results[word] = filename
                progress.update(task_id, advance=1, description=f"[cyan]Image: {word}")
                
        return results

if __name__ == "__main__":
    ui = GeneratorDisplay(app_name="ChineseIsEasy Factory", version="2.0")
    ui.print_banner()

    try:
        img_gen = ImageGenerator(ui, output_dir="images")
        tasks = [
            (
                "火车", 
                "a modern high-speed bullet train speeding through a futuristic station, cinematic lighting, ultra-realistic, 8k, highly detailed"
            ),
            (
                "森林", 
                "a lush green ancient forest with sunlight rays filtering through thick leaves, misty atmosphere, mossy ground, hyper-realistic"
            )
        ]

        results = img_gen.process_batch(tasks, size=256)

        for word, filename in results.items():
            if filename:
                ui.success(f"Word: {word} | File: [blue]{filename}[/]")
            else:
                ui.error(f"Failed for word: {word}")

    except Exception as e:
        ui.error(f"Critical error during test: {e}")