# #
# # # app/routers/event.py
# # from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
# # from typing import List, Optional
# # from datetime import datetime
# #
# # from app.models.schemas import (
# #     EventCreate, EventResponse, EventJoin, EventStats
# # )
# # from app.database import database
# # from app.routers.auth import get_current_user
# #
# # router = APIRouter(prefix="/events", tags=["events"])
# #
# #
# # # ===========================
# # # Endpoints ללא אימות - לבדיקות
# # # ===========================
# #
# # @router.get("/test")
# # async def test_events():
# #     return {"message": "Events router is working!", "timestamp": datetime.now()}
# #
# #
# # # @router.post("/test-create")
# # # async def test_create_event(event: EventCreate):
# # #     """יצירת אירוע לבדיקה - בלי אימות"""
# # #     try:
# # #         # יצירת משתמש דמה לבדיקות
# # #         test_user_id = "test-user-123"
# # #
# # #         event_id = await database.create_event(
# # #             name=event.name,
# # #             event_code=event.event_code,
# # #             created_by=test_user_id
# # #         )
# # #
# # #         return {
# # #             "message": "Event created successfully (test mode)",
# # #             "event_id": event_id,
# # #             "event_code": event.event_code,
# # #             "warning": "This is a test endpoint - use /create with authentication in production"
# # #         }
# # #     except ValueError as e:
# # #         raise HTTPException(status_code=400, detail=str(e))
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")
# #
# #
# # # ===========================
# # # Endpoints עם אימות - לפרודקשן
# # # ===========================
# #
# # @router.post("/create", response_model=EventResponse)
# # async def create_event(
# #         event: EventCreate,
# #         current_user: str = Depends(get_current_user)
# # ):
# #     """יצירת אירוע חדש - דורש אימות"""
# #     try:
# #         event_id = await database.create_event(
# #             name=event.name,
# #             event_code=event.event_code,
# #             created_by=current_user
# #         )
# #
# #         # קבלת פרטי האירוע שנוצר
# #         new_event = await database.get_event_by_id(event_id)
# #
# #         return EventResponse(
# #             event_id=event_id,
# #             name=new_event["name"],
# #             event_code=new_event["event_code"],
# #             created_by=new_event["created_by"],
# #             created_at=new_event["created_at"]
# #         )
# #     except ValueError as e:
# #         raise HTTPException(status_code=400, detail=str(e))
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")
# #
# #
# # @router.post("/join")
# # async def join_event(
# #         event_join: EventJoin,
# #         current_user: str = Depends(get_current_user)
# # ):
# #     """הצטרפות לאירוע - דורש אימות"""
# #     success = await database.join_event(event_join.event_code, current_user)
# #
# #     if not success:
# #         raise HTTPException(
# #             status_code=400,
# #             detail="Failed to join event. Event may not exist or you're already a participant."
# #         )
# #
# #     return {"message": "Successfully joined event", "event_code": event_join.event_code}
# #
# #
# # @router.get("/my-events", response_model=List[EventResponse])
# # async def get_my_events(current_user: str = Depends(get_current_user)):
# #     events = await database.get_user_events(current_user)
# #
# #     # המרה לפורמט EventResponse
# #     event_responses = []
# #     for event in events:
# #         event_responses.append(EventResponse(
# #             event_id=event["event_id"],
# #             name=event["name"],
# #             event_code=event["event_code"],
# #             created_by=event["created_by"],
# #             created_at=event["created_at"]
# #         ))
# #
# #     return event_responses
# #
# #
# # # 🆕 הendpoint החדש - הוספה יחידה!
# # @router.get("/my-events-with-photos")
# # async def get_my_events_with_photos(current_user: str = Depends(get_current_user)):
# #     """קבלת כל האירועים שאני משתתף בהם או יצרתי עם מספר תמונות"""
# #     try:
# #         print(f"🔍 Getting events for user: {current_user}")
# #
# #         # קבלת אירועים שיצרתי
# #         created_events = await database.events.find({
# #             "created_by": current_user
# #         }).to_list(None)
# #
# #         # קבלת אירועים שאני משתתף בהם
# #         participations = await database.event_participants.find({
# #             "user_id": current_user
# #         }).to_list(None)
# #
# #         participant_event_ids = [p["event_id"] for p in participations]
# #
# #         participated_events = []
# #         if participant_event_ids:
# #             participated_events = await database.events.find({
# #                 "event_id": {"$in": participant_event_ids}
# #             }).to_list(None)
# #
# #         # איחוד כל האירועים
# #         all_events = created_events + participated_events
# #
# #         # הסרת כפילויות
# #         unique_events = []
# #         seen_event_ids = set()
# #
# #         for event in all_events:
# #             event_id = event.get("event_id")
# #             if event_id and event_id not in seen_event_ids:
# #                 seen_event_ids.add(event_id)
# #                 unique_events.append(event)
# #
# #         print(f"📊 Found {len(unique_events)} events for user")
# #
# #         # עיבוד האירועים לפורמט תגובה
# #         events_response = []
# #         for event in unique_events:
# #             # בדיקה אם יש תמונות באירוע
# #             photos_count = await database.event_photos.count_documents({
# #                 "event_id": event["event_id"]
# #             })
# #
# #             # בדיקה אם יש לי תמונות באירוע
# #             my_photos_count = await database.face_detections.count_documents({
# #                 "event_id": event["event_id"],
# #                 "$or": [
# #                     {"detected_user_id": current_user},
# #                     {"user_id": current_user}
# #                 ]
# #             })
# #
# #             events_response.append({
# #                 "event_id": event["event_id"],
# #                 "name": event.get("name", "אירוע ללא שם"),
# #                 "description": event.get("description", ""),
# #                 "event_date": event.get("event_date"),
# #                 "event_code": event.get("event_code"),
# #                 "created_at": event.get("created_at"),
# #                 "created_by": event.get("created_by"),
# #                 "is_creator": event.get("created_by") == current_user,
# #                 "total_photos": photos_count,
# #                 "my_photos_count": my_photos_count,
# #                 "has_photos": my_photos_count > 0
# #             })
# #
# #         return {
# #             "success": True,
# #             "events": events_response,
# #             "total_events": len(events_response),
# #             "message": f"נמצאו {len(events_response)} אירועים"
# #         }
# #
# #     except Exception as e:
# #         print(f"❌ Error getting user events: {e}")
# #         raise HTTPException(status_code=500, detail=str(e))
# #
# #
# # @router.get("/{event_id}", response_model=EventResponse)
# # async def get_event(
# #         event_id: str,
# #         current_user: str = Depends(get_current_user)
# # ):
# #     """קבלת פרטי אירוע - דורש אימות"""
# #     event = await database.get_event_by_id(event_id)
# #
# #     if not event:
# #         raise HTTPException(status_code=404, detail="Event not found")
# #
# #     # בדיקה שהמשתמש משתתף באירוע
# #     user_events = await database.get_user_events(current_user)
# #     if not any(e["event_id"] == event_id for e in user_events):
# #         raise HTTPException(
# #             status_code=403,
# #             detail="You don't have permission to view this event"
# #         )
# #
# #     return EventResponse(
# #         event_id=event["event_id"],
# #         name=event["name"],
# #         event_code=event["event_code"],
# #         created_by=event["created_by"],
# #         created_at=event["created_at"]
# #     )
# #
# #
# # @router.get("/{event_id}/stats", response_model=EventStats)
# # async def get_event_statistics(
# #         event_id: str,
# #         current_user: str = Depends(get_current_user)
# # ):
# #     # בדיקת הרשאות
# #     event = await database.get_event_by_id(event_id)
# #     if not event:
# #         raise HTTPException(status_code=404, detail="Event not found")
# #
# #     if event["created_by"] != current_user:
# #         user_events = await database.get_user_events(current_user)
# #         if not any(e["event_id"] == event_id for e in user_events):
# #             raise HTTPException(
# #                 status_code=403,
# #                 detail="You don't have permission to view this event's statistics"
# #             )
# #
# #     stats = await database.get_event_statistics(event_id)
# #
# #     return EventStats(
# #         event_id=stats["event_id"],
# #         participants=stats["participants"],
# #         total_photos=stats["total_photos"],
# #         processed_photos=stats["processed_photos"],
# #         total_detections=stats["total_detections"],
# #         processing_rate=stats["processing_rate"]
# #     )
# #
# #
# # # ===========================
# # # Endpoints נוספים ללא אימות - לפיתוח
# # # ===========================
# #
# # @router.get("/")
# # async def list_all_events_test():
# #     try:
# #         # שליפת כל האירועים מהמסד
# #         all_events = await database.events.find().to_list(100)
# #
# #         events_list = []
# #         for event in all_events:
# #             event.pop('_id', None)
# #             events_list.append({
# #                 "event_id": event.get("event_id"),
# #                 "name": event.get("name"),
# #                 "event_code": event.get("event_code"),
# #                 "created_by": event.get("created_by"),
# #                 "created_at": event.get("created_at")
# #             })
# #
# #         return {
# #             "total_events": len(events_list),
# #             "events": events_list,
# #             "warning": "This is a test endpoint - remove in production"
# #         }
# #     except Exception as e:
# #         return {"error": str(e), "events": []}
# #
# #
# # @router.delete("/test/{event_id}")
# # async def delete_event_test(event_id: str):
# #     try:
# #         # מחיקת האירוע
# #         result = await database.events.delete_one({"event_id": event_id})
# #
# #         if result.deleted_count == 0:
# #             raise HTTPException(status_code=404, detail="Event not found")
# #
# #         # מחיקת משתתפים
# #         await database.event_participants.delete_many({"event_id": event_id})
# #
# #         return {
# #             "message": "Event deleted successfully",
# #             "event_id": event_id,
# #             "warning": "This is a test endpoint - use proper deletion with auth in production"
# #         }
# #
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
# #
# #
# # app/routers/event.py
# # app/routers/event.py
# from fastapi import APIRouter, Depends, HTTPException
# from typing import List
# from datetime import datetime
#
# from app.models.schemas import (
#     EventCreate, EventResponse, EventJoin, EventStats
# )
# from app.database import database
# from app.routers.auth import get_current_user
# from app.config import config
#
# router = APIRouter(prefix="/events", tags=["events"])
#
#
# @router.get("/test")
# async def test_events():
#     return {"message": "Events router is working!", "timestamp": datetime.now()}
#
#
# @router.post("/create", response_model=EventResponse)
# async def create_event(
#         event: EventCreate,
#         current_user: str = Depends(get_current_user)
# ):
#     """יצירת אירוע חדש - דורש אימות"""
#     try:
#         event_id = await database.create_event(
#             name=event.name,
#             event_code=event.event_code,
#             created_by=current_user
#         )
#
#         new_event = await database.get_event_by_id(event_id)
#
#         return EventResponse(
#             event_id=event_id,
#             name=new_event["name"],
#             event_code=new_event["event_code"],
#             created_by=new_event["created_by"],
#             created_at=new_event["created_at"]
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=config.HTTP_400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=config.HTTP_500, detail=f"Failed to create event: {str(e)}")
#
#
# @router.post("/join")
# async def join_event(
#         event_join: EventJoin,
#         current_user: str = Depends(get_current_user)
# ):
#     """הצטרפות לאירוע - דורש אימות"""
#
#     if getattr(event_join, 'as_manager', False):
#         event = await database.events.find_one({"event_code": event_join.event_code})
#
#         if not event:
#             raise HTTPException(
#                 status_code=config.HTTP_404,
#                 detail="Event not found"
#             )
#
#         if event["created_by"] != current_user:
#             raise HTTPException(
#                 status_code=config.HTTP_403,
#                 detail="You don't have permission to manage this event - only the event creator can manage it"
#             )
#
#         return {
#             "success": True,
#             "message": "Successfully connected as event manager",
#             "event_code": event_join.event_code,
#             "data": {
#                 "event_id": event["event_id"],
#                 "name": event["name"],
#                 "event_code": event["event_code"],
#                 "created_by": event["created_by"],
#                 "created_at": event["created_at"]
#             }
#         }
#
#     success = await database.join_event(event_join.event_code, current_user)
#
#     if not success:
#         raise HTTPException(
#             status_code=config.HTTP_400,
#             detail="Failed to join event. Event may not exist or you're already a participant."
#         )
#
#     return {"message": "Successfully joined event", "event_code": event_join.event_code}
#
#
# @router.get("/my-events", response_model=List[EventResponse])
# async def get_my_events(current_user: str = Depends(get_current_user)):
#     events = await database.get_user_events(current_user)
#
#     event_responses = []
#     for event in events:
#         event_responses.append(EventResponse(
#             event_id=event["event_id"],
#             name=event["name"],
#             event_code=event["event_code"],
#             created_by=event["created_by"],
#             created_at=event["created_at"]
#         ))
#
#     return event_responses
#
#
# @router.get("/my-events-with-photos")
# async def get_my_events_with_photos(current_user: str = Depends(get_current_user)):
#     """קבלת כל האירועים שאני משתתף בהם או יצרתי עם מספר תמונות"""
#     try:
#         created_events = await database.events.find({
#             "created_by": current_user
#         }).to_list(None)
#
#         participations = await database.event_participants.find({
#             "user_id": current_user
#         }).to_list(None)
#
#         participant_event_ids = [p["event_id"] for p in participations]
#
#         participated_events = []
#         if participant_event_ids:
#             participated_events = await database.events.find({
#                 "event_id": {"$in": participant_event_ids}
#             }).to_list(None)
#
#         all_events = created_events + participated_events
#
#         unique_events = []
#         seen_event_ids = set()
#
#         for event in all_events:
#             event_id = event.get("event_id")
#             if event_id and event_id not in seen_event_ids:
#                 seen_event_ids.add(event_id)
#                 unique_events.append(event)
#
#         events_response = []
#         for event in unique_events:
#             photos_count = await database.event_photos.count_documents({
#                 "event_id": event["event_id"]
#             })
#
#             my_photos_count = await database.face_detections.count_documents({
#                 "event_id": event["event_id"],
#                 "$or": [
#                     {"detected_user_id": current_user},
#                     {"user_id": current_user}
#                 ]
#             })
#
#             events_response.append({
#                 "event_id": event["event_id"],
#                 "name": event.get("name", "Untitled Event"),
#                 "description": event.get("description", ""),
#                 "event_date": event.get("event_date"),
#                 "event_code": event.get("event_code"),
#                 "created_at": event.get("created_at"),
#                 "created_by": event.get("created_by"),
#                 "is_creator": event.get("created_by") == current_user,
#                 "total_photos": photos_count,
#                 "my_photos_count": my_photos_count,
#                 "has_photos": my_photos_count > config.PHOTOS_COUNT_ZERO
#             })
#
#         return {
#             "success": True,
#             "events": events_response,
#             "total_events": len(events_response),
#             "message": f"Found {len(events_response)} events"
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=config.HTTP_500, detail=str(e))
#
#
# @router.get("/{event_id}", response_model=EventResponse)
# async def get_event(
#         event_id: str,
#         current_user: str = Depends(get_current_user)
# ):
#     """קבלת פרטי אירוע - דורש אימות"""
#     event = await database.get_event_by_id(event_id)
#
#     if not event:
#         raise HTTPException(status_code=config.HTTP_404, detail="Event not found")
#
#     user_events = await database.get_user_events(current_user)
#     if not any(e["event_id"] == event_id for e in user_events):
#         raise HTTPException(
#             status_code=config.HTTP_403,
#             detail="You don't have permission to view this event"
#         )
#
#     return EventResponse(
#         event_id=event["event_id"],
#         name=event["name"],
#         event_code=event["event_code"],
#         created_by=event["created_by"],
#         created_at=event["created_at"]
#     )
#
#
# @router.get("/{event_id}/stats", response_model=EventStats)
# async def get_event_statistics(
#         event_id: str,
#         current_user: str = Depends(get_current_user)
# ):
#     event = await database.get_event_by_id(event_id)
#     if not event:
#         raise HTTPException(status_code=config.HTTP_404, detail="Event not found")
#
#     if event["created_by"] != current_user:
#         user_events = await database.get_user_events(current_user)
#         if not any(e["event_id"] == event_id for e in user_events):
#             raise HTTPException(
#                 status_code=config.HTTP_403,
#                 detail="You don't have permission to view this event's statistics"
#             )
#
#     stats = await database.get_event_statistics(event_id)
#
#     return EventStats(
#         event_id=stats["event_id"],
#         participants=stats["participants"],
#         total_photos=stats["total_photos"],
#         processed_photos=stats["processed_photos"],
#         total_detections=stats["total_detections"],
#         processing_rate=stats["processing_rate"]
#     )
#
#
# @router.get("/")
# async def list_all_events_test():
#     try:
#         all_events = await database.events.find().to_list(config.DB_FIND_LIMIT)
#
#         events_list = []
#         for event in all_events:
#             event.pop('_id', None)
#             events_list.append({
#                 "event_id": event.get("event_id"),
#                 "name": event.get("name"),
#                 "event_code": event.get("event_code"),
#                 "created_by": event.get("created_by"),
#                 "created_at": event.get("created_at")
#             })
#
#         return {
#             "total_events": len(events_list),
#             "events": events_list,
#             "warning": "This is a test endpoint - remove in production"
#         }
#     except Exception as e:
#         return {"error": str(e), "events": []}
#
#
# @router.delete("/test/{event_id}")
# async def delete_event_test(event_id: str):
#     try:
#         result = await database.events.delete_one({"event_id": event_id})
#
#         if result.deleted_count == config.DELETE_COUNT_ZERO:
#             raise HTTPException(status_code=config.HTTP_404, detail="Event not found")
#
#         await database.event_participants.delete_many({"event_id": event_id})
#
#         return {
#             "message": "Event deleted successfully",
#             "event_id": event_id,
#             "warning": "This is a test endpoint - use proper deletion with auth in production"
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=config.HTTP_500, detail=str(e))


