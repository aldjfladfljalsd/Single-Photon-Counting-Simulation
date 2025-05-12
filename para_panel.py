from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import os
import numpy as np

from sim_core import SimCore

import sys

path_this_file = os.path.realpath(sys.argv[0])
path_this_dir = os.path.dirname(path_this_file)
path_png_samp = os.path.join(path_this_dir, "png_samp")
png_path_list = os.listdir(path_png_samp)
'''
png_path_list = [os.path.join(path_png_samp, png) for png in png_path_list]
png_path_list = [png for png in png_path_list if png.endswith(".png")]
'''
png_path_list = [os.path.join(path_png_samp, png) for png in png_path_list]
png_path_list = [png for png in png_path_list]



# 参数设定
sub_wind_size = (300, 100)  #详情见sub_window.geometry
default_img_size = (150, 150)  #新增：默认图片大小变量
sub_wind_img_size = (250, 250)  #新增：窗口图片大小变量
padding_root_sub = "5 5 12 12"


glbSim_dict = {
    't_intg': 1e-1,
    'n_tStep': 20,
    'dt_samp': 0.5e-9,
    'tmper': 293.15
}
info_glbSim = ['积分时间 s', '迭代次数', '采样间隔 s', '温度 K']
key_glbSim = ['t_intg', 'n_tStep', 'dt_samp', 'tmper']

optfilter_dict = {
    'trans_rate': 0.1,
}
info_optfilter = ['透过率']
key_optfilter = ['trans_rate']

lghtSrc_dict = {
    'walen': 532e-9,
    'flo_rate': 2.678e9,
}
info_lghtSrc = ['波长 m', '频率 Hz']
key_lghtSrc = ['walen', 'flo_rate']

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
info_pmt = ['量子效率', '二次电子发射系数', '热电子发射系数', '表面功函数 eV',
            '倍增管级数', '每电子产生的电压 V', '最小级数(热中子)', 'RC时间常数 s',
            'LC时间常数 s', '高斯时间常数 s', '边界延拓 100%', '噪声率']
key_pmt = ['quan_eff', 'secdElctEmis_coef', 'thermElctEmis_coef',
           'surfWork_tmper', 'n_stage', 'nElct2Vol_coef', 'use_min_stage',
           'tau_rc', 'tau_lc', 'tau_gauss', 'broder_coef', 'noise_rate']

amplifier_dict = {
    'mgnfc': 100,
    'noise_rate': 0.4e-3,
    'tau_gauss': 0.2e-9,
}
info_amplifier = ['放大倍数', '噪声率', '高斯时间常数 s']
key_amplifier = ['mgnfc', 'noise_rate', 'tau_gauss']

discriminator_dict = {
    'dead_time': 5e-9,
}
info_discriminator = ['死时间 s']
key_discriminator = ['dead_time']


class paraDictSaver:
    def __init__(self, info_para, key_para, para_dict):
        self.para_dict = para_dict
        self.info_para = info_para
        self.key_para = key_para


glbSim_saver = paraDictSaver(info_glbSim, key_glbSim, glbSim_dict)
lghtSrc_saver = paraDictSaver(info_lghtSrc, key_lghtSrc, lghtSrc_dict)
optfilter_saver = paraDictSaver(
    info_optfilter, key_optfilter, optfilter_dict)
pmt_saver = paraDictSaver(info_pmt, key_pmt, pmt_dict)
amplifier_saver = paraDictSaver(
    info_amplifier, key_amplifier, amplifier_dict)
discriminator_saver = paraDictSaver(
    info_discriminator, key_discriminator, discriminator_dict)


def pack_data_solver_list(para_dict_list):
    glbSim_saver = paraDictSaver(info_glbSim, key_glbSim, para_dict_list[0])
    lghtSrc_saver = paraDictSaver(info_lghtSrc, key_lghtSrc, para_dict_list[1])
    optfilter_saver = paraDictSaver(
        info_optfilter, key_optfilter, para_dict_list[2])
    pmt_saver = paraDictSaver(info_pmt, key_pmt, para_dict_list[3])
    amplifier_saver = paraDictSaver(
        info_amplifier, key_amplifier, para_dict_list[4])
    discriminator_saver = paraDictSaver(
        info_discriminator, key_discriminator, para_dict_list[5])
    data_solver_list = [glbSim_saver, lghtSrc_saver, optfilter_saver,
                        pmt_saver, amplifier_saver, discriminator_saver]
    return data_solver_list


# 载入图片


def load_image(idx_img_temp=None, size=None):
    if idx_img_temp is None:
        idx_img_temp = np.random.randint(len(png_path_list))#随机图片
    original_image = Image.open(png_path_list[idx_img_temp])
    '''
    aspect_ratio = original_image.height / original_image.width
    new_height = int(100 * aspect_ratio)
    resized_image = original_image.resize(
        (100, new_height), Image.Resampling.LANCZOS)
    
    if new_height > 50:
        top = (new_height - 100) // 2
        bottom = top + 100
        resized_image = resized_image.crop((0, top, 100, bottom))
    '''

    resized_image = original_image.resize(default_img_size if size==None else size)
    photo = ImageTk.PhotoImage(resized_image)

    return photo


# 参数设定子窗口界面


def draw_setting_frame(parent_frame, root, data_saver: paraDictSaver, img_id = None):  #新增：固定图片
    setting_frame = ttk.Frame(parent_frame, padding=3)
    setting_frame.grid(column=0, row=0)

    img_temp = load_image(img_id, sub_wind_img_size)
    image_ = ttk.Label(setting_frame, image=img_temp)
    image_.image = img_temp
    image_.padx = (sub_wind_size[0]-sub_wind_img_size[0])/2  #新增：使图片居中
    image_.grid(column=0, row=0, columnspan=1, padx=image_.padx, pady=10, sticky=(N, W, E, S))

    canvas = Canvas(setting_frame, width=270, height=1000)
    #scrollbar = ttk.Scrollbar(
     #   setting_frame, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    #canvas.configure(yscrollcommand=scrollbar.set)
    '''
    def _on_mouse_wheel(event):
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
    '''
    canvas.grid(column=0, row=2,columnspan=1, sticky=(N, W, E, S))
    #scrollbar.grid(column=1, row=2, sticky=(N, S))

    key_para_list = data_saver.key_para
    para_init_dict = data_saver.para_dict
    info_lghtSrc = data_saver.info_para

    def read_all_parameters():
        para_dict_new = {}
        for i, key in enumerate(key_para_list):
            entry_widget = scrollable_frame.grid_slaves(row=i, column=1)[0]
            para_dict_new[key] = entry_widget.get()
            try:
                para_dict_new[key] = int(para_dict_new[key])
            except ValueError:
                try:
                    para_dict_new[key] = float(para_dict_new[key])
                except ValueError:
                    para_dict_new[key] = str(para_dict_new[key])
        for key in para_dict_new.keys():
            print('reset data')
            print(f"{key}: {para_dict_new[key]}")
        data_saver.para_dict = para_dict_new
        root.event_generate("<<para_reset>>")

    button_read_params = ttk.Button(
        setting_frame, text="应用参数", command=read_all_parameters)
    button_read_params.grid(column=0, row=1, columnspan=1, pady=5)

    for i in range(len(info_lghtSrc)):  # Example: Adding 20 labels
        ttk.Label(scrollable_frame,
                  text=f"{info_lghtSrc[i]}").grid(column=0, row=i, padx=5, pady=5)
        entry = ttk.Entry(scrollable_frame)
        entry.grid(column=1, row=i, padx=5, pady=5)
        entry.insert(0, para_init_dict[key_para_list[i]])

    # Configure the parent frame to expand and include the scrollbar
    setting_frame.columnconfigure(0, weight=1)
    setting_frame.rowconfigure(0, weight=1)

    return setting_frame


# 悬浮参数显示


def create_tooltip(widget, data_saver: paraDictSaver):
    tooltip = None

    def show_tooltip(event):
        text = ""
        for i in range(len(data_saver.info_para)):
            value = data_saver.para_dict[data_saver.key_para[i]]
            if isinstance(value, (float, int)) and abs(value) >= 1e4 or abs(value) < 1e-3:
                text += f"{data_saver.info_para[i]}: {value:.3e}\n"
            else:
                text += f"{data_saver.info_para[i]}: {value}\n"
        text = text[:-1]
        nonlocal tooltip
        if tooltip is None and widget.cget("text")[0] != '关':
            tooltip = Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = Label(tooltip, text=text, background="yellow",
                          relief="solid", borderwidth=1, font=("Arial", 10))
            label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip is not None:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


