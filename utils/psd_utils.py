"""
psd_tooli.py
一个轻量封装的 psd-tools 小模块，用于解析PSD并合成图片。

主要函数
----------------
inspect_psd(path:str) -> dict
compose_image(path:str, pose:str, clothing:str|None=None,
              action:str|None=None, expression:str|None=None) -> PIL.Image
"""
from __future__ import annotations

import threading
from functools import lru_cache
from typing import Dict, List, Optional

from psd_tools import PSDImage
from PIL import Image

# ---------- 缓存 ----------
_CACHE_LOCK = threading.RLock()
_CACHE_SIZE = 8  # 最多缓存 8 个 PSD 文件，可按需调大


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
    """返回组内所有"非组"图层的干净名字列表"""
    return [_clean(l.name) for l in group.descendants() if not l.is_group()]


def _alpha_composite(base: Image.Image, overlay: Image.Image, position: tuple) -> Image.Image:
    """
    Alpha混合两个图像
    base: 底图
    overlay: 上层图像（半透明）
    position: 上层图像在底图中的位置 (x, y)
    """
    x, y = position
    # 创建一个与底图相同大小的临时图像
    temp = Image.new('RGBA', base.size, (0, 0, 0, 0))
    # 将上层图像放到临时图像的正确位置
    temp.paste(overlay, (x, y))
    # 使用alpha混合
    return Image.alpha_composite(base, temp)


# ---------- 1. 解析 ----------
def inspect_psd(path: str) -> dict:
    """
    返回结构
    {
      "poses": {
        "<pose_name>": {
          "clothes": {
            "<cloth_name>": ["action1", "action2", ...]   # 空列表表示无动作
          },
          "expressions": ["expr1", "expr2", ...]
        }
      }
    }
    """
    psd = _load_psd(path)
    pose_root = _find_group(psd, "姿态")
    if pose_root is None:
        raise ValueError("PSD 顶层未找到名字以'姿态'开头的组")

    poses: Dict[str, dict] = {}
    for pose_grp in pose_root:
        if not pose_grp.is_group():
            continue
        pose_name = _clean(pose_grp.name)
        cloth_dict: Dict[str, List[str]] = {}
        expr_list: List[str] = []

        # --- 服装 ---
        cloth_root = _find_group(pose_grp, "服装")
        if cloth_root:
            for item in cloth_root:
                cloth_name = _clean(item.name)
                if item.is_group():
                    # 把子层里的非组图层当动作
                    actions = _leaf_names(item)
                else:
                    actions = []  # 单层服装，无动作
                cloth_dict[cloth_name] = actions

        # --- 表情 ---
        expr_root = _find_group(pose_grp, "表情")
        if expr_root:
            expr_list = _leaf_names(expr_root)

        poses[pose_name] = {"clothes": cloth_dict, "expressions": expr_list}

    return {"poses": poses}


def _layer_topil(layer):
    if hasattr(layer, 'topil'):
        return layer.topil()
    return layer.composite()


def compose_image(path: str, pose: str,
                  clothing: Optional[str] = None,
                  action: Optional[str] = None,
                  expression: Optional[str] = None) -> Image.Image:
    psd = _load_psd(path)
    # 1. 拿到姿态组
    pose_root = _find_group(psd, "姿态")
    pose_grp = next((g for g in pose_root if g.is_group() and _clean(g.name) == pose), None)
    if pose_grp is None:
        raise ValueError(f"姿态 {pose} 不存在")

    # 2. 收集需要显示的图层
    # 使用列表来存储，每个元素是(layer, is_expression)元组
    layers_to_render = []

    # 2.1 姿态组里除"服装/表情"外的所有叶子层
    for lyr in pose_grp.descendants():
        if lyr.is_group():
            continue
        if any(_clean(lyr.parent.name).startswith(sw) for sw in ("服装", "表情")):
            continue
        layers_to_render.append((lyr, False))  # 不是表情图层

    # 2.2 服装
    if clothing:
        cloth_root = _find_group(pose_grp, "服装")
        target = next((item for item in cloth_root if _clean(item.name) == clothing), None)
        if target is None:
            raise ValueError(f"服装 {clothing} 不存在")
        if target.is_group() and action:
            found = next((sub for sub in target if _clean(sub.name) == action), None)
            if found is None:
                raise ValueError(f"动作 {action} 不存在")
            # 添加动作组内的所有图层
            for lyr in found.descendants():
                if not lyr.is_group():
                    layers_to_render.append((lyr, False))
        else:
            # 添加服装组或服装图层
            if target.is_group():
                for lyr in target.descendants():
                    if not lyr.is_group():
                        layers_to_render.append((lyr, False))
            else:
                layers_to_render.append((target, False))

    # 2.3 表情
    if expression:
        expr_root = _find_group(pose_grp, "表情")
        if expr_root:
            found = next((lyr for lyr in expr_root.descendants()
                        if not lyr.is_group() and _clean(lyr.name) == expression), None)
            if found is None:
                print(f"表情 {expression} 不存在")
            else:
                layers_to_render.append((found, True))  # 是表情图层，需要alpha混合

    # 3. 按照图层的top值排序（从底层到顶层）
    layers_to_render.sort(key=lambda x: x[0].top)

    # 4. 渲染图层
    w, h = psd.size
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    
    for layer, is_expression in layers_to_render:
        im = _layer_topil(layer)
        if im is None:
            continue
            
        l, t, _, _ = layer.bbox
        
        if is_expression:
            # 对表情图层使用alpha混合
            canvas = _alpha_composite(canvas, im, (l, t))
        else:
            # 其他图层使用原来的paste方式
            canvas.paste(im, (l, t), im)
    
    return canvas


# ---------- demo ----------
# if __name__ == "__main__":
#     import time
#     psd_path = r"assets/chara/sora/sora.psd"
#     print("--- 解析 ---")
#     st = time.time()
#     info = inspect_psd(psd_path)
#     from pprint import pprint
#     pprint(info, width=120)
# 
#     print(f"耗时 {time.time() - st:.3f} 秒")
#     print("--- 合成 ---")
#     st = time.time()
#     img = compose_image(
#         psd_path,
#         pose="左向",
#         clothing="校服",
#         action="",
#         expression="无语",
#     )
#     print(f"耗时 {time.time() - st:.3f} 秒")
#     img.show()