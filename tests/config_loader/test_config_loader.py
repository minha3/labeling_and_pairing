import os
import unittest

from random import choice
from string import ascii_lowercase

from config import load_config


class TestConfigLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.dirname(os.path.realpath(__file__))

    def test_load_default_config(self):
        conf = load_config()
        self.assertIs(type(conf), dict)

    def test_load_custom_config(self):
        conf = load_config(dirname=self.config_dir)
        self.assertIs(type(conf), dict)

    def test_read_envs(self):
        env_key = 'LAP_UNITTEST_KEY1'
        env_val = ''.join(choice(ascii_lowercase) for _ in range(8))

        os.environ.update({env_key: env_val})
        conf = load_config(dirname=self.config_dir)
        self.assertIs(type(conf), dict)
        self.assertEqual(env_val, conf['unittest']['key1'])

        # clear
        os.environ.pop(env_key)

    def test_ignore_envs(self):
        env_key = 'LAP_UNITTEST_KEY2'
        env_val = ''.join(choice(ascii_lowercase) for _ in range(8))

        os.environ.update({env_key: env_val})
        conf = load_config(dirname=self.config_dir, read_envs=False)
        self.assertNotEqual(env_val, conf['unittest']['key2'])

        # clear
        os.environ.pop(env_key)


if __name__ == '__main__':
    unittest.main()