class ParaPanel:
    def __init__(self, frame, root, data_saver_list):
        # 载入数据
        self.glbSim_saver = data_saver_list[0]
        self.lghtSrc_saver = data_saver_list[1]
        self.optfilter_saver = data_saver_list[2]
        self.pmt_saver = data_saver_list[3]
        self.amplifier_saver = data_saver_list[4]
        self.discriminator_saver = data_saver_list[5]

        self.sub_window = {'积分': None, '光源': None,
                           '滤光器': None, '光电倍增管': None, '放大器': None, '甄别器': None}

        # 窗口创建
        self.frame = frame
        self.root = root
        self.lf_paras = ttk.LabelFrame(
            self.frame, text='参数设定', padding=padding_root_sub)
        self.lf_paras.grid(column=0, row=0, sticky=(
            N, W, E, S), padx=5, pady=5)
        self.lf_device = ttk.LabelFrame(
            self.lf_paras, text="装置", padding=padding_root_sub)
        self.lf_device.grid(column=0, row=0, sticky=(
            N, W, E, S), padx=5, pady=5)
        self.lf_glb = ttk.LabelFrame(
            self.lf_paras, text="全局参数", padding=padding_root_sub)
        self.lf_glb.grid(column=0, row=1, sticky=(N, W, E, S), padx=5, pady=5)

        for i in range(2):
            self.lf_paras.grid_columnconfigure(i, weight=1)
        self.lf_paras.grid_rowconfigure(0, weight=1)
        self.lf_glb.grid_columnconfigure(0, weight=1)
        self.lf_glb.grid_rowconfigure(1, weight=1)

        # 全局积分参数
        self.button_glbsim_setting = ttk.Button(
            self.lf_glb, text="设定")
        glbsim_handle = self.get_toggle_handle(
            self.button_glbsim_setting, "积分", self.glbSim_saver, 5)
        self.button_glbsim_setting.configure(command=glbsim_handle)
        self.button_glbsim_setting.grid(column=0, row=1, sticky=(N, W, E, S))

        # 各个窗口添加元件  #新增：固定图片
        # 设定光源按钮
        lf_light_src = ttk.LabelFrame(
            self.lf_device, text="光源", padding=padding_root_sub)
        lf_light_src.grid(column=0, row=0, sticky=(N, W, E, S))
        img_temp = load_image(0)
        image_light_src = ttk.Label(lf_light_src, image=img_temp)
        image_light_src.image = img_temp  # Keep a reference to avoid garbage collection
        image_light_src.grid(column=0, row=0, sticky=(N, W, E, S))
        self.button_light_src_setting = ttk.Button(
            lf_light_src, text="设定")
        light_src_button_handle = self.get_toggle_handle(
            self.button_light_src_setting, "光源", self.lghtSrc_saver, 0)
        self.button_light_src_setting.configure(
            command=light_src_button_handle)
        self.button_light_src_setting.grid(column=0, row=1)

        # 设定滤波片按钮
        lf_filter = ttk.LabelFrame(
            self.lf_device, text="滤波片", padding=padding_root_sub)
        lf_filter.grid(column=1, row=0, sticky=(N, W, E, S))
        img_temp = load_image(1)
        image_filter = ttk.Label(lf_filter, image=img_temp)
        image_filter.image = img_temp  # Keep a reference to avoid garbage collection
        image_filter.grid(column=0, row=0, sticky=(N, W, E, S))
        self.button_filter_setting = ttk.Button(
            lf_filter, text="设定")
        filter_setting_handle = self.get_toggle_handle(
            self.button_filter_setting, "滤光器", self.optfilter_saver, 1)
        self.button_filter_setting.configure(command=filter_setting_handle)
        self.button_filter_setting.grid(column=0, row=1)

        # 设定光电倍增管
        lf_pmt = ttk.LabelFrame(
            self.lf_device, text="光电倍增管", padding=padding_root_sub)
        lf_pmt.grid(column=2, row=0, sticky=(N, W, E, S))
        img_temp = load_image(2)
        image_pmt = ttk.Label(lf_pmt, image=img_temp)
        image_pmt.image = img_temp  # Keep a reference to avoid garbage collection
        image_pmt.grid(column=0, row=0, sticky=(N, W, E, S))
        self.button_pmt_setting = ttk.Button(
            lf_pmt, text="设定")
        pmt_handle = self.get_toggle_handle(
            self.button_pmt_setting, "光电倍增管", self.pmt_saver, 2)
        self.button_pmt_setting.configure(command=pmt_handle)
        self.button_pmt_setting.grid(column=0, row=1)

        # 设定信号放大器
        lf_amplifier = ttk.LabelFrame(
            self.lf_device, text="信号放大器", padding=padding_root_sub)
        lf_amplifier.grid(column=3, row=0, sticky=(N, W, E, S))
        img_temp = load_image(3)
        image_amplifier = ttk.Label(lf_amplifier, image=img_temp)
        image_amplifier.image = img_temp  # Keep a reference to avoid garbage collection
        image_amplifier.grid(column=0, row=0, sticky=(N, W, E, S))
        self.button_amplifier_setting = ttk.Button(
            lf_amplifier, text="设定")
        amplifier_handle = self.get_toggle_handle(
            self.button_amplifier_setting, "放大器", self.amplifier_saver, 3)
        self.button_amplifier_setting.configure(command=amplifier_handle)
        self.button_amplifier_setting.grid(column=0, row=1)

        # 设定甄别器
        lf_discriminator = ttk.LabelFrame(
            self.lf_device, text="甄别器", padding=padding_root_sub)
        lf_discriminator.grid(column=4, row=0, sticky=(N, W, E, S))
        img_temp = load_image(4)
        image_discriminator = ttk.Label(lf_discriminator, image=img_temp)
        image_discriminator.image = img_temp
        image_discriminator.grid(column=0, row=0, sticky=(N, W, E, S))
        self.button_discriminator_setting = ttk.Button(
            lf_discriminator, text="设定")
        discr_handle = self.get_toggle_handle(
            self.button_discriminator_setting, "甄别器", self.discriminator_saver, 4)
        self.button_discriminator_setting.configure(command=discr_handle)
        self.button_discriminator_setting.grid(column=0, row=1)

        for i in range(5):
            self.lf_device.grid_columnconfigure(i, weight=1)
        self.lf_device.grid_rowconfigure(0, weight=1)

        create_tooltip(self.button_light_src_setting, self.lghtSrc_saver)
        create_tooltip(self.button_filter_setting, self.optfilter_saver)
        create_tooltip(self.button_pmt_setting, self.pmt_saver)
        create_tooltip(self.button_amplifier_setting, self.amplifier_saver)
        create_tooltip(self.button_discriminator_setting,
                       self.discriminator_saver)
        create_tooltip(self.button_glbsim_setting, self.glbSim_saver)

    def get_toggle_handle(self, button: Button, name: str, data_saver: paraDictSaver, img_id = None):  #新增：固定图片
        def toggle_event():
            sub_window = self.sub_window[name]
            if sub_window is not None and Toplevel.winfo_exists(sub_window):
                sub_window.destroy()
                sub_window = None
                button.config(text="设定")
            else:
                button.config(text="关闭设定")
                sub_window = Toplevel(self.root)
                sub_window.title(name+"设定")
                draw_setting_frame(sub_window, self.root, data_saver, img_id)
                sub_window.geometry(str(sub_wind_size[0])+"x"+str(sub_wind_size[1]+sub_wind_img_size[1]+32*len(data_saver.para_dict)))  #新增：根据列表长度设置界面长度
                sub_window.resizable(0,0)
                sub_window.protocol("WM_DELETE_WINDOW", toggle_event)
            self.sub_window[name] = sub_window
        return toggle_event

    def update_all_paras_bylist(self, data_dict_list):
        window_name_list = ['积分', '光源',
                            '滤光器', '光电倍增管', '放大器', '甄别器']
        for name in window_name_list:
            sub_window = self.sub_window[name]
            if sub_window is not None and Toplevel.winfo_exists(sub_window):
                sub_window.destroy()
                sub_window = None
            self.sub_window[name] = None
        self.button_glbsim_setting.config(text="设定")
        self.button_light_src_setting.config(text="设定")
        self.button_filter_setting.config(text="设定")
        self.button_pmt_setting.config(text="设定")
        self.button_amplifier_setting.config(text="设定")
        self.button_discriminator_setting.config(text="设定")
        self.glbSim_saver.para_dict = data_dict_list[0]
        self.lghtSrc_saver.para_dict = data_dict_list[1]
        self.optfilter_saver.para_dict = data_dict_list[2]
        self.pmt_saver.para_dict = data_dict_list[3]
        self.amplifier_saver.para_dict = data_dict_list[4]
        self.discriminator_saver.para_dict = data_dict_list[5]

        return

    def get_para_dict_list(self):
        res_list = [self.glbSim_saver.para_dict,
                    self.lghtSrc_saver.para_dict,
                    self.optfilter_saver.para_dict,
                    self.pmt_saver.para_dict,
                    self.amplifier_saver.para_dict,
                    self.discriminator_saver.para_dict,]

        return res_list


if __name__ == '__main__':
    glbSim_dict['t_intg'] = 1e-3
    data_solver_list = pack_data_solver_list([glbSim_dict, lghtSrc_dict, optfilter_dict,
                                              pmt_dict, amplifier_dict, discriminator_dict])
    root = Tk()
    root.title("参数窗口")
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    para_panel = ParaPanel(frame, root, data_solver_list)

    # 设置行列权重，使其可以自适应窗口大小

    root.mainloop()
