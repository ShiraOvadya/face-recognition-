
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# תוספת מינימלית למיילים
from dotenv import load_dotenv

load_dotenv()  # טוען משתני סביבה מקובץ .env

app = FastAPI(
    title="Face Recognition Event System",
    version="1.0.0",
    description="מערכת זיהוי פנים לאירועים - אחסון במסד נתונים"
)

# הגדרת CORS - מעודכן לתמוך בכל הכתובות הרלוונטיות
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # ← הוספתי עבור הקליינט שלך
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "*"  # זמנית - להסיר בפרודקשן
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "*",
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since"
    ],
)


# Middleware ללוגים - מעודכן עם מידע נוסף
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # הדפסת מידע נוסף על הבקשה
    print(f" {request.method} {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Origin: {request.headers.get('origin', 'None')}")

    response = await call_next(request)

    process_time = time.time() - start_time
    print(f" Response time: {process_time:.2f}s | Status: {response.status_code}")
    print("-" * 50)
    return response


# ייבוא הנתיבים - כאן התיקון הראשי!
try:
    from app.routers import auth, event, face_recognition, face_recognition_enhanced

    # רישום הנתיבים - כאן התיקון השני!
    app.include_router(auth.router)
    app.include_router(event.router)
    app.include_router(face_recognition.router)
    app.include_router(face_recognition_enhanced.router)  # ← זה החדש!

    print(" All routers loaded successfully")
    print("Face recognition enhanced router added")
    print("Using MongoDB for all data storage (no local files)")
    print("CORS configured for localhost:3001")

except ImportError as e:
    print(f" Warning: Could not import routers: {e}")


# === אתחול השרת עם בדיקת מיילים ===
@app.on_event("startup")
async def startup_event():
    """אתחול בהפעלת השרת - עם בדיקת מיילים"""
    print(" Initializing Face Recognition Server...")
    print("=" * 50)

    try:
        # אתחול מסד הנתונים
        print(" Initializing database...")
        from app.database import database
        await database.init_database()
        print("Database initialized successfully")

        # בדיקת חיבור למסד
        user_count = await database.users.count_documents({})
        event_count = await database.events.count_documents({})
        print(f" Database connected - {user_count} users, {event_count} events in system")

        # אתחול שירותי קבצים (אם יש)
        try:
            from app.services.file_manager import file_manager
            file_manager._ensure_directories()
            print(" File directories initialized")
        except ImportError:
            print(" File manager not found - using MongoDB storage only")

        # בדיקת מיילים - תוספת חדשה
        print(" Testing email configuration...")
        from app.services.email_service import email_service
        email_service.test_email_connection()

        print("=" * 50)
        print("Server startup completed successfully!")
        print(f"Server running on: http://127.0.0.1:8000")
        print(f" API Documentation: http://127.0.0.1:8000/docs")
        print(" CORS enabled for:")
        print("   - http://localhost:3001 (React app)")
        print("   - http://localhost:3000")
        print("   - http://127.0.0.1:8000")
        print(" Enhanced endpoints now available:")
        print("  - POST /face-recognition/upload-and-process-event-photos/{event_id}")
        print("  - GET /face-recognition/processing-status/{event_id}")
        print("  - GET /face-recognition/user-photos/{event_id}")
        print("  - GET /face-recognition/event-stats/{event_id}")
        print("Email test endpoints:")
        print("  - GET /test-email/your_email@gmail.com")
        print("  - GET /email-status")
        print("=" * 50)

    except Exception as e:
        print(f"Startup error: {e}")
        print("Please check your MongoDB connection and try again")


@app.on_event("shutdown")
async def shutdown_event():
    """נקיון בסגירת השרת"""
    print(" Shutting down server...")
    try:
        from app.database import database
        await database.close_connection()
        print("Database connection closed")
    except Exception as e:
        print(f" Error during shutdown: {e}")
    print("Server shutdown completed")


