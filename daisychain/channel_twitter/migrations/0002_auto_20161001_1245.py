# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-01 12:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('channel_twitter', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='twitteraccount',
            options={'verbose_name': 'twitter account', 'verbose_name_plural': 'twitter accounts'},
        ),
    ]