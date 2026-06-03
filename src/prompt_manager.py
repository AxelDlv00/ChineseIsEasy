import yaml
from display import GeneratorDisplay

class PromptManager:
    def __init__(self, file_path="prompts/catalog.yaml"):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.catalog = yaml.safe_load(f)

    def get(self, key):
        """Returns (system_prompt, user_prompt) for the given key."""
        section = self.catalog.get(key)
        if not section:
            raise ValueError(f"Prompt '{key}' not found in catalog.")
        return section['system'], section['user']

if __name__ == "__main__":
    ui = GeneratorDisplay(app_name="Prompt Manager", version="1.0")
    ui.print_banner()
    pm = PromptManager()
    system, user = pm.get("generate_examples")
    ui.info(f"System: {system}")
    ui.info(f"User: {user}")