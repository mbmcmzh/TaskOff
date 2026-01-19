"""
操作动作数据模型
定义自动化操作的类型和数据结构
"""
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import json
import uuid


class ActionType(Enum):
    """操作类型枚举"""
    MOUSE_CLICK = "mouse_click"           # 鼠标点击
    MOUSE_DOUBLE_CLICK = "mouse_double_click"  # 鼠标双击
    MOUSE_RIGHT_CLICK = "mouse_right_click"    # 鼠标右键点击
    MOUSE_MOVE = "mouse_move"             # 鼠标移动
    MOUSE_DRAG = "mouse_drag"             # 鼠标拖拽
    MOUSE_SCROLL = "mouse_scroll"         # 鼠标滚轮
    
    KEYBOARD_TYPE = "keyboard_type"       # 键盘输入文本
    KEYBOARD_PRESS = "keyboard_press"     # 按键按下
    KEYBOARD_HOTKEY = "keyboard_hotkey"   # 组合键
    
    DELAY = "delay"                       # 延迟等待
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        names = {
            ActionType.MOUSE_CLICK: "鼠标点击",
            ActionType.MOUSE_DOUBLE_CLICK: "鼠标双击",
            ActionType.MOUSE_RIGHT_CLICK: "鼠标右键",
            ActionType.MOUSE_MOVE: "鼠标移动",
            ActionType.MOUSE_DRAG: "鼠标拖拽",
            ActionType.MOUSE_SCROLL: "鼠标滚轮",
            ActionType.KEYBOARD_TYPE: "输入文本",
            ActionType.KEYBOARD_PRESS: "按键",
            ActionType.KEYBOARD_HOTKEY: "组合键",
            ActionType.DELAY: "延迟等待",
        }
        return names.get(self, self.value)


@dataclass
class Action:
    """操作动作数据类"""
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    enabled: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.description:
            self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        """根据操作类型和参数生成描述"""
        if self.action_type == ActionType.MOUSE_CLICK:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"点击位置 ({x}, {y})"
        
        elif self.action_type == ActionType.MOUSE_DOUBLE_CLICK:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"双击位置 ({x}, {y})"
        
        elif self.action_type == ActionType.MOUSE_RIGHT_CLICK:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"右键点击 ({x}, {y})"
        
        elif self.action_type == ActionType.MOUSE_MOVE:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"移动到 ({x}, {y})"
        
        elif self.action_type == ActionType.MOUSE_DRAG:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"拖拽到 ({x}, {y})"
        
        elif self.action_type == ActionType.MOUSE_SCROLL:
            amount = self.params.get('amount', 0)
            direction = "向上" if amount > 0 else "向下"
            return f"滚动 {direction} {abs(amount)} 格"
        
        elif self.action_type == ActionType.KEYBOARD_TYPE:
            text = self.params.get('text', '')
            if len(text) > 20:
                text = text[:20] + "..."
            return f"输入: {text}"
        
        elif self.action_type == ActionType.KEYBOARD_PRESS:
            key = self.params.get('key', '')
            return f"按键: {key}"
        
        elif self.action_type == ActionType.KEYBOARD_HOTKEY:
            keys = self.params.get('keys', [])
            return f"组合键: {'+'.join(keys)}"
        
        elif self.action_type == ActionType.DELAY:
            seconds = self.params.get('seconds', 0)
            return f"等待 {seconds} 秒"
        
        return self.action_type.get_display_name()
    
    def update_description(self):
        """更新描述"""
        self.description = self._generate_description()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'action_type': self.action_type.value,
            'params': self.params,
            'description': self.description,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """从字典创建"""
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            action_type=ActionType(data['action_type']),
            params=data.get('params', {}),
            description=data.get('description', ''),
            enabled=data.get('enabled', True)
        )


@dataclass
class ActionSequence:
    """操作序列"""
    name: str = "未命名序列"
    actions: List[Action] = field(default_factory=list)
    
    def add_action(self, action: Action):
        """添加操作"""
        self.actions.append(action)
    
    def remove_action(self, action_id: str):
        """移除操作"""
        self.actions = [a for a in self.actions if a.id != action_id]
    
    def move_action(self, from_index: int, to_index: int):
        """移动操作位置"""
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """获取操作"""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None
    
    def clear(self):
        """清空所有操作"""
        self.actions.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'actions': [a.to_dict() for a in self.actions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionSequence':
        """从字典创建"""
        sequence = cls(name=data.get('name', '未命名序列'))
        for action_data in data.get('actions', []):
            sequence.add_action(Action.from_dict(action_data))
        return sequence
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'ActionSequence':
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 创建操作的工厂函数
def create_mouse_click(x: int, y: int, button: str = 'left') -> Action:
    """创建鼠标点击操作"""
    return Action(
        action_type=ActionType.MOUSE_CLICK,
        params={'x': x, 'y': y, 'button': button}
    )


def create_mouse_double_click(x: int, y: int) -> Action:
    """创建鼠标双击操作"""
    return Action(
        action_type=ActionType.MOUSE_DOUBLE_CLICK,
        params={'x': x, 'y': y}
    )


def create_mouse_right_click(x: int, y: int) -> Action:
    """创建鼠标右键操作"""
    return Action(
        action_type=ActionType.MOUSE_RIGHT_CLICK,
        params={'x': x, 'y': y}
    )


def create_mouse_move(x: int, y: int, duration: float = 0.25) -> Action:
    """创建鼠标移动操作"""
    return Action(
        action_type=ActionType.MOUSE_MOVE,
        params={'x': x, 'y': y, 'duration': duration}
    )


def create_mouse_drag(x: int, y: int, duration: float = 0.5) -> Action:
    """创建鼠标拖拽操作"""
    return Action(
        action_type=ActionType.MOUSE_DRAG,
        params={'x': x, 'y': y, 'duration': duration}
    )


def create_mouse_scroll(amount: int, x: Optional[int] = None, y: Optional[int] = None) -> Action:
    """创建鼠标滚轮操作"""
    return Action(
        action_type=ActionType.MOUSE_SCROLL,
        params={'amount': amount, 'x': x, 'y': y}
    )


def create_keyboard_type(text: str, interval: float = 0.0) -> Action:
    """创建键盘输入操作"""
    return Action(
        action_type=ActionType.KEYBOARD_TYPE,
        params={'text': text, 'interval': interval}
    )


def create_keyboard_press(key: str, presses: int = 1) -> Action:
    """创建按键操作"""
    return Action(
        action_type=ActionType.KEYBOARD_PRESS,
        params={'key': key, 'presses': presses}
    )


def create_keyboard_hotkey(keys: List[str]) -> Action:
    """创建组合键操作"""
    return Action(
        action_type=ActionType.KEYBOARD_HOTKEY,
        params={'keys': keys}
    )


def create_delay(seconds: float) -> Action:
    """创建延迟操作"""
    return Action(
        action_type=ActionType.DELAY,
        params={'seconds': seconds}
    )
