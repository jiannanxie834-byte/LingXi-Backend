import uvicorn

if __name__ == "__main__":
    # 启动命令：运行 app.main 里的 app 实例，端口 8000，开启热重载(reload)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)