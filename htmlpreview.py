from scoring import custom_filter_and_sort_complements
from converters import hsllist2hex, hex2rgb

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

def wrap_in_span(text, color):
    return "<span style='font-family:monospace;font-size:18px;color:" + color + ";'>" + text + "</span>"

def get_preview_image(img_file_path, ansi_colors, bg_and_fg_colors):
    hex = hsllist2hex(ansi_colors)
    bg_fg_hex = hsllist2hex(bg_and_fg_colors)

    bg_rgb = hex2rgb(bg_fg_hex[0])

    print(hex)
    # hex = hex[2:]

    print("===============================================")
    print("ANSI color scheme for " + img_file_path)
    print("Background")
    print(bg_fg_hex[0])
    print("")
    # print("Foreground")
    # print(bg_and_fg_colors[1])
    # print("")
    print("Normal")
    for j in range(len(hex) // 2):
        print(hex[2*j])
    print("")
    print("Bright")
    for j in range(len(hex) // 2):
        print(hex[2*j + 1])
    print("===============================================")

    black =    0
    red =      2
    green =    4
    yellow =   6
    blue =     8
    magenta =  10
    cyan =     12
    white =    14

    sample = """package colorscheme.example

import Stream._
trait Stream[+A] {

  // The natural recursive solution
  def toListRecursive: List[A] = this match {
    case Cons(head, tail) => head() :: tail().toListRecursive
    case _ => List()
  }

  def toList: List[A] = {
    @annotation.tailrec
    def go(stream: Stream[A], acc: List[A]): List[A] = stream match {
      case Cons(head, tail) => go(tail(), head() :: acc)
      case _ => acc
    }
    go(this, List()).reverse
  }
}

case object Empty extends Stream[Nothing]
case class Cons[+A](head: () => A, tail: () => Stream[A]) extends Stream[A]
"""

    color_groups = [
        (cyan, ["def"]),
        (yellow, ["acc"]),
        (black, ["::"]),
        (yellow, ["tail: "]),
        (white, [": "]),
        (magenta, ["@annotation.tailrec", "match", "case", "."]),
        (yellow, ["toListRecursive", "toList", "colorscheme", "example", "_", "this", "head", "tail(", "tail)", " go", "stream", "reverse"]),
        (red, ["= ", "=>"]),
        (green, ["// The natural recursive solution"]),
        (blue, ["List[", " List", "Stream", "A", "Nothing", "Cons", "Empty"]),
        (cyan, ["package", "object", "class", "trait", "import"]),
        (black, ["extends", "+"]),
        (white, ["{", "}", "[", "]", "(", ")", ","])
    ]

    width = 1200
    height = 700
    terminal_padding = 30
    text_padding = 14

    html = "<img src='" + img_file_path + "' style='object-fit: cover; height: " + str(height) + "px; width: " + str(width) + "px; position: absolute; top: 0; left: 0;'/>"
    html += "<div style='z-index: 10; padding: " + str(text_padding) + "px; position: absolute; top: " + str(terminal_padding) + "px; left: " + str(terminal_padding) + "px;right: " + str(terminal_padding) + "px;bottom: " + str(terminal_padding) + "px; background-color: rgba(" + str(bg_rgb[0]) + ", " +str(bg_rgb[1]) + ", " +str(bg_rgb[2]) + ", 1.0)'><pre style='margin: 0;'>"

    for group in color_groups:
        for word in group[1]:
            sample = sample.replace(word, wrap_in_span(word, hex[group[0] + 1]))

    lines = sample.split('\n')
    vim = ''
    for i in range(28):
        prefix = str(i + 1) + ' '

        if (i + 1 < 10):
            prefix = ' ' + prefix

        prefix = wrap_in_span(prefix, hex[black])

        if (i < len(lines)):
            vim += prefix + lines[i] + '\n'
        else:
            vim += wrap_in_span('~\n', hex[black])


    html += vim
    html += "</pre></div>"

    img_preview = "<img src='" + img_file_path + "' style='margin-bottom: 40px; object-fit: contain; height: " + str(height) + "px; width: " + str(width) + "px;'/>"

    return img_preview + "<div style='margin-bottom: 200px; height: " + str(height) + "px; width: " + str(width) + "px; overflow: hidden; position: relative;'>" + html + "</div>"

def get_html_contents(center, improved_centers, bg_and_fg_colors, img_file_path):
    colors, bg_color = custom_filter_and_sort_complements(improved_centers, bg_and_fg_colors[0])
    html = get_preview_image(img_file_path, colors, bg_color)
    html += "<div style='display: flex; overflow: scroll;'>"
    # html += html_color_list("3D HSL", sort_by_h(centers))
    # html += html_color_list("Filtered 3D HSL", custom_filter_and_sort(centers))
    # html += html_color_list("4D HSL", sort_by_h(improved_centers))
    # html += html_color_list("Filtered 4D HSL", filter_by_custom(improved_centers))
    # html += html_color_list("Filtered 4D HSL Comp", colors)
    html += "</div>"
    
    return html

