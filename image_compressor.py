import os
import io
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量压缩工具")
        self.root.geometry("550x550")
        # 设置窗口居中
        self.root.eval('tk::PlaceWindow . center')
        
        self.files = []
        self.output_dir = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # --- 1. 文件选择区 ---
        frame_file = ttk.LabelFrame(self.root, text="第一步：选择文件", padding=10)
        frame_file.pack(fill="x", padx=15, pady=10)
        
        ttk.Button(frame_file, text="选择图片", command=self.select_files).pack(side="left")
        self.lbl_file_count = ttk.Label(frame_file, text="未选择任何文件")
        self.lbl_file_count.pack(side="left", padx=10)
        
        # --- 2. 导出设置区 ---
        frame_output = ttk.LabelFrame(self.root, text="第二步：导出设置", padding=10)
        frame_output.pack(fill="x", padx=15, pady=5)
        
        # 导出路径
        ttk.Label(frame_output, text="导出路径:").grid(row=0, column=0, sticky="e", pady=8)
        ttk.Entry(frame_output, textvariable=self.output_dir, width=35).grid(row=0, column=1, padx=5)
        ttk.Button(frame_output, text="浏览...", command=self.select_output_dir).grid(row=0, column=2)
        
        # 文件后缀
        ttk.Label(frame_output, text="自动添加后缀:").grid(row=1, column=0, sticky="e", pady=8)
        self.entry_suffix = ttk.Entry(frame_output, width=15)
        self.entry_suffix.insert(0, "_compressed")
        self.entry_suffix.grid(row=1, column=1, sticky="w", padx=5)
        
        # 导出格式
        ttk.Label(frame_output, text="导出图片格式:").grid(row=2, column=0, sticky="e", pady=8)
        self.combo_format = ttk.Combobox(frame_output, values=["原格式", "JPEG", "PNG", "WEBP"], state="readonly", width=12)
        self.combo_format.current(0)
        self.combo_format.grid(row=2, column=1, sticky="w", padx=5)
        
        # --- 3. 压缩参数区 ---
        frame_limit = ttk.LabelFrame(self.root, text="第三步：限制参数 (留空表示不限制)", padding=10)
        frame_limit.pack(fill="x", padx=15, pady=5)
        
        # 分辨率限制
        ttk.Label(frame_limit, text="最大宽度 (px):").grid(row=0, column=0, sticky="e", pady=5)
        self.entry_width = ttk.Entry(frame_limit, width=15)
        self.entry_width.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(frame_limit, text="(等比例缩放)").grid(row=0, column=2, sticky="w", padx=5)
        
        ttk.Label(frame_limit, text="最大高度 (px):").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_height = ttk.Entry(frame_limit, width=15)
        self.entry_height.grid(row=1, column=1, sticky="w", padx=5)
        
        # 文件大小限制
        ttk.Label(frame_limit, text="最大文件大小 (KB):").grid(row=2, column=0, sticky="e", pady=5)
        self.entry_size = ttk.Entry(frame_limit, width=15)
        self.entry_size.grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(frame_limit, text="(仅对 JPEG/WEBP 有效)").grid(row=2, column=2, sticky="w", padx=5)
        
        # --- 4. 进度及操作区 ---
        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.btn_start = ttk.Button(frame_action, text="开始批量压缩", command=self.start_compression)
        self.btn_start.pack(pady=10)
        
        self.progress = ttk.Progressbar(frame_action, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")
        
        self.lbl_status = ttk.Label(frame_action, text="准备就绪")
        self.lbl_status.pack(pady=5)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择要压缩的图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff")]
        )
        if files:
            self.files = list(files)
            self.lbl_file_count.config(text=f"已选择 {len(self.files)} 张图片")
            # 默认导出路径设为第一张图片所在的目录
            if not self.output_dir.get():
                self.output_dir.set(os.path.dirname(self.files[0]))

    def select_output_dir(self):
        dir_path = filedialog.askdirectory(title="选择导出路径")
        if dir_path:
            self.output_dir.set(dir_path)
            
    def start_compression(self):
        if not self.files:
            messagebox.showwarning("提示", "请先选择需要压缩的图片！")
            return
        if not self.output_dir.get():
            messagebox.showwarning("提示", "请选择导出路径！")
            return
            
        self.btn_start.config(state="disabled")
        self.progress["maximum"] = len(self.files)
        self.progress["value"] = 0
        
        # 使用多线程处理，防止界面卡死
        threading.Thread(target=self.process_images, daemon=True).start()
        
    def process_images(self):
        try:
            max_w = int(self.entry_width.get()) if self.entry_width.get().strip().isdigit() else 0
            max_h = int(self.entry_height.get()) if self.entry_height.get().strip().isdigit() else 0
            max_size_kb = int(self.entry_size.get()) if self.entry_size.get().strip().isdigit() else 0
        except ValueError:
            self.root.after(0, lambda: messagebox.showerror("错误", "限制参数必须为纯数字！"))
            self.root.after(0, lambda: self.btn_start.config(state="normal"))
            return

        suffix = self.entry_suffix.get().strip()
        fmt_selection = self.combo_format.get()
        out_dir = self.output_dir.get()
        
        success_count = 0
        
        for idx, file_path in enumerate(self.files):
            try:
                filename = os.path.basename(file_path)
                self.root.after(0, lambda f=filename: self.lbl_status.config(text=f"正在处理: {f}"))
                
                with Image.open(file_path) as img:
                    # 获取原始格式
                    orig_format = img.format if img.format else "JPEG"
                    
                    # 确定输出格式
                    out_format = orig_format if fmt_selection == "原格式" else fmt_selection
                    
                    # JPEG不支持Alpha通道(透明度)，需要转换
                    if out_format == "JPEG" and img.mode in ("RGBA", "P", "LA"):
                        # 使用白色背景替换透明背景
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "RGBA":
                            background.paste(img, mask=img.split()[3]) # 第4个通道是Alpha
                        else:
                            background.paste(img)
                        img = background
                    elif img.mode == "P" and out_format not in ("PNG", "GIF"):
                        img = img.convert("RGB")
                        
                    # 1. 限制分辨率处理
                    if max_w > 0 or max_h > 0:
                        # 如果其中一个为0，代表该方向不限制，直接取原尺寸
                        target_w = max_w if max_w > 0 else img.width
                        target_h = max_h if max_h > 0 else img.height
                        # thumbnail 方法会按比例缩放，并保证宽和高都不超过给定值
                        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    
                    # 确定输出文件名及扩展名
                    base_name, orig_ext = os.path.splitext(filename)
                    if fmt_selection == "原格式":
                        out_ext = orig_ext
                    else:
                        out_ext = ".jpg" if out_format == "JPEG" else f".{out_format.lower()}"
                        
                    out_name = f"{base_name}{suffix}{out_ext}"
                    out_path = os.path.join(out_dir, out_name)
                    
                    # 2. 限制文件大小处理 (使用二分法查找最优质量)
                    if max_size_kb > 0 and out_format in ('JPEG', 'WEBP'):
                        target_bytes = max_size_kb * 1024
                        low, high = 1, 95
                        best_quality = low
                        best_img_bytes = None
                        
                        while low <= high:
                            mid = (low + high) // 2
                            temp_io = io.BytesIO()
                            img.save(temp_io, format=out_format, quality=mid)
                            size = temp_io.tell()
                            
                            if size <= target_bytes:
                                best_quality = mid
                                best_img_bytes = temp_io.getvalue()
                                low = mid + 1 # 尝试看能不能提高质量
                            else:
                                high = mid - 1 # 文件太大，必须降低质量
                        
                        if best_img_bytes:
                            # 找到了合适的大小，保存
                            with open(out_path, 'wb') as f:
                                f.write(best_img_bytes)
                        else:
                            # 即使是最低质量也超出限制，只能以最低质量保存
                            img.save(out_path, format=out_format, quality=1)
                    else:
                        # 没有大小限制，或者是不支持质量调整的格式(如PNG)
                        if out_format in ('JPEG', 'WEBP'):
                            img.save(out_path, format=out_format, quality=85)
                        else:
                            img.save(out_path, format=out_format, optimize=True)
                            
                success_count += 1
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
                
            self.root.after(0, self.update_progress, idx + 1)
            
        self.root.after(0, lambda: self.finish_processing(success_count, len(self.files)))

    def update_progress(self, val):
        self.progress["value"] = val
        
    def finish_processing(self, success_count, total_count):
        self.lbl_status.config(text=f"处理完成！成功: {success_count}/{total_count}")
        self.btn_start.config(state="normal")
        messagebox.showinfo("处理完成", f"批量压缩完成！\n成功处理 {success_count}/{total_count} 张图片。")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()
