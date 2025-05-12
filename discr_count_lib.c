#include <stdlib.h>
#include <time.h>

float generate_random_float()
{
    return (float)rand() / RAND_MAX;
}

char rand_int_01(double prob)
{
    if (prob > generate_random_float())
    {
        return 1;
    }
    else
    {
        return 0;
    }
}

int get_ndead(int ndead, double prob)
{
    return ndead + rand_int_01(prob);
}

__declspec(dllexport) int *__stdcall process_volt_series(
    const double *input_array, int length,
    double vmin, double vmax, int nv,
    double dead_t, double dt_samp)
{

    int *count_list = (int *)malloc(nv * sizeof(int));
    int *last_pos_list = (int *)malloc(nv * sizeof(int));
    double *thresh_list = (double *)malloc(nv * sizeof(double));
    double dv = 1. * (vmax - vmin) / (nv - 1);
    int _sub_ndead = (int)(dead_t / dt_samp);
    double _prob_res = 1. * (dead_t - _sub_ndead * dt_samp) / dt_samp;
    double v_last = 0, v_now = 0;

    int pointer_now = 0;

    for (int i = 0; i < nv; i++)
    {
        count_list[i] = 0;
        thresh_list[i] = vmin + 1. * i * dv;
        last_pos_list[i] = -_sub_ndead - 1;
    }

    for (int i = 0; i < length; i++)
    {
        v_now = input_array[i];
        if (v_last >= v_now)
        {
            v_last = v_now;
            continue;
        }
        pointer_now = (int)(v_last - vmin) / dv;
        pointer_now += 1;
        if (pointer_now < 0)
        {
            pointer_now = 0;
        }
        while (pointer_now < nv && thresh_list[pointer_now] < v_now)
        {
            if (i - last_pos_list[pointer_now] >= get_ndead(_sub_ndead, _prob_res))
            {
                last_pos_list[pointer_now] = i;
                count_list[pointer_now] += 1;
            }
            pointer_now += 1;
        }

        v_last = v_now;
    }
    free(thresh_list);
    free(last_pos_list);

    return count_list;
}

// 添加释放内存的函数
__declspec(dllexport) void __stdcall free_array(int *array)
{
    free(array);
}
