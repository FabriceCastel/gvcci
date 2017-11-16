import os
import sys
from shutil import copyfile

import numpy as np

from skimage import io

import hasel

import pystache

from config import get_args
from clustering import hhsl_cluster_centers_as_hsl, hsl_cluster_centers
from converters import hex2rgb, rgb2hex, rgblist2hex, hsllist2hex, hsl2rgb, hsl2hex
from htmlpreview import get_html_contents
from scoring import pick_n_best_colors, clip_between_boundaries, find_dominant_by_frequency, sort_colors_by_closest_counterpart, pick_n_best_colors_with_reference
from colorgenerator import generate_complementary, generate_similar, correct_saturation
from logger import log

n_colors = 16 # must be less than or equal to n_clusters

def get_pixels_for_image(img_file_path):
    log("reading image \"" + img_file_path + "\"")
    img_rgb = io.imread(img_file_path)

    log("converting color space...")
    img_hsl = hasel.rgb2hsl(img_rgb[:,:,0:3])
    hsl_colors = img_hsl.reshape((-1, 3))

    return hsl_colors


dir_path = os.path.expanduser("~/.gvcci")
try:
    os.stat(dir_path)
except:
    os.mkdir(dir_path)

dir_path = os.path.expanduser("~/.gvcci/themes")
try:
    os.stat(dir_path)
except:
    os.mkdir(dir_path)

html_contents = ""

args = get_args()

images = args['images']
background = args['background']
template_path = args['template_path']
print_output = args['print_output']
symlink_wallpaper = args['symlink_wallpaper']

with open('resources/gvcci-title-ascii.txt', 'r') as logo:
    log(logo.read())

image_paths = map(os.path.realpath, images)

