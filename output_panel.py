from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import numpy as np
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams
import time
from typing import List, Dict

from sim_core import SimCore, discrim_detect
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import pandas as pd


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


class OutPutPanel:
    def __init__(self, parent, root):
        self.root = root
        self.parent = parent
        self.have_data = False
        self.sim_core_history_list: List[SimCore] = []
        self.chosen_idx = 0

        self.progress = 0
        # 数据导出面板
        self.data_var = StringVar()
        self.data_dropdown = ttk.Combobox(
            self.parent, textvariable=self.data_var, state="readonly")

        self.data_dropdown['values'] = ['-无数据-']
        self.data_dropdown.grid(row=0, column=0, padx=10, pady=10)
        self.data_dropdown.bind("<<ComboboxSelected>>", self.dropdown_update)
        self.data_dropdown.current(0)
        self.export_button = Button(
            self.parent,
            text="导出",
            command=self.open_export_dialog,
            state=DISABLED,
            width=20
        )
        self.export_button.grid(row=0, column=1,
                                padx=5, pady=5, sticky="ewns")
        for i in range(2):
            self.parent.grid_rowconfigure(i, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

    def dropdown_update(self, event=None):
        selected_data = self.data_var.get()
        if self.have_data:
            chose_idx = selected_data.split(" ")[-1]
            chose_idx = int(chose_idx) - 1
            self.chosen_idx = chose_idx

    def update_state(self, sim_core_history_list: List[SimCore]):
        if sim_core_history_list is None or len(sim_core_history_list) == 0:
            self.data_dropdown['values'] = ['-无数据-']
            self.have_data = False
            self.export_button.config(state=DISABLED)
            self.data_dropdown.current(0)
        else:
            self.sim_core_history_list = sim_core_history_list
            self.have_data = True
            self.export_button.config(state=NORMAL)
            self.data_dropdown['values'] = ['数据 {}'.format(
                i+1) for i in range(len(sim_core_history_list))]
            self.data_dropdown.current(len(sim_core_history_list)-1)
            self.chosen_idx = len(sim_core_history_list)-1

    def open_export_dialog(self):
        file_path = filedialog.asksaveasfilename(
            title="选择保存路径",
            filetypes=[("Excel表格", "*.xlsx"), ]
        )
        if file_path:
            if file_path[-5:] != '.xlsx':
                file_path += '.xlsx'
            chosen_simcore = self.sim_core_history_list[self.chosen_idx]
            wave_form = chosen_simcore.v_patch_amplf
            wave_t = np.arange(len(wave_form), dtype=float) * \
                chosen_simcore.glbSim_dict['dt_samp']

            v_thresh_list = chosen_simcore.v_thresh_list
            v_count_list_list = chosen_simcore.v_disc_count_list

            df_wf = pd.DataFrame({'时间t/s': wave_t, '电压U/V': wave_form})
            v_count_dict = {}
            v_count_dict['阈值 /V'] = v_thresh_list
            for i in range(len(v_count_list_list)):
                v_count_dict['计数{}'.format(i+1)] = v_count_list_list[i]
            idx_list = ['阈值 /V']+['计数{}'.format(_+1)
                                  for _ in range(len(v_count_list_list))]
            df_v_count = pd.DataFrame(v_count_dict, columns=idx_list)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_wf.to_excel(writer, sheet_name='波形', index=False)
                df_v_count.to_excel(writer, sheet_name='甄别计数', index=True)
            print("文件已成功保存到 Excel 文件中")


if __name__ == '__main__':
    glbSim_dict['t_intg'] = 1e-3
    root = Tk()
    root.title("可视化面板")
    root.geometry("600x300")

    sim_history_list = [SimCore() for _ in range(3)]
    for sim in sim_history_list:
        sim.update_param(glbSim_dict, lghtSrc_dict, optfilter_dict,
                         pmt_dict, amplifier_dict, discriminator_dict)
        sim.cal_init(n_step=20)
        sim.run_step()
        sim.run_step()

    output_panel = OutPutPanel(root, root)
    output_panel.update_state(sim_history_list)

    root.mainloop()
