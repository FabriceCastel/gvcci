import numpy as np

from scoring import contrast_between

def generate_complementary(colors, delta_l = 0.12):
    base = np.copy(colors)
    num_colors = base.shape[0]
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
    print(color_hsl)

    while (contrast_between(corrected, reference_hsl) > max_contrast):
        current_mix -= increment
        print(current_mix)
        print(contrast_between(corrected, reference_hsl))
        corrected = (current_mix * color_hsl) + ((1 - current_mix) * reference_hsl)
        corrected[0][0] = color_hsl[0][0] # retain original hue
        if (current_mix <= 0):
            return reference_hsl

    return corrected

def correct_saturation(color_hsl):
    # curb the saturation for yellow + blue tones but not others
    # yellow is at 60 degrees, blue is at 240 degrees
    # they're at opposite sides of the 360 deg wheel
    hue = color_hsl[0][0]
    shifted_hue = hue - (60 / 360) # align the yellow at 0 deg and blue at 180 deg
    half_hue = (((1 + shifted_hue) * 2) % 1) / 2 # now blue and yellow are at 0 and other tones are in (0:1]
    corrected_saturation = half_hue * color_hsl[0][1]
    corrected_saturation = 0.2 + (corrected_saturation * 0.6)

    return np.array([[color_hsl[0][0], min(color_hsl[0][1], corrected_saturation), color_hsl[0][2]]])