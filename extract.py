import os
import sys

import numpy as np

from skimage import io
from skimage import color

from sklearn.cluster import MiniBatchKMeans

# Constants
kmeans_batch_size = 100
n_clusters = 32
n_colors = 16 # must be less than or equal to n_clusters
v_threshold = 0.05 # ignore colors darker than this

# Utils
def rgb2hex(r,g,b):
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex


def get_pixels_for_image(img_file_path):
    print("reading image...")
    img_rgb = io.imread(img_file_path)

    print("converting color space...")
    img_hsv = color.convert_colorspace(img_rgb, 'RGB', 'HSV')
    hsv_colors = img_hsv.reshape((-1, 3))

    print("filtering out darkest colors before clustering for better results...")
    samples_before = hsv_colors.shape[0]
    hsv_colors = hsv_colors[hsv_colors[:,2] > v_threshold]
    samples_after = hsv_colors.shape[0]

    print("filtered out " + str(100 - (100 * samples_after) // samples_before) + "% of pixels")
    return hsv_colors

# convert the hue component into two values, sin(pi * h) and cos(pi * h)
def hsv_to_hhsv(colors):
    cos_h = np.cos(2 * np.pi * colors[:,0])
    sin_h = np.sin(2 * np.pi * colors[:,0])
    hh_colors = np.vstack((cos_h, sin_h)).T
    return np.vstack((hh_colors[:,0], hh_colors[:,1], hsv_colors[:,1], hsv_colors[:,2])).T

def hhsv_cluster_centers(colors):
    kmeans_model_hhsv = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hhsv = kmeans_model_hhsv.fit(hsv_to_hhsv(colors))
    return kmeans_hhsv.cluster_centers_

def hh_cluster_centers_to_h_cluster_centers(hh_centers):
    circular_hue_center_radii = np.multiply(hh_centers[:,0], hh_centers[:,0]) + np.multiply(hh_centers[:,1], hh_centers[:,1])
    circular_hue_center_radii = np.reshape(circular_hue_center_radii, (n_clusters, 1))
    norm_circular_hue_centers = hh_centers / circular_hue_center_radii
    norm_circular_hue_centers = np.clip(norm_circular_hue_centers, -1, 1)
    return hcos_hsin_to_h(norm_circular_hue_centers)

def hcos_hsin_to_h(hh_array):
    h_array = []
    for i in range(hh_array.shape[0]):
        cosinus = hh_array[i][0]
        sinus = hh_array[i][1]
        original = np.arccos(cosinus)
        if (sinus < 0):
            original = (2 * np.pi) - original

        original = original / (2 * np.pi)
        h_array.append(original)
    return np.array(h_array).reshape(-1, 1)

def hhsv_to_hsv(colors):
    h = hh_cluster_centers_to_h_cluster_centers(colors[:,0:2])
    s = colors[:,2].reshape(-1, 1)
    v = colors[:,3].reshape(-1, 1)
    return np.hstack((h, s, v))

def hsv_cluster_centers(colors):
    kmeans_model_hsv = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hsv = kmeans_model_hsv.fit(hsv_colors)
    return kmeans_hsv.cluster_centers_

def get_col_for_property(property):
    if (property == 'h'):
        return 0
    if (property == 's'):
        return 1
    if (property == 'v'):
        return 2
    return -1

def sort_by_property(colors, property):
    return colors[np.argsort(colors[:,get_col_for_property(property)])]

def trim_colors(colors, property, keep):
    sorted = sort_by_property(colors, property)
    return sorted[keep:]

def custom_sort(colors):
    pow_s = 1
    pow_v = 1
    s = colors[:,1]
    v = colors[:,2]
    sort_criteria = -1 * (v + (np.power(s, pow_s) * np.power(v, pow_v)))
    return colors[np.argsort(sort_criteria)]

def filter_by_custom(colors):
    # TODO - Find a way to filter by saturation + value but also
    #        prefer colors with larger delta between each others hues
    return custom_sort(colors)[:n_colors]

def sort_by_v(colors):
    return sort_by_property(colors, 'v')

def sort_by_h(colors):
    return sort_by_property(colors, 'h')

def filter_by_v(colors):
    return trim_colors(colors, 'v', n_colors)

def filter_v_and_sort_by_h(colors):
    v_filtered = filter_by_v(colors)
    h_sorted = sort_by_h(v_filtered)
    return h_sorted

def custom_filter_and_sort(colors):
    return custom_sort(filter_by_v(colors))

def generate_complementary(colors, delta_v = 0.12, delta_s = 0.07):
    base = np.copy(colors)
    num_colors = base.shape[0]
    avg_s = np.sum(colors[:,1]) / num_colors
    avg_v = np.sum(colors[:,2]) / num_colors
    complements = np.zeros(base.shape)
    for i in range(num_colors):
        complements[i] = base[i]
        if (colors[i][2] < avg_v):
            complements[i][2] += delta_v
            complements[i][1] -= delta_s
        else:
            base[i][2] -= delta_v
            base[i][1] += delta_s

    complements = np.clip(complements, 0, 1)
    combined = np.empty((num_colors * 2, 3), dtype = colors.dtype)
    combined[0::2] = base
    combined[1::2] = complements
    return combined

def custom_filter_and_sort_complements(colors):
    print("Pruning similar colors...")
    distance_threshold = 0.015 # all distances between S/V colors larger than that are OK by default
    v_lower_bound = 0.6 # if you can't remove similar colors without making the lowest V of the filtered group fall below this, then don't do it

    # do something about the fact that saturated blues need higher V to be legible

    sorted = sort_by_v(colors)
    above_v_lower_bound = colors[colors[:,2] >= v_lower_bound]

    # distance between two colors' hue/saturation/value
    def dist(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2

    if above_v_lower_bound.shape[0] <= (n_colors // 2):
        result = custom_sort(colors)[:n_colors // 2]
        return generate_complementary(result)

    while above_v_lower_bound.shape[0] > (n_colors // 2):
        closest_pair = [above_v_lower_bound[0], above_v_lower_bound[1]]
        closest_dist = dist(closest_pair[0], closest_pair[1])
        index_1 = 0
        index_2 = 1 # this is so stupid...
        for i in range(len(above_v_lower_bound)):
            a = above_v_lower_bound[i]
            rest = above_v_lower_bound[:]
            rest = np.delete(rest, i, 0)
            # closest = min(
            #     map(lambda b: (dist(a, b), b), rest),
            #     key=lambda p: p[0])

            # soooo... silly >_> all this for an index...
            # look at all these nested loops.. yeesh ;-;
            min_dist_a = np.inf
            index_b = 0
            for j in range(len(above_v_lower_bound)):
                cur_dist = dist(a, above_v_lower_bound[j])
                if i != j and cur_dist < min_dist_a:
                    min_dist_a = cur_dist
                    index_b = j

            if min_dist_a < closest_dist:
                closest_dist = min_dist_a
                index_1 = i
                index_2 = index_b

        if closest_dist > distance_threshold:
            break

        # TODO - be smarter about which of the two colors to remove
        # index = above_v_lower_bound.index(closes_pair[0])
        scored = custom_sort(np.array([above_v_lower_bound[index_1], above_v_lower_bound[index_2]]))
        a = scored[0]
        b = above_v_lower_bound[index_1]
        if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]:
            above_v_lower_bound = np.delete(above_v_lower_bound, index_2, 0)
        else:
            above_v_lower_bound = np.delete(above_v_lower_bound, index_1, 0)

    result = custom_sort(above_v_lower_bound)[:n_colors // 2]
    return generate_complementary(result)

def get_hex_codes(rgb_list):
    hex_codes = []
    for i in range(rgb_list.shape[0]):
        rgb = rgb_list[i]
        hex_codes.append(rgb2hex(rgb[0], rgb[1], rgb[2]))
    return hex_codes

def hex_codes_to_html_list(hex_codes, hsv_colors):
    html = "<ul style='padding: 0; list-style-type: none; margin-right: 20px'>\n"
    for i in range(len(hex_codes)):
        html += "<li style='height: 24px; overflow: hidden; color: " + hex_codes[i] + "'>"
        html += "<p style='font-family: monospace; whitespace: no-wrap; margin-top: -5px; font-size: 18px;'>def a = " + str((100 * np.clip(hsv_colors[i], 0, 1)).astype(int)) + "</p>"
        html += "</li>\n"
    return html + "</ul>\n"

def hsv_colors_to_hex_codes(color_list):
    rgb_normalized = color.convert_colorspace(color_list.reshape(-1, 1, 3), 'HSV', 'RGB')
    rgb_colors = (255 * rgb_normalized.reshape(-1, 3)).astype(int)
    rgb_colors = np.clip(rgb_colors, 0, 255)
    hex_codes = get_hex_codes(rgb_colors)
    return hex_codes

def hsv_color_list_to_html_list(color_list):
    rgb_normalized = color.convert_colorspace(color_list.reshape(-1, 1, 3), 'HSV', 'RGB')
    rgb_colors = (255 * rgb_normalized.reshape(-1, 3)).astype(int)
    rgb_colors = np.clip(rgb_colors, 0, 255)
    hex_codes = get_hex_codes(rgb_colors)
    return hex_codes_to_html_list(hex_codes, color_list.reshape(-1, 3))

def html_color_list(title, colors, col_width = 300):
    html = "<div style='flex-basis: " + str(col_width) + "px;'>"
    html += "<h2 style='color: white;'>" + str(title) + "</h4>"
    html += hsv_color_list_to_html_list(colors)
    html += "</div>"
    return html

def wrap_in_span(text, color):
    return "<span style='font-family:monospace;font-size:18px;color:" + color + ";'>" + text + "</span>"

def get_preview_image(img_file_path, ansi_colors):
    hex = hsv_colors_to_hex_codes(ansi_colors)
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
        (black, ["::"]),
        (yellow, ["tail: "]),
        (magenta, ["@annotation.tailrec", "match", "case", ".", ": "]), 
        (yellow, ["toListRecursive", "toList", "colorscheme", "example", "_", "this", "head", "acc", "tail(", "tail)", " go", "stream", "reverse"]),
        (red, ["= ", "=>"]),
        (green, ["// The natural recursive solution"]),
        (blue, ["List[", " List", "Stream", "A", "Nothing", "Cons", "Empty"]),
        (cyan, ["package", "object", "class", "def", "trait", "import"]),
        (black, ["extends", "+"]),
        (white, ["{", "}", "[", "]", "(", ")", ","])
    ]

    width = 1200
    height = 700
    terminal_padding = 30
    text_padding = 14

    html = "<img src='" + img_file_path + "' style='object-fit: cover; height: " + str(height) + "px; width: " + str(width) + "px; position: absolute; top: 0; left: 0;'/>"
    html += "<div style='z-index: 10; padding: " + str(text_padding) + "px; position: absolute; top: " + str(terminal_padding) + "px; left: " + str(terminal_padding) + "px;right: " + str(terminal_padding) + "px;bottom: " + str(terminal_padding) + "px; background-color: rgba(0, 0, 0, 0.85)'><pre style='margin: 0;'>"

    for group in color_groups:
        for word in group[1]:
            sample = sample.replace(word, wrap_in_span(word, hex[group[0]]))

    lines = sample.split('\n')
    vim = ''
    for i in range(28):
        prefix = str(i + 1) + ' '
        if (i < 10):
            prefix = ' ' + prefix

        prefix = wrap_in_span(prefix, hex[black])
        
        if (i < len(lines)):
            vim += prefix + lines[i] + '\n'
        else:
            vim += wrap_in_span('~\n', hex[black])

    
    html += vim
    html += "</pre></div>"

    img_preview = "<img src='" + img_file_path + "' style='margin-bottom: 40px; object-fit: cover; height: " + str(height) + "px; width: " + str(width) + "px;'/>"

    return img_preview + "<div style='margin-bottom: 200px; height: " + str(height) + "px; width: " + str(width) + "px; overflow: hidden; position: relative;'>" + html + "</div>"

def get_html_contents(center, improved_centers, img_file_path):
    print("generating html preview...")
    html = get_preview_image(img_file_path, custom_filter_and_sort_complements(improved_centers))
    # html += "<div style='display: flex; overflow: scroll;'>"
    # html += html_color_list("3D HSV", sort_by_h(centers))
    # html += html_color_list("Filtered 3D HSV", custom_filter_and_sort(centers))
    # html += html_color_list("4D HSV", sort_by_h(improved_centers))
    # html += html_color_list("Filtered 4D HSV", filter_by_custom(improved_centers))
    # html += html_color_list("Filtered 4D HSV Comp", custom_filter_and_sort_complements(improved_centers))
    # html += "</div>"
    return html

html_contents = ""

for i in range(1, len(sys.argv)):
    print("Generating colors for input " + str(i) + " of " + str(len(sys.argv) - 1))
    img_file_path = sys.argv[i]
    hsv_colors = get_pixels_for_image(img_file_path)
    hhsv_centers = hhsv_cluster_centers(hsv_colors)
    improved_centers = hhsv_to_hsv(hhsv_centers)
    centers = hsv_cluster_centers(hsv_colors)
    html_contents += get_html_contents(centers, improved_centers, img_file_path)
    html =  "<body style='background: #000'>\n"
    html += "<div>"
    html += html_contents
    html += "</div>"
    html += "</body>\n"

    result_file = open("result.html", "w")
    result_file.write(html)
    result_file.close()