# app/routers/event.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from app.models.schemas import (
    EventCreate, EventResponse, EventJoin, EventStats
)
from app.database import database
from app.routers.auth import get_current_user, verify_event_manager_by_code, verify_event_manager_by_id
from app.config import config

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/test")
async def test_events():
    return {"message": "Events router is working!", "timestamp": datetime.now()}


@router.post("/create", response_model=EventResponse)
async def create_event(
        event: EventCreate,
        current_user: str = Depends(get_current_user)
):
    """יצירת אירוע חדש - דורש אימות"""
    try:
        event_id = await database.create_event(
            name=event.name,
            event_code=event.event_code,
            created_by=current_user
        )

        new_event = await database.get_event_by_id(event_id)

        return EventResponse(
            event_id=event_id,
            name=new_event["name"],
            event_code=new_event["event_code"],
            created_by=new_event["created_by"],
            created_at=new_event["created_at"]
        )
    except ValueError as e:
        raise HTTPException(status_code=config.HTTP_400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=config.HTTP_500, detail=f"Failed to create event: {str(e)}")


@router.post("/join")
async def join_event(
        event_join: EventJoin,
        current_user: str = Depends(get_current_user)
):
    """הצטרפות לאירוע - משתמש רגיל או מנהל"""

    # בדיקה אם המשתמש מנסה להתחבר כמנהל
    if getattr(event_join, 'as_manager', False):
        # בדיקה אם המשתמש הוא באמת מנהל האירוע
        is_manager = await verify_event_manager_by_code(event_join.event_code, current_user)

        if not is_manager:
            raise HTTPException(
                status_code=config.HTTP_403,
                detail="You don't have permission to manage this event - only the event creator can manage it"
            )

        event = await database.events.find_one({"event_code": event_join.event_code})

        if not event:
            raise HTTPException(
                status_code=config.HTTP_404,
                detail="Event not found"
            )

        return {
            "success": True,
            "message": "Successfully connected as event manager",
            "event_code": event_join.event_code,
            "data": {
                "event_id": event["event_id"],
                "name": event["name"],
                "event_code": event["event_code"],
                "created_by": event["created_by"],
                "created_at": event["created_at"]
            }
        }

    # משתמש רגיל יכול להצטרף לאירוע כדי לקבל תמונו
    success = await database.join_event(event_join.event_code, current_user)

    if not success:
        raise HTTPException(
            status_code=config.HTTP_400,
            detail="Failed to join event. Event may not exist or you're already a participant."
        )

    return {"message": "Successfully joined event", "event_code": event_join.event_code}


