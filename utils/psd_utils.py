"""
psd_tooli.py
一个轻量封装的 psd-tools 小模块，用于解析PSD并合成图片。

主要函数
----------------
inspect_psd(path:str) -> dict
compose_image(path:str, pose:str, clothing:str|None=None,
              action:str|None=None, expression:str|None=None) -> PIL.Image

目前支持以下图层结构：
A:
姿态/
├── 站立/
│   └── 表情/
└── 坐下/
服装/
├── 校服
└── 便服
动作/
├── 跑
└── 跳

B:
姿态/
├── 站立/
│   ├── 服装/
│   │   ├── 校服/
│   │   ├── 便服/
│   │   └── 动作/
│   │        ├── 跑/
│   │        └── 跳/
│   └── 表情/

"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import Dict, List, Optional

from psd_tools import PSDImage
from PIL import Image

# ---------- 缓存 ----------
_CACHE_LOCK = threading.RLock()
_CACHE_SIZE = 8


@lru_cache(maxsize=_CACHE_SIZE)
def _load_psd(path: str) -> PSDImage:
    """线程安全的 PSD 缓存（进程内）"""
    with _CACHE_LOCK:
        return PSDImage.open(path)


# ---------- 小工具 ----------
def _clean(name: str) -> str:
    """去掉 PSD 里常见的 \x00 及前后空格"""
    return name.strip().strip("\x00").strip()


def _find_group(parent, name: str):
    """在 parent 下找第一个名字 startswith `name` 的组（不区分大小写）"""
    for lyr in parent:
        if lyr.is_group() and _clean(lyr.name).lower().startswith(name.lower()):
            return lyr
    return None


def _leaf_names(group) -> List[str]:
    """返回组内所有"非组"图层的干净名字列表
    Args:
        group: 图层组
        exclude_special: 是否排除名称以 BASE 或 FORE 开头的图层
    """
    names = []
    for layer in group.descendants():
        if not layer.is_group():
            clean_name = _clean(layer.name)
            if clean_name.startswith("BASE") or clean_name.startswith("FORE"):
                continue
            names.append(clean_name)
    return names


def _alpha_composite(base: Image.Image, overlay: Image.Image, position: tuple) -> Image.Image:
    """
    Alpha混合两个图像
    base: 底图
    overlay: 上层图像（半透明）
    position: 上层图像在底图中的位置 (x, y)
    """
    x, y = position
    temp = Image.new('RGBA', base.size, (0, 0, 0, 0))
    temp.paste(overlay, (x, y))
    return Image.alpha_composite(base, temp)


# ---------- 1. 解析 ----------
def inspect_psd(path: str) -> dict:
    """
    增强版PSD解析，支持灵活的图层结构
    
    返回结构
    {
      "poses": {
        "<pose_name>": {
          "clothes": {
            "<cloth_name>": ["action1", "action2", ...]   # 空列表表示无动作
          },
          "expressions": ["expr1", "expr2", ...],
          "clothes_source": "pose" | "global",           # 服装来源
          "actions_source": "pose" | "global" | "none"   # 动作来源
        }
      },
      "global_clothes": {                              # 全局服装（如果存在）
        "<cloth_name>": ["action1", ...]
      },
      "global_actions": ["action1", "action2", ...]    # 全局动作（如果存在）
    }
    """
    psd = _load_psd(path)
    
    # 查找顶层组
    top_clothes_root = _find_group(psd, "服装")
    top_actions_root = _find_group(psd, "动作")
    pose_root = _find_group(psd, "姿态")
    
    if pose_root is None:
        raise ValueError("PSD 顶层未找到名字以'姿态'开头的组")
    
    # 解析全局服装（结构A）
    global_clothes = {}
    if top_clothes_root:
        for item in top_clothes_root:
            cloth_name = _clean(item.name)
            if item.is_group():
                # 服装组内可能包含动作子组
                actions = _leaf_names(item)
                global_clothes[cloth_name] = actions
            else:
                global_clothes[cloth_name] = []
    
    # 解析全局动作（结构A）
    global_actions = []
    if top_actions_root:
        global_actions = _leaf_names(top_actions_root)
    
    # 解析姿态组（支持结构B）
    poses: Dict[str, dict] = {}
    for pose_grp in pose_root:
        if not pose_grp.is_group():
            continue
        
        pose_name = _clean(pose_grp.name)
        
        # 查找姿态内的组
        pose_clothes_root = _find_group(pose_grp, "服装")
        pose_actions_root = _find_group(pose_grp, "动作")
        expr_root = _find_group(pose_grp, "表情")
        
        # 确定服装来源：优先使用姿态内的，否则使用全局的
        if pose_clothes_root:
            # 姿态内有服装组（结构B）
            clothes_source = "pose"
            clothes_dict: Dict[str, List[str]] = {}
            for item in pose_clothes_root:
                cloth_name = _clean(item.name)
                if item.is_group():
                    actions = _leaf_names(item)
                    clothes_dict[cloth_name] = actions
                else:
                    clothes_dict[cloth_name] = []
        elif global_clothes:
            # 使用全局服装（结构A）
            clothes_source = "global"
            clothes_dict = global_clothes
        else:
            # 没有服装
            clothes_source = "global"
            clothes_dict = {}
        
        # 确定动作来源
        if pose_clothes_root and any(pose_clothes_root.descendants()):
            # 动作在服装组内（结构B的子情况）
            actions_source = "pose"
        elif pose_actions_root:
            # 动作直接在姿态下（结构B的变体）
            actions_source = "pose"
        elif global_actions:
            # 使用全局动作（结构A）
            actions_source = "global"
        else:
            actions_source = "none"
        
        # 获取表情列表
        expressions = _leaf_names(expr_root) if expr_root else []
        
        poses[pose_name] = {
            "clothes": clothes_dict,
            "expressions": expressions,
            "clothes_source": clothes_source,
            "actions_source": actions_source
        }
    
    return {
        "poses": poses,
        "global_clothes": global_clothes if global_clothes else {},
        "global_actions": global_actions if global_actions else {}
    }


def _get_psd_path(chara_id: str) -> str:
    """获取角色PSD文件路径"""
    from config import CONFIGS
    import os
    return os.path.join(CONFIGS.ASSETS_PATH, "chara", chara_id, f"{chara_id}.psd")


def get_pose_options(chara_id: str) -> List[str]:
    """获取角色的所有姿态选项"""
    from config import CONFIGS
    psd_info = CONFIGS.get_psd_info(chara_id)
    return list(psd_info["poses"].keys()) if psd_info else []


def get_clothing_action_options(chara_id: str, pose: str) -> tuple[List[str], List[str]]:
    """
    获取指定姿态下的服装和动作列表
    返回: (服装列表, 动作列表)
    """
    from config import CONFIGS
    psd_info = CONFIGS.get_psd_info(chara_id)
    if not psd_info:
        return [], []
    
    pose_info = psd_info["poses"].get(pose, {})
    
    # 获取服装列表
    clothes = list(pose_info.get("clothes", {}).keys()) if pose_info.get("clothes") else []
    
    # 获取动作列表（去重）
    actions = set()
    if pose_info.get("actions_source") == "pose":
        # 从服装组内收集
        for clothing_actions in pose_info.get("clothes", {}).values():
            actions.update(clothing_actions)
        # 从姿态直接收集
        psd = _load_psd(_get_psd_path(chara_id))
        pose_root = _find_group(psd, "姿态")
        if pose_root:
            pose_grp = next((g for g in pose_root if _clean(g.name) == pose), None)
            if pose_grp:
                pose_actions = _find_group(pose_grp, "动作")
                if pose_actions:
                    actions.update(_leaf_names(pose_actions))
    elif pose_info.get("actions_source") == "global" and psd_info.get("global_actions"):
        actions.update(psd_info["global_actions"])
    
    return clothes, sorted(list(actions))


def get_emotion_filter_emotion_options(chara_id: str, pose: str, clothing: str = None) -> tuple[List[str], Dict[str, List[str]]]:
    """
    获取表情筛选选项和对应的表情列表
    返回: (筛选器列表, {筛选器名称: 表情列表})
    """
    from config import CONFIGS
    psd_info = CONFIGS.get_psd_info(chara_id)
    if not psd_info:
        return [], {}
    
    # 获取表情根组
    psd = _load_psd(_get_psd_path(chara_id))
    pose_root = _find_group(psd, "姿态")
    if not pose_root:
        return [], {}
    
    pose_grp = next((g for g in pose_root if g.is_group() and _clean(g.name) == pose), None)
    if not pose_grp:
        return [], {}
    
    # 优先检查服装层级
    if clothing:
        pose_clothes_root = _find_group(pose_grp, "服装")
        if pose_clothes_root:
            target_cloth = next((item for item in pose_clothes_root if _clean(item.name) == clothing), None)
            if target_cloth and target_cloth.is_group():
                cloth_expr_root = _find_group(target_cloth, "表情")
                if cloth_expr_root:
                    return _extract_emotion_filters(cloth_expr_root)
    
    # 检查姿态层级
    expr_root = _find_group(pose_grp, "表情")
    if expr_root:
        return _extract_emotion_filters(expr_root)
    
    return [], {}


def _extract_emotion_filters(expr_root) -> tuple[List[str], Dict[str, List[str]]]:
    """从表情组提取筛选器和表情列表"""
    subgroups = [g for g in expr_root if g.is_group()]
    
    if subgroups:
        # 有子组，作为筛选器
        filters = []
        options = {}
        
        for subgroup in subgroups:
            filter_name = _clean(subgroup.name)
            filters.append(filter_name)
            options[filter_name] = _leaf_names(subgroup)
        
        # 添加"全部"选项
        if filters:
            filters.insert(0, "全部")
            all_emotions = []
            for emo_list in options.values():
                all_emotions.extend(emo_list)
            options["全部"] = sorted(list(set(all_emotions)))
        
        return filters, options
    else:
        # 无子组，直接是表情列表
        emotions = _leaf_names(expr_root)
        return ["全部"], {"全部": emotions}

# ---------- 2. 合成 ----------

def _layer_topil(layer):
    """兼容不同版本的psd-tools"""
    if hasattr(layer, 'topil'):
        return layer.topil()
    return layer.composite()


def compose_image(path: str, pose: str,
                  clothing: Optional[str] = None,
                  action: Optional[str] = None,
                  expression: Optional[str] = None,
                  filter_name: Optional[str] = None) -> Image.Image:
    """
    重构后的图像合成函数 - 深度优先遍历版本
    只合成指定的图层 + 在选项层级中发现的BASE/FORE图层
    """
    psd = _load_psd(path)
    # psd_info = inspect_psd(path)
    
    pose_root = _find_group(psd, "姿态")
    if not pose_root:
        raise ValueError("PSD中未找到姿态组")
    
    # 双栈：基础栈和顶层栈
    base_stack = []  # 基础图层（按顺序合成）
    fore_stack = []  # 顶层图层（最后覆盖）
    
    # 标志位：记录是否已经处理了各个选项
    found_pose = False
    found_clothing = False
    found_action = False
    found_expression = False
    
    # 收集所有符合条件的图层 - 深度优先遍历
    def collect_layers(group, is_fore=False):
        """深度优先遍历，只进入选中的选项组，同时收集BASE/FORE"""
        nonlocal found_pose, found_clothing, found_action, found_expression
        for layer in group:
            layer_name = _clean(layer.name)
            
            if layer.is_group():
                # 处理选项组
                if not found_pose and layer_name.startswith("姿态"):
                    # 进入选中的姿态
                    target_pose = next((p for p in layer if _clean(p.name) == pose), None)
                    if target_pose and target_pose.is_group():
                        found_pose = True
                        # 收集姿态下的直接图层（不属于任何选项组）
                        for child in target_pose:
                            if not child.is_group():
                                base_stack.append(child)
                        # 在姿态组内继续查找其他选项和BASE/FORE
                        collect_layers(target_pose, is_fore)
                    continue
                
                elif clothing and not found_clothing and layer_name.startswith("服装"):
                    # 进入选中的服装
                    target_cloth = next((c for c in layer if _clean(c.name) == clothing), None)
                    if target_cloth:
                        found_clothing = True
                        if target_cloth.is_group():
                            # 收集服装下的所有图层（但不包括选项组）
                            for child in target_cloth:
                                if not child.is_group():
                                    base_stack.append(child)
                                elif child.name.startswith(("BASE", "FORE")):
                                    # 在服装组内继续查找BASE/FORE
                                    collect_layers(child, is_fore)
                        else:
                            base_stack.append(target_cloth)
                    continue
                
                elif action and  not found_action and layer_name.startswith("动作"):
                    # 进入选中的动作
                    target_action = next((a for a in layer if _clean(a.name) == action), None)
                    if target_action:
                        found_action = True
                        if target_action.is_group():
                            for child in target_action:
                                if not child.is_group():
                                    base_stack.append(child)
                                elif child.name.startswith(("BASE", "FORE")):
                                    collect_layers(child, is_fore)
                        else:
                            base_stack.append(target_action)
                    continue
                
                elif expression and  not found_expression and layer_name.startswith("表情"):
                    # 在表情组中查找选中的表情
                    found_expression = True
                    
                    # 检查是否有子组（表情筛选）
                    subgroups = [g for g in layer if g.is_group()]
                    if subgroups:
                        # 有子组，查找包含目标表情的子组
                        for subgroup in subgroups:
                            # 在子组中查找目标表情
                            found_target_in_subgroup = False
                            for child in subgroup:
                                if not child.is_group() and _clean(child.name) == expression:
                                    fore_stack.append(child)
                                    found_target_in_subgroup = True
                                    break
                            
                            if found_target_in_subgroup:
                                # 只在当前子组内查找BASE/FORE图层（不递归）
                                for child in subgroup:
                                    if not child.is_group() and child.name.startswith(("BASE", "FORE")):
                                        fore_stack.append(child)
                                # 找到目标表情后，跳出循环，不再检查其他子组
                                break
                    else:
                        # 无子组，直接查找
                        for child in layer:
                            if not child.is_group() and _clean(child.name) == expression:
                                fore_stack.append(child)
                            elif not child.is_group() and child.name.startswith(("BASE", "FORE")):
                                fore_stack.append(child)
                    continue
                
                # 对于其他组，如果已经在某个选项内部，继续递归查找BASE/FORE
                elif found_pose or found_clothing or found_action or found_expression:
                    collect_layers(layer, is_fore)
            
            else:
                # 普通图层
                # 如果已经在选项组内或者是BASE/FORE的直接子图层，加入栈
                if found_pose or found_clothing or found_action or found_expression or is_fore:
                    (fore_stack if is_fore else base_stack).append(layer)
    
    # 从PSD根开始深度遍历
    collect_layers(psd)
    
    # 获取增强的图像加载器
    from image_processor import get_enhanced_loader
    loader = get_enhanced_loader()
    
    # 开始PSD合成
    w, h = psd.size
    if not loader.start_psd_composition(w, h):
        raise RuntimeError("Failed to start PSD composition")
    
    # 合成基础栈
    for layer in base_stack:
        im = _layer_topil(layer)
        if im:
            l, t, _, _ = layer.bbox
            # 使用C++合成而不是PIL
            loader.add_psd_layer(im, l, t)
    
    # 合成顶层栈
    for layer in fore_stack:
        im = _layer_topil(layer)
        if im:
            l, t, _, _ = layer.bbox
            loader.add_psd_layer(im, l, t)
    
    # 结束合成并返回索引
    psd_index = loader.finish_psd_composition()
    
    return psd_index