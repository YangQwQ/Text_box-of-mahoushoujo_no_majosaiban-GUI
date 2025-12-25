# filename: draw_utils.py
from io import BytesIO
from typing import Tuple, Union, Literal, Optional, List, Any, Dict
from PIL import Image
import emoji

from config import CONFIGS


# --- 辅助函数：提取emoji并替换为占位符 ---
def _extract_emojis_and_replace(src: str):
    emoji_infos = emoji.emoji_list(
        src
    )  # 返回列表，每个元素包含 'emoji', 'match_start', 'match_end'
    if not emoji_infos:
        return [], []

    emojis = []
    positions = []  # 记录字节位置

    # 用于将字符索引转换为字节索引的辅助函数
    def char_index_to_byte_index(char_index):
        # 将前char_index个字符编码为UTF-8，然后返回字节数
        return len(src[:char_index].encode("utf-8"))

    for info in emoji_infos:
        s = info["match_start"]  # 字符索引
        e = info["match_end"]
        # 转换为字节索引
        s_byte = char_index_to_byte_index(s)
        e_byte = char_index_to_byte_index(e)
        emojis.append(src[s:e])
        positions.append((s_byte, e_byte))  # 记录字节位置元组
    return emojis, positions  # 返回三个值


def draw_content_auto(
    text: Optional[str] = None, content_image: Optional[Image.Image] = None
) -> bytes:
    """简化的绘制函数，只处理emoji提取，其他交给C++"""

    import time

    st = time.time()

    # 提取emoji
    emoji_list = []
    if text:
        emoji_list, emoji_position = _extract_emojis_and_replace(text)

    print(f"Emoji提取用时: {int((time.time()-st)*1000)}ms")
    st = time.time()

    # 准备图片数据
    image_data = None
    image_width = 0
    image_height = 0
    image_pitch = 0

    if content_image:
        # 将图片转换为RGBA格式
        img_rgba = content_image.convert("RGBA")
        import numpy as np

        img_array = np.array(img_rgba)
        image_height, image_width = img_array.shape[:2]
        image_pitch = image_width * 4
        image_data = img_array.flatten().tobytes()

    # 调用C++端的简化函数
    try:
        from image_loader import draw_content_simple_dll

        result_image = draw_content_simple_dll(
            text=text or "",
            emoji_list=emoji_list,
            emoji_position=emoji_position,
            image_data=image_data,
            image_width=image_width,
            image_height=image_height,
            image_pitch=image_pitch,
        )

        print(f"C++ drawing time: {int((time.time()-st)*1000)}ms")
        st = time.time()

        if not result_image:
            raise Exception("C++ drawing failed")

        # 图片压缩（可选）
        compression_setting = CONFIGS.gui_settings.get("image_compression", None)
        if compression_setting and compression_setting.get(
            "pixel_reduction_enabled", False
        ):
            reduction_ratio = (
                compression_setting.get("pixel_reduction_ratio", 50) / 100.0
            )
            new_width = max(int(result_image.width * (1 - reduction_ratio)), 300)
            new_height = max(int(result_image.height * (1 - reduction_ratio)), 100)
            result_image = result_image.resize(
                (new_width, new_height), Image.Resampling.BILINEAR
            )
            print(f"压缩耗时: {int((time.time()-st)*1000)}ms")
            st = time.time()

        # 转换为BMP格式
        buf = BytesIO()
        img_rgb = result_image.convert("RGB")
        img_rgb.save(buf, format="BMP")
        bmp_data = buf.getvalue()[14:]

        print(f"输出耗时: {int((time.time()-st)*1000)}ms")
        return bmp_data

    except Exception as e:
        print(f"绘制失败: {str(e)}")
        import traceback

        traceback.print_exc()
        raise