@router.get("/my-events", response_model=List[EventResponse])
async def get_my_events(current_user: str = Depends(get_current_user)):
    events = await database.get_user_events(current_user)

    event_responses = []
    for event in events:
        event_responses.append(EventResponse(
            event_id=event["event_id"],
            name=event["name"],
            event_code=event["event_code"],
            created_by=event["created_by"],
            created_at=event["created_at"]
        ))

    return event_responses


@router.get("/my-events-with-photos")
async def get_my_events_with_photos(current_user: str = Depends(get_current_user)):
    """קבלת כל האירועים שאני משתתף בהם או יצרתי עם מספר תמונות"""
    try:
        created_events = await database.events.find({
            "created_by": current_user
        }).to_list(None)

        participations = await database.event_participants.find({
            "user_id": current_user
        }).to_list(None)

        participant_event_ids = [p["event_id"] for p in participations]

        participated_events = []
        if participant_event_ids:
            participated_events = await database.events.find({
                "event_id": {"$in": participant_event_ids}
            }).to_list(None)

        all_events = created_events + participated_events

        unique_events = []
        seen_event_ids = set()

        for event in all_events:
            event_id = event.get("event_id")
            if event_id and event_id not in seen_event_ids:
                seen_event_ids.add(event_id)
                unique_events.append(event)

        events_response = []
        for event in unique_events:
            photos_count = await database.event_photos.count_documents({
                "event_id": event["event_id"]
            })

            my_photos_count = await database.face_detections.count_documents({
                "event_id": event["event_id"],
                "$or": [
                    {"detected_user_id": current_user},
                    {"user_id": current_user}
                ]
            })

            events_response.append({
                "event_id": event["event_id"],
                "name": event.get("name", "Untitled Event"),
                "description": event.get("description", ""),
                "event_date": event.get("event_date"),
                "event_code": event.get("event_code"),
                "created_at": event.get("created_at"),
                "created_by": event.get("created_by"),
                "is_creator": event.get("created_by") == current_user,
                "total_photos": photos_count,
                "my_photos_count": my_photos_count,
                "has_photos": my_photos_count > config.PHOTOS_COUNT_ZERO
            })

        return {
            "success": True,
            "events": events_response,
            "total_events": len(events_response),
            "message": f"Found {len(events_response)} events"
        }

    except Exception as e:
        raise HTTPException(status_code=config.HTTP_500, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
        event_id: str,
        current_user: str = Depends(get_current_user)
):
    """קבלת פרטי אירוע - דורש אימות"""
    event = await database.get_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=config.HTTP_404, detail="Event not found")

    user_events = await database.get_user_events(current_user)
    if not any(e["event_id"] == event_id for e in user_events):
        raise HTTPException(
            status_code=config.HTTP_403,
            detail="You don't have permission to view this event"
        )

    return EventResponse(
        event_id=event["event_id"],
        name=event["name"],
        event_code=event["event_code"],
        created_by=event["created_by"],
        created_at=event["created_at"]
    )


