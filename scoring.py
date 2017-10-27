import numpy as np

from colorgenerator import generate_complementary

# TODO move out of here
n_colors = 16

# --- OLD ---

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

def inv_custom_sort(colors):
    pow_s = 1
    pow_v = 1
    s = colors[:,1]
    v = -1 * colors[:,2]

    sort_criteria = -1 * (v + (np.power(s, pow_s) * np.power(v, pow_v)))
    return colors[np.argsort(sort_criteria)]

def custom_sort(colors, bg_color):
    if (bg_color[2] > 0.5):
        return inv_custom_sort(colors)

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


def adjust_contrast(colors, bg):
    min_contrast = 0.35
    fixed_colors = np.array([]).reshape(0, 3)
    for color in colors:
        delta = np.abs(color[2] - bg[2])
        fixed_color = color
        if delta < min_contrast:
            if bg[2] > 0.5:
                fixed_color[2] -= delta
            else:
                fixed_color[2] += delta
        fixed_colors = np.vstack((fixed_colors, fixed_color))
    return fixed_colors


def custom_filter_and_sort_complements(colors, bg_color):
    print("Pruning similar colors...")
    distance_threshold = 0.015 # all distances between S/V colors larger than that are OK by default
    min_contrast = 0.35

    above_min_contrast_threshold = colors[contrast_between_all(colors, bg_color) >= min_contrast]

    def dist(a, b):
        return distance_between_colors(a, b)

    if above_min_contrast_threshold.shape[0] <= (n_colors // 2):
        above_min_contrast_threshold = custom_sort(colors, bg_color)[:n_colors // 2]
        # result = custom_sort(colors, bg_color)[:n_colors // 2]
        # return generate_complementary(result), bg_color

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
    result = adjust_contrast(result, bg_color)

    return generate_complementary(result), bg_color


# --- NEW ---

# CONSTANTS
black = np.array([[0, 0, 0]])
white = np.array([[0, 0, 1]])

def mode_rows(a):
    a = np.ascontiguousarray(a)
    void_dt = np.dtype((np.void, a.dtype.itemsize * np.prod(a.shape[1:])))
    _, ids, count = np.unique(a.view(void_dt).ravel(), return_index=1,return_counts=1)
    largest_count_id = ids[count.argmax()]
    return a[largest_count_id], np.max(count)

def clip_between_boundaries(hsl_colors, dark_boundary = black, light_boundary = white, min_contrast = 0.4):
    fixed_colors = np.array([]).reshape(0, 3)
    for color in hsl_colors:
        dark_delta = np.abs(color[2] - dark_boundary[0][2])
        light_delta = np.abs(light_boundary[0][2] - color[2])

        fixed_color = color.copy()
        
        if dark_delta < min_contrast:
            fixed_color[2] += dark_delta
        elif light_delta < min_contrast:
            fixed_color[2] -= light_delta

        fixed_colors = np.vstack((fixed_colors, fixed_color))

    return fixed_colors

def find_nearest_pair(colors):
    closest_pair = [colors[0], colors[1]]
    closest_dist = dist(colors[0], colors[1])
    index_1 = 0
    index_2 = 1 # this is so stupid...
    
    for i in range(len(colors)):
        a = colors[i]
        rest = colors[:]
        rest = np.delete(rest, i, 0)

        # soooo... silly >_> all this for an index...
        # look at all these nested loops.. yeesh ;-;
        min_dist_a = np.inf
        index_b = 0
        for j in range(len(colors)):
            cur_dist = distance_between_colors(a, colors[j])
            if i != j and cur_dist < min_dist_a:
                min_dist_a = cur_dist
                index_b = j

        if min_dist_a < closest_dist:
            closest_dist = min_dist_a
            index_1 = i
            index_2 = index_b

    return (index_1, index_2)

def pick_n_best_colors(n_colors, hsl_colors, dark_boundary = black, light_boundary = white, min_contrast = 0.4):
    def contrast_between_boundaries(colors):
        dark_contrast = contrast_between_all(colors, dark_boundary)
        light_contrast = contrast_between_all(colors, light_boundary)
        return np.minimum(dark_contrast, light_contrast)

    def sort_by_contrast(colors):
        return colors[np.argsort(-1 * contrast_between_boundaries(colors))]

    def filter_within_bounds(colors, contrast_threshold):
        return colors[contrast_between_boundaries(colors) >= contrast_threshold]

    within_bounds = filter_within_bounds(hsl_colors, min_contrast)
    print("Found " + str(len(within_bounds)) + " qualified color candidates")

    if len(within_bounds) <= n_colors:
        within_bounds = sort_by_contrast(hsl_colors)[:n_colors]

    while len(within_bounds) > n_colors:
        pair = find_nearest_pair(within_bounds)
        scored = sort_by_contrast(np.array([within_bounds[pair[0]], within_bounds[pair[1]]]))
        a = scored[0]
        b = within_bounds[index_1]
        if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]:
            within_bounds = np.delete(within_bounds, pair[1], 0)
        else:
            within_bounds = np.delete(within_bounds, pair[0], 0)

    return within_bounds

# number of dar, mid-tones and light colors needed
def pick_best(hsl_colors, num_dark, num_mid, num_light):
    return [], [], []

def find_dominant_by_frequency(hsl_colors):
    dominant_dark = black
    dominant_light = white
    dark_frequency = 0
    light_frequency = 0

    precision = 32
    dark_l = 0.2;
    light_l = 0.8;
    light_l_upper = 0.95;
    light_s_upper = 0.4;

    light_colors = hsl_colors[hsl_colors[:,2] > light_l]
    light_colors = light_colors[light_colors[:,2] < light_l_upper]
    light_colors = light_colors[light_colors[:,1] < light_s_upper]

    dark_colors = hsl_colors[hsl_colors[:,2] < dark_l]

    if len(dark_colors) > 0:
        dominant_dark, dark_frequency = mode_rows((dark_colors * precision).astype(int))
        dominant_dark = dominant_dark.reshape(1, 3) / precision

    if len(light_colors) > 0:
        dominant_light, light_frequency = mode_rows((light_colors * precision).astype(int))
        dominant_light = dominant_light.reshape(1, 3) / precision

    if dark_frequency >= light_frequency:
        return (dominant_dark, dominant_light)
    else:
        return (dominant_light, dominant_dark)



