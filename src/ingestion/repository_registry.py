import json
from datetime import datetime
from pathlib import Path
from src.config import DATA_DIR

METADATA_DIR=DATA_DIR / "metadata"
REGISTRY_FILE=METADATA_DIR / "repositories.json"

class RepositoryRegistry:

    def __init__(self):
        
        METADATA_DIR.mkdir(parents=True,exist_ok=True)
        
        if not REGISTRY_FILE.exists():
            REGISTRY_FILE.write_text("{}")

    def load(self):
        with open(REGISTRY_FILE,"r") as f:
            return json.load(f)

    def save(self,data):
        with open(REGISTRY_FILE,"w") as f:
            json.dump(data,f,indent=4)

    def register(self,repository_name:str):
        data=self.load()
        data[repository_name]={
            "indexed":True,
            "last_indexed":datetime.now().isoformat()
        }
        self.save(data)

    def is_registered(self,repository_name: str):
        data=self.load()
        return repository_name in data

    def get(self,repository_name: str):
        data=self.load()

        return data.get(repository_name)

       