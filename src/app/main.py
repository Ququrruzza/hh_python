from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import models, schemas
from database import get_db, engine


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

app = FastAPI(title="Simple API for hh")

@app.on_event("startup")
async def startup_event():
    await create_tables()

@app.post("/tasks/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    task_id = str(uuid.uuid4())
    db_task = models.Task(
        id=task_id,
        title=task.title,
        description=task.description)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@app.get("/tasks/", response_model=list[schemas.Task])
async def read_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()
    return tasks


@app.get("/tasks/{task_id}", response_model=schemas.Task)
async def read_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task).where(models.Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
async def update_task(task_id: str, task_update: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task).where(models.Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = task_update.title
    task.description = task_update.description
    await db.commit()
    await db.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task).where(models.Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}