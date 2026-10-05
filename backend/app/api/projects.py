from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.projects import project_service

router = APIRouter()


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    chat_id: Optional[int] = None


class ProjectOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    file_path: Optional[str]
    file_size: int

    class Config:
        from_attributes = True


class WriteFilesRequest(BaseModel):
    files: Dict[str, str]  # path -> content


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = project_service.create_project(
        db=db,
        user=current_user,
        title=payload.title,
        description=payload.description,
        chat_id=payload.chat_id,
    )
    return project


@router.get("/", response_model=List[ProjectOut])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/files")
def write_files(
    project_id: int,
    payload: WriteFilesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    paths = project_service.write_files(project_id, payload.files)
    return {"written": len(paths), "files": list(payload.files.keys())}


@router.get("/{project_id}/files")
def list_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"files": project_service.list_files(project_id)}


@router.post("/{project_id}/build")
def build_zip(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        zip_path = project_service.build_zip(db, project_id)
        return {"status": "ready", "zip_path": zip_path, "project_id": project_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/download")
def download_zip(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    zip_path = project.file_path or project_service.get_zip_path(project_id)
    if not zip_path or not __import__("os").path.exists(zip_path):
        # Пробуем собрать
        try:
            zip_path = project_service.build_zip(db, project_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Архив ещё не готов")

    return FileResponse(
        path=zip_path,
        filename=f"{project.title}.zip",
        media_type="application/zip",
    )
