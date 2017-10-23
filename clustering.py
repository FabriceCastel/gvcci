import numpy as np

from sklearn.cluster import MiniBatchKMeans

#
# Constants
#

kmeans_batch_size = 100
n_clusters = 32

#
# HSL <> HHSL methods
#

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

def hsl_to_hhsl(hsl_colors):
    cos_h = np.cos(2 * np.pi * hsl_colors[:,0])
    sin_h = np.sin(2 * np.pi * hsl_colors[:,0])
    hh_colors = np.vstack((cos_h, sin_h)).T

    # scale the size of the hh circle with the lightness for a bicone shape
    hh_colors = 2 * np.multiply(hh_colors, (0.5 - np.abs(0.5 - hsl_colors[:,2])).reshape(-1, 1))

    return np.vstack((hh_colors[:,0], hh_colors[:,1], hsl_colors[:,1], hsl_colors[:,2])).T

def hh_cluster_centers_to_h_cluster_centers(hh_centers):
    circular_hue_center_radii = np.sqrt(np.multiply(hh_centers[:,0], hh_centers[:,0]) + np.multiply(hh_centers[:,1], hh_centers[:,1]))
    circular_hue_center_radii = np.reshape(circular_hue_center_radii, (-1, 1))
    norm_circular_hue_centers = hh_centers / circular_hue_center_radii
    norm_circular_hue_centers = np.clip(norm_circular_hue_centers, -1, 1)
    return hcos_hsin_to_h(norm_circular_hue_centers)

# TODO maybe get a measure for how representative the clusters are for the set and prune the ones that score lower?
def hhsl_cluster_centers_as_hsl(hsl_colors):
    kmeans_model_hhsl = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hhsl = kmeans_model_hhsl.fit(hsl_to_hhsl(hsl_colors))
    labels = kmeans_hhsl.labels_
    
    return hhsl_to_hsl(kmeans_hhsl.cluster_centers_)

def hsl_cluster_centers(hsl_colors):
    kmeans_model_hsl = MiniBatchKMeans(n_clusters = n_clusters, batch_size = kmeans_batch_size)
    kmeans_hsl = kmeans_model_hsl.fit(hsl_colors)
    return kmeans_hsl.cluster_centers_