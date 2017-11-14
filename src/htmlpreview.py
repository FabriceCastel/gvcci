from converters import hsllist2hex, hex2rgb, hsl2rgb

import numpy as np

def hex_codes_to_html_list(hex_codes, hsl_colors):
    html = "<ul style='padding: 0; list-style-type: none; margin-right: 20px'>\n"
    for i in range(len(hex_codes)):
        html += "<li style='height: 24px; overflow: hidden; color: " + hex_codes[i] + "'>"
        html += "<p style='font-family: monospace; whitespace: no-wrap; margin-top: -5px; font-size: 18px;'>def a = " + str((100 * np.clip(hsl_colors[i], 0, 1)).astype(int)) + "</p>"
        html += "</li>\n"
    return html + "</ul>\n"

def hsl_color_list_to_html_list(color_list):
    hex_codes = hsllist2hex(color_list)
    return hex_codes_to_html_list(hex_codes, color_list)

def html_color_list(title, colors, col_width = 300):
    html = "<div style='flex-basis: " + str(col_width) + "px;'>"
    html += "<h2 style='color: white;'>" + str(title) + "</h4>"
    html += hsl_color_list_to_html_list(colors)
    html += "</div>"
    return html

def wrap_in_span(text, color, bg_color = None):
    if (bg_color == None):
        return "<span style='font-family:monospace;font-size:18px;color:" + color + ";'>" + text + "</span>"
    else:
        return "<span style='font-family:monospace;font-size:18px;background:" + bg_color + ";color:" + color + ";'>" + text + "</span>"

def get_preview_image(img_file_path, ansi_colors, bg_color, fg_color):
    hex = hsllist2hex(np.vstack((ansi_colors, fg_color, fg_color)))
    bg_rgb = hsl2rgb(bg_color)

    black =    0
    red =      2
    green =    4
    yellow =   6
    blue =     8
    magenta =  10
    cyan =     12
    white =    14
    # throwaway at 16, 17
    fg =       18

    sample = """package colorscheme.example

import Stream._
trait Stream[+A] {

  // The natural recursive solution
  def toListRecursive: List[A] = this match {
    case Cons(head, tail) => head() :: tail().toListRecursive
    case _ => List()
  }
}

case object Empty extends Stream[Nothing]
case class Cons[+A](head: () => A, tail: () => Stream[A]) extends Stream[A]

Foreground
Black
Red
Green
Yellow
Blue
Magenta
Cyan
White"""

    color_groups = [
        (cyan, ["def"]),
        (fg, ["acc"]),
        (magenta, ["::"]),
        (fg, ["tail: "]),
        (magenta, [": "]),
        (yellow, ["@annotation.tailrec", "match", "case", "."]),
        (fg, ["toListRecursive", "toList", "colorscheme", "example", "_", "this", "head", "tail(", "tail)", " go", "stream", "reverse"]),
        (red, ["= ", "=>"]),
        (green, ["// The natural recursive solution"]),
        (blue, ["List[", " List", "Stream", "A", "Nothing", "Cons", "Empty"]),
        (cyan, ["package", "object", "class", "trait", "import"]),
        (magenta, ["extends", "+"]),
        (magenta, ["{", "}", "[", "]", "(", ")", ","]),
        (black, ["Black"]),
        (red, ["Red"]),
        (green, ["Green"]),
        (yellow, ["Yellow"]),
        (blue, ["Blue"]),
        (magenta, ["Magenta"]),
        (cyan, ["Cyan"]),
        (white, ["White"]),
        (fg, ["Foreground"])
    ]


    width = 1200
    height = 700
    terminal_padding = 30
    text_padding = 14

    html = "<img src='" + img_file_path + "' style='object-fit: cover; height: " + str(height) + "px; width: " + str(width) + "px; position: absolute; top: 0; left: 0;'/>"
    html += "<div style='z-index: 10; padding: " + str(text_padding) + "px; position: absolute; top: " + str(terminal_padding) + "px; left: " + str(terminal_padding) + "px;right: " + str(terminal_padding) + "px;bottom: " + str(terminal_padding) + "px; background-color: rgba(" + str(bg_rgb[0]) + ", " +str(bg_rgb[1]) + ", " +str(bg_rgb[2]) + ", 1.0)'><pre style='margin: 0;'>"

    for group in color_groups:
        if (group[0] == white or group[0] == black):
            for word in group[1]:
                sample = sample.replace(word, wrap_in_span(word, hex[group[0]], hex[black] if group[0] == white else hex[white]))
        else:
            for word in group[1]:
                sample = sample.replace(word, wrap_in_span(word, hex[group[0]]))

    lines = sample.split('\n')
    vim = ''
    for i in range(28):
        prefix = str(i + 1) + ' '

        if (i + 1 < 10):
            prefix = ' ' + prefix

        prefix = wrap_in_span(prefix, hex[fg])

        if (i < len(lines)):
            vim += prefix + lines[i] + '\n'
        else:
            vim += wrap_in_span('~\n', hex[fg])


    html += vim
    html += "</pre></div>"

    img_preview = "<img src='" + img_file_path + "' style='margin-bottom: 40px; object-fit: contain; height: " + str(height) + "px; width: " + str(width) + "px;'/>"

    return img_preview + "<div style='margin-bottom: 200px; height: " + str(height) + "px; width: " + str(width) + "px; overflow: hidden; position: relative;'>" + html + "</div>"

def get_html_contents(ansi_colors, bg_color, fg_color, img_file_path):
    html = get_preview_image(img_file_path, ansi_colors, bg_color, fg_color)
    html += "<div style='display: flex; overflow: scroll;'>"
    # html += html_color_list("3D HSL", sort_by_h(centers))
    # html += html_color_list("Filtered 3D HSL", custom_filter_and_sort(centers))
    # html += html_color_list("4D HSL", sort_by_h(improved_centers))
    # html += html_color_list("Filtered 4D HSL", filter_by_custom(improved_centers))
    # html += html_color_list("List", ansi_colors)
    html += "</div>"
    
    return html