@router.get("/{event_id}/stats", response_model=EventStats)
async def get_event_statistics(
        event_id: str,
        current_user: str = Depends(get_current_user)
):
    """ קבלת סטטיסטיקות אירוע - רק מנהל האירוע"""
    event = await database.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=config.HTTP_404, detail="Event not found")

    # בדיקה שרק מנהל האירוע יכול לראות סטטיסטיקות
    is_manager = await verify_event_manager_by_id(event_id, current_user)
    if not is_manager:
        raise HTTPException(
            status_code=config.HTTP_403,
            detail="You don't have permission to view this event's statistics - only event managers can access stats"
        )

    stats = await database.get_event_statistics(event_id)

    return EventStats(
        event_id=stats["event_id"],
        participants=stats["participants"],
        total_photos=stats["total_photos"],
        processed_photos=stats["processed_photos"],
        total_detections=stats["total_detections"],
        processing_rate=stats["processing_rate"]
    )


@router.get("/")
async def list_all_events_test():
    try:
        all_events = await database.events.find().to_list(config.DB_FIND_LIMIT)

        events_list = []
        for event in all_events:
            event.pop('_id', None)
            events_list.append({
                "event_id": event.get("event_id"),
                "name": event.get("name"),
                "event_code": event.get("event_code"),
                "created_by": event.get("created_by"),
                "created_at": event.get("created_at")
            })

        return {
            "total_events": len(events_list),
            "events": events_list,
            "warning": "This is a test endpoint - remove in production"
        }
    except Exception as e:
        return {"error": str(e), "events": []}


@router.delete("/test/{event_id}")
async def delete_event_test(event_id: str):
    try:
        result = await database.events.delete_one({"event_id": event_id})

        if result.deleted_count == config.DELETE_COUNT_ZERO:
            raise HTTPException(status_code=config.HTTP_404, detail="Event not found")

        await database.event_participants.delete_many({"event_id": event_id})

        return {
            "message": "Event deleted successfully",
            "event_id": event_id,
            "warning": "This is a test endpoint - use proper deletion with auth in production"
        }

    except Exception as e:
        raise HTTPException(status_code=config.HTTP_500, detail=str(e))