from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from selenium import webdriver
import os
