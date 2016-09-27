# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-21 14:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('username', models.CharField(max_length=256)),
                ('expire_date', models.DateField(auto_now_add=True)),
                ('last_post_id', models.TextField()),
                ('last_post_time', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Facebook Account',
                'verbose_name_plural': 'Facebook Accounts',
            },
        ),
    ]
