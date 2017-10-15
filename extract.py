import os
import sys

import numpy as np

from skimage import io
from skimage import color

from sklearn.cluster import MiniBatchKMeans

# Force prints of the full numpy arrays
# np.set_printoptions(threshold=np.inf)

# Constants
kmeans_batch_size = 100
n_clusters = 32
n_colors = 16 # must be less than or equal to n_clusters
v_threshold = 0.05 # ignore colors darker than this
sort_s_weight = 1
sort_v_weight = 2

# Utils
def rgb2hex(r,g,b):
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex


print("reading image...")
img_file_path = sys.argv[1]
img_rgb = io.imread(img_file_path)

print("converting color space...")
img_hsv = color.convert_colorspace(img_rgb, 'RGB', 'HSV')
hsv_colors = img_hsv.reshape((-1, 3))

print("filtering out darkest colors before clustering for better results...")
samples_before = hsv_colors.shape[0]
hsv_colors = hsv_colors[hsv_colors[:,2] > v_threshold]
samples_after = hsv_colors.shape[0]

print("filtered out " + str(100 - (100 * samples_after) // samples_before) + "% of pixels")

print("initializing kmeans model... this is going to take a while, go grab a coffee or some tea")


# convert the hue component into two values, sin(pi * h) and cos(pi * h)
cos_h = np.cos(2 * np.pi * hsv_colors[:,0])
sin_h = np.sin(2 * np.pi * hsv_colors[:,0])

hh_colors = np.vstack((cos_h, sin_h)).T
hhsv_colors = np.vstack((hh_colors[:,0], hh_colors[:,1], hsv_colors[:,1], hsv_colors[:,2])).T
print(hhsv_colors.shape)

kmeans_model_hhsv = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
kmeans_hhsv = kmeans_model_hhsv.fit(hhsv_colors)

hhsv_centers = kmeans_hhsv.cluster_centers_
circular_hue_centers = hhsv_centers[:,0:2]
circular_hue_center_radii = np.multiply(circular_hue_centers[:,0], circular_hue_centers[:,0]) + np.multiply(circular_hue_centers[:,1], circular_hue_centers[:,1])
circular_hue_center_radii = np.reshape(circular_hue_center_radii, (n_clusters, 1))
norm_circular_hue_centers = circular_hue_centers / circular_hue_center_radii
norm_circular_hue_centers = np.clip(norm_circular_hue_centers, -1, 1)

# Arc Cos returns the x in [0, pi] such that cos(x) = y
#h_centers_arccos = np.arccos(norm_circular_hue_centers[:,0])
#h_centers_arcsin = np.arcsin(norm_circular_hue_centers[:,1])

#h_centers = np.vstack((h_centers_arccos, h_centers_arcsin)).T / (2 * np.pi)

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

h_centers = hcos_hsin_to_h(norm_circular_hue_centers)
s_centers = hhsv_centers[:,2].reshape(-1, 1)
v_centers = hhsv_centers[:,3].reshape(-1, 1)
improved_centers = np.hstack((h_centers, s_centers, v_centers))



# centers = hsv_centers
# </end new stuff>



kmeans_model_hsv = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
kmeans_hsv = kmeans_model_hsv.fit(hsv_colors)
centers = kmeans_hsv.cluster_centers_
# convert the two values for hue back into a single hue value
print(centers)


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
    
# centers_v_filtered = trim_colors(centers, 'v', n_colors)

# Sort all 32 centers found in 3D HSV kmeans
centers_sort_criteria = -1 * (centers[:,1] + np.power(centers[:,2], 2))
sorted_centers = centers[np.argsort(centers_sort_criteria)]

# centers_v_filtered = trim_colors(centers, 'v', n_colors)
# sorted_h_centers = centers_v_filtered[np.argsort(centers_v_filtered[:,0])]

def custom_sort(colors):
    sort_criteria = -1 * (colors[:,1] + np.power(colors[:,2], 2))
    return colors[np.argsort(sort_criteria)]

def sort_by_h(colors):
    return sort_by_property(colors, 'h')

def filter_v_and_sort_by_h(colors):
    v_filtered = trim_colors(colors, 'v', n_colors)
    h_sorted = sort_by_h(v_filtered)
    return h_sorted


print("formatting cluster center results...")

def get_hex_codes(rgb_list):
    hex_codes = []
    for i in range(rgb_list.shape[0]):
        rgb = rgb_list[i]
        hex_codes.append(rgb2hex(rgb[0], rgb[1], rgb[2]))
    return hex_codes

def hex_codes_to_html_list(hex_codes, hsv_colors):
    html = "<ul style='padding: 0; list-style-type: none; margin-right: 20px'>\n"
    for i in range(len(hex_codes)):
        html += "<li style='height: 20px; background: " + hex_codes[i] + "'>"
        html += "HSV: (" + str((255 * hsv_colors[i]).astype(int)) + ")"
        html += "</li>\n"
    return html + "</ul>\n"

def hsv_color_list_to_html_list(color_list):
    rgb_normalized = color.convert_colorspace(color_list.reshape(-1, 1, 3), 'HSV', 'RGB')
    rgb_colors = (255 * rgb_normalized.reshape(-1, 3)).astype(int)
    hex_codes = get_hex_codes(rgb_colors)
    return hex_codes_to_html_list(hex_codes, color_list.reshape(-1, 3))

def html_color_list(title, colors, col_width = 300):
    html = "<div style='flex-basis: " + str(col_width) + "px;'>"
    html += "<h2 style='color: white;'>" + str(title) + "</h4>"
    html += hsv_color_list_to_html_list(colors)
    html += "</div>"
    return html

print("generating html preview...")
html =  "<body style='background: #000'><img src='" + img_file_path + "' style='max-width: 100%'/>\n"
html += "<div style='display: flex'>"
html += html_color_list("3D HSV", sort_by_h(centers))
html += html_color_list("Filtered 3D HSV", filter_v_and_sort_by_h(centers))
html += html_color_list("4D HSV", sort_by_h(improved_centers))
html += html_color_list("Filtered 4D HSV", filter_v_and_sort_by_h(improved_centers))
html += "</div>"
html += "</body>\n"

result_file = open("result.html", "w")
result_file.write(html)
result_file.close()
