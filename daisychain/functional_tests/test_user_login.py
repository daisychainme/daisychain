from functional_tests.context import *


class LoginTestCase(LiveServerTestCase):
    def create_user(self):
        user = User.objects.create_user('Lisa',
                                        'daisychain_lisa@testingmail.org',
                                        'hunter22')
        EmailAddress.objects.create(user=user,
                                    email='daisychain_lisa@testingmail.org',
                                    primary=True,
                                    verified=True)
        user.save()

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
        self.create_user()

    def tearDown(self):
        self.browser.quit()

    def test_can_login_to_site(self):
        self.browser.get(self.live_server_url + '/accounts/login/')

        self.assertNotIn('Not Found', self.browser.page_source)

        # Lisa logs into the site
        login_inputbox = self.browser.find_element_by_name('login')
        login_inputbox.send_keys('Lisa')
        password_inputbox = self.browser.find_element_by_name('password')
        password_inputbox.send_keys('hunter22')
        self.browser.find_element_by_xpath('//button[@type="submit"]').click()

        # Redirect to valid site
        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn("Welcome Lisa", self.browser.page_source)

    # User is already logged in and go to loginsite
    def test_user_redirect_if_logged_in(self):
        self.test_can_login_to_site()
        redirect_url = "/home/profile"
        self.browser.get(
                self.live_server_url + '/accounts/login/?next=' + redirect_url)
        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn(redirect_url, self.browser.current_url)
        self.assertIn('Welcome Lisa', self.browser.page_source)
