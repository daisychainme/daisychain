from functional_tests.context import *


class UserRegisterTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
        # Set reCaptcha to Testing-Mode
        os.environ['NORECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        self.browser.quit()
        # Set reCaptcha to Testing-Mode
        del os.environ['NORECAPTCHA_TESTING']

    def test_user_registers_different_passwords(self):
        # User story:
        # Lisa opens her web browser and registers at daisychain.me.
        self.browser.get('%s%s' % (self.live_server_url, '/accounts/signup/'))

        # She enters her name, email address and password.
        username_input = self.browser.find_element_by_name("username")
        username_input.send_keys('H4x0r')

        email_input = self.browser.find_element_by_name("email")
        email_input.send_keys('42@1337.org')

        password_input = self.browser.find_element_by_name("password1")
        password_input.send_keys('LuckyLuke1234')
        # TODO: what is the name  of the tag?
        password_confirm_input = self.browser.find_element_by_name("password2")
        password_confirm_input.send_keys('LuckyLuke123')

        self.browser.execute_script(
                "document.getElementById('g-recaptcha-response')"
                ".style.display='block';")
        captcha = self.browser.find_element_by_name("g-recaptcha-response")
        captcha.send_keys('PASSED')
        # A web page is rendered that says
        # that a confirmation link has been sent.

        self.browser.find_element_by_xpath('//button[@type="submit"]').click()
        # self.browser.find_element_by_id('submit').click()
        self.browser.implicitly_wait(30)
        self.assertIn('accounts/signup/', self.browser.current_url)
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('You must type the same password each time.', body.text)

    def test_user_registers(self):
        # User story:
        # Lisa opens her web browser and registers at daisychain.me.
        self.browser.get('%s%s' % (self.live_server_url, '/accounts/signup/'))

        # She enters her name, email address and password.
        username_input = self.browser.find_element_by_name("username")
        username_input.send_keys('Lisa')

        email_input = self.browser.find_element_by_name("email")
        email_input.send_keys('daisychain_lisa@testingmail.org')

        password_input = self.browser.find_element_by_name("password1")
        password_input.send_keys('hunter22')
        # TODO: what is the name  of the tag?
        password_confirm_input = self.browser.find_element_by_name("password2")
        password_confirm_input.send_keys('hunter22')

        self.browser.execute_script(
                "document.getElementById('g-recaptcha-response')"
                ".style.display='block';")
        captcha = self.browser.find_element_by_name("g-recaptcha-response")
        captcha.send_keys('PASSED')
        # A web page is rendered that says
        # that a confirmation link has been sent.

        self.browser.find_element_by_xpath('//button[@type="submit"]').click()
        # self.browser.find_element_by_id('submit').click()
        self.browser.implicitly_wait(30)
        self.assertIn('accounts/confirm-email/', self.browser.current_url)
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('We have sent an e-mail to you for verification',
                      body.text)

        # The email has been sent.
        self.assertEqual(len(mail.outbox), 1)
