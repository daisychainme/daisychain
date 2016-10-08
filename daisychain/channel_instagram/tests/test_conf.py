from django.test import TestCase
from channel_instagram.conf import Config


class ConfigTest(TestCase):

    def test_get(self):

        Config.get("API_BASE_URI")

        with self.assertRaises(KeyError):
            Config.get("NON_EXISTENT_KEY")

        self.assertEqual("defaultValue",
                         Config.get("NON_EXISTENT_KEY", "defaultValue"))
