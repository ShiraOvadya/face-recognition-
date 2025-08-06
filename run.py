import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # מפנה ל-main.py בתיקיית השורש
        host="localhost",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )