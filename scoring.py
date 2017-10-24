import numpy as np

from colorgenerator import generate_complementary

# TODO move out of here
n_colors = 16

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
        print(scored)
        if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]:
            above_min_contrast_threshold = np.delete(above_min_contrast_threshold, index_2, 0)
        else:
            above_min_contrast_threshold = np.delete(above_min_contrast_threshold, index_1, 0)

    result = custom_sort(above_min_contrast_threshold, bg_color)[:n_colors // 2]
    result = adjust_contrast(result, bg_color)

    return generate_complementary(result), bg_color
