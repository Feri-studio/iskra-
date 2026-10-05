"""
Сервис генерации проектов и сборки zip-папок.
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectStatus
from app.models.user import User


PROJECTS_ROOT = Path("./data/projects")
PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)


class ProjectService:
    def create_project(
        self,
        db: Session,
        user: User,
        title: str,
        description: str = "",
        chat_id: Optional[int] = None,
    ) -> Project:
        project = Project(
            user_id=user.id,
            chat_id=chat_id,
            title=title,
            description=description,
            status=ProjectStatus.in_progress,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Создаём папку проекта
        project_dir = PROJECTS_ROOT / str(project.id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project

    def write_file(self, project_id: int, relative_path: str, content: str) -> str:
        """Записывает файл внутрь папки проекта."""
        project_dir = PROJECTS_ROOT / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        full_path = project_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    def write_files(self, project_id: int, files: Dict[str, str]) -> List[str]:
        """files = {\"path/to/file.py\": \"code...\"}"""
        paths = []
        for rel, content in files.items():
            paths.append(self.write_file(project_id, rel, content))
        return paths

    def list_files(self, project_id: int) -> List[str]:
        project_dir = PROJECTS_ROOT / str(project_id)
        if not project_dir.exists():
            return []
        result = []
        for p in project_dir.rglob("*"):
            if p.is_file():
                result.append(str(p.relative_to(project_dir)))
        return sorted(result)

    def build_zip(self, db: Session, project_id: int) -> str:
        """
        Собирает zip из папки проекта.
        Возвращает путь к zip-файлу.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")

        project_dir = PROJECTS_ROOT / str(project_id)
        if not project_dir.exists():
            raise ValueError("Project folder is empty")

        zip_name = f"{project.title.replace(' ', '_')}_{project_id}.zip"
        zip_path = PROJECTS_ROOT / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir)
                    zf.write(file_path, arcname)

        project.file_path = str(zip_path)
        project.file_size = zip_path.stat().st_size
        project.status = ProjectStatus.ready
        db.commit()

        return str(zip_path)

    def get_zip_path(self, project_id: int) -> Optional[str]:
        project_dir = PROJECTS_ROOT
        # Ищем zip по id
        for p in project_dir.glob(f"*_{project_id}.zip"):
            return str(p)
        return None


project_service = ProjectService()
