import numpy as np

from scoring import contrast_between

def generate_complementary(colors, delta_l = 0.12):
    base = np.copy(colors)
    num_colors = base.shape[0]
    # avg_s = np.sum(colors[:,1]) / num_colors
    avg_l = np.sum(colors[:,2]) / num_colors
    complements = np.zeros(base.shape)
    for i in range(num_colors):
        complements[i] = base[i]
        if (colors[i][2] < avg_l):
            complements[i][2] += delta_l
            complements[i][1] += complements[i][2] ** 8
        else:
            base[i][2] -= delta_l
            base[i][1] -= complements[i][2] ** 8 # when the light value is high, put a HARD dampener on the saturation of the darker complement

    complements = np.clip(complements, 0, 1)
    base = np.clip(base, 0, 1)

    combined = np.empty((num_colors * 2, 3), dtype = colors.dtype)
    combined[0::2] = base
    combined[1::2] = complements
    return combined

def generate_similar(color_hsl, reference_hsl, max_contrast):
    increment = 0.05
    current_mix = 1
    corrected = color_hsl

    while (contrast_between(corrected, reference_hsl) > max_contrast):
        print('adjusting...')
        current_mix -= increment
        corrected = (current_mix * color_hsl) + ((1 - current_mix) * reference_hsl)
        corrected[0][0] = color_hsl[0][0] # retain original hue
        if (current_mix <= 0):
            print('failed to adjust')
            return reference_hsl

    return corrected