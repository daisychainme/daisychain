from channel_facebook.config import Config
from .test_base import FacebookBaseTestCase


class ConfigTest(FacebookBaseTestCase):
    def test_set_environment_vars(self):
        self.assertEqual("localhost.daisychain.me", Config.get("DOMAIN_BASE"))

    def test_get(self):
        Config.get("API_BASE_URI")

        with self.assertRaises(KeyError):
            Config.get("NON_EXISTENT_KEY")

        self.assertEqual("defaultValue",
                         Config.get("NON_EXISTENT_KEY", "defaultValue"))
