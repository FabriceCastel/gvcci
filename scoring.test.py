import unittest

import numpy as np

from scoring import contrast_between, clip_between_boundaries

white_hsl = np.array([0, 0, 1])
black_hsl = np.array([0, 0, 0])
red_hsl = np.array([0, 1, 0.5])
dark_red_hsl = np.array([0, 1, 0.2])
light_red_hsl = np.array([0, 1, 0.95])

class ScoringTest(unittest.TestCase):
	def test_contrast_between_black_and_white(self):
		self.assertTrue(20.9 <= contrast_between(white_hsl, black_hsl) <= 21)

	def test_contrast_between_self(self):
		self.assertEqual(contrast_between(white_hsl, white_hsl), 1)
		self.assertEqual(contrast_between(black_hsl, black_hsl), 1)

	def test_contrast_pure_black(self):
		self.assertTrue(5.24 <= contrast_between(black_hsl, red_hsl) <= 5.26)

	def test_clip_between_boundaries_good_value(self):
		clipped = clip_between_boundaries(red_hsl, black_hsl, white_hsl, 1, 1)[0]
		self.assertEqual(clipped[0], red_hsl[0])
		self.assertEqual(clipped[1], red_hsl[1])
		self.assertEqual(clipped[2], red_hsl[2])

	def test_clip_between_boundaries_value_too_dark(self):
		clipped = clip_between_boundaries(dark_red_hsl, black_hsl, white_hsl, 4.5, 1)[0]
		clipped_contrast_black = contrast_between(clipped, black_hsl)
		clipped_contrast_white = contrast_between(clipped, white_hsl)

		self.assertEqual(clipped[0], 0)
		self.assertEqual(clipped[1], 1)
		self.assertTrue(0.4 < clipped[2] < 0.6)
		self.assertTrue(4.5 <= clipped_contrast_black <= 5)
		self.assertTrue(clipped_contrast_white >= 1)

	def test_clip_between_boundaries_value_too_light(self):
		clipped = clip_between_boundaries(light_red_hsl, black_hsl, white_hsl, 4.5, 4.5)[0]
		clipped_contrast_black = contrast_between(clipped, black_hsl)
		clipped_contrast_white = contrast_between(clipped, white_hsl)

		self.assertEqual(clipped[0], 0)
		self.assertEqual(clipped[1], 1)
		self.assertTrue(0.4 < clipped[2])
		self.assertTrue(4.5 <= clipped_contrast_black)
		self.assertTrue(4.5 <= clipped_contrast_white <= 5)
		

if __name__ == '__main__':
    unittest.main()
