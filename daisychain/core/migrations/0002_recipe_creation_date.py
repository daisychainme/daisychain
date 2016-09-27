# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-23 09:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Creation Date'),
        ),
    ]
