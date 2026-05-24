import uvicorn

if __name__ == "__main__":
    # 比赛演示优先保证稳定启动，避免热重载文件监听在部分系统权限下失败。
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
