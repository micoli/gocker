import unittest

if __name__ == "__main__":
    suite1 = unittest.defaultTestLoader.discover("./", pattern='test*.py')
    runner1 = unittest.TextTestRunner()
    runner1.run(suite1)
