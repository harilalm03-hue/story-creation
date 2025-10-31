import os
from openai import OpenAI
from dotenv import load_dotenv
from db.database import SessionLocal
from models.story import Story, StoryNode

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StoryGenerator:
    @staticmethod
    def generate_story(db, session_id: str, theme: str):
        try:
            if not os.getenv("OPENAI_API_KEY"):
                raise Exception("OPENAI_API_KEY missing in .env file")

            prompt = f"Write a short story (200-400 words) about: {theme}"

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative story writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.9,
            )

            text = response.choices[0].message.content.strip()

            story = Story(title=theme, session_id=session_id)
            db.add(story)
            db.commit()
            db.refresh(story)

            root_node = StoryNode(
                story_id=story.id,
                content=text,
                is_root=True,
                is_ending=False,
                is_winning_ending=False,
                options={}
            )
            db.add(root_node)
            db.commit()
            db.refresh(root_node)

            print("✅ Story generated successfully.")
            return story

        except Exception as e:
            print(" Story generation failed:", e)
            raise
