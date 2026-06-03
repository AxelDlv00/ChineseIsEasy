# ╔════════════════════════════════════════════════════════╗
# ║                    Generator Class                     ║
# ╚════════════════════════════════════════════════════════╝

# +--------------------------------------------------------+
# | This class manages multithreaded requests to the OpenAI|
# |                    API for content generation.         |
# +--------------------------------------------------------+

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
from display import GeneratorDisplay
from prompt_manager import PromptManager

load_dotenv()

class GeneralGenerator:
    def __init__(self, display_handler, model="gpt-4o-mini", API_KEY_NAME="OPENAI_API_KEY"):
        self.model = model
        self.ui = display_handler
        api_key = os.getenv(API_KEY_NAME)
        
        if not api_key:
            self.ui.error(f"[bold]{API_KEY_NAME}[/] was not found in environment variables.")
            raise ValueError("API key not found.")
            
        self.client = OpenAI(api_key=api_key)

    def _inject_placeholders(self, prompt, args):
        """
        The assumption is that the prompt contains placeholders like <1>, <2>, etc.
        args[0] will replace <1>, args[1] will replace <2>, and so on.
        """
        for i, value in enumerate(args, start=1):
            placeholder = f"<{i}>"
            prompt = prompt.replace(placeholder, str(value))
        return prompt

    def _fetch_field(self, name, prompt_tmpl, args, system):
        """Internal method for a single request to OpenAI."""
        try:
            prompt = self._inject_placeholders(prompt_tmpl, args)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return name, response.choices[0].message.content.strip()
        except Exception as e:
            return name, f"Error: {str(e)}"

    def generate_batch(self, tasks, prompt_tmpl, system, max_workers=5):
        """
        Process a batch of generation tasks concurrently using a thread pool.
        Updates a progress bar in real-time via the display handler.
        """
        results = {}
        total_tasks = len(tasks)
        
        with self.ui.get_progress() as progress:
            task_id = progress.add_task("[magenta]Processing batch...", total=total_tasks)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_name = {
                    executor.submit(self._fetch_field, name, prompt_tmpl, args, system): name 
                    for name, args in tasks
                }
                
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        name, content = future.result()
                        results[name] = content
                        progress.update(task_id, advance=1, description=f"[cyan]Generated: {name}")
                    except Exception as e:
                        results[name] = f"Error: {str(e)}"
                        self.ui.error(f"Task failed: {name} -> {e}")

        self.ui.success(f"Batch processing complete. {total_tasks} items generated.")
        return results

if __name__ == "__main__":
    # Example usage

    ui = GeneratorDisplay(app_name="AI Content Generator", version="1.0")
    ui.print_banner()   
    generator = GeneralGenerator(ui)

    tasks = [
        ("Word1", ["你好", 1]),
        ("Word2", ["学习", 2]),
        ("Word3", ["和平", 3]),
    ]

    prompt_manager = PromptManager()
    system_msg, prompt_template = prompt_manager.get("generate_examples")

    generator = GeneralGenerator(display_handler=ui)
    results = generator.generate_batch(tasks, prompt_template, system_msg, max_workers=3)

    for name, description in results.items():
        ui.info(f"{name} Exemples:\n{description}")