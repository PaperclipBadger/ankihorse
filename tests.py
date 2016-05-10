import unittest

suite = unittest.defaultTestLoader.discover('ankihorse', top_level_dir='.')
runner = unittest.TextTestRunner()
runner.run(suite)

