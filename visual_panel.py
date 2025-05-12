from tkinter import *
from tkinter import ttk
import numpy as np
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams
import time
from typing import List, Dict

from sim_core import SimCore, discrim_detect
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


# 设置字体，避免字体缺失问题
rcParams['font.sans-serif'] = ['SimHei']  # 使用 SimHei 字体（黑体）
rcParams['axes.unicode_minus'] = False   # 解决负号显示问题
# 参数字典
glbSim_dict = {
    't_intg': 1e-3,
    'n_tStep': 20,
    'dt_samp': 0.5e-9,
    'tmper': 293.15
}

optfilter_dict = {
    'trans_rate': 0.1,
}

lghtSrc_dict = {
    'walen': 532e-9,
    'flo_rate': 2.678e9,
}

pmt_dict = {
    'quan_eff': 0.2,
    'secdElctEmis_coef': 6,
    'thermElctEmis_coef': 2e4,
    'surfWork_tmper': 10e2,
    'n_stage': 10,
    'nElct2Vol_coef': 1e-8,
    'use_min_stage': 3,
    'tau_rc': 4e-9,
    'tau_lc': 8e-9,
    'tau_gauss': 0.8e-9,
    'broder_coef': 0.1e-2,
    'noise_rate': 0.4e-3,
}

amplifier_dict = {
    'mgnfc': 100,
    'noise_rate': 0.4e-3,
    'tau_gauss': 0.2e-9,
}

discriminator_dict = {
    'dead_time': 5e-9,
}

# 主视图


class VisualPanel:
    def __init__(self, parent, root, sim_history_list: List[SimCore]):
        self.sim_history_list = sim_history_list

        self.parent = parent
        self.root = root
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky=(N, S, E, W))

        self.frame_flow = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_flow, text="流量")
        self.waveform_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.waveform_frame, text="波形")
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="统计")
        self.flow_panel = FlowPanel(
            self.frame_flow, root, sim_history_list)
        self.flow_panel.init_state()
        self.waveform_panel = WaveFormPanel(
            self.waveform_frame, root, sim_history_list)
        self.waveform_panel.init_state()
        self.stats_panel = StatsPanel(
            self.stats_frame, root, sim_history_list)
        self.stats_panel.init_state()

        self.notebook.grid_rowconfigure(0, weight=1)
        self.notebook.grid_columnconfigure(0, weight=1)
        self.frame_flow.grid_rowconfigure(0, weight=1)
        self.frame_flow.grid_columnconfigure(0, weight=1)
        self.waveform_frame.grid_rowconfigure(0, weight=1)
        self.waveform_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_rowconfigure(0, weight=1)
        self.stats_frame.grid_columnconfigure(0, weight=1)

# 计数流


