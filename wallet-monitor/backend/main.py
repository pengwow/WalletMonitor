from fastapi import FastAPI
from plugins.plugin_manager import PluginManager

# 创建FastAPI应用
app = FastAPI(
    title="区块链钱包监控系统",
    description="一个功能完整的区块链钱包监控系统插件",
    version="1.0.0"
)

# 初始化插件管理器
plugin_manager = PluginManager()

# 加载所有插件
plugin_manager.load_all_plugins()

# 注册插件路由
plugin_manager.register_plugins(app)

# 根路径
@app.get("/")
def read_root():
    return {
        "message": "欢迎使用区块链钱包监控系统",
        "version": "1.0.0",
        "status": "运行中"
    }

# 健康检查
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "plugins": plugin_manager.get_loaded_plugins()
    }
