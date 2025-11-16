from db.models import Users, Messages, Replies
from sqlalchemy import select
from db.database import get_session
from datetime import datetime


async def get_context(user_id: int):
    async with get_session() as session:
        user_res = await session.execute(
            select(Users).where(Users.user_id == user_id)
        )
        user = user_res.scalar_one_or_none()
        if not user:
            return None

        msgs_res = await session.execute(
            select(Messages)
            .where(Messages.user_id == user.id, Messages.id > user.context_msg_id)
            .order_by(Messages.published_at.asc())
        )
        messages = msgs_res.scalars().all()

        replies_res = await session.execute(
            select(Replies)
            .join(Messages, Replies.message_id == Messages.id)
            .where(Messages.user_id == user.id, Replies.id > user.context_reply_id)
            .order_by(Replies.published_at.asc())
        )
        replies = replies_res.scalars().all()

        conversation = []
        for m in messages:
            conversation.append({
                "role": "user",
                "content": m.message,
                "timestamp": (m.published_at or datetime.min).strftime("%Y-%m-%d %H:%M"),
                "_ts": m.published_at or datetime.min,
            })
        for r in replies:
            conversation.append({
                "role": "assistant",
                "content": r.reply,
                "timestamp": (r.published_at or datetime.min).strftime("%Y-%m-%d %H:%M"),
                "_ts": r.published_at or datetime.min,
            })
        conversation.sort(key=lambda x: x.get("_ts") or datetime.min)
        conversation = conversation[-300:]
        for item in conversation:
            item.pop("_ts", None)

        return {
            "language": "ua",
            "conversation": conversation,
        }
        

# if __name__ == "__main__":
#     import asyncio
#     print(asyncio.run(get_context(6628418858)))