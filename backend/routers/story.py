from fastapi import APIRouter, Depends, BackgroundTasks, Response, Cookie, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from db.database import get_db, SessionLocal
from models.job import StoryJob
from models.story import Story, StoryNode
from schemas.story import CreateStoryRequest, CompleteStoryResponse, CompleteStoryNodeResponse
from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator

router = APIRouter(
    tags=["stories"]
)

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/create", response_model=StoryJobResponse)
def create_story(
    request: CreateStoryRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    job_id = str(uuid.uuid4())
    job = StoryJob(job_id=job_id, session_id=session_id, theme=request.theme, status="pending")
    db.add(job)
    db.commit()

    background_tasks.add_task(generate_story_task, job_id, request.theme, session_id)
    return job

def generate_story_task(job_id: str, theme: str, session_id: str):
    db = SessionLocal()
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            return
        job.status = "processing"
        db.commit()

        story = StoryGenerator.generate_story(db, session_id, theme)

        job.story_id = getattr(story, "id", None)
        job.status = "completed"
        job.completed_at = datetime.now()
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.now()
        db.commit()
    finally:
        db.close()

@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    node_dict = {}
    for node in nodes:
        node_dict[node.id] = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=node.options,
        )

    root_node = next((n for n in nodes if n.is_root), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Story root node not found")

    return CompleteStoryResponse(
        id=story.id,
        title=story.title,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict,
    )
