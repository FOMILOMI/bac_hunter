from __future__ import annotations
import shutil
import logging
from typing import List, Dict, Optional

log = logging.getLogger("integrations.manager")

class ToolManager:
    """إدارة توفر الأدوات الخارجية"""
    
    REQUIRED_TOOLS = {
        'nuclei': {
            'name': 'Nuclei',
            'install_url': 'https://github.com/projectdiscovery/nuclei',
            'description': 'قوالب فحص الثغرات'
        },
        'dirsearch': {
            'name': 'Dirsearch', 
            'install_url': 'https://github.com/maurosoria/dirsearch',
            'description': 'اكتشاف المجلدات والملفات'
        },
        'httpx': {
            'name': 'httpx',
            'install_url': 'https://github.com/projectdiscovery/httpx',
            'description': 'HTTP toolkit متقدم'
        }
    }
    
    def check_available_tools(self) -> Dict[str, bool]:
        """فحص الأدوات المتوفرة"""
        available = {}
        for tool_name in self.REQUIRED_TOOLS:
            available[tool_name] = shutil.which(tool_name) is not None
            
        return available
    
    def get_installation_instructions(self) -> str:
        """تعليمات التثبيت للأدوات المفقودة"""
        available = self.check_available_tools()
        missing = [tool for tool, is_available in available.items() if not is_available]
        
        if not missing:
            return "جميع الأدوات المطلوبة متوفرة!"
            
        instructions = "الأدوات المفقودة:\n\n"
        for tool in missing:
            info = self.REQUIRED_TOOLS[tool]
            instructions += f"• {info['name']}: {info['description']}\n"
            instructions += f"  التثبيت: {info['install_url']}\n\n"
            
        return instructions
