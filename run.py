import uvicorn

if __name__ == "__main__":
    # 默认关闭热重载，避免部分系统的文件监听权限影响服务启动。
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
