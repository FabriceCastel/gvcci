import os
import sys

import numpy as np

from skimage import io
# from skimage import color

from sklearn.cluster import MiniBatchKMeans

import hasel

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
    img_hsl = hasel.rgb2hsl(img_rgb)
    hsl_colors = img_hsl.reshape((-1, 3))

    # print("filtering out darkest colors before clustering for better results...")
    # samples_before = hsl_colors.shape[0]
    # hsl_colors = hsl_colors[hsl_colors[:,2] > v_threshold]
    # samples_after = hsl_colors.shape[0]

    # print("filtered out " + str(100 - (100 * samples_after) // samples_before) + "% of pixels")
    return hsl_colors

# convert the hue component into two values, sin(pi * h) and cos(pi * h)
def hsl_to_hhsl(hsl_colors):
    cos_h = np.cos(2 * np.pi * hsl_colors[:,0])
    sin_h = np.sin(2 * np.pi * hsl_colors[:,0])
    hh_colors = np.vstack((cos_h, sin_h)).T

    # scale the size of the hh circle with the lightness for a bicone shape
    hh_colors = 2 * np.multiply(hh_colors, (0.5 - np.abs(0.5 - hsl_colors[:,2])).reshape(-1, 1))

    return np.vstack((hh_colors[:,0], hh_colors[:,1], hsl_colors[:,1], hsl_colors[:,2])).T

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

# TODO maybe get a measure for how representative the clusters are for the set and prune the ones that score lower?
def hhsl_cluster_centers(colors):
    kmeans_model_hhsl = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hhsl = kmeans_model_hhsl.fit(hsl_to_hhsl(colors))
    labels = kmeans_hhsl.labels_
    
    return kmeans_hhsl.cluster_centers_

def hh_cluster_centers_to_h_cluster_centers(hh_centers):
    circular_hue_center_radii = np.sqrt(np.multiply(hh_centers[:,0], hh_centers[:,0]) + np.multiply(hh_centers[:,1], hh_centers[:,1]))
    circular_hue_center_radii = np.reshape(circular_hue_center_radii, (-1, 1))
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

def hhsl_to_hsl(colors):
    h = hh_cluster_centers_to_h_cluster_centers(colors[:,0:2])
    s = colors[:,2].reshape(-1, 1)
    v = colors[:,3].reshape(-1, 1)
    return np.hstack((h, s, v))

def hsl_cluster_centers(colors):
    kmeans_model_hsl = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hsl = kmeans_model_hsl.fit(hsl_colors)
    return kmeans_hsl.cluster_centers_

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

# TODO add legit implementation for this!
# https://webaim.org/resources/contrastchecker/
# TODO !!!
def contrast_between(a, b):
    return np.abs(a[2] - b[2])

def contrast_between_all(a, b):
    return np.abs(a.reshape(-1, 3)[:,2] - b.reshape(-1, 3)[:,2])

def custom_sort(colors, bg_color):
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

# TODO use a combination of contrast and delta hue here?
def distance_between_colors(a, b):
    # HSL looks like a bicone, the distance function should take this into account

    # adjust the saturation component for more accurate distance calculation
    sa = 2 * (0.5 - abs(0.5 - a[2])) * a[1]
    sb = 2 * (0.5 - abs(0.5 - b[2])) * b[2]
    ds = sa - sb

    dh = a[0] - b[0]
    dl = a[2] - b[2]

    return (dh ** 2) + (ds ** 2) + (dl ** 2)

