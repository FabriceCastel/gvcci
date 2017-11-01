import unittest

import numpy as np

from scoring import contrast_between
from converters import hsl2rgb

white_hsl = np.array([0, 0, 1])
black_hsl = np.array([0, 0, 0])
red_hsl = np.array([0, 1, 0.5])

class ScoringTest(unittest.TestCase):
	def test_contrast_between_black_and_white(self):
		self.assertTrue(20.9 <= contrast_between(white_hsl, black_hsl) <= 21)

	def test_contrast_between_self(self):
		self.assertEqual(contrast_between(white_hsl, white_hsl), 1)
		self.assertEqual(contrast_between(black_hsl, black_hsl), 1)

	def test_contrast_pure_black(self):
		self.assertTrue(5.24 <= contrast_between(black_hsl, red_hsl) <= 5.26)
		

if __name__ == '__main__':
    unittest.main()
