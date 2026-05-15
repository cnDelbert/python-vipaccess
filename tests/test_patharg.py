"""Tests for patharg module."""

import unittest
import tempfile
import os
from argparse import ArgumentTypeError
from vipaccess.patharg import PathType


class TestPathType(unittest.TestCase):
    """Test PathType class."""

    def test_exists_true_with_existing_file(self):
        """Test PathType with exists=True and existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            path_type = PathType(exists=True, type="file")
            result = path_type(temp_path)
            self.assertEqual(result, temp_path)
        finally:
            os.unlink(temp_path)

    def test_exists_true_with_nonexistent_file(self):
        """Test PathType with exists=True and nonexistent file."""
        path_type = PathType(exists=True, type="file")
        with self.assertRaises(ArgumentTypeError):
            path_type("/nonexistent/path/file.txt")

    def test_exists_false_with_existing_file(self):
        """Test PathType with exists=False and existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            path_type = PathType(exists=False, type="file")
            with self.assertRaises(ArgumentTypeError):
                path_type(temp_path)
        finally:
            os.unlink(temp_path)

    def test_exists_none_with_any_path(self):
        """Test PathType with exists=None (don't care)."""
        path_type = PathType(exists=None, type=None)
        result = path_type("any_file.txt")
        self.assertEqual(result, "any_file.txt")

    def test_type_file_with_directory(self):
        """Test PathType with type=file and directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path_type = PathType(exists=True, type="file")
            with self.assertRaises(ArgumentTypeError):
                path_type(temp_dir)

    def test_type_dir_with_file(self):
        """Test PathType with type=dir and file path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            path_type = PathType(exists=True, type="dir")
            with self.assertRaises(ArgumentTypeError):
                path_type(temp_path)
        finally:
            os.unlink(temp_path)

    def test_type_dir_with_directory(self):
        """Test PathType with type=dir and directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path_type = PathType(exists=True, type="dir")
            result = path_type(temp_dir)
            self.assertEqual(result, temp_dir)

    def test_dash_ok_true(self):
        """Test PathType with dash_ok=True."""
        path_type = PathType(exists=True, type="file", dash_ok=True)
        result = path_type("-")
        self.assertEqual(result, "-")

    def test_dash_ok_false(self):
        """Test PathType with dash_ok=False."""
        path_type = PathType(exists=True, type="file", dash_ok=False)
        with self.assertRaises(ArgumentTypeError):
            path_type("-")

    def test_dash_not_allowed_for_dir(self):
        """Test that dash is not allowed for directory type."""
        path_type = PathType(exists=True, type="dir")
        with self.assertRaises(ArgumentTypeError):
            path_type("-")

    def test_dash_not_allowed_for_symlink(self):
        """Test that dash is not allowed for symlink type."""
        path_type = PathType(exists=True, type="symlink")
        with self.assertRaises(ArgumentTypeError):
            path_type("-")

    def test_custom_type_function(self):
        """Test PathType with custom type function."""

        def custom_validator(path):
            return path.endswith(".txt")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            temp_path = f.name
        try:
            path_type = PathType(exists=True, type=custom_validator)
            result = path_type(temp_path)
            self.assertEqual(result, temp_path)
        finally:
            os.unlink(temp_path)

    def test_custom_type_function_fails(self):
        """Test PathType with custom type function that fails."""

        def custom_validator(path):
            return path.endswith(".txt")

        path_type = PathType(exists=True, type=custom_validator)
        with self.assertRaises(ArgumentTypeError):
            path_type("test.py")

    def test_symlink_type(self):
        """Test PathType with symlink type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            symlink_path = os.path.join(temp_dir, "link")
            target_path = os.path.join(temp_dir, "target")
            with open(target_path, "w") as f:
                f.write("test")
            os.symlink(target_path, symlink_path)
            try:
                path_type = PathType(exists=True, type="symlink")
                result = path_type(symlink_path)
                self.assertEqual(result, symlink_path)
            finally:
                os.unlink(symlink_path)
                os.unlink(target_path)


if __name__ == "__main__":
    unittest.main()
