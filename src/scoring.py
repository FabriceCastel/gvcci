import numpy as np

from converters import hsllist2rl, hsl2rl


def contrast_between(a, b):
    rl_a = hsl2rl(a)
    rl_b = hsl2rl(b)
    rl_max = max(rl_a, rl_b)
    rl_min = min(rl_a, rl_b)
    return (rl_max + 0.05) / (rl_min + 0.05)

def contrast_between_all(a, b):
    rl_a = hsllist2rl(a)
    rl_b = hsl2rl(b)
    rl_max = np.maximum(rl_a, rl_b)
    rl_min = np.minimum(rl_a, rl_b)
    return (rl_max + 0.05) / (rl_min + 0.05)

def distance_measures_between_colors(a, b):
    # HSL looks like a bicone

    # adjust the saturation component for more accurate distance calculation
    sa = 2 * (0.5 - abs(0.5 - a[2])) * a[1]
    sb = 2 * (0.5 - abs(0.5 - b[2])) * b[1]
    ds = sa - sb

    # hue is circular
    #
    # 0            1/0            1
    # |---A-----B---|
    #               |---A-----B---|
    # 
    #           |---|---|
    #           1-B + A
    #
    #     |---------|---------|
    #        1 - A  +    B
    #
    #     |-----|
    #      B - A
    #
    dh = min(abs(a[0] - b[0]), abs(1 - a[0] - b[0]))

    dl = a[2] - b[2]

    return abs(dh), abs(ds), abs(dl)


def distance_between_colors(a, b):
    dh, ds, dl = distance_measures_between_colors(a, b)
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

def mode_rows(a):
    a = np.ascontiguousarray(a)
    void_dt = np.dtype((np.void, a.dtype.itemsize * np.prod(a.shape[1:])))
    _, ids, count = np.unique(a.view(void_dt).ravel(), return_index=1,return_counts=1)
    largest_count_id = ids[count.argmax()]
    return a[largest_count_id], np.max(count)

def contrast_between_boundaries(colors, dark_boundary, light_boundary, min_dark_contrast, min_light_contrast):
    dark_contrast = contrast_between_all(colors, dark_boundary)
    light_contrast = contrast_between_all(colors, light_boundary)
    
    if (min_dark_contrast > min_light_contrast):
        light_contrast += min_dark_contrast - min_light_contrast
    elif (min_light_contrast > min_dark_contrast):
        dark_contrast += min_light_contrast - min_dark_contrast

    return np.minimum(dark_contrast, light_contrast)

def clip_between_boundaries(hsl_colors, dark_boundary, light_boundary, min_dark_contrast, min_light_contrast):
    hsl_colors = hsl_colors.reshape(-1, 3)
    dark_contrast = contrast_between_all(hsl_colors, dark_boundary)
    light_contrast = contrast_between_all(hsl_colors, light_boundary)

    increment = 0.01

    for i in range(len(hsl_colors)):

        while (dark_contrast[i] < min_dark_contrast):
            hsl_colors[i][2] += increment
            if hsl_colors[i][2] > 1:
                hsl_colors[i][2] = 1
                break;
            dark_contrast = contrast_between_all(hsl_colors, dark_boundary)

        # recompute the light contrast once the dark contrast is adjusted
        light_contrast = contrast_between_all(hsl_colors, light_boundary)

        while (light_contrast[i] < min_light_contrast):
            hsl_colors[i][2] -= increment
            if hsl_colors[i][2] < 0:
                hsl_colors[i][2] = 0
                break;
            light_contrast = contrast_between_all(hsl_colors, light_boundary)

    return hsl_colors

def find_nearest_pair(colors):
    closest_pair = [colors[0], colors[1]]
    closest_dist = distance_between_colors(colors[0], colors[1])
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

def pick_n_best_colors_with_reference(n_colors, hsl_colors, ansi_reference, dark_boundary, light_boundary, dark_min_contrast, light_min_contrast):
    max_contrast_requirement = max(dark_min_contrast, light_min_contrast)

    # remove exact duplicates
    hsl_unique_colors = np.vstack({tuple(row) for row in hsl_colors})
    hsl_colors = hsl_unique_colors
    while(len(hsl_colors) < n_colors):
        # needs to output at least n_colors
        hsl_colors = np.vstack((hsl_colors, hsl_unique_colors))

    def boundary_contrast(colors):
        return contrast_between_boundaries(colors, dark_boundary, light_boundary, dark_min_contrast, light_min_contrast)

    def sort_by_contrast(colors):
        return colors[np.argsort(-1 * boundary_contrast(colors))]

    def filter_within_bounds(colors, contrast_threshold):
        return colors[boundary_contrast(colors) >= contrast_threshold]

    within_bounds = filter_within_bounds(hsl_colors, max_contrast_requirement)

    if len(within_bounds) <= n_colors:
        # TODO make sure the unfiltered hsl_colors don't yield poor results - if they do, revert
        within_bounds = hsl_colors # sort_by_contrast(hsl_colors)[:n_colors]

    return sort_colors_by_closest_counterpart(within_bounds, ansi_reference)

def pick_n_best_colors(n_colors, hsl_colors, dark_boundary, light_boundary, dark_min_contrast, light_min_contrast):
    max_contrast_requirement = max(dark_min_contrast, light_min_contrast)

    # remove exact duplicates
    hsl_unique_colors = np.vstack({tuple(row) for row in hsl_colors})
    hsl_colors = hsl_unique_colors
    while(len(hsl_colors) < n_colors):
        # needs to output at least n_colors
        hsl_colors = np.vstack((hsl_colors, hsl_unique_colors))

    def boundary_contrast(colors):
        return contrast_between_boundaries(colors, dark_boundary, light_boundary, dark_min_contrast, light_min_contrast)

    def sort_by_contrast(colors):
        return colors[np.argsort(-1 * boundary_contrast(colors))]

    def filter_within_bounds(colors, contrast_threshold):
        return colors[boundary_contrast(colors) >= contrast_threshold]

    within_bounds = filter_within_bounds(hsl_colors, max_contrast_requirement)

    if len(within_bounds) <= n_colors:
        within_bounds = sort_by_contrast(hsl_colors)[:n_colors]

    while len(within_bounds) > n_colors:
        pair = find_nearest_pair(within_bounds)
        scored = sort_by_contrast(np.array([within_bounds[pair[0]], within_bounds[pair[1]]]))
        a = scored[0]
        b = within_bounds[pair[0]]

        if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]:
            within_bounds = np.delete(within_bounds, pair[1], 0)
        else:
            within_bounds = np.delete(within_bounds, pair[0], 0)

    return within_bounds

def find_dominant_by_frequency(hsl_colors):
    dark_frequency_boost = 2.0 # prefer dark backgrounds over light
    dominant_dark = np.array([[0, 0, 0]]) # black
    dominant_light = np.array([[0, 0, 1]]) # white
    dark_frequency = 0
    light_frequency = 0

    precision = 32
    dark_l = 0.2
    light_l = 0.7
    light_l_upper = 0.95

    light_colors = hsl_colors[hsl_colors[:,2] > light_l]
    light_colors = light_colors[light_colors[:,2] < light_l_upper]

    dark_colors = hsl_colors[hsl_colors[:,2] < dark_l]

    if len(dark_colors) > 0:
        dominant_dark, dark_frequency = mode_rows((dark_colors * precision).astype(int))
        dominant_dark = dominant_dark.reshape(1, 3) / precision

    if len(light_colors) > 0:
        dominant_light, light_frequency = mode_rows((light_colors * precision).astype(int))
        dominant_light = dominant_light.reshape(1, 3) / precision

    if (dark_frequency * dark_frequency_boost) >= light_frequency:
        return (dominant_dark, dominant_light)
    else:
        return (dominant_light, dominant_dark)

def sort_colors_by_closest_counterpart(hsl_colors, hsl_counterparts):
    hsl_colors_copy = hsl_colors.copy()
    hsl_colors_sorted = []
    for counterpart in hsl_counterparts:
        closest_index = 0
        closest_dist = 10000
        for i in range(len(hsl_colors_copy)):
            dh, ds, dl = distance_measures_between_colors(hsl_colors_copy[i], counterpart)
            dist = (dh ** 2) * (1 + ds) * (1.5 + dl) if (0.2 <= counterpart[2] <= 0.8) else dl
            if (dist < closest_dist):
                closest_index = i
                closest_dist = dist

        hsl_colors_sorted.append(hsl_colors_copy[closest_index])
        hsl_colors_copy = np.vstack((hsl_colors_copy[:closest_index], hsl_colors_copy[closest_index + 1:]))

    return np.array(hsl_colors_sorted)

