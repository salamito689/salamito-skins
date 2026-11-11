import unittest
from scripts.probe_youpin_batch import run

class BatchInputTests(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError): run([])
    def test_duplicate(self):
        with self.assertRaises(ValueError): run(["123", "123"])
    def test_over_limit(self):
        with self.assertRaises(ValueError): run([str(x) for x in range(6)])
    def test_non_numeric(self):
        with self.assertRaises(ValueError): run(["123; echo bad"])
if __name__ == "__main__": unittest.main()
