from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 数据库连接配置 (SQLite 会直接在项目根目录下创建一个 lingxi.db 文件)
DATABASE_URL = "sqlite:///./lingxi.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite 专属配置，允许 FastAPI 多线程并发访问
)

# 创建会话工厂，用于后续对数据库进行增删改查
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有数据库表模型的“亲生父亲” Base 基类
Base = declarative_base()

def get_db():
    """FastAPI 专属依赖项：每次请求自动创建数据库连接，用完自动关闭防止死锁"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_seeding_data():
    """初始化真数据库的种子数据（如果发现是空库，自动塞入默认学生和管理员）"""
    db = SessionLocal()
    from app.models.schemas import User  # 延迟引入防止循环依赖
    
    try:
        # 1. 检查数据库里是不是已经有用户了
        exist_user = db.query(User).first()
        if not exist_user:
            print(" 侦测到全新空数据库，正在注入初始超级管理员与默认学生...")
            
            # 2. 创建一个跟之前虚拟字典一模一样的超级管理员
            admin_user = User(
                username="admin",
                password="123456",  # 比赛演示用简易明文，后期可加加密
                role="admin",
                avatar="",
                bio="全站最高权限智能系统控制枢纽",
                hours=999,
                tags="系统管理,架构师"
            )
            
            # 3. 创建一个默认的学生账号
            student_user = User(
                username="student",
                password="123456",
                role="student",
                avatar="",
                bio="正在跟随黑马程序员攻克 IHRM 人力资源管理系统的前端架构师",
                hours=15,
                tags="Vue3,Element Plus,后端,Python"
            )
            
            # 4. 把他们两个物理刻录进数据库文件中
            db.add(admin_user)
            db.add(student_user)
            db.commit()
            print("✨ 初始账号（admin / student）物理通电成功！")
        else:
            print("📂 数据库已存在全真数据，跳过初始化。")
    except Exception as e:
        print(f" 初始化注入失败: {e}")
        db.rollback()
    finally:
        db.close()