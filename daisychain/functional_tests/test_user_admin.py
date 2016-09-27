from functional_tests.context import *


class UseradminTestCase(LiveServerTestCase):
    def create_user(self):
        user = User.objects.create_user('Lisa',
                                        'lisa@example.org',
                                        'password',
                                        is_active=True)
        user.is_staff = True
        user.save()
        EmailAddress.objects.create(user=user,
                                    email='lisa@example.org',
                                    primary=True,
                                    verified=True)
        user = User.objects.create_user('Alice',
                                        'alice@example.org',
                                        'password',
                                        is_active=True)
        user.save()
        EmailAddress.objects.create(user=user,
                                    email='alice@example.org',
                                    primary=True,
                                    verified=True)
        user = User.objects.create_user('Bob',
                                        'bob@example.org',
                                        'password',
                                        is_active=True)
        user.save()
        EmailAddress.objects.create(user=user,
                                    email='bobcd @example.org',
                                    primary=True,
                                    verified=True)

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
        self.create_user()

    def tearDown(self):
        self.browser.quit()

    def test_useradmin_table(self):

        # load page
        self.browser.get(self.live_server_url + '/useradmin/')

        # should see a login page
        self.browser.find_element_by_name('login')
        self.browser.find_element_by_name('password')

        # force login for Lisa who is staff
        self.client.force_login(User.objects.get(username="Lisa"))
        cookie = self.client.cookies['sessionid']
        self.browser.add_cookie({'name': 'sessionid',
                                 'value': cookie.value,
                                 'secure': False,
                                 'path': '/'})
        self.browser.refresh()
        self.browser.get(self.live_server_url + '/useradmin/')

        # make sure the page is there
        self.assertNotIn('Not Found', self.browser.page_source)

        # Lisa should see everything
        self.browser.find_element_by_css_selector('table')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(2) td:first-child')
        self.assertEqual(td.text, 'Lisa')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(2) td:nth-child(4)')
        self.assertEqual(td.text, 'lisa@example.org')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(3) td:first-child')
        self.assertEqual(td.text, 'Alice')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(3) td:nth-child(4)')
        self.assertEqual(td.text, 'alice@example.org')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(4) td:first-child')
        self.assertEqual(td.text, 'Bob')

        td = self.browser.find_element_by_css_selector(
                'table tr:nth-child(4) td:nth-child(4)')
        self.assertEqual(td.text, 'bob@example.org')

        # logout Lisa
        self.client.logout()

        # force login for Alice who is NOT staff
        self.client.force_login(User.objects.get(username="Alice"))
        cookie = self.client.cookies['sessionid']
        self.browser.add_cookie({'name': 'sessionid',
                                 'value': cookie.value,
                                 'secure': False,
                                 'path': '/'})
        self.browser.refresh()
        self.browser.get(self.live_server_url + '/useradmin/')

        # detect the custom 403 page
        td = self.browser.find_element_by_css_selector('div.error-template')
