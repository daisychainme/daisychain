from django.test import TestCase
from channel_instagram.conf import Config


class ConfigTest(TestCase):

    def test_set_domain_base(self):

        Config.set_domain_base("test://domain:1111/")
        self.assertEqual("test://domain:1111", Config.get("DOMAIN_BASE"))

        Config.set_domain_base("test://domain:2222")
        self.assertEqual("test://domain:2222", Config.get("DOMAIN_BASE"))

    def test_get(self):

        Config.get("API_BASE_URI")

        with self.assertRaises(KeyError):
            Config.get("NON_EXISTENT_KEY")

        self.assertEqual("defaultValue",
                         Config.get("NON_EXISTENT_KEY", "defaultValue"))
