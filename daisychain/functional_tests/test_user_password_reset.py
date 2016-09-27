from functional_tests.context import *


class ResetPasswordTestCase(LiveServerTestCase):
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
        self.create_user()
        self.browser.implicitly_wait(3)
        # Set reCaptcha to Testing-Mode
        os.environ['NORECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        self.browser.implicitly_wait(300)
        self.browser.quit()

    def test_reset_available_execute_done(self):
        self.browser.get(
                self.live_server_url + reverse('account_reset_password'))
        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn('Password Reset', self.browser.page_source)

        email_box = self.browser.find_element_by_id('id_email')
        email_box.send_keys('daisychain_lisa@testingmail.org')
        self.browser.find_element_by_xpath('//button[@type="submit"]').click()

        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn(('We have sent you an e-mail. Please contact us if you '
                       'do not receive it within a few minutes.'),
                      self.browser.page_source)

        # The email has been sent.
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_available_execute_done_with_fakemail(self):
        self.browser.get(
                self.live_server_url + reverse('account_reset_password'))
        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn('Password Reset', self.browser.page_source)

        email_box = self.browser.find_element_by_id('id_email')
        email_box.send_keys('dummy@foo.com')
        self.browser.find_element_by_xpath('//button[@type="submit"]').click()

        self.assertNotIn('Not Found', self.browser.page_source)
        self.assertIn(('We have sent you an e-mail. Please contact us if you '
                       'do not receive it within a few minutes.'),
                      self.browser.page_source)

        # The email has been sent.
        self.assertEqual(len(mail.outbox), 0)
