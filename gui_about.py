# gui_about.py
"""关于窗口"""

import tkinter as tk
from tkinter import messagebox
import webbrowser
from update_checker import update_checker
from config import CONFIGS


class AboutWindow:
    """关于窗口"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.update_result = None
        # 存储背景颜色
        self.bg_color = None

    def open(self):
        """打开关于窗口"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("关于 - 魔裁文本框生成器")
        self.window.geometry("500x650")
        self.window.minsize(400, 400)  # 设置最小尺寸，避免窗口过小
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()

        # 添加图标
        from path_utils import set_window_icon
        set_window_icon(self.window)

        # 获取窗口背景颜色
        self.bg_color = self.window.cget("background")

        self.setup_ui()

        # 居中显示
        self.center_window()

        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def center_window(self):
        """窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """设置UI界面"""
        # 获取程序信息
        program_info = CONFIGS.get_program_info()
        contact_info = CONFIGS.get_contact_info()

        # 创建主框架
        main_frame = tk.Frame(self.window, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建一个可滚动的框架
        canvas = tk.Canvas(main_frame, bg=self.bg_color)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        # 创建滚动区域
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)

        # 配置滚动区域
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮事件 - 跨平台兼容
        def _on_mousewheel(event):
            # Windows 和 macOS 的滚轮事件处理
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        # 绑定滚轮事件
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows, macOS
        canvas.bind("<Button-4>", _on_mousewheel)  # Linux
        canvas.bind("<Button-5>", _on_mousewheel)  # Linux

        # 设置Canvas宽度自适应
        def _configure_canvas(event):
            canvas.itemconfig(canvas_frame_id, width=event.width)

        canvas.bind("<Configure>", _configure_canvas)

        canvas_frame_id = canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw"
        )

        # 布局滚动组件
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 内容框架
        content_frame = tk.Frame(scrollable_frame, bg=self.bg_color, padx=10, pady=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 版本信息 - 使用tkinter的LabelFrame
        version_frame = tk.LabelFrame(
            content_frame, text="版本信息", bg=self.bg_color, padx=10, pady=10
        )
        version_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建一个Frame来包含当前版本文本和按钮（同一行）
        version_header_frame = tk.Frame(version_frame, bg=self.bg_color)
        version_header_frame.pack(fill=tk.X, pady=(0, 5))

        # 当前版本（左对齐）
        version_text = f"当前版本: v{program_info['version']}"
        version_label = tk.Label(
            version_header_frame, text=version_text, bg=self.bg_color
        )
        version_label.pack(side=tk.LEFT)

        # 按钮框架（右对齐）
        button_frame = tk.Frame(version_header_frame, bg=self.bg_color)
        button_frame.pack(side=tk.RIGHT)

        # 版本历史按钮
        history_button = tk.Button(
            button_frame, text="版本历史", command=self.show_version_history, width=8
        )
        history_button.pack(side=tk.LEFT, padx=(0, 5))

        # 检查更新按钮
        update_button = tk.Button(
            button_frame, text="检查更新", command=self.check_update, width=8
        )
        update_button.pack(side=tk.LEFT)

        # 更新结果显示区域
        self.update_result_frame = tk.Frame(version_frame, bg=self.bg_color)
        self.update_result_frame.pack(fill=tk.X, pady=(5, 0))

        # 程序描述 - 使用tkinter的LabelFrame
        desc_frame = tk.LabelFrame(
            content_frame, text="程序描述", bg=self.bg_color, padx=10, pady=10
        )
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        desc_text = (
            program_info.get("description", "")
            + """

情感匹配使用说明：
1. 下载ollama
2. 在ollama中运行 OmniDimen 模型
3. 启用程序内的情感匹配功能
（在setting.yml中启用sentiment_matching的display）
4. 勾选主界面的情感匹配即可

注意事项：
• 有bug请及时反馈
• 检查更新按钮可能对网络有要求"""
        )

        # 创建Text控件，使用窗口的背景颜色，确保自动换行
        desc_text_widget = tk.Text(
            desc_frame,
            wrap=tk.WORD,
            font=("TkDefaultFont", 10),  # 使用系统默认字体
            bg=self.bg_color,
            relief=tk.FLAT,
            borderwidth=0,
        )
        desc_text_widget.insert(1.0, desc_text)
        desc_text_widget.config(state=tk.DISABLED)

        # 添加滚动条
        desc_scrollbar = tk.Scrollbar(desc_frame)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        desc_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_text_widget.config(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.config(command=desc_text_widget.yview)

        # 联系信息 - 使用tkinter的LabelFrame
        contact_frame = tk.LabelFrame(
            content_frame, text="联系信息", bg=self.bg_color, padx=10, pady=10
        )
        contact_frame.pack(fill=tk.X, pady=(0, 10))

        # 作者信息 - 支持多个作者
        author_frame = tk.Frame(contact_frame, bg=self.bg_color)
        author_frame.pack(fill=tk.X, pady=2)  # 使用fill=tk.X确保宽度自适应

        tk.Label(
            author_frame, text="贡献者: ", bg=self.bg_color, width=8, anchor=tk.W
        ).pack(side=tk.LEFT)

        authors = program_info.get("author", [])
        if isinstance(authors, list):
            # 多个作者，用逗号分隔
            authors_text = ", ".join(authors)
            tk.Label(
                author_frame, text=authors_text, bg=self.bg_color, wraplength=400
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            # 单个作者
            tk.Label(
                author_frame, text=str(authors), bg=self.bg_color, wraplength=400
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # GitHub链接 - 使用origin_project
        origin_project_url = program_info.get("origin_project", "")

        # 修复：确保origin_project_url不为空
        if origin_project_url and origin_project_url.strip():
            github_frame = tk.Frame(contact_frame, bg=self.bg_color)
            github_frame.pack(fill=tk.X, pady=2)

            tk.Label(
                github_frame, text="项目地址: ", bg=self.bg_color, width=8, anchor=tk.W
            ).pack(side=tk.LEFT)

            # 使用wraplength确保链接文本能够换行
            github_link = tk.Label(
                github_frame,
                text=origin_project_url.strip(),
                fg="blue",
                bg=self.bg_color,
                cursor="hand2",
                wraplength=400,  # 设置换行宽度
                justify=tk.LEFT,
            )
            github_link.pack(side=tk.LEFT, fill=tk.X, expand=True)
            github_link.bind(
                "<Button-1>", lambda e: self.open_url(origin_project_url.strip())
            )

        # 交流群 - 支持多个QQ群
        qq_groups = contact_info.get("qq_group", [])
        if qq_groups:
            if not isinstance(qq_groups, list):
                qq_groups = [qq_groups]

            qq_frame = tk.Frame(contact_frame, bg=self.bg_color)
            qq_frame.pack(fill=tk.X, pady=2)

            tk.Label(
                qq_frame, text="QQ交流群: ", bg=self.bg_color, width=8, anchor=tk.W
            ).pack(side=tk.LEFT)

            # 多个群用逗号分隔
            qq_groups_text = ", ".join(qq_groups)
            tk.Label(
                qq_frame, text=qq_groups_text, bg=self.bg_color, wraplength=400
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def show_version_history(self):
        """显示版本历史"""
        version_history = CONFIGS.get_version_history()

        if not version_history:
            messagebox.showinfo("版本历史", "暂无版本历史信息")
            return

        # 创建版本历史窗口
        history_window = tk.Toplevel(self.window)
        history_window.title("版本历史")
        history_window.geometry("500x400")
        history_window.minsize(400, 300)
        history_window.transient(self.window)

        # 获取背景颜色
        bg_color = history_window.cget("bg")

        # 创建主框架
        main_frame = tk.Frame(history_window, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建带滚动条的Text控件
        text_frame = tk.Frame(main_frame, bg=bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,  # 确保自动换行
            font=("TkDefaultFont", 10),  # 使用系统默认字体
            bg=bg_color,
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        # 绑定鼠标滚轮 - 跨平台兼容
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                text_widget.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                text_widget.yview_scroll(1, "units")

        text_widget.bind("<MouseWheel>", _on_mousewheel)  # Windows, macOS
        text_widget.bind("<Button-4>", _on_mousewheel)  # Linux
        text_widget.bind("<Button-5>", _on_mousewheel)  # Linux

        # 添加版本历史内容
        for i, version in enumerate(version_history, 1):
            text_widget.insert(tk.END, f"版本 {version.get('version', '未知')}\n")
            text_widget.insert(tk.END, f"发布时间: {version.get('date', '未知')}\n")
            text_widget.insert(tk.END, "更新说明:\n")

            descriptions = version.get("description", [])
            if isinstance(descriptions, list):
                # 每行前面加•符号
                for desc in descriptions:
                    text_widget.insert(tk.END, f"• {desc}\n")
            else:
                # 如果是字符串，直接显示
                text_widget.insert(tk.END, f"• {descriptions}\n")

            if i < len(version_history):
                text_widget.insert(tk.END, "\n" + "-" * 50 + "\n\n")

        text_widget.config(state=tk.DISABLED)

        # 关闭按钮
        button_frame = tk.Frame(history_window, bg=bg_color, pady=10)
        button_frame.pack(fill=tk.X)

        close_button = tk.Button(
            button_frame, text="关闭", command=history_window.destroy, width=10
        )
        close_button.pack(anchor=tk.CENTER)

        # 居中显示
        history_window.update_idletasks()
        width = history_window.winfo_width()
        height = history_window.winfo_height()
        x = (history_window.winfo_screenwidth() // 2) - (width // 2)
        y = (history_window.winfo_screenheight() // 2) - (height // 2)
        history_window.geometry(f"+{x}+{y}")

    def check_update(self):
        """检查更新"""
        # 清空之前的结果
        for widget in self.update_result_frame.winfo_children():
            widget.destroy()

        # 显示检查中
        checking_label = tk.Label(
            self.update_result_frame,
            text="正在检查更新...",
            fg="blue",
            bg=self.bg_color,
        )
        checking_label.pack()

        # 异步检查更新 - 仍然使用原来的github链接
        self.window.after(100, self._do_check_update)

    def _do_check_update(self):
        """执行检查更新"""
        try:
            # 调用更新检查器，使用CONFIGS.version作为当前版本
            result = update_checker.check_update(CONFIGS.version)

            # 清除检查中标签
            for widget in self.update_result_frame.winfo_children():
                widget.destroy()

            if isinstance(result, dict) and "error" in result:
                # 检查出错
                error_label = tk.Label(
                    self.update_result_frame,
                    text=f"检查更新失败: {result['error']}",
                    fg="red",
                    bg=self.bg_color,
                    wraplength=500,  # 确保错误信息能够换行
                )
                error_label.pack(pady=5)
                return

            if result.get("has_update", False):
                # 有更新可用
                latest = result["latest_release"]

                # 更新提示
                update_label = tk.Label(
                    self.update_result_frame,
                    text=f"有新版本可用: {latest['version']}",
                    fg="green",
                    font=("TkDefaultFont", 10, "bold"),
                    bg=self.bg_color,
                    wraplength=500,
                )
                update_label.pack(pady=(0, 5))

                # 版本信息
                info_text = f"版本: {latest['version']}\n"
                info_text += f"名称: {latest['version_name']}\n"
                info_text += f"发布时间: {latest.get('published_at', '未知')}\n"
                info_text += (
                    f"预发布: {'是' if latest.get('is_prerelease', False) else '否'}"
                )

                info_label = tk.Label(
                    self.update_result_frame,
                    text=info_text,
                    justify=tk.LEFT,
                    bg=self.bg_color,
                    wraplength=500,
                )
                info_label.pack(anchor=tk.W, pady=(0, 5))

                # 发布说明（截取前500字符）
                notes = latest.get("release_notes", "无更新说明")
                if len(notes) > 500:
                    notes = notes[:500] + "..."

                notes_frame = tk.LabelFrame(
                    self.update_result_frame,
                    text="发布说明",
                    bg=self.bg_color,
                    padx=5,
                    pady=5,
                )
                notes_frame.pack(fill=tk.X, pady=(0, 5))

                notes_text = tk.Text(
                    notes_frame,
                    wrap=tk.WORD,  # 确保自动换行
                    height=4,
                    font=("TkFixedFont", 9),  # 使用系统默认字体
                    bg=self.bg_color,
                    relief=tk.FLAT,
                    borderwidth=0,
                    spacing1=3,
                    spacing2=3,
                )
                notes_text.insert(1.0, notes)
                notes_text.config(state=tk.DISABLED)
                notes_text.pack(fill=tk.BOTH, expand=True)

                # 下载链接
                assets = latest.get("assets", [])
                if assets:
                    download_frame = tk.Frame(
                        self.update_result_frame, bg=self.bg_color
                    )
                    download_frame.pack(fill=tk.X, pady=(0, 5))

                    tk.Label(download_frame, text="下载链接: ", bg=self.bg_color).pack(
                        side=tk.LEFT, anchor=tk.N
                    )

                    links_frame = tk.Frame(download_frame, bg=self.bg_color)
                    links_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                    for i, asset in enumerate(assets):
                        if i >= 3:  # 最多显示3个下载链接
                            if len(assets) > 3:
                                more_label = tk.Label(
                                    links_frame,
                                    text=f"... 等 {len(assets)} 个文件",
                                    fg="gray",
                                    bg=self.bg_color,
                                    font=("TkDefaultFont", 9),
                                )
                                more_label.pack(anchor=tk.W)
                            break

                        link_frame = tk.Frame(links_frame, bg=self.bg_color)
                        link_frame.pack(fill=tk.X, pady=1)

                        link_label = tk.Label(
                            link_frame,
                            text=f"{asset.get('name', '未知文件')} ({self._format_size(asset.get('size', 0))})",
                            fg="blue",
                            bg=self.bg_color,
                            cursor="hand2",
                            wraplength=400,  # 确保链接文本能够换行
                            justify=tk.LEFT,
                        )
                        link_label.pack(anchor=tk.W)
                        link_label.bind(
                            "<Button-1>",
                            lambda e, url=asset.get("download_url", ""): self.open_url(
                                url
                            ),
                        )

                # GitHub页面链接 - 使用原来的github链接
                github_link = tk.Label(
                    self.update_result_frame,
                    text="前往GitHub发布页面",
                    fg="blue",
                    bg=self.bg_color,
                    cursor="hand2",
                    font=("TkDefaultFont", 9, "underline"),
                    wraplength=500,
                )
                github_link.pack(pady=(5, 0))
                github_link.bind(
                    "<Button-1>",
                    lambda e: self.open_url(
                        f"{update_checker.repo_url}releases/latest"
                    ),
                )

            else:
                # 已是最新版本
                up_to_date_label = tk.Label(
                    self.update_result_frame,
                    text="当前已是最新版本！",
                    fg="green",
                    bg=self.bg_color,
                    font=("TkDefaultFont", 10, "bold"),
                    wraplength=500,
                )
                up_to_date_label.pack(pady=5)

        except Exception as e:
            # 清除检查中标签
            for widget in self.update_result_frame.winfo_children():
                widget.destroy()

            error_label = tk.Label(
                self.update_result_frame,
                text=f"检查更新时出错: {str(e)}",
                fg="red",
                bg=self.bg_color,
                wraplength=500,  # 确保错误信息能够换行
            )
            error_label.pack(pady=5)

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def open_url(self, url: str):
        """打开URL"""
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开链接: {str(e)}")

    def close(self):
        """关闭窗口"""
        if self.window:
            # 解绑鼠标滚轮事件
            self.window.unbind_all("<MouseWheel>")
            self.window.unbind_all("<Button-4>")
            self.window.unbind_all("<Button-5>")

            self.window.grab_release()
            self.window.destroy()
            self.window = None