for img_file_path in image_paths:
    log("Generating colors for input " + str(img_file_path))

    hsl_colors = get_pixels_for_image(img_file_path)
    improved_centers = hhsl_cluster_centers_as_hsl(hsl_colors)

    dominant_dark_and_light_colors = find_dominant_by_frequency(hsl_colors)

    bg_color = dominant_dark_and_light_colors[0]
    fg_color = dominant_dark_and_light_colors[1]

    dominant_dark = dominant_dark_and_light_colors[0]
    dominant_light = dominant_dark_and_light_colors[1]

    if (dominant_dark[0][2] > dominant_light[0][2]):
        tmp = dominant_light
        dominant_light = dominant_dark
        dominant_dark = tmp

    max_dominant_dark_saturation = 0.4

    reference_dominant_light_color = np.array([[0, 0, 0.94]])
    reference_dominant_light_color = np.array([[0, 0, min(max(dominant_light[0][2], 0.8), 0.95)]])

    if background == "dark" or (background == "auto" and bg_color[0][2] < 0.5):
        if (dominant_dark[0][1] > max_dominant_dark_saturation):
            dominant_dark[0][1] = max_dominant_dark_saturation
        bg_color = dominant_dark
        fg_color = dominant_light
    elif background == "light" or (background == "auto" and bg_color[0][2] >= 0.5):
        dominant_light = correct_saturation(dominant_light)
        bg_color = dominant_light
        fg_color = dominant_dark
    elif background[0] == "#":
        bg_color = hex2rgb(background)
        bg_color = hasel.rgb2hsl(np.array(bg_color).reshape(1, 1, 3)).reshape(1, 3)
        if (bg_color[0][2] < 0.5):
            fg_color = dominant_light
        else:
            fg_color = dominant_dark

    # Accessibility contrast levels:
    # WCAG 2.0 level AA requires a contrast ratio of [4.5 : 1] for normal text
    # WCAG 2.0 level AAA requires a contrast ratio of [7 : 1] for normal text
    # Note: the contrast maxes out at 21.0 for white / black contrast

    # dark theme settings
    min_dark_contrast = 5
    min_light_contrast = 1.7

    # light theme settings
    if (bg_color[0][2] > 0.5):
        min_dark_contrast = 16
        min_light_contrast = 3

    # ansi constants
    black   = [0,       0, 0. ]
    red     = [0,       1, 0.5]
    green   = [0.33333, 1, 0.4]
    yellow  = [0.16666, 1, 0.5]
    blue    = [0.66666, 1, 0.6]
    magenta = [0.83333, 1, 0.5]
    cyan    = [0.5,     1, 0.5]
    white   = [0,       0, 1.0]

    standard_ansi_colors = np.array([
        red,
        green,
        yellow,
        blue,
        magenta,
        cyan,
        white,
        black
    ])

    # ansi_colors_unconstrained = pick_n_best_colors_with_reference(8, improved_centers, standard_ansi_colors, dominant_dark, dominant_light, min_dark_contrast, min_light_contrast)
    ansi_colors_unconstrained = pick_n_best_colors(8, improved_centers, dominant_dark, dominant_light, min_dark_contrast, min_light_contrast)
    ansi_colors_normal = clip_between_boundaries(ansi_colors_unconstrained, dominant_dark, dominant_light, min_dark_contrast, min_light_contrast)
    ansi_colors_sorted = sort_colors_by_closest_counterpart(ansi_colors_normal, standard_ansi_colors)
    # ansi_colors_sorted = ansi_colors_normal # already sorted when you run it through pick_n_best_with_ref
    ansi_colors_normal_and_bright = generate_complementary(ansi_colors_sorted)
    ansi_colors = ansi_colors_normal_and_bright

    black = bg_color.copy()

    if (bg_color[0][2] < 0.1):
        black[0][2] += 0.1
    elif (bg_color[0][2] < 0.5):
        black[0][2] -= 0.1
    else:
        black[0][2] = 0.2

    black_bright = black.copy()
    black_bright[0][2] += 0.1

    white_l_threshold = 0.85
    if ansi_colors[12][2] < white_l_threshold:
        ansi_colors[12][2] = white_l_threshold # white l value lower bound
        ansi_colors[13][2] = white_l_threshold + 0.12

    html_contents += get_html_contents(np.vstack((black, black_bright, ansi_colors)), bg_color, fg_color, img_file_path)
    html =  "<body style='background: #000'>\n"
    html += "<div>"
    html += html_contents
    html += "</div>"
    html += "</body>\n"

    result_file = open("examples.html", "w")
    result_file.write(html)
    result_file.close()

    colors_hsl = {
        "background":          bg_color,
        "foreground":          fg_color,
        "bold":                fg_color, # TODO!
        "cursor":              ansi_colors[14],
        "selection":           ansi_colors[15],
        "selected-text":       bg_color,
        "ansi-black-normal":   black,
        "ansi-black-bright":   black_bright,
        "ansi-red-normal":     ansi_colors[0],
        "ansi-red-bright":     ansi_colors[1],
        "ansi-green-normal":   ansi_colors[2],
        "ansi-green-bright":   ansi_colors[3],
        "ansi-yellow-normal":  ansi_colors[4],
        "ansi-yellow-bright":  ansi_colors[5],
        "ansi-blue-normal":    ansi_colors[6],
        "ansi-blue-bright":    ansi_colors[7],
        "ansi-magenta-normal": ansi_colors[8],
        "ansi-magenta-bright": ansi_colors[9],
        "ansi-cyan-normal":    ansi_colors[10],
        "ansi-cyan-bright":    ansi_colors[11],
        "ansi-white-normal":   ansi_colors[12],
        "ansi-white-bright":   ansi_colors[13]
    }

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

    log("=========== Terminal Colors ===========")
    with open('templates/columns-with-headers.txt', 'r') as print_template:
        log(pystache.render(print_template.read(), colors))
    log("=======================================")

    image_name = os.path.basename(img_file_path).split(".")[0]
    image_extension = os.path.basename(img_file_path).split(".")[-1]

    output_dir_path = os.path.join(os.path.expanduser("~/.gvcci/themes"), image_name)
    try:
        os.stat(output_dir_path)
    except:
        os.mkdir(output_dir_path)        

    output_image_path = os.path.join(output_dir_path, "wallpaper")

    try:
        os.remove(output_image_path)
    except OSError:
        pass
        
    if (symlink_wallpaper):
        os.symlink(img_file_path, output_image_path)
    else:
        copyfile(img_file_path, output_image_path)
    
    log("Output: " + output_image_path)

    template_file_or_dir_path = os.path.realpath(template_path)
    if (os.path.isfile(template_file_or_dir_path)):
        template_file_path = template_file_or_dir_path
        with open(template_file_path, 'r') as template_file:
            template = template_file.read()
            template_file_name = os.path.basename(template_file_path)
            
            output_theme_path = os.path.join(output_dir_path, template_file_name)


            with open(output_theme_path, 'w') as out_file:
                filled_out_template = pystache.render(template, colors)
                out_file.write(filled_out_template)
                if (print_output):
                    print(filled_out_template)
            
            log("Output: " + output_theme_path)
    elif (os.path.isdir(template_file_or_dir_path)):
        for template_file in os.listdir(template_file_or_dir_path):
            template_file_path = os.path.join(template_file_or_dir_path, template_file)
            with open(template_file_path, 'r') as template_file:
                template = template_file.read()
                template_file_name = os.path.basename(template_file_path)
                
                output_theme_path = os.path.join(output_dir_path, template_file_name)

                with open(output_theme_path, 'w') as out_file:
                    filled_out_template = pystache.render(template, colors)
                    out_file.write(filled_out_template)
                    if (print_output):
                        print(filled_out_template)
                
                log("Output: " + output_theme_path)

    log("=======================================")

