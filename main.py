import os

import aiohttp
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware, db
from sqlalchemy.sql import exists

from schema import Question_num
from models import Question as ModelQuestion

load_dotenv(".env")
app = FastAPI()

app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])


def is_question_id_exists(question: dict, model:
ModelQuestion = ModelQuestion) -> bool:
    return db.session.query(
        exists().where(model.question_id == question["id"])
    ).scalar()


def get_last_question(model: ModelQuestion = ModelQuestion) -> ModelQuestion:
    return db.session.query(model).order_by(model.id.desc()).first()


@app.post("/questions/bulk")
async def questions(item: Question_num):
    last = get_last_question()
    question_num = item.question_num
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"https://jservice.io/api/random?count={question_num}"
        ) as resp:
            api_data = await resp.json()
            for q in api_data:
                while is_question_id_exists(q):
                    print(
                        f'id {q["id"]} with question: "{q["question"]}" '
                        f'is already exists in database!'
                    )
                    async with session.get(f"https://jservice.io/api/random") as api_res:
                        new_question = await api_res.json()
                        q = new_question[0]

                db_question = ModelQuestion(
                    question_id=q["id"],
                    question=q["question"],
                    answer=q["answer"],
                    created_at=q["created_at"],
                )
                db.session.add(db_question)
            db.session.commit()

    return last.question if last else []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
