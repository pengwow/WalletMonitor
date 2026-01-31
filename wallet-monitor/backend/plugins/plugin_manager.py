import os
import importlib.util
from typing import List, Dict, Any
import logging

class PluginManager:
    def __init__(self):
        """初始化插件管理器"""
        self.plugins = []
        self.logger = logging.getLogger("plugin_manager")
        self.logger.setLevel(logging.INFO)
        
        # 添加控制台处理器
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def scan_plugins(self) -> List[str]:
        """扫描插件目录
        
        Returns:
            插件目录列表
        """
        plugins_dir = os.path.join(os.path.dirname(__file__), "wallet_monitor")
        plugin_dirs = []
        
        if os.path.exists(plugins_dir):
            plugin_dirs.append(plugins_dir)
        
        return plugin_dirs
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载指定插件
        
        Args:
            plugin_path: 插件路径
            
        Returns:
            是否加载成功
        """
        try:
            # 检查插件是否有register_plugin函数
            plugin_file = os.path.join(plugin_path, "plugin.py")
            if not os.path.exists(plugin_file):
                self.logger.error(f"插件文件不存在: {plugin_file}")
                return False
            
            # 导入插件模块
            spec = importlib.util.spec_from_file_location("plugin", plugin_file)
            if spec is None:
                self.logger.error(f"无法创建插件模块规范: {plugin_file}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                self.logger.error(f"无法获取插件模块加载器: {plugin_file}")
                return False
            
            spec.loader.exec_module(module)
            
            # 检查是否有register_plugin函数
            if not hasattr(module, "register_plugin"):
                self.logger.error(f"插件缺少register_plugin函数: {plugin_file}")
                return False
            
            # 注册插件
            plugin = module.register_plugin()
            self.plugins.append(plugin)
            self.logger.info(f"成功加载插件: {plugin.name} v{plugin.version}")
            
            return True
        except Exception as e:
            self.logger.error(f"加载插件失败: {e}")
            return False
    
    def load_all_plugins(self) -> List[str]:
        """加载所有插件
        
        Returns:
            加载成功的插件名称列表
        """
        plugin_dirs = self.scan_plugins()
        loaded_plugins = []
        
        for plugin_dir in plugin_dirs:
            if self.load_plugin(plugin_dir):
                # 获取插件名称
                plugin_name = os.path.basename(plugin_dir)
                loaded_plugins.append(plugin_name)
        
        return loaded_plugins
    
    def register_plugins(self, app):
        """注册插件路由
        
        Args:
            app: FastAPI应用实例
        """
        for plugin in self.plugins:
            if hasattr(plugin, "router"):
                app.include_router(plugin.router)
                self.logger.info(f"注册插件路由: {plugin.name}")
            
            # 调用插件的register方法
            plugin.register(self)
            
            # 启动插件
            plugin.start()
    
    def get_loaded_plugins(self) -> List[Dict[str, str]]:
        """获取已加载的插件列表
        
        Returns:
            插件信息列表
        """
        return [plugin.get_info() for plugin in self.plugins]
