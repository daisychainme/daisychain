# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-12 14:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RssFeed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feed_url', models.CharField(max_length=2000, verbose_name='Feed URL')),
                ('last_modified', models.DateTimeField()),
            ],
        ),
    ]