class FlowPanel:
    def __init__(self, parent, root, sim_history_list: List[SimCore]):
        self.parent = parent
        self.root = root
        self.sim_history_list = sim_history_list

        self.data_var = StringVar()
        self.data_dropdown = ttk.Combobox(
            self.parent, textvariable=self.data_var, state="readonly")
        self.data_dropdown['values'] = ['数据 {}'.format(
            i+1) for i in range(len(sim_history_list))]
        self.data_dropdown.grid(row=0, column=0, padx=10, pady=10)
        self.data_dropdown.bind("<<ComboboxSelected>>", self.dropdown_update)
        self.data_dropdown.current(0)

        # Add slider to select threshold
        self.threshold_var = DoubleVar()
        self.threshold_slider = Scale(self.parent, from_=0, to=1, resolution=0.01,
                                      orient=HORIZONTAL, variable=self.threshold_var, label="甄别器阈值 V")
        self.threshold_slider.grid(row=0, column=1, padx=5, pady=5)
        self.threshold_slider.bind("<Motion>", self.update_plot)

        # Add matplotlib figure
        self.plot_frame = ttk.LabelFrame(self.parent, text="计数流绘图")
        self.plot_frame.grid(row=3, column=0, columnspan=2,
                             padx=10, pady=10, sticky="ew")
        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=BOTH, expand=True)

        # # 悬浮
        # self.tooltip = Label(
        #     self.root, text="", bg="yellow", relief=SOLID, bd=1)
        # self.tooltip.place_forget()
        # self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # 绘图要素复选框
        self.pho_t_var = IntVar(value=1)
        self.the_t_var = IntVar(value=1)
        self.pho_t_eff_var = IntVar(value=1)
        self.trig_t_var = IntVar(value=1)

        self.pho_t_checkbox = Checkbutton(
            self.parent, text="光子计数", variable=self.pho_t_var, command=self.update_plot)
        self.pho_t_checkbox.grid(row=1, column=0, sticky='we', padx=10)

        self.the_t_checkbox = Checkbutton(
            self.parent, text="热电子计数", variable=self.the_t_var, command=self.update_plot)
        self.the_t_checkbox.grid(row=1, column=1, sticky='we', padx=10)

        self.pho_t_eff_checkbox = Checkbutton(
            self.parent, text="有效光子", variable=self.pho_t_eff_var, command=self.update_plot)
        self.pho_t_eff_checkbox.grid(row=2, column=0, sticky='we', padx=10)

        self.trig_t_checkbox = Checkbutton(
            self.parent, text="触发计数", variable=self.trig_t_var, command=self.update_plot)
        self.trig_t_checkbox.grid(row=2, column=1, sticky='we', padx=10)

        # Add matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side=TOP, fill=X)

        for i in range(3):
            self.parent.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.parent.grid_columnconfigure(i, weight=1)

    def init_state(self):
        self.dropdown_update()

    def dropdown_update(self, event=None):
        selected_data = self.data_var.get()
        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        v_patch_temp = self.sim_history_list[chose_idx].v_patch_amplf
        self.threshold_slider.config(from_=np.min(
            v_patch_temp), to=np.max(v_patch_temp), resolution=(np.max(v_patch_temp)-np.min(v_patch_temp))/1000)
        self.threshold_var.set(
            min(np.std(v_patch_temp)*2, np.max(v_patch_temp)))
        self.update_plot(selected_data)

    def update_plot(self, event=None):
        self.ax.clear()
        selected_data = self.data_var.get()
        threshold = self.threshold_var.get()

        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        v_patch_amplf = self.sim_history_list[chose_idx].v_patch_amplf
        pho_t = self.sim_history_list[chose_idx].pho_t
        the_t = self.sim_history_list[chose_idx].the_t
        pho_t_eff = self.sim_history_list[chose_idx].pho_t_eff
        idx_v_res = discrim_detect(
            v_patch_amplf, threshold, self.sim_history_list[chose_idx].discriminator_dict, self.sim_history_list[chose_idx].glbSim_dict)
        trig_t = idx_v_res * \
            self.sim_history_list[chose_idx].glbSim_dict['dt_samp']
        t_span = self.sim_history_list[chose_idx].glbSim_dict['t_intg'] / \
            self.sim_history_list[chose_idx].glbSim_dict['n_tStep']
        dt_samp = self.sim_history_list[chose_idx].glbSim_dict['dt_samp']

        if selected_data:

            # Update plot based on checkbox states
            if self.pho_t_var.get():
                self.ax.plot(pho_t, np.arange(len(pho_t)), label="光子计数")
            if self.the_t_var.get():
                self.ax.plot(the_t, np.arange(len(the_t)), label="热电子计数")
            if self.pho_t_eff_var.get():
                self.ax.plot(pho_t_eff, np.arange(
                    len(pho_t_eff)), label="有效光子计数")
            if self.trig_t_var.get():
                self.ax.plot(trig_t, np.arange(len(trig_t)), label="触发计数")
            self.ax.legend()

        self.ax.set_title("计数流")
        self.ax.set_xlabel("时间 ns")

        self.ax.set_ylabel("计数")
        self.canvas.draw()

    def on_hover(self, event):
        if event.inaxes == self.ax:
            for x, y in zip(self.x_data, self.y_data):
                if abs(event.xdata - x) < 0.2 and abs(event.ydata - y) < 2:
                    self.tooltip.config(text=f"({x}, {y})")
                    self.tooltip.place(x=event.guiEvent.x,
                                       y=event.guiEvent.y - 20)
                    return
        self.tooltip.place_forget()

# 波形图


