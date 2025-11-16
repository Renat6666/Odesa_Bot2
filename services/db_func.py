from datetime import datetime, timezone
from db.models import Users, Language, Messages, Replies, RequestedApartment
from db.database import get_session
from sqlalchemy import select
from typing import Optional


async def get_or_create_user(user_id: int):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = Users(
                user_id=user_id,
                username=None,
                language=Language.UA,
                started_at=datetime.utcnow(),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

async def update_user_last_active(user_id: int):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        user.last_active_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        return user.id

async def update_user_contact(user_id: int, username: str):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        user.username = username
        await session.commit()
        await session.refresh(user)
        return user.id


async def save_message(user_id: int, message: str):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        msg = Messages(
            user_id=user.id,
            message=message,
            published_at=datetime.utcnow(),
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg.id


async def save_reply(message_id: int, reply: str):
    async with get_session() as session:
        rep = Replies(
            message_id=message_id,
            reply=reply,
            published_at=datetime.utcnow(),
        )
        session.add(rep)
        await session.commit()
        await session.refresh(rep)
        return rep.id


async def save_api_data(user_id: int, phone: str, data: dict):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        api_data = RequestedApartment(
            user_id=user.id,
            phone=phone,
            rooms_in=data.get("rooms_in") if data.get("rooms_in") else None,
            price_min=data.get("price_min") if data.get("price_min") else None,
            price_max=data.get("price_max") if data.get("price_max") else None,
            area_min=data.get("area_min") if data.get("area_min") else None,
            area_max=data.get("area_max") if data.get("area_max") else None,
            floor_min=data.get("floor_min") if data.get("floor_min") else None,
            floor_max=data.get("floor_max") if data.get("floor_max") else None,
            condition_in=data.get("condition_in") if data.get("condition_in") else None,
            district_ids=data.get("district_ids") if data.get("district_ids") else None,
            microarea_ids=data.get("microarea_ids") if data.get("microarea_ids") else None,
            created_at=datetime.utcnow(),
        )
        session.add(api_data)
        await session.commit()
        await session.refresh(api_data)
        return api_data.id


async def update_user(user_id: int, data: dict):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        user.username = data.get("username") if data.get("username") else user.username
        user.language = data.get("language") if data.get("language") else user.language
        user.lead = data.get("lead") if data.get("lead") else user.lead
        user.avg_budget = data.get("avg_budget") if data.get("avg_budget") else user.avg_budget
        user.reason_decline = data.get("reason_decline") if data.get("reason_decline") else user.reason_decline
        user.response_time = data.get("response_time") if data.get("response_time") else user.response_time
        await session.commit()
        await session.refresh(user)
        return user.id


async def get_user_data(user_id: int):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        return {
            "user_id": user.user_id,
            "username": user.username,
            "language": user.language,
            "lead": user.lead,
            "avg_budget": user.avg_budget,
            "reason_decline": user.reason_decline,
            "response_time": user.response_time,
            "started_at": user.started_at,
            "last_action": user.last_action,
        }


async def clear_context(user_id: int):
    async with get_session() as session:
        res = await session.execute(select(Users).where(Users.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(user_id)
        
        # Використовуємо user.id (внутрішній ID), а не user_id (Telegram ID)
        user_context_msg_id_res = await session.execute(
            select(Messages)
            .where(Messages.user_id == user.id)  # ← Виправлено: user.id замість user_id
            .order_by(Messages.published_at.desc())
            .limit(1)
        )
        user_context_msg_id = user_context_msg_id_res.scalar_one_or_none()
        user.context_msg_id = user_context_msg_id.id if user_context_msg_id else 0
        
        # Якщо є повідомлення, шукаємо останню відповідь
        if user_context_msg_id:
            user_context_reply_id_res = await session.execute(
                select(Replies)
                .where(Replies.message_id == user_context_msg_id.id)
                .order_by(Replies.published_at.desc())
                .limit(1)
            )
            user_context_reply_id = user_context_reply_id_res.scalar_one_or_none()
            user.context_reply_id = user_context_reply_id.id if user_context_reply_id else 0
        else:
            user.context_reply_id = 0
        
        await session.commit()
        await session.refresh(user)
        return user.id
        
            
