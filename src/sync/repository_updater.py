from pathlib import Path
import subprocess

from src.sync.incremental_indexer import IncrementalIndexer

class RepositoryUpdater:

    def __init__(self,repository_path: str):
        self.repository_path=Path(repository_path)
        self.repository_name=self.repository_path.name

    def get_current_commit(self)->str:
        result=subprocess.run(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            check=True,
        )

    def pull_repository(self):
        subprocess.run(
            [
                "git",
                "pull",
            ],
            cwd=self.repository_path,
            check=True,
        )

    def get_changed_files(self,old_commit:str,new_commit:str):
        result=subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                old_commit,
                new_commit,
            ],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return[
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def synchronize(self):
        old_commit=self.get_current_commit()

        self.pull_repository()
        new_commit=self.get_current_commit()

        if old_commit == new_commit:
            print("Repository already up to date")
            return

        changed_files=self.get_changed_files(
            old_commit,
            new_commit,
        )

        

        IncrementalIndexer(
            self.repository_name
        ).updated_files(
            repository_path=str(
                self.repository_path
            ),
            changed_files=changed_files,
        )





            