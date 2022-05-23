import unittest
from req_provider import RequirementsProvider


class TestProvider(unittest.TestCase):

    def __init__(self) -> None:
        self.provider = RequirementsProvider("/RS/RS.mixml")

    def setUp(self) -> None:
        # создать слой с названием из системы требований
        # создать объекты с атрибутами

        pass

    def test_saving(self) -> None:
        a = 2
        b = 4
        self.assertEqual(a * b, 8)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
