import os
import sys

import numpy as np

from skimage import io

import hasel

import pystache

from clustering import hhsl_cluster_centers_as_hsl, hsl_cluster_centers
from converters import hex2rgb, rgb2hex, rgblist2hex, hsllist2hex, hsl2rgb, hsl2hex
from htmlpreview import get_html_contents
from scoring import custom_filter_and_sort_complements

n_colors = 16 # must be less than or equal to n_clusters
v_threshold = 0.05 # ignore colors darker than this


def get_pixels_for_image(img_file_path):
    print("reading image...")
    img_rgb = io.imread(img_file_path)

    print("converting color space...")
    img_hsl = hasel.rgb2hsl(img_rgb)
    hsl_colors = img_hsl.reshape((-1, 3))

    print("filtering out darkest colors before clustering for better results...")
    samples_before = hsl_colors.shape[0]
    hsl_colors = hsl_colors[hsl_colors[:,2] > v_threshold]
    samples_after = hsl_colors.shape[0]

    print("filtered out " + str(100 - (100 * samples_after) // samples_before) + "% of pixels")
    return hsl_colors

def mode_rows(a):
    a = np.ascontiguousarray(a)
    void_dt = np.dtype((np.void, a.dtype.itemsize * np.prod(a.shape[1:])))
    _,ids, count = np.unique(a.view(void_dt).ravel(), \
                                return_index=1,return_counts=1)
    largest_count_id = ids[count.argmax()]
    return a[largest_count_id]
    # print(count)
    # print(a)
    # most_frequent_rows = a[np.argsort(count)]
    # return most_frequent_rows

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
            complements[i][1] += complements[i][2] ** 5
        else:
            base[i][2] -= delta_l
            base[i][1] -= complements[i][2] ** 5 # when the light value is high, put a HARD dampener on the saturation of the darker complement

    complements = np.clip(complements, 0, 1)
    base = np.clip(base, 0, 1)

    combined = np.empty((num_colors * 2, 3), dtype = colors.dtype)
    combined[0::2] = base
    combined[1::2] = complements
    return combined

def print_color_scheme(colors):
    print("===============================================")
    print("ANSI color scheme for " + img_file_path)
    print("Background")
    print(hsl2hex(colors["background"]))
    
    print("")
    print("Foreground")
    print(hsl2hex(colors["foreground"]))
    
    print("")
    print("Normal")
    print(hsl2hex(colors["ansi-black-normal"]))
    print(hsl2hex(colors["ansi-red-normal"]))
    print(hsl2hex(colors["ansi-green-normal"]))
    print(hsl2hex(colors["ansi-yellow-normal"]))
    print(hsl2hex(colors["ansi-blue-normal"]))
    print(hsl2hex(colors["ansi-magenta-normal"]))
    print(hsl2hex(colors["ansi-cyan-normal"]))
    print(hsl2hex(colors["ansi-white-normal"]))

    print("")
    print("Bright")
    print(hsl2hex(colors["ansi-black-bright"]))
    print(hsl2hex(colors["ansi-red-bright"]))
    print(hsl2hex(colors["ansi-green-bright"]))
    print(hsl2hex(colors["ansi-yellow-bright"]))
    print(hsl2hex(colors["ansi-blue-bright"]))
    print(hsl2hex(colors["ansi-magenta-bright"]))
    print(hsl2hex(colors["ansi-cyan-bright"]))
    print(hsl2hex(colors["ansi-white-bright"]))

    print("===============================================")

with open('resources/gvcci-title-ascii.txt', 'r') as logo:
    print(logo.read())



html_contents = ""

# --background [dark|light|auto|<hex>]
background_color_param_name = "--background"
background_color_param_default = "auto"

template_param_name = "--template"
template_param_default = "./templates/iterm.itermcolors"

config = {
    background_color_param_name: background_color_param_default,
    template_param_name: template_param_default
}

image_paths = []

# TODO look into pythonic way of parsing cmdline arguments
arg_id = 1
while arg_id < len(sys.argv):
    commandline_param = sys.argv[arg_id]
    if (len(commandline_param) > 2):
        if (commandline_param[:2] == "--"):
            config[commandline_param] = sys.argv[arg_id + 1]
            arg_id += 1
        else:
            image_paths.append(commandline_param)
    arg_id += 1

for img_file_path in image_paths:
    print("Generating colors for input " + str(img_file_path))

    hsl_colors = get_pixels_for_image(img_file_path)
    improved_centers = hhsl_cluster_centers_as_hsl(hsl_colors)

    bg_fg_colors = np.array([[0, 0, 0], [0, 0, 0.96]]) # default fallback values
    if (config[background_color_param_name] == "light"):
        bg_fg_colors = np.array([[0, 0, 0.96], [0, 0, 0]]) # light fallback values

    precision = 32
    dark_l = 0.2;
    light_l = 0.8;
    light_l_upper = 0.95;
    light_s_upper = 0.4;

    light_colors = hsl_colors[hsl_colors[:,2] > light_l]
    light_colors = light_colors[light_colors[:,2] < light_l_upper]
    light_colors = light_colors[light_colors[:,1] < light_s_upper]

    dark_colors = hsl_colors[hsl_colors[:,2] < dark_l]

    dark_and_light_colors = np.vstack((dark_colors, light_colors))

    if config[background_color_param_name] == "auto" and len(dark_and_light_colors) > 0:
        bg_color = mode_rows((dark_and_light_colors * precision).astype(int)).reshape(1, 3) / precision
        bg_fg_colors = np.vstack((bg_color, bg_color))
    elif config[background_color_param_name] == "dark" and len(dark_colors) > 0:
        bg_color = mode_rows((dark_colors * precision).astype(int)).reshape(1, 3) / precision
        bg_fg_colors = np.vstack((bg_color, bg_color))
    elif config[background_color_param_name] == "light" and len(light_colors) > 0:
        bg_color = mode_rows((light_colors * precision).astype(int)).reshape(1, 3) / precision
        bg_fg_colors = np.vstack((bg_color, bg_color))
    elif config[background_color_param_name][0] == "#":
        bg_color = hex2rgb(config[background_color_param_name])
        bg_color = hasel.rgb2hsl(np.array(bg_color).reshape(1, 1, 3)).reshape(1, 3)
        bg_fg_colors = np.vstack((bg_color, bg_color))

    # TODO the gb colour detection sucks for light colors
    # TODO adjust the bg color by picking the nearest color cluster to it and assigning it that value
    # TODO bg color breaks for the isaac example because the black bg is a flat #000000 color that's filtered out

    # improved_centers = np.vstack((bg_fg_colors, improved_centers))

    ansi_colors, bg_color = custom_filter_and_sort_complements(improved_centers, bg_fg_colors[0])

    html_contents += get_html_contents(ansi_colors, bg_fg_colors, img_file_path)
    html =  "<body style='background: #000'>\n"
    html += "<div>"
    html += html_contents
    html += "</div>"
    html += "</body>\n"

    result_file = open("examples.html", "w")
    result_file.write(html)
    result_file.close()

    # black_default_lightness = 0.1

    black = bg_color.copy()

    if (bg_color[2] < 0.1):
        black[2] += 0.1
    elif (bg_color[2] < 0.5):
        black[2] -= 0.1
    else:
        black[2] = 0.2

    black_bright = black.copy()
    black_bright[2] += 0.1

    colors_hsl = {
        "background":          bg_color,
        "foreground":          ansi_colors[0],
        "bold":                ansi_colors[1],
        "cursor":              ansi_colors[2],
        "selection":           ansi_colors[0],
        "selected-text":       bg_color,
        "ansi-black-normal":   black,
        "ansi-black-bright":   black_bright,
        "ansi-red-normal":     ansi_colors[2],
        "ansi-red-bright":     ansi_colors[3],
        "ansi-green-normal":   ansi_colors[4],
        "ansi-green-bright":   ansi_colors[5],
        "ansi-yellow-normal":  ansi_colors[6],
        "ansi-yellow-bright":  ansi_colors[7],
        "ansi-blue-normal":    ansi_colors[8],
        "ansi-blue-bright":    ansi_colors[9],
        "ansi-magenta-normal": ansi_colors[10],
        "ansi-magenta-bright": ansi_colors[11],
        "ansi-cyan-normal":    ansi_colors[12],
        "ansi-cyan-bright":    ansi_colors[13],
        "ansi-white-normal":   ansi_colors[14],
        "ansi-white-bright":   ansi_colors[15]
    }

    # print_color_scheme(colors)

    colors = {}
    for name, hsl in colors_hsl.items():
        rgb = hsl2rgb(hsl)
        hex = hsl2hex(hsl)

        colors[name + "-red-255"]     = rgb[0]
        colors[name + "-green-255"]   = rgb[1]
        colors[name + "-blue-255"]    = rgb[2]
        colors[name + "-red-float"]   = rgb[0] / 255
        colors[name + "-green-float"] = rgb[1] / 255
        colors[name + "-blue-float"]  = rgb[2] / 255
        colors[name + "-hex"]         = hex

    template_file_path = config[template_param_name]
    template_file_name = template_file_path.split('/')[-1]
    template_file_name_parts = template_file_name.split('.')
    template_file_extension = ""
    if len(template_file_name_parts) > 1:
        template_file_extension = "." + "".join(template_file_name_parts[1:])

    with open(template_file_path, 'r') as template_file:
        template = template_file.read()

        # set name constant for the iTerm dynamic profile
        image_name = "gvcci" # ".".join(img_file_path.split('/')[-1].split('.')[:-1])
        with open(image_name + template_file_extension, 'w') as out_file:
            out_file.write(pystache.render(template, colors))
            print("Output: " + image_name + template_file_extension)