def custom_filter_and_sort_complements(colors, bg_color = np.array([1, 1, 1])):
    print("Pruning similar colors...")
    distance_threshold = 0.015 # all distances between S/V colors larger than that are OK by default
    min_contrast = 0.4

    above_min_contrast_threshold = colors[contrast_between_all(colors, bg_color) >= min_contrast]

    def dist(a, b):
        return distance_between_colors(a, b)

    if above_min_contrast_threshold.shape[0] <= (n_colors // 2):
        result = custom_sort(colors, bg_color)[:n_colors // 2]
        return generate_complementary(result)

    while above_min_contrast_threshold.shape[0] > (n_colors // 2):
        closest_pair = [above_min_contrast_threshold[0], above_min_contrast_threshold[1]]
        closest_dist = dist(closest_pair[0], closest_pair[1])
        index_1 = 0
        index_2 = 1 # this is so stupid...
        for i in range(len(above_min_contrast_threshold)):
            a = above_min_contrast_threshold[i]
            rest = above_min_contrast_threshold[:]
            rest = np.delete(rest, i, 0)
            # closest = min(
            #     map(lambda b: (dist(a, b), b), rest),
            #     key=lambda p: p[0])

            # soooo... silly >_> all this for an index...
            # look at all these nested loops.. yeesh ;-;
            min_dist_a = np.inf
            index_b = 0
            for j in range(len(above_min_contrast_threshold)):
                cur_dist = dist(a, above_min_contrast_threshold[j])
                if i != j and cur_dist < min_dist_a:
                    min_dist_a = cur_dist
                    index_b = j

            if min_dist_a < closest_dist:
                closest_dist = min_dist_a
                index_1 = i
                index_2 = index_b

        if closest_dist > distance_threshold:
            print('Colors are now different enough to stop pruning')
            break
        else:
            print('Colors are still similar, pruning...')

        # TODO - be smarter about which of the two colors to remove
        # index = above_min_contrast_threshold.index(closes_pair[0])
        scored = custom_sort(np.array([above_min_contrast_threshold[index_1], above_min_contrast_threshold[index_2]]), bg_color)
        a = scored[0]
        b = above_min_contrast_threshold[index_1]
        if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]:
            above_min_contrast_threshold = np.delete(above_min_contrast_threshold, index_2, 0)
        else:
            above_min_contrast_threshold = np.delete(above_min_contrast_threshold, index_1, 0)

    result = custom_sort(above_min_contrast_threshold, bg_color)[:n_colors // 2]

    bg_and_fg = np.array([[1, 1, 1], [1, 1, 1]]).reshape(-1, 3)

    return np.vstack((bg_and_fg, generate_complementary(result)))

def get_hex_codes(rgb_list):
    hex_codes = []
    for i in range(rgb_list.shape[0]):
        rgb = rgb_list[i]
        hex_codes.append(rgb2hex(rgb[0], rgb[1], rgb[2]))
    return hex_codes

def hex_codes_to_html_list(hex_codes, hsl_colors):
    html = "<ul style='padding: 0; list-style-type: none; margin-right: 20px'>\n"
    for i in range(len(hex_codes)):
        html += "<li style='height: 24px; overflow: hidden; color: " + hex_codes[i] + "'>"
        html += "<p style='font-family: monospace; whitespace: no-wrap; margin-top: -5px; font-size: 18px;'>def a = " + str((100 * np.clip(hsl_colors[i], 0, 1)).astype(int)) + "</p>"
        html += "</li>\n"
    return html + "</ul>\n"

def hsl_colors_to_hex_codes(color_list):
    rgb_colors = hasel.hsl2rgb(color_list.reshape(-1, 1, 3)).reshape(-1, 3)
    rgb_colors = np.clip(rgb_colors, 0, 255)
    hex_codes = get_hex_codes(rgb_colors)
    return hex_codes

def hsl_color_list_to_html_list(color_list):
    hex_codes = hsl_colors_to_hex_codes(color_list)
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
    hex = hsl_colors_to_hex_codes(np.vstack((bg_and_fg_colors, ansi_colors)))

    bg_color = hex[0]
    fg_color = hex[1]

    bg_rgb = h = tuple(int(hex[0].lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))

    hex = hex[2:]

    print("===============================================")
    print("ANSI color scheme for " + img_file_path)
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
        (black, ["::"]),
        (yellow, ["tail: "]),
        (white, [": "]),
        (magenta, ["@annotation.tailrec", "match", "case", "."]), 
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
    html += "<div style='z-index: 10; padding: " + str(text_padding) + "px; position: absolute; top: " + str(terminal_padding) + "px; left: " + str(terminal_padding) + "px;right: " + str(terminal_padding) + "px;bottom: " + str(terminal_padding) + "px; background-color: rgba(" + str(bg_rgb[0]) + ", " +str(bg_rgb[1]) + ", " +str(bg_rgb[2]) + ", 0.85)'><pre style='margin: 0;'>"

    for group in color_groups:
        for word in group[1]:
            sample = sample.replace(word, wrap_in_span(word, hex[group[0]]))

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
    print("generating html preview...")
    html = get_preview_image(img_file_path, custom_filter_and_sort_complements(improved_centers, bg_and_fg_colors[0]), bg_and_fg_colors)
    # html += "<div style='display: flex; overflow: scroll;'>"
    # html += html_color_list("3D HSL", sort_by_h(centers))
    # html += html_color_list("Filtered 3D HSL", custom_filter_and_sort(centers))
    # html += html_color_list("4D HSL", sort_by_h(improved_centers))
    # html += html_color_list("Filtered 4D HSL", filter_by_custom(improved_centers))
    # html += html_color_list("Filtered 4D HSL Comp", custom_filter_and_sort_complements(improved_centers))
    # html += "</div>"
    return html

html_contents = ""

for i in range(1, len(sys.argv)):
    print("Generating colors for input " + str(i) + " of " + str(len(sys.argv) - 1))
    img_file_path = sys.argv[i]
    hsl_colors = get_pixels_for_image(img_file_path)
    hhsl_centers = hhsl_cluster_centers(hsl_colors)
    improved_centers = hhsl_to_hsl(hhsl_centers)
    centers = hsl_cluster_centers(hsl_colors)

    precision = 32
    bg_color = mode_rows((hsl_colors * precision).astype(int)).reshape(1, 3) / precision
    bg_fg_colors = np.vstack((bg_color, bg_color))

    # improved_centers = np.vstack((bg_fg_colors, improved_centers))

    html_contents += get_html_contents(centers, improved_centers, bg_fg_colors, img_file_path)
    html =  "<body style='background: #000'>\n"
    html += "<div>"
    html += html_contents
    html += "</div>"
    html += "</body>\n"

    result_file = open("examples.html", "w")
    result_file.write(html)
    result_file.close()