class WaveFormPanel:
    def __init__(self, parent, root, sim_history_list: List[SimCore]):
        self.parent = parent
        self.root = root
        self.sim_history_list = sim_history_list

        self.data_var = StringVar()
        self.data_dropdown = ttk.Combobox(
            self.parent, textvariable=self.data_var, state="readonly")
        self.data_dropdown['values'] = ['数据 {}'.format(
            i+1) for i in range(len(sim_history_list))]
        self.data_dropdown.grid(row=0, column=0, padx=10, pady=10)
        self.data_dropdown.bind("<<ComboboxSelected>>", self.dropdown_update)
        self.data_dropdown.current(0)

        self.threshold_var = DoubleVar()
        self.threshold_slider = Scale(self.parent, from_=0, to=1, resolution=0.01,
                                      orient=HORIZONTAL, variable=self.threshold_var, label="甄别器阈值 V")
        self.threshold_slider.grid(row=0, column=1, padx=10, pady=10)
        # self.threshold_slider.bind("<Motion>", self.update_plot)

        # Add matplotlib figure
        self.plot_frame = ttk.LabelFrame(self.parent, text="数据波形")
        self.plot_frame.grid(row=4, column=0, columnspan=2,
                             padx=10, pady=10, sticky="ew")
        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=BOTH, expand=True)
        # 绘图要素复选框

        self.pho_t_eff_var = IntVar(value=1)
        self.trig_t_var = IntVar(value=1)
        self.v_thresh_var = IntVar(value=1)
        self.dead_t_var = IntVar(value=1)
        self.plt_legend_var = IntVar(value=1)       #新增：添加显示图标可选项变量


        self.pho_t_eff_checkbox = Checkbutton(
            self.parent, text="有效光子", variable=self.pho_t_eff_var)
        self.pho_t_eff_checkbox.grid(row=1, column=0, sticky='we', padx=10)

        self.trig_t_checkbox = Checkbutton(
            self.parent, text="触发点", variable=self.trig_t_var)
        self.trig_t_checkbox.grid(row=1, column=1, sticky='we', padx=10)

        self.dead_t_checkbox = Checkbutton(
            self.parent, text="死时间", variable=self.dead_t_var)
        self.dead_t_checkbox.grid(row=2, column=0, sticky='we', padx=10)

        self.v_thresh_checkbox = Checkbutton(
            self.parent, text="波形", variable=self.v_thresh_var)
        self.v_thresh_checkbox.grid(row=2, column=1, sticky='we', padx=10)

        # Add matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side=TOP, fill=X)

        # 添加绘图按钮
        self.update_button = ttk.Button(
            self.parent, text="更新绘图", command=self.update_plot)
        self.update_button.grid(
            row=3, column=0, padx=10, columnspan=2)

        for i in range(4):
            self.parent.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.parent.grid_columnconfigure(i, weight=1)
        
        '''
        # 新增：添加显示图标可选项
        self.plt_legend_checkbox = Checkbutton(
            self.parent, text="显示图标", variable=self.plt_legend_var)
        self.plt_legend_checkbox.grid(row=3, column=0, sticky='we', padx=10)
        '''

    def init_state(self):
        self.dropdown_update()

    def dropdown_update(self, event=None):
        selected_data = self.data_var.get()
        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        v_patch_temp = self.sim_history_list[chose_idx].v_patch_amplf
        self.threshold_slider.config(from_=np.min(
            v_patch_temp), to=np.max(v_patch_temp), resolution=(np.max(v_patch_temp)-np.min(v_patch_temp))/1000)
        self.threshold_var.set(
            min(np.std(v_patch_temp)*2, np.max(v_patch_temp)))

    def update_plot(self, event=None):
        self.ax.clear()
        selected_data = self.data_var.get()
        threshold = self.threshold_var.get()

        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        v_patch_amplf = self.sim_history_list[chose_idx].v_patch_amplf
        pho_t_eff = self.sim_history_list[chose_idx].pho_t_eff
        idx_v_res = discrim_detect(
            v_patch_amplf, threshold, self.sim_history_list[chose_idx].discriminator_dict, self.sim_history_list[chose_idx].glbSim_dict)
        trig_t = idx_v_res * \
            self.sim_history_list[chose_idx].glbSim_dict['dt_samp']
        dead_t = self.sim_history_list[chose_idx].discriminator_dict['dead_time']
        dt_samp = self.sim_history_list[chose_idx].glbSim_dict['dt_samp']

        if selected_data:

            self.ax.plot(np.arange(len(v_patch_amplf))*dt_samp,
                         v_patch_amplf, lw=1, label="波形")
            if self.dead_t_var.get():
                for idx_temp, trig_t_temp in enumerate(trig_t):
                    if idx_temp == 0:
                        self.ax.axvspan(trig_t_temp, trig_t_temp+dead_t,
                                        color='yellow', alpha=0.5, label="死时间")
                    else:
                        self.ax.axvspan(trig_t_temp, trig_t_temp+dead_t,
                                        color='yellow', alpha=0.5)
            if self.pho_t_eff_var.get():

                self.ax.vlines(
                    pho_t_eff, 0, np.max(v_patch_amplf), alpha=0.4, lw=0.8, color='red', label="有效光子")

            if self.trig_t_var.get():
                if len(trig_t) > 0:
                    self.ax.plot(
                        trig_t, v_patch_amplf[idx_v_res], 'x', ms=6, color='green', label="触发点")
            if self.v_thresh_var.get():
                self.ax.axhline(y=threshold, color='black',
                                alpha=0.8, label="阈值")    #这边改了一点

            self.ax.legend()

        self.ax.set_title("波形图")
        self.ax.set_xlabel("时间 ns")

        self.ax.set_ylabel("计数")
        self.canvas.draw()

# 统计图


