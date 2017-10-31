import hasel
import numpy as np

def hex2rgb(hex):
    return tuple(int(hex.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))

def rgb2hex(r,g,b):
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex

def rgblist2hex(rgb_list):
    hex_codes = []
    for i in range(rgb_list.shape[0]):
        rgb = rgb_list[i]
        hex_codes.append(rgb2hex(rgb[0], rgb[1], rgb[2]))
    return hex_codes

def hsl2rgb(hsl):
	return hasel.hsl2rgb(np.array([hsl]).reshape(-1, 1, 3)).reshape(-1, 3)[0]

def hsl2hex(hsl):
	rgb = hsl2rgb(hsl)
	return rgb2hex(rgb[0], rgb[1], rgb[2])

def hsllist2hex(color_list):
    rgb_colors = hasel.hsl2rgb(color_list.reshape(-1, 1, 3)).reshape(-1, 3)
    rgb_colors = np.clip(rgb_colors, 0, 255)
    hex_codes = rgblist2hex(rgb_colors)
    return hex_codes

# https://ux.stackexchange.com/questions/82056/how-to-measure-the-contrast-between-any-given-color-and-white
def rgb2rl(rgb_color):
    rgb = rgb_color.reshape(-1, 3)[0]

    r = rgb[0]
    g = rgb[1]
    b = rgb[2]

    # TODO make this more robust
    # This is a workaround to avoid dark values too close to zero always yielding good contrast results
    # when they really shouldn't
    min_val = 25

    if (r < min_val):
        r = min_val
    if (g < min_val):
        g = min_val
    if (b < min_val):
        b = min_val

    rg = r / 3294 if (r <= 10) else (r / 269 + 0.0513) ** 2.4
    gg = g / 3294 if (g <= 10) else (g / 269 + 0.0513) ** 2.4
    bg = b / 3294 if (b <= 10) else (b / 269 + 0.0513) ** 2.4

    return (0.2126 * rg) + (0.7152 * gg) + (0.0722 * bg)

def hsl2rl(hsl_color):
    return rgb2rl(hsl2rgb(hsl_color))

def hsllist2rl(hsl_color_list):
    rgb_colors = hasel.hsl2rgb(hsl_color_list.reshape(-1, 1, 3)).reshape(-1, 3)
    rl_values = []
    for i in range(rgb_colors.shape[0]):
        rl_values.append(rgb2rl(rgb_colors[i]))
    return np.array(rl_values)