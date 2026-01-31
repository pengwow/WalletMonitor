from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

class PluginBase(ABC):
    def __init__(self, name: str, version: str):
        """初始化插件
        
        Args:
            name: 插件名称
            version: 插件版本
        """
        self.name = name
        self.version = version
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 添加控制台处理器
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def register(self, plugin_manager):
        """注册插件
        
        Args:
            plugin_manager: 插件管理器实例
        """
        pass
    
    def start(self):
        """启动插件"""
        pass
    
    def stop(self):
        """停止插件"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """获取插件信息
        
        Returns:
            插件信息
        """
        return {
            "name": self.name,
            "version": self.version
        }
