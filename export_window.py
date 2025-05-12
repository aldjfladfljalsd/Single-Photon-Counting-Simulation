import tkinter as tk
from tkinter import filedialog


def open_export_dialog(selected_sample):
    # 打开文件保存对话框，添加文件类型选项
    file_path = filedialog.asksaveasfilename(
        title=f"保存样本: {selected_sample}",
        filetypes=[
            ("文本文件", "*.txt"),
            ("CSV文件", "*.csv"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
    )
    if file_path:
        print(f"样本 '{selected_sample}' 将保存到: {file_path}")


def main():
    # 创建主窗口
    root = tk.Tk()
    root.title("导出窗口")

    # 样本数据列表
    samples = []  # 假设样本列表为空
    selected_sample = tk.StringVar(
        value="无数据" if not samples else samples[0])  # 默认显示“无数据”
    

    # 创建下拉列表
    if samples:
        dropdown = tk.OptionMenu(root, selected_sample, *samples)
    else:
        dropdown = tk.OptionMenu(root, selected_sample, "无数据")
    dropdown.pack(pady=10)

    # 创建“导出”按钮
    export_button = tk.Button(
        root,
        text="导出",
        command=lambda: open_export_dialog(selected_sample.get()),
        state=tk.NORMAL if samples else tk.DISABLED  # 如果无数据，禁用按钮
    )
    export_button.pack(pady=20)

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
