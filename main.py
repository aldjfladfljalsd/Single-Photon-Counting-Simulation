from tkinter import *
from tkinter import ttk
import numpy as np
from tkinter.scrolledtext import ScrolledText
import asyncio
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams
import time
from typing import List, Dict
import os
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from sim_core import SimCore, discrim_detect
from visual_panel import VisualPanel
from intg_panel import IntgPanel
from para_panel import ParaPanel, paraDictSaver, pack_data_solver_list
from para_preset import para_dict_list_list_pre
from output_panel import OutPutPanel

# 设置字体，避免字体缺失问题
rcParams['font.sans-serif'] = ['SimHei']  # 使用 SimHei 字体（黑体）
rcParams['axes.unicode_minus'] = False   # 解决负号显示问题


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        # 仿真核心
        self.sim_core = SimCore()
        self.sim_core_hist_list = []

        # 界面分块
        self.para_frame = ttk.Frame(self.root)
        self.para_frame.grid(column=0, row=1, sticky=(
            N, W, E, S), padx=5, pady=5)
        self.operate_frame = ttk.Frame(self.root)
        self.operate_frame.grid(column=0, row=0, sticky=(
            N, W, E, S), padx=5, pady=5)

        # 初始选择第一个参数预设方案
        data_saver_list = pack_data_solver_list(para_dict_list_list_pre[0])
        self.para_setting_module = ParaPanel(
            self.para_frame, self.root, data_saver_list)
        self.para_frame.grid_rowconfigure(0, weight=1)
        self.para_frame.grid_rowconfigure(1, weight=1)
        self.para_frame.grid_columnconfigure(0, weight=1)

        # 操作界面
        #新增：标题
        self.title_label = ttk.Label(self.operate_frame, text='单光子计数虚拟仿真程序   (∠・ω< )⌒☆', font=('等线', 15, 'bold'))
        self.title_label.grid(
            row=0, column=0, columnspan=3, sticky='ewn', padx=10, pady=10)
        # 下拉菜单
        self.data_var = StringVar()
        self.data_dropdown = ttk.Combobox(
            self.operate_frame, textvariable=self.data_var, state="readonly")
        self.data_dropdown['values'] = ['预设参数 {}'.format(
            i+1) for i in range(len(para_dict_list_list_pre))]
        self.data_dropdown.grid(row=1, column=0, padx=10, pady=10, sticky='esw')
        self.data_dropdown.bind("<<ComboboxSelected>>", self.dropdown_update)
        self.data_dropdown.current(0)
        # 计算界面
        self.button_open_intg = ttk.Button(
            self.operate_frame, text="计算界面", command=self.toggle_open_intg)
        self.button_open_intg.grid(
            column=1, row=1, sticky='esw', padx=10, pady=10)
        self.intg_window = None
        self.intg_module = None
        # 检视界面
        self.button_open_visual = ttk.Button(
            self.operate_frame, text="可视化界面", command=self.toggle_open_visual)
        self.button_open_visual.config(state='disable')
        self.button_open_visual.grid(
            column=2, row=1, sticky='esw', padx=10, pady=10)
        self.visual_window = None
        self.visual_module = None
        # 保存界面
        self.data_save_frame = ttk.LabelFrame(self.operate_frame, text='数据保存')
        self.data_save_frame.grid(column=3, row=0, rowspan=2, sticky=(
            N, W, E, S), padx=5, pady=5)
        self.data_save_module = OutPutPanel(self.data_save_frame, self.root)

        self.operate_frame.grid_rowconfigure(0, weight=1)
        for i in range(4):
            self.operate_frame.grid_columnconfigure(i, weight=1)

        self.root.bind('<<startcal>>', self.cope_with_start)
        self.root.bind('<<stopcal>>', self.cope_with_stop)
        self.root.bind('<<para_reset>>', self.cope_with_reset)

    def dropdown_update(self, event=None):
        selected_data = self.data_var.get()
        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1

        selected_data = para_dict_list_list_pre[chose_idx]
        self.para_setting_module.update_all_paras_bylist(
            selected_data)

        root.event_generate("<<para_reset>>")

    def toggle_open_intg(self):
        sub_window = self.intg_window
        button = self.button_open_intg
        if sub_window is not None and Toplevel.winfo_exists(sub_window):
            sub_window.destroy()
            sub_window = None
            self.root.event_generate("<<stopcal>>") #新增：关闭页面时自动停止计算
            if self.intg_module is not None:
                self.sim_core_hist_list = self.intg_module.sim_core_history_list
                self.sim_core = self.intg_module.sim_core
                del self.intg_module
                self.intg_module = None
            button.config(text="计算界面")
        else:
            button.config(text="关闭计算界面")
            sub_window = Toplevel(self.root)
            sub_window.title("计算界面")
            sub_window.geometry("400x650")
            sub_window.resizable(0,0)
            #frame_temp = ttk.Frame(sub_window)
            #frame_temp.grid(row=0, column=0, padx=10, pady=10, sticky='nesw')
            para_dict_list_temp = self.para_setting_module.get_para_dict_list()
            self.sim_core.update_param(*para_dict_list_temp)
            self.intg_module = IntgPanel(sub_window, self.root)  #修改：intgPanel直接套在subwindow上而不先建Frame
            self.intg_module.bind_sim_core(self.sim_core)
            sub_window.protocol("WM_DELETE_WINDOW", self.toggle_open_intg)
        self.intg_window = sub_window

    def toggle_open_visual(self):
        sub_window = self.visual_window
        button = self.button_open_visual
        if sub_window is not None and Toplevel.winfo_exists(sub_window):
            sub_window.destroy()
            sub_window = None
            if self.visual_module is not None:
                del self.visual_module
                self.visual_module = None
            button.config(text="可视化界面")
        else:
            button.config(text="关闭可视化界面")
            sub_window = Toplevel(self.root)
            sub_window.title("可视化界面")
            sub_window.geometry("450x650")
            sub_window.resizable(0,0)
            #frame_temp = ttk.Frame(sub_window)
            #frame_temp.grid(row=0, column=0, padx=10, pady=10)
            sub_window.grid_rowconfigure(0, weight=1)
            sub_window.grid_columnconfigure(0, weight=1)
            self.visual_module = VisualPanel(
                sub_window, sub_window, self.sim_core_hist_list)  #修改：同intg_panel
            self.visual_module.flow_panel.init_state()
            sub_window.protocol("WM_DELETE_WINDOW", self.toggle_open_visual)
        self.visual_window = sub_window

    def cope_with_start(self, event):
        if self.para_setting_module.button_glbsim_setting.cget("text")[0] == '关':
            self.para_setting_module.button_glbsim_setting.invoke()
        if self.para_setting_module.button_light_src_setting.cget("text")[0] == '关':
            self.para_setting_module.button_light_src_setting.invoke()
        if self.para_setting_module.button_filter_setting.cget("text")[0] == '关':
            self.para_setting_module.button_filter_setting.invoke()
        if self.para_setting_module.button_pmt_setting.cget("text")[0] == '关':
            self.para_setting_module.button_pmt_setting.invoke()
        if self.para_setting_module.button_amplifier_setting.cget("text")[0] == '关':
            self.para_setting_module.button_amplifier_setting.invoke()
        if self.para_setting_module.button_discriminator_setting.cget("text")[0] == '关':
            self.para_setting_module.button_discriminator_setting.invoke()
        self.para_setting_module.button_glbsim_setting.config(state="disabled")
        self.para_setting_module.button_light_src_setting.config(
            state="disabled")
        self.para_setting_module.button_filter_setting.config(state="disabled")
        self.para_setting_module.button_pmt_setting.config(state="disabled")
        self.para_setting_module.button_amplifier_setting.config(
            state="disabled")
        self.para_setting_module.button_discriminator_setting.config(
            state="disabled")
        if self.button_open_visual.cget("text")[0] == '关':
            self.toggle_open_visual()
        self.button_open_visual.config(state='disable')
        self.data_dropdown.config(state='disable')
        self.data_save_module.update_state([])

    def cope_with_stop(self, event):
        self.para_setting_module.button_glbsim_setting.config(state="normal")
        self.para_setting_module.button_light_src_setting.config(
            state="normal")
        self.para_setting_module.button_filter_setting.config(state="normal")
        self.para_setting_module.button_pmt_setting.config(state="normal")
        self.para_setting_module.button_amplifier_setting.config(
            state="normal")
        self.para_setting_module.button_discriminator_setting.config(
            state="normal")
        self.data_dropdown.config(state='normal')
        if self.sim_core.has_result:
            self.button_open_visual.config(state='normal')
            self.sim_core_hist_list = self.intg_module.sim_core_history_list
            self.sim_core = self.intg_module.sim_core
            self.data_save_module.update_state(self.sim_core_hist_list)

    def cope_with_reset(self, event):
        if self.button_open_intg.cget("text")[0] == '关':
            self.button_open_intg.invoke()
        if self.button_open_visual.cget("text")[0] == '关':
            self.button_open_visual.invoke()

        self.sim_core.update_param(
            *self.para_setting_module.get_para_dict_list())
        self.sim_core.has_result = False
        self.sim_core_hist_list = []
        self.button_open_visual.config(state='disable')
        self.data_save_module.update_state(self.sim_core_hist_list)


def print_widget_tree(widget, indent=0):
    print(' ' * indent + str(widget))
    for child in widget.winfo_children():
        print_widget_tree(child, indent + 4)


if __name__ == '__main__':
    root = Tk()
    root.title("近代物理实验-研究性课题-单光子计数仿真程序-14组")
    root.geometry('1000x500')
    root.resizable(0,0)  #新增：固定窗口大小


    def on_closing():
        # print_widget_tree(root)
        root.destroy()
        root.quit()
        os._exit(0)

    main_window = MainWindow(root)

    #root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()