# === endpoints לבדיקת מיילים - תוספת חדשה ===
@app.get("/test-email/{email}")
async def test_email_endpoint(email: str):
    """בדיקת שליחת מייל ידנית"""
    try:
        from app.services.email_service import email_service
        success = email_service.send_test_email(email)
        if success:
            return {
                "success": True,
                "message": f"Test email sent successfully to {email}",
                "check": "Please check your inbox (and spam folder)"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test email",
                "reason": "Check server logs. Probably missing EMAIL_ADDRESS or EMAIL_PASSWORD environment variables"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@app.get("/email-status")
async def email_status():
    """בדיקת סטטוס הגדרות המייל"""
    try:
        from app.services.email_service import email_service
        import os

        return {
            "email_configured": bool(email_service.email_address and email_service.email_password),
            "smtp_server": email_service.smtp_server,
            "smtp_port": email_service.smtp_port,
            "email_address": "Set" if email_service.email_address else " Missing",
            "email_password": " Set" if email_service.email_password else " Missing",
            "environment_variables": {
                "EMAIL_ADDRESS": " Set" if os.getenv("EMAIL_ADDRESS") else " Missing",
                "EMAIL_PASSWORD": " Set" if os.getenv("EMAIL_PASSWORD") else "Missing",
                "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "SMTP_PORT": os.getenv("SMTP_PORT", "587")
            },
            "instructions": "Create .env file with EMAIL_ADDRESS and EMAIL_PASSWORD to enable email sending"
        }
    except Exception as e:
        return {"error": str(e)}


# === נתיבי בדיקה ודיבוג מעודכנים ===
@app.get("/api/status")
async def api_status():
    """סטטוס פשוט לבדיקה מ-React"""
    return {
        "api_online": True,
        "server": "FastAPI",
        "cors_enabled": True,
        "ready_for_react": True,
        "storage": "MongoDB",
        "face_recognition": "available",
        "enhanced_features": True,
        "email_testing": "available",
        "cors_origins": [
            "http://localhost:3001",
            "http://localhost:3000",
            "http://127.0.0.1:8000"
        ]
    }


@app.get("/upload-test")
async def upload_test():
    """בדיקה שהעלאות עובדות"""
    try:
        from app.database import database
        users_count = await database.users.count_documents({})
        events_count = await database.events.count_documents({})
        photos_count = await database.user_photos.count_documents({})

        return {
            "upload_ready": True,
            "database_collections": {
                "users": users_count,
                "events": events_count,
                "user_photos": photos_count
            },
            "upload_endpoints": [
                "/face-recognition/upload-reference-photo",
                "/face-recognition/upload-event-photos/{event_id}",
                "/face-recognition/upload-and-process-event-photos/{event_id}"  # החדש!
            ]
        }
    except Exception as e:
        return {"upload_ready": False, "error": str(e)}


@app.get("/test-connection")
async def test_connection():
    """בדיקת חיבור פשוטה"""
    return {
        "status": "connected",
        "message": "Server is running",
        "timestamp": time.time(),
        "cors_enabled": True,
        "enhanced_router": "loaded",
        "email_testing": "available",
        "server_url": "http://127.0.0.1:8000"
    }


# נתיב מיוחד לבדיקת CORS
@app.options("/{path:path}")
async def handle_options(request: Request):
    """טיפול בבקשות OPTIONS עבור CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/debug/routes")
async def list_routes():
    """רשימת כל הנתיבים הזמינים"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unnamed')
            })

    # חיפוש הנתיב החדש שהיה חסר
    upload_process_route = next(
        (r for r in routes if "upload-and-process-event-photos" in r["path"]),
        None
    )

    return {
        "available_routes": routes,
        "total_routes": len(routes),
        "enhanced_routes_included": True,
        "email_routes_included": True,
        "new_endpoint_found": upload_process_route is not None,
        "new_endpoint_details": upload_process_route if upload_process_route else "Not found"
    }


@app.get("/debug/database")
async def debug_database():
    """בדיקת חיבור למסד נתונים"""
    try:
        from app.database import database
        user_count = await database.users.count_documents({})
        event_count = await database.events.count_documents({})
        return {
            "database_connected": True,
            "users_count": user_count,
            "events_count": event_count,
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "message": "Database connection failed"
        }


# Exception handler גלובלי - מעודכן
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global exception: {str(exc)}")
    print(f" Request: {request.method} {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Origin: {request.headers.get('origin', 'None')}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": str(request.url)
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/")
async def root():
    """נקודת כניסה ראשית"""
    return {
        "message": "Face Recognition Event System API",
        "version": "1.0.0",
        "status": "running",
        "storage": "MongoDB (Base64 encoded images)",
        "endpoints": {
            "auth": "/auth/",
            "events": "/events/",
            "face-recognition": "/face-recognition/",
            "email-testing": "/test-email/",
            "email-status": "/email-status",
            "docs": "/docs",
            "health": "/health"
        },
        "enhanced_features": [
            "Upload and process event photos immediately",
            "Real-time processing status",
            "User photo retrieval by event",
            "Event processing statistics",
            "Email notification testing"
        ],
        "cors_info": {
            "enabled": True,
            "supports_localhost_3001": True,
            "ready_for_react": True
        }
    }


@app.get("/health")
async def health_check():
    """בדיקת בריאות המערכת"""
    try:
        from app.database import database
        await database.users.find_one({})

        try:
            from app.services.face_features_extractor import FaceFeatureExtractor
            face_extractor = FaceFeatureExtractor()
            face_recognition_status = "available" if face_extractor else "unavailable"
        except:
            face_recognition_status = "unavailable"

        try:
            from app.services.email_service import email_service
            email_status = "configured" if (
                        email_service.email_address and email_service.email_password) else "not_configured"
        except:
            email_status = "unavailable"

        return {
            "status": "healthy",
            "message": "API is running",
            "database": "connected",
            "face_recognition": face_recognition_status,
            "email_service": email_status,
            "storage_type": "MongoDB with Base64 images",
            "enhanced_router": "loaded",
            "cors_configured": True,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/storage-info")
async def storage_info():
    """מידע על אחסון המערכת"""
    try:
        from app.database import database
        stats = await database.get_total_storage_stats()
        return {
            "storage_type": "MongoDB Database",
            "image_encoding": "Base64",
            "vector_storage": "MongoDB Arrays",
            "statistics": stats,
            "advantages": [
                "אין צורך בתיקיות מקומיות",
                "גיבוי אוטומטי של כל הנתונים",
                "אבטחה טובה יותר",
                "קלה לפריסה בענן"
            ]
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    print(" Starting Face Recognition Server...")
    print("Storage: MongoDB Database (no local files)")
    print(" Access the API at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print(" CORS configured for React app on localhost:3001")
    print(" Enhanced features enabled:")
    print("  - Upload and process photos in one step")
    print("  - Real-time processing status")
    print("  - Event statistics and user photos")
    print("  - CORS support for frontend")
    print("  - Email notification testing")
    print("=" * 50)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )