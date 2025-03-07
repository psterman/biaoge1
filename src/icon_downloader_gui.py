import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
from icon_downloader import IconDownloader
import os
import requests
from PIL import Image
from io import BytesIO
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class IconDownloaderGUI:
    def __init__(self, root):
        # 首先定义所有需要的方法
        def toggle_all_services(self):
            """切换全选/取消全选"""
            state = self.select_all_var.get()
            for var in self.service_vars.values():
                var.set(state)

        def check_select_all(self):
            """检查是否所有服务都被选中"""
            all_selected = all(var.get() for var in self.service_vars.values())
            self.select_all_var.set(all_selected)

        def get_selected_services(self):
            """获取选中的服务列表"""
            return [service for service, var in self.service_vars.items() if var.get()]

        # 将这些方法绑定到实例
        self.toggle_all_services = toggle_all_services.__get__(self)
        self.check_select_all = check_select_all.__get__(self)
        self.get_selected_services = get_selected_services.__get__(self)

        self.root = root
        self.root.title("标哥 - 图标搜索工具")
        self.root.geometry("1000x800")
        self.root.state('zoomed')
        
        # 设置全局字体
        self.default_font = ('微软雅黑', 10)
        self.small_font = ('微软雅黑', 9)
        self.title_font = ('微软雅黑', 20, 'bold')
        
        # 创建主框架并添加内边距
        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题区域（使用卡片风格）
        title_card = ttk.Frame(main_frame, style='Card.TFrame')
        title_card.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20), padx=5)
        title_card.configure(padding=15)
        
        title_label = ttk.Label(title_card, 
                              text="标哥",
                              font=self.title_font,
                              bootstyle="primary")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_card,
                               text="- 牵图标回家，哥",
                               font=self.default_font,
                               bootstyle="secondary")
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 创建左侧卡片
        left_card = ttk.Frame(main_frame)
        left_card.grid(row=1, column=0, sticky=(tk.N, tk.W), padx=(0, 10))
        left_card.configure(padding=15)
        
        # 输入区域
        input_label = ttk.Label(left_card, 
                              text="请输入网址或名称（每行一个）:",
                              font=self.default_font,
                              bootstyle="primary")
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 文本输入区域
        self.input_text = scrolledtext.ScrolledText(left_card, 
                                                  width=40,
                                                  height=10,
                                                  font=self.default_font)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.input_text.insert(tk.END, "www.google.com\nwww.facebook.com\n微信\n支付宝")
        
        # 添加输入框提示
        ToolTip(self.input_text, "在这里输入要下载图标的网址或名称，每行一个\n支持直接输入网址或中英文名称")
        
        # 示例说明（使用独立卡片）
        example_card = ttk.Labelframe(left_card, text="支持输入格式", 
                                    padding=(10, 5, 10, 5),
                                    bootstyle="primary")
        example_card.pack(fill=tk.X, pady=(0, 10))
        
        formats = [
            "1. 直接输入网址，如：www.google.com",
            "2. 输入品牌名称，如：微信、支付宝等",
            "3. 支持任意中英文名称，系统会自动搜索对应网站"
        ]
        
        for format_text in formats:
            ttk.Label(example_card,
                     text=format_text,
                     font=self.small_font,
                     bootstyle="secondary").pack(anchor=tk.W)
        
        # 图标尺寸选择（使用独立卡片）
        size_card = ttk.Labelframe(left_card, text="图标尺寸", 
                                 padding=(10, 5, 10, 5),
                                 bootstyle="primary")
        size_card.pack(fill=tk.X)
        
        self.size_var = tk.StringVar(value="256")
        sizes = ["64", "128", "256", "512"]
        
        size_frame = ttk.Frame(size_card)
        size_frame.pack(fill=tk.X, pady=5)
        
        for size in sizes:
            rb = ttk.Radiobutton(size_frame, 
                               text=f"{size}x{size}",
                               variable=self.size_var,
                               value=size,
                               bootstyle="primary-toolbutton")
            rb.pack(side=tk.LEFT, padx=5)
            ToolTip(rb, f"选择 {size}x{size} 像素的图标尺寸")
        
        # 创建右侧卡片
        right_card = ttk.Frame(main_frame)
        right_card.grid(row=1, column=1, sticky=(tk.N, tk.W), padx=(10, 0))
        right_card.configure(padding=15)
        
        # 服务选择框架
        services_card = ttk.Labelframe(right_card, text="下载服务选择",
                                     padding=(10, 5, 10, 5),
                                     bootstyle="primary")
        services_card.pack(fill=tk.X)

        # 创建服务选择变量
        self.service_vars = {}
        services = [
            ("全选", "", "选择或取消选择所有下载服务"),
            ("Google Favicon", "需要特殊网络环境", "从Google Favicon服务下载图标（需要特殊网络环境）"),
            ("DuckDuckGo", "国内可用", "从DuckDuckGo下载图标（推荐国内用户使用）"),
            ("Yandex", "国内可用", "从Yandex下载图标（推荐国内用户使用）"),
            ("ico.kucat.cn", "", "从ico.kucat.cn下载图标"),
            ("直接从网站下载", "自动尝试多种路径", "直接从目标网站下载图标（自动尝试多种路径）")
        ]

        # 创建全选按钮和服务选择复选框
        self.select_all_var = tk.BooleanVar(value=True)
        for i, (service, note, tooltip) in enumerate(services):
            if i == 0:  # 全选按钮
                cb = ttk.Checkbutton(services_card, 
                                   text=service,
                                   variable=self.select_all_var,
                                   command=self.toggle_all_services,
                                   bootstyle="primary-round-toggle")
                cb.pack(anchor=tk.W, padx=5, pady=2)
                ToolTip(cb, tooltip)
                continue
                
            var = tk.BooleanVar(value=True)
            self.service_vars[service] = var
            
            service_frame = ttk.Frame(services_card)
            service_frame.pack(anchor=tk.W, padx=5, pady=2)
            
            cb = ttk.Checkbutton(service_frame, 
                               text=service,
                               variable=var,
                               command=self.check_select_all,
                               bootstyle="primary-round-toggle")
            cb.pack(side=tk.LEFT)
            
            if note:
                note_label = ttk.Label(service_frame,
                                     text=f"({note})",
                                     font=self.small_font,
                                     bootstyle="secondary")
                note_label.pack(side=tk.LEFT, padx=(5, 0))
            
            ToolTip(cb, tooltip)
        
        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 10))
        
        self.download_button = ttk.Button(button_frame, 
                                        text="开始下载",
                                        command=self.toggle_download,
                                        bootstyle="success",
                                        width=25)
        self.download_button.pack(side=tk.LEFT)
        ToolTip(self.download_button, "点击开始下载或停止下载")
        
        self.open_folder_button = ttk.Button(button_frame, 
                                           text="打开下载文件夹",
                                           command=self.open_output_folder,
                                           bootstyle="primary",
                                           width=25)
        self.open_folder_button.pack(side=tk.LEFT, padx=(20, 0))
        ToolTip(self.open_folder_button, "打开保存下载图标的文件夹")
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame,
                                      bootstyle="success-striped",
                                      length=900,
                                      mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 输出区域
        output_card = ttk.Labelframe(main_frame, text="下载结果",
                                   padding=(10, 5, 10, 5),
                                   bootstyle="primary")
        output_card.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.output_text = scrolledtext.ScrolledText(output_card, 
                                                   width=80,
                                                   height=12,
                                                   font=self.default_font)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, 
                                    text="就绪",
                                    font=self.small_font,
                                    bootstyle="secondary")
        self.status_label.pack(side=tk.RIGHT)
        
        # 下载器实例
        self.downloader = IconDownloader()
        
        # 配置根窗口的网格权重
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # 配置主框架的网格权重
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 确保窗口可以调整大小
        root.resizable(True, True)
        
        # 设置最小窗口大小
        root.minsize(900, 700)
        
        # 配置请求会话
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        # 添加下载状态控制
        self.is_downloading = False
        self.download_thread = None

    def toggle_download(self):
        """切换下载状态"""
        if not self.is_downloading:
            # 开始新的下载
            names_text = self.input_text.get("1.0", tk.END).strip()
            if not names_text:
                messagebox.showwarning("提示", "请输入至少一个网址或名称！", font=self.default_font)
                return
                
            names = [name.strip() for name in names_text.split('\n') if name.strip()]
            
            # 禁用界面元素
            self.input_text.config(state='disabled')
            self.output_text.delete("1.0", tk.END)
            self.progress['value'] = 0
            
            # 更改按钮状态和文本
            self.download_button.config(text="停止下载")
            self.download_button.configure(bootstyle="danger")
            self.status_label.config(text="下载中...")
            
            # 设置下载状态
            self.is_downloading = True
            
            # 在新线程中执行下载
            self.download_thread = threading.Thread(target=self.download_task, args=(names,))
            self.download_thread.daemon = True
            self.download_thread.start()
        else:
            # 停止当前下载
            self.is_downloading = False
            
            # 恢复界面状态
            self.download_button.config(text="开始下载")
            self.download_button.configure(bootstyle="success")
            self.input_text.config(state='normal')
            self.status_label.config(text="已停止下载")
            
            # 等待线程结束
            if self.download_thread and self.download_thread.is_alive():
                self.download_thread.join(0.1)

    def download_task(self, names):
        total = len(names)
        progress_step = 100.0 / total
        selected_services = self.get_selected_services()
        
        for i, name in enumerate(names):
            # 检查是否停止下载
            if not self.is_downloading:
                self.output_text.insert(tk.END, "\n下载已停止\n")
                self.output_text.see(tk.END)
                return
                
            self.output_text.insert(tk.END, f"\n正在处理 {name}...\n")
            self.output_text.see(tk.END)
            
            # 获取域名
            self.output_text.insert(tk.END, "正在查找域名...\n")
            self.output_text.see(tk.END)
            domain = self.downloader.get_domain_from_name(name)
            
            if not domain:
                self.output_text.insert(tk.END, f"✗ 未找到 {name} 对应的域名，跳过下载\n")
                self.output_text.see(tk.END)
                continue
            
            # 检查是否停止下载
            if not self.is_downloading:
                self.output_text.insert(tk.END, "\n下载已停止\n")
                self.output_text.see(tk.END)
                return
                
            self.output_text.insert(tk.END, f"✓ 已找到域名: {domain}\n")
            self.output_text.see(tk.END)
            
            # 下载图标
            self.output_text.insert(tk.END, "正在从选中的服务下载图标...\n")
            self.output_text.see(tk.END)
            
            size = int(self.size_var.get())
            service_results = []
            
            # 从选中的服务下载
            if "Google Favicon" in selected_services and self.is_downloading:
                result = self.downloader.download_google_favicon(domain, size)
                if result:
                    service_results.append({
                        'service': 'Google Favicon',
                        'filepath': result,
                        'size': size
                    })
            
            # 其他选中的在线服务
            online_services = {
                "DuckDuckGo": f"https://icons.duckduckgo.com/ip3/{domain}.ico",
                "Yandex": f"https://favicon.yandex.net/favicon/{domain}",
                "ico.kucat.cn": f"https://ico.kucat.cn/get.php?url={domain}"
            }
            
            for service_name in selected_services:
                # 检查是否停止下载
                if not self.is_downloading:
                    self.output_text.insert(tk.END, "\n下载已停止\n")
                    self.output_text.see(tk.END)
                    return
                    
                if service_name in online_services:
                    success = False
                    retry_count = 0
                    max_retries = 3
                    
                    while not success and retry_count < max_retries and self.is_downloading:
                        try:
                            response = self.session.get(
                                online_services[service_name],
                                headers=self.downloader.headers,
                                timeout=(5, 15)  # 增加超时时间
                            )
                            if response.status_code == 200:
                                try:
                                    img = Image.open(BytesIO(response.content))
                                    if max(img.size) >= 16:  # 确保图标不是空的
                                        # 获取原始尺寸
                                        original_size = max(img.size)
                                        
                                        # 如果原始尺寸大于目标尺寸，保持原始尺寸
                                        target_size = max(size, original_size)
                                        
                                        filename = f"{self.downloader.clean_filename(domain)}_{service_name}_{target_size}.png"
                                        filepath = os.path.join(self.downloader.output_dir, filename)
                                        
                                        # 只有当原始尺寸小于目标尺寸时才进行放大
                                        if img.size != (target_size, target_size):
                                            img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                                        
                                        # 转换为 RGBA 模式以确保透明度
                                        if img.mode != 'RGBA':
                                            img = img.convert('RGBA')
                                            
                                        img.save(filepath, "PNG")
                                        
                                        service_results.append({
                                            'service': service_name,
                                            'filepath': filepath,
                                            'size': target_size
                                        })
                                        success = True
                                except Exception as e:
                                    self.output_text.insert(tk.END, f"✗ {service_name} 图标处理失败: {str(e)}\n")
                            else:
                                self.output_text.insert(tk.END, f"✗ {service_name} 返回状态码: {response.status_code}\n")
                        except requests.exceptions.Timeout:
                            self.output_text.insert(tk.END, f"✗ {service_name} 请求超时，正在重试...\n")
                        except requests.exceptions.ConnectionError:
                            self.output_text.insert(tk.END, f"✗ {service_name} 连接错误，正在重试...\n")
                        except Exception as e:
                            self.output_text.insert(tk.END, f"✗ {service_name} 下载失败: {str(e)}\n")
                        
                        if not success:
                            retry_count += 1
                            if retry_count < max_retries and self.is_downloading:
                                time.sleep(1)  # 重试前等待1秒
                    
                    if not success:
                        self.output_text.insert(tk.END, f"✗ {service_name} 在 {max_retries} 次尝试后仍然失败\n")
                    
                    self.output_text.see(tk.END)
            
            # 检查是否停止下载
            if not self.is_downloading:
                self.output_text.insert(tk.END, "\n下载已停止\n")
                self.output_text.see(tk.END)
                return
                
            # 直接从网站下载
            if "直接从网站下载" in selected_services and self.is_downloading:
                direct_result = self.downloader.download_direct_favicon(domain)
                if direct_result:
                    service_results.append({
                        'service': '直接从网站下载',
                        'filepath': direct_result,
                        'size': size
                    })
            
            # 更新结果
            if service_results:
                self.output_text.insert(tk.END, "\n下载结果:\n")
                for result in service_results:
                    self.output_text.insert(tk.END, f"✓ 从 {result['service']} 下载的图标已保存: {result['filepath']}\n")
            else:
                self.output_text.insert(tk.END, "✗ 未能从任何选中的服务下载到图标\n")
            
            self.output_text.see(tk.END)
            
            # 更新进度条
            self.progress['value'] = (i + 1) * progress_step
            self.root.update_idletasks()
        
        # 恢复界面状态
        self.is_downloading = False
        self.download_button.config(text="开始下载")
        self.download_button.configure(bootstyle="success")
        self.input_text.config(state='normal')
        self.status_label.config(text="下载完成")
        
        if total > 0:
            messagebox.showinfo("完成", "所有图标下载完成！", font=self.default_font)
        
    def open_output_folder(self):
        output_dir = self.downloader.output_dir
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showerror("错误", "下载文件夹不存在！", font=self.default_font)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip, text=self.text, 
                         justify=tk.LEFT,
                         padding=(5, 3, 5, 3),
                         font=('微软雅黑', 9),
                         bootstyle="secondary")
        label.pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def main():
    root = ttk.Window(themename="litera")
    app = IconDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 