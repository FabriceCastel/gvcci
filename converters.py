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
	return hasel.hsl2rgb(np.array([hsl]).reshape(1, 1, 3)).reshape(1, 3)[0]

def hsllist2hex(color_list):
    rgb_colors = hasel.hsl2rgb(color_list.reshape(-1, 1, 3)).reshape(-1, 3)
    rgb_colors = np.clip(rgb_colors, 0, 255)
    hex_codes = rgblist2hex(rgb_colors)
    return hex_codes
