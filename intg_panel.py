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

from sim_core import SimCore
from tooltip import tooltip

# 设置字体，避免字体缺失问题
rcParams['font.sans-serif'] = ['SimHei']  # 使用 SimHei 字体（黑体）
rcParams['axes.unicode_minus'] = False   # 解决负号显示问题

MAX_HISTORY = 10

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

# 积分运算界面


class IntgPanel:
    def __init__(self, parent, root):
        self.root = root
        self.parent = parent
        self.sim_core = None
        self.sim_core_history_list = []

        self.running = False
        self.progress = 0
        
        #新增参数
        self.auto_scan_volt = True
        self.caculation_mode = 0

        
        # 参数设定界面
        self.param_frame = ttk.LabelFrame(parent, text="参数设置")
        self.param_frame.grid(row=0, column=0, columnspan=2,
                              padx=5, pady=5, sticky="ewn")

        ttk.Label(self.param_frame, text="最小电压 V:").grid(
            row=0, column=0, padx=5, pady=5)
        self.vmin_para = ttk.Entry(self.param_frame)
        self.vmin_para.grid(row=0, column=1, padx=5, pady=5)
        self.vmin_para.insert(0, "auto")
        ttk.Label(self.param_frame, text="最大电压 V:").grid(
            row=1, column=0, padx=5, pady=5)
        self.vmax_para = ttk.Entry(self.param_frame)
        self.vmax_para.grid(row=1, column=1, padx=5, pady=5)
        self.vmax_para.insert(0, "auto")
        ttk.Label(self.param_frame, text="采样点数").grid(
            row=2, column=0, padx=5, pady=5)
        self.nv_para = ttk.Entry(self.param_frame)
        self.nv_para.grid(row=2, column=1, padx=5, pady=5)
        self.nv_para.insert(0, "120")
        
        #新增：积分和微分模式选择
        self.mode_select_button = ttk.Button(
            self.param_frame, text="微分模式", command=self.select_mode)
        self.mode_select_button.grid(row=0, rowspan=3, column=2, columnspan=1, padx=5, pady=5, sticky="sne")
        tooltip.create_tooltip(self.mode_select_button, tooltip.preinstall['select_mode'])


        # 开始按钮
        self.start_button = ttk.Button(
            parent, text="开始计算", command=self.start_calculation)
        self.start_button.grid(row=1, column=0, padx=5, pady=5, sticky="ewn")
        # 停止按钮
        self.stop_button = ttk.Button(
            parent, text="停止计算", command=self.stop_calculation_pressed, state="disabled")
        self.stop_button.grid(row=1, column=1, padx=5, pady=5, sticky="ewn")

        # 进度条
        self.progress_bar = ttk.Progressbar(
            parent, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ewn")

        # 日志窗口
        self.log_text = ScrolledText(parent, height=10, state="disabled")
        self.log_text.grid(row=3, column=0, columnspan=2,
                           padx=5, pady=5, sticky="ew")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="blue")
        self.log_text.tag_configure("success", foreground="green")

        # Matplotlib嵌入
        self.figure, self.ax = plt.subplots(figsize=(3, 3))
        self.ax.set_title("动态绘图")
        self.ax.set_xlabel("电压 V")
        self.ax.set_ylabel("计数")
        #self.ax.set_yticks([])
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(
            row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # 设置行列权重，使其可以自适应窗口大小
        for i in range(5):
            parent.grid_rowconfigure(i, weight=1)

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def log(self, message, tag=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def bind_sim_core(self, sim_core: SimCore):
        self.sim_core = sim_core
        self.log("载入参数 成功", "success")
        return

    def start_calculation(self):
        self.running = True
        self.root.event_generate("<<startcal>>")
        self.start_button.config(state="disabled")
        self.log("开始计算", "info")
        self.stop_button.config(state="normal")
        flag, v_range, n_step = self.extract_vrangvn()
        if not flag:
            self.log("参数设置错误，计算停止", "error")
            self.stop_calculation()
            return
        self.sim_core.cal_init(v_range, n_step)
        threading.Thread(target=self.run_async_task,
                         daemon=True).start()

    def stop_calculation_pressed(self):
        self.running = False
        self.log("正在停止...", "info")
        self.stop_calculation()


    def stop_calculation(self):
        self.running = False
        self.start_button.config(state="normal")
        self.log("已成功停止计算", "success")
        self.stop_button.config(state="disabled")
        self.progress_bar["value"] = 0
        self.root.event_generate("<<stopcal>>")

    def extract_vrangvn(self):
        vmin_str = self.vmin_para.get()
        vmax_str = self.vmax_para.get()
        nv_str = self.nv_para.get()
        try:
            nv = int(nv_str)
            if nv <= 0:
                self.log("采样点数必须大于0", "error")
                return False, None, None
        except ValueError:
            self.log("采样点数必须为整数", "error")
            return False, None, None
        try:
            vmin = float(vmin_str)
            vmax = float(vmax_str)
        except ValueError:
            self.log("自动估计电压范围", "info")
            return True, None, nv
            self.auto_scan_volt = True  #新增：将自动扫描模式设为真
            return True, None, nv
        self.log(f"使用用户输入的电压范围: {vmin}V ~ {vmax}V", "info")  #新增：输出手动输入的电压范围
        self.auto_scan_volt = False  #新增：将自动扫描模式设为否
        return True, [vmin, vmax], nv

    async def run_calculation(self):
        self.progress = 0
        self.progress_bar["value"] = 0
        self.log("开始计算...", "info")
        num_iter = self.sim_core.glbSim_dict['n_tStep']
        time_start = time.time()
        i = 0
        num_iter = int(num_iter)
        for i in range(num_iter):
            if not self.running:
                break
            self.ax.clear()  #改动：将clear移至上边        
            self.progress = int((i + 1) / num_iter * 100)
            self.progress_bar["value"] = self.progress
            time_now = time.time()
            time_diff = time_now - time_start
            if time_diff < 60:
                time_str = f"{time_diff:.2f} 秒"
            elif time_diff < 3600:
                minutes = int(time_diff // 60)
                seconds = time_diff % 60
                time_str = f"{minutes} 分 {seconds:.2f} 秒"
            else:
                hours = int(time_diff // 3600)
                minutes = int((time_diff % 3600) // 60)
                seconds = time_diff % 60
                time_str = f"{hours} 时 {minutes} 分 {seconds:.2f} 秒"
            self.log(
                f"计算进度: {self.progress}% ,迭代数: {i+1}/{num_iter},用时: {time_str}", "info")
            self.sim_core.run_step()
            self.sim_core_history_list.append(self.sim_core.copy())
            if len(self.sim_core_history_list) > MAX_HISTORY:
                self.sim_core_history_list.pop(0)
            
            if self.caculation_mode == 0:   #新增：对模式作讨论 
                x_data = self.sim_core.v_thresh_list[:-1]
            else:
                x_data = self.sim_core.v_thresh_list
    
            y_data_list = self.sim_core.v_disc_count_list
            y_data_list = np.array(y_data_list)
            
            if self.caculation_mode == 0:  #新增：对模式作讨论
                y_data = -np.mean(np.diff(y_data_list), axis=0)  #对曲线作微分
                self.ax.plot(x_data, y_data, label="微分曲线")
            else:
                y_data = np.mean(y_data_list, axis=0)
                self.ax.plot(x_data, y_data, label="积分曲线")
                           
            if y_data_list.shape[0] > 1:
                
                if self.caculation_mode == 0:  #新增：对模式作讨论
                    y_data_err = np.std(np.diff(y_data_list, axis=1), axis=0) / \
                        np.sqrt(y_data_list.shape[0]-1)*1.96
                else:
                    y_data_err = np.std(y_data_list, axis=0) / \
                        np.sqrt(y_data_list.shape[0]-1)*1.96

                self.ax.fill_between(
                    x_data, y_data - y_data_err, y_data + y_data_err, alpha=0.4, label="误差范围")
            else:
                self.ax.fill_between(
                    x_data, y_data, y_data, alpha=0.4, label="误差范围")
            self.ax.legend()
            self.ax.set_ylim(0, 1.2 * np.max(y_data))
            self.ax.set_xlabel("电压 V")
            self.ax.set_ylabel("计数")
            #self.ax.set_yticks([])
            self.canvas.draw()
        
        
        if self.running:
            self.stop_calculation()        
        if i == num_iter-1:
            self.log("计算完成", "success")
        if self.auto_scan_volt:  #新增：获取自动扫描电压范围
            v_range = self.sim_core.v_range_auto
            self.log(
                f"自动估计电压范围: {v_range[0]}V ~ {v_range[1]}V", "info")

    def run_async_task(self):
        asyncio.run(self.run_calculation())
    
    #新增：模式选择按钮
    def select_mode(self):
        if self.mode_select_button.cget("text")=='微分模式':
            self.caculation_mode=1
            self.mode_select_button.config(text='积分模式')
            self.log("已将扫描模式更改为积分模式", "success")
        else:
            self.caculation_mode=0
            self.mode_select_button.config(text='微分模式')
            self.log("已将扫描模式更改为微分模式", "success")



if __name__ == '__main__':
    #glbSim_dict['t_intg'] = 1e-3
    root = Tk()
    root.title("计算窗口")
    root.geometry("400x600")
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    # 创建积分运算面板
    intg_panel = IntgPanel(frame, root)

    # 设置行列权重，使其可以自适应窗口大小

    sim_core = SimCore()
    sim_core.update_param(glbSim_dict, lghtSrc_dict, optfilter_dict,
                          pmt_dict, amplifier_dict, discriminator_dict)
    intg_panel.bind_sim_core(sim_core)
    root.event_generate("<<StartCalculation>>", when='tail')

    root.mainloop()
