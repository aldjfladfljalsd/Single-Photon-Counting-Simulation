import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import convolve
from tqdm import tqdm
from scipy.ndimage import gaussian_filter1d
from typing import List, Dict, Any
from ctypes import cdll, c_int, c_double, POINTER

import sys
import os
path_this_file = os.path.realpath(sys.argv[0])
path_this_dir = os.path.dirname(path_this_file)
path_disc_count_dll = os.path.join(path_this_dir, "discr_count_lib.dll")
discCount_lib = cdll.LoadLibrary(path_disc_count_dll)

discCount_lib.process_volt_series.argtypes = (
    POINTER(c_double), c_int, c_double, c_double, c_int, c_double, c_double)
discCount_lib.process_volt_series.restype = POINTER(c_int)

discCount_lib.free_array.argtypes = (POINTER(c_int),)
discCount_lib.free_array.restype = None


# 参数字典
glbSim_dict = {
    't_intg': 1e-1,
    'n_tStep': 100,
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

# 基本函数
# 生成光子到达时间序列


def gen_lght_t_series(glbSim_dict, lghtSrc_dict):

    flo_rate = lghtSrc_dict['flo_rate']
    t_intg = glbSim_dict['t_intg']
    n_tStep = glbSim_dict['n_tStep']
    t_span = t_intg/n_tStep

    num_photo = np.random.poisson(flo_rate * t_span)
    t_series = np.random.uniform(0, t_span, num_photo)
    idx_sort = np.argsort(t_series)
    t_series = t_series[idx_sort]

    return t_series

# 按照效率枪毙


def kill_with_eff(t_series, eff):
    n_photo = len(t_series)
    eff_arr = np.random.uniform(0, 1, n_photo)
    idx_eff = eff_arr < eff
    t_series_eff = t_series[idx_eff]

    return t_series_eff

# 生成电压峰值


def get_voltSeries(len_ser, n_stage, pmt_dict):
    secdElctEmis_coef = pmt_dict['secdElctEmis_coef']
    nElect2Vol_coef = pmt_dict['nElct2Vol_coef']
    num_elct = np.ones(len_ser)
    for i in range(n_stage):
        num_elct += np.random.poisson(secdElctEmis_coef*num_elct)
    volt_series = num_elct*nElect2Vol_coef

    return volt_series

# 热电子发射
# 生成热电子发射时间序列和电压峰值


def gen_thermElctEmis(glbSim_dict, pmt_dict):
    n_stage = pmt_dict['n_stage']
    t_intg = glbSim_dict['t_intg']
    n_tStep = glbSim_dict['n_tStep']
    t_span = t_intg/n_tStep
    temperature = glbSim_dict['tmper']

    thermElctEmis_coef = pmt_dict['thermElctEmis_coef']
    surfWork_tmper = pmt_dict['surfWork_tmper']
    use_min_stage = pmt_dict['use_min_stage']

    t_series_list = []
    volt_series_list = []
    for i in range(n_stage-use_min_stage):
        the_flow = thermElctEmis_coef*temperature**2 * \
            np.exp(-surfWork_tmper/temperature)
        num_t_series = np.random.poisson(the_flow*t_span)
        t_series = np.random.uniform(0, t_span, num_t_series)
        t_series_list.append(t_series)
        volt_series = get_voltSeries(num_t_series, i+use_min_stage, pmt_dict)
        volt_series_list.append(volt_series)

    t_series = np.concatenate(t_series_list)
    volt_series = np.concatenate(volt_series_list)
    idx_sort = np.argsort(t_series)
    t_series = t_series[idx_sort]
    volt_series = volt_series[idx_sort]

    return t_series, volt_series

# 离散采样，系统相应


def pach_tSeries(ts_pho, vs_pho, ts_the, vs_the, glbSim_dict, pmt_dict):
    t_intg = glbSim_dict['t_intg']
    n_tStep = glbSim_dict['n_tStep']
    dt_samp = glbSim_dict['dt_samp']
    broder_coef = pmt_dict['broder_coef']

    t_span = t_intg/n_tStep
    n_pach = int(t_span/dt_samp*(1+broder_coef))

    volt_series_pach = np.zeros((n_pach,))
    n_t_float = ts_the/dt_samp
    idx_arr = np.int32(np.floor(n_t_float))
    n_t_float -= idx_arr
    idx_arr += n_t_float > np.random.random(n_t_float.shape)
    volt_series_pach[idx_arr] += vs_the
    n_t_float = ts_pho/dt_samp
    idx_arr = np.int32(np.floor(n_t_float))
    n_t_float -= idx_arr
    idx_arr += n_t_float > np.random.random(n_t_float.shape)
    volt_series_pach[idx_arr] += vs_pho

    tau_rc = pmt_dict['tau_rc']
    tau_lc = pmt_dict['tau_lc']
    tau_gauss = pmt_dict['tau_gauss']
    t_line_temp = np.arange(n_pach)*dt_samp
    sys_conv_arr = np.exp(-t_line_temp/tau_rc)*np.cos(t_line_temp/tau_lc)
    volt_series_pach = convolve(volt_series_pach, sys_conv_arr, mode='full')
    volt_series_pach = volt_series_pach[:n_pach]
    volt_series_pach = gaussian_filter1d(
        volt_series_pach, sigma=tau_gauss/dt_samp, mode='nearest')

    return volt_series_pach

# 离散采样,系统相应,代码优化


def pach_tSeries_v2(ts_pho, vs_pho, ts_the, vs_the, glbSim_dict, pmt_dict):
    t_intg = glbSim_dict['t_intg']
    n_tStep = glbSim_dict['n_tStep']
    dt_samp = glbSim_dict['dt_samp']
    broder_coef = pmt_dict['broder_coef']

    t_span = t_intg/n_tStep
    n_pach = int(t_span/dt_samp*(1+broder_coef))

    volt_series_pach = np.zeros((n_pach,))
    n_t_float = ts_the/dt_samp
    idx_arr = np.int32(np.floor(n_t_float))
    n_t_float -= idx_arr
    idx_arr += n_t_float > np.random.random(n_t_float.shape)
    volt_series_pach[idx_arr] += vs_the
    n_t_float = ts_pho/dt_samp
    idx_arr = np.int32(np.floor(n_t_float))
    n_t_float -= idx_arr
    idx_arr += n_t_float > np.random.random(n_t_float.shape)
    volt_series_pach[idx_arr] += vs_pho

    tau_rc = pmt_dict['tau_rc']
    tau_lc = pmt_dict['tau_lc']
    tau_gauss = pmt_dict['tau_gauss']
    t_line_temp = np.arange(int(12*tau_rc/dt_samp))*dt_samp
    sys_conv_arr = np.exp(-t_line_temp/tau_rc)*np.cos(t_line_temp/tau_lc)
    volt_series_pach = convolve(volt_series_pach, sys_conv_arr, mode='full')
    volt_series_pach = volt_series_pach[:n_pach]
    volt_series_pach = gaussian_filter1d(
        volt_series_pach, sigma=tau_gauss/dt_samp, mode='nearest')

    return volt_series_pach

# 添加热噪声


def add_therm_noise(volt_series_pach, noise_ratio, glbSim_dict):

    tmper = glbSim_dict['tmper']

    noise = np.random.normal(0, 1, len(volt_series_pach)
                             )*np.sqrt(tmper)*noise_ratio

    return noise + volt_series_pach

# 放大器处理


def pass_magnf(volt_series_pach, amplfier_dict, glbSim_dict):
    mgnfc = amplfier_dict['mgnfc']
    noise_rate = amplfier_dict['noise_rate']
    tau_gauss = amplfier_dict['tau_gauss']
    temper = glbSim_dict['tmper']

    volt_series_pach *= mgnfc
    volt_series_pach = gaussian_filter1d(
        volt_series_pach, sigma=tau_gauss, mode='nearest')
    volt_series_pach += np.random.normal(0, 1,
                                         len(volt_series_pach))*noise_rate*np.sqrt(temper)

    return volt_series_pach

# 甄别器处理


def discrim_detect(volt_series_pach, thresh, discriminator_dict, glbSim_dict):
    dead_time = discriminator_dict['dead_time']
    dt_samp = glbSim_dict['dt_samp']

    def check_dead_time_n():
        resf = dead_time/dt_samp
        n_dead_time = int(np.floor(resf))
        resf -= n_dead_time
        n_dead_time += resf > np.random.random()
        return n_dead_time

    bigger_bool = volt_series_pach > thresh
    diff_bool = np.diff(bigger_bool.astype(int))
    idx_arr = np.where(diff_bool == 1)[0]
    idx_chosen = []
    trig_pos = -np.inf
    for i in range(len(idx_arr)):
        idx_temp = idx_arr[i]
        if idx_temp - trig_pos > check_dead_time_n():
            idx_chosen.append(i)
            trig_pos = idx_temp
    idx_chosen = np.array(idx_chosen)
    if len(idx_chosen) == 0:
        return np.array([])
    return idx_arr[idx_chosen]

# 甄别器处理所有电压使用c


def c_discrim_detect_all(volt_series_pach, vmin, vmax, nv, discriminator_dict, glbSim_dict):
    dt_samp = glbSim_dict['dt_samp']
    dead_time = discriminator_dict['dead_time']

    input_ptr = volt_series_pach.ctypes.data_as(POINTER(c_double))
    length = len(volt_series_pach)
    result_ptr = discCount_lib.process_volt_series(
        input_ptr, length, vmin, vmax, nv, dead_time, dt_samp)
    disc_count = np.ctypeslib.as_array(result_ptr, shape=(nv,)).copy()
    discCount_lib.free_array(result_ptr)
    return disc_count


class SimCore:
    def __init__(self):
        self.has_result = False
        self.glbSim_dict = None
        self.optfilter_dict = None
        self.lghtSrc_dict = None
        self.pmt_dict = None
        self.amplifier_dict = None
        self.discriminator_dict = None

        self.pho_t = None
        self.pho_t_eff = None
        self.the_t = None
        self.pho_v = None
        self.the_v = None
        self.tirg_idx = None
        self.v_patch = None
        self.v_patch_amplf = None
        self.v_thresh_list = None
        self.v_disc_count = None
        self.v_disc_count_list = None
        
        self.v_range_auto = [0, 0] #新增，获取自动扫描电压的数值


    def update_param(self, glbSim_dict, lghtSrc_dict, optfilter_dict,
                     pmt_dict, amplifier_dict, discriminator_dict):
        self.has_result = False
        self.glbSim_dict = glbSim_dict
        self.optfilter_dict = optfilter_dict
        self.lghtSrc_dict = lghtSrc_dict
        self.pmt_dict = pmt_dict
        self.amplifier_dict = amplifier_dict
        self.discriminator_dict = discriminator_dict

    def load_patch(self):
        self.pho_t = gen_lght_t_series(self.glbSim_dict, self.lghtSrc_dict)
        self.pho_t_eff = kill_with_eff(
            self.pho_t, self.optfilter_dict['trans_rate'])
        self.pho_t_eff = kill_with_eff(
            self.pho_t_eff, self.pmt_dict['quan_eff'])
        self.the_t, self.the_v = gen_thermElctEmis(
            self.glbSim_dict, self.pmt_dict)
        self.pho_v = get_voltSeries(
            len(self.pho_t_eff), self.pmt_dict['n_stage'], self.pmt_dict)
        self.v_patch = pach_tSeries_v2(self.pho_t_eff, self.pho_v,
                                       self.the_t, self.the_v, self.glbSim_dict, self.pmt_dict)
        self.v_patch = add_therm_noise(
            self.v_patch, self.pmt_dict['noise_rate'], self.glbSim_dict)
        self.v_patch_amplf = pass_magnf(
            self.v_patch, self.amplifier_dict, self.glbSim_dict)
        return

    def cal_init(self, v_range=None, n_step=100):
        self.has_result = False
        if v_range is None:
            self.load_patch()
            v_range = [0,
                       np.max(self.v_patch_amplf)*1.1]
            self.v_range_auto = v_range  #新增，将该变量赋值为扫描的电压大小

        self.v_thresh_list = np.linspace(v_range[0], v_range[1], n_step)
        self.v_disc_count = np.zeros(len(self.v_thresh_list))
        self.v_disc_count_list = []
        return

    def run_step(self):
        self.has_result = True
        self.load_patch()
        v_thresh_temp = self.v_thresh_list
        self.v_disc_count = c_discrim_detect_all(self.v_patch_amplf, v_thresh_temp.min(), v_thresh_temp.max(),
                                                 len(v_thresh_temp), self.discriminator_dict, self.glbSim_dict
                                                 )
        self.v_disc_count_list.append(
            self.v_disc_count.copy()
        )
        # print(self.v_disc_count_list)
        return

    def copy(self):
        new_sim_core = SimCore()
        new_sim_core.update_param(self.glbSim_dict, self.optfilter_dict,
                                  self.lghtSrc_dict, self.pmt_dict,
                                  self.amplifier_dict, self.discriminator_dict)
        new_sim_core.pho_t = self.pho_t.copy()
        new_sim_core.pho_t_eff = self.pho_t_eff.copy()
        new_sim_core.the_t = self.the_t.copy()
        new_sim_core.pho_v = self.pho_v.copy()
        new_sim_core.the_v = self.the_v.copy()
        new_sim_core.v_patch = self.v_patch.copy()
        new_sim_core.v_patch_amplf = self.v_patch_amplf.copy()
        new_sim_core.v_thresh_list = self.v_thresh_list.copy()
        new_sim_core.v_disc_count = self.v_disc_count.copy()
        new_sim_core.v_disc_count_list = self.v_disc_count_list.copy()
        return new_sim_core


if __name__ == '__main__':
    glbSim_dict['t_intg'] = 1e-3
    sim_core = SimCore()
    sim_core.update_param(glbSim_dict, lghtSrc_dict, optfilter_dict,
                          pmt_dict, amplifier_dict, discriminator_dict)
    sim_core.cal_init()

    for i in tqdm(range(10)):
        sim_core.run_step()

    plt.plot(sim_core.v_thresh_list[:-1], -np.diff(sim_core.v_disc_count))
    plt.ylim(0, 1.2*np.max(-np.diff(sim_core.v_disc_count)))
    plt.show()
