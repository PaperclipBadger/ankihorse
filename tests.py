import unittest

from ankihorse import updateraddon
from ankihorse.autopicture import imagefetch
from ankihorse.autovoice import audiofetch


def RunTestsForModule(m):
    print('Running tests for {} ...'.format(m.__name__))
    unittest.main(module=m, exit=False)


RunTestsForModule(updateraddon)
RunTestsForModule(imagefetch)
RunTestsForModule(audiofetch)
