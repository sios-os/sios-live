"""Integration tests for string_toolkit."""
import unittest
import sys
sys.path.insert(0, ".")

class TestStringToolkit(unittest.TestCase):
    def test_imports(self):
        """Verify the project code can be imported."""
        # The main code is executed as a module
        # This is a smoke test — specific tests would be added per project
        try:
            exec(open(__file__.replace("tests.py", "main.py")).read(), {})
        except Exception as e:
            self.fail(f"Failed to load project code: {e}")

    def test_has_functions(self):
        """Verify the project code defines at least one function."""
        ns = {}
        exec(open(__file__.replace("tests.py", "main.py")).read(), ns)
        funcs = [k for k, v in ns.items() if callable(v) and not k.startswith("_")]
        self.assertGreater(len(funcs), 0, "No functions defined in project code")

if __name__ == "__main__":
    unittest.main()