class StatsPanel:
    def __init__(self, parent, root, sim_history_list: List[SimCore]):
        self.parent = parent
        self.root = root
        self.sim_history_list = sim_history_list

        self.data_var = StringVar()
        self.data_dropdown = ttk.Combobox(
            self.parent, textvariable=self.data_var, state="readonly")
        self.data_dropdown['values'] = ['数据 {}'.format(
            i+1) for i in range(len(sim_history_list))]
        self.data_dropdown.grid(row=0, column=0, padx=10, pady=10)
        self.data_dropdown.bind("<<ComboboxSelected>>", self.dropdown_update)
        self.data_dropdown.current(len(sim_history_list)-1)

        self.plot_frame_diff = ttk.LabelFrame(self.parent, text="差分曲线")
        self.plot_frame_diff.grid(row=1, column=0,
                                  padx=10, pady=10, sticky="ew")
        self.figure_diff, self.ax_diff = plt.subplots(figsize=(5, 2.5))
        self.canvas_diff = FigureCanvasTkAgg(
            self.figure_diff, master=self.plot_frame_diff)
        self.canvas_widget_diff = self.canvas_diff.get_tk_widget()
        self.canvas_widget_diff.pack(fill=BOTH, expand=True)

        self.plot_frame_intg = ttk.LabelFrame(self.parent, text="积分曲线")
        self.plot_frame_intg.grid(row=2, column=0,
                                  padx=10, pady=10, sticky="ew")
        self.figure_intg, self.ax_intg = plt.subplots(figsize=(5, 2.5))
        self.canvas_intg = FigureCanvasTkAgg(
            self.figure_intg, master=self.plot_frame_intg)
        self.canvas_widget_intg = self.canvas_intg.get_tk_widget()
        self.canvas_widget_intg.pack(fill=BOTH, expand=True)

        # Add matplotlib toolbar
        self.toolbar_diff = NavigationToolbar2Tk(
            self.canvas_diff, self.plot_frame_diff)
        self.toolbar_diff.update()
        self.toolbar_diff.pack(side=TOP, fill=X)
        # Add matplotlib toolbar
        self.toolbar_intg = NavigationToolbar2Tk(
            self.canvas_intg, self.plot_frame_intg)
        self.toolbar_intg.update()
        self.toolbar_intg.pack(side=TOP, fill=X)

        for i in range(3):
            self.parent.grid_rowconfigure(i, weight=1)
        parent.grid_rowconfigure(0, weight=1)

    def init_state(self):
        self.dropdown_update()

    def dropdown_update(self, event=None):
        selected_data = self.data_var.get()
        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        self.update_plot()

    def update_plot(self, event=None):
        self.ax_diff.clear()
        self.ax_intg.clear()
        selected_data = self.data_var.get()
        chose_idx = selected_data.split(" ")[-1]
        chose_idx = int(chose_idx) - 1
        v_thresh_list = self.sim_history_list[chose_idx].v_thresh_list
        v_disc_count_list = np.array(
            self.sim_history_list[chose_idx].v_disc_count_list)
        v_count_mean = np.mean(v_disc_count_list, axis=0)
        v_diff_mean = np.mean(-np.diff(v_disc_count_list, axis=1), axis=0)

        if selected_data:
            self.ax_diff.plot(
                v_thresh_list[1:], v_diff_mean, label="差分曲线", color='blue', lw=1.5)
            ylim_diff = self.ax_diff.get_ylim()
            self.ax_diff.set_ylim((0, ylim_diff[1]))
            self.ax_intg.plot(v_thresh_list, v_count_mean,
                              label='积分曲线', color='blue', lw=1.5)
            if len(v_disc_count_list) > 1:
                v_count_err = np.std(v_disc_count_list, axis=0) / \
                    np.sqrt(len(v_disc_count_list)-1)
                v_diff_err = np.std(
                    np.diff(v_disc_count_list, axis=1), axis=0)/np.sqrt(len(v_disc_count_list)-1)
                self.ax_diff.fill_between(
                    v_thresh_list[1:], v_diff_mean-v_diff_err, v_diff_mean+v_diff_err, color='blue', alpha=0.4, label='差分曲线误差')
                self.ax_intg.fill_between(v_thresh_list, v_count_mean-v_count_err,
                                          v_count_mean+v_count_err, color='blue', alpha=0.4, label='积分曲线误差')
        self.ax_diff.legend()
        self.ax_intg.legend()
        self.canvas_diff.draw()
        self.canvas_intg.draw()


if __name__ == '__main__':
    glbSim_dict['t_intg'] = 1e-3
    root = Tk()
    root.title("可视化面板")
    root.geometry("500x600")

    # 创建模拟数据
    sim_history_list = [SimCore() for _ in range(3)]
    for sim in sim_history_list:
        sim.update_param(glbSim_dict, lghtSrc_dict, optfilter_dict,
                         pmt_dict, amplifier_dict, discriminator_dict)
        sim.cal_init(n_step=20)
        sim.run_step()
        sim.run_step()

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    visual_panel = VisualPanel(root, root, sim_history_list)
    visual_panel.flow_panel.init_state()

    root.mainloop()
