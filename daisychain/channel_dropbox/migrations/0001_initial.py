# -*- coding: utf-8 -*-

# Generated by Django 1.9.6 on 2016-08-17 09:06

# Generated by Django 1.9.6 on 2016-07-14 17:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DropboxAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(max_length=255, verbose_name='Access Token')),
                ('cursor', models.CharField(max_length=255, verbose_name='Cursor')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Dropbox Account',
                'verbose_name_plural': 'Dropbox Accounts',
            },
        ),
        migrations.CreateModel(
            name='DropboxUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dropbox_userid', models.CharField(max_length=255, verbose_name='DropBox User ID')),
                ('display_name', models.CharField(max_length=100, verbose_name='DropBox Display Name')),
                ('email', models.CharField(max_length=100, verbose_name='email')),
                ('profile_photo_url', models.CharField(max_length=255, null=True, verbose_name='email')),
                ('disk_used', models.DecimalField(decimal_places=4, max_digits=12, verbose_name='Used Disk Space')),
                ('disk_allocated', models.DecimalField(decimal_places=4, max_digits=12, verbose_name='Total Allocated Disk Usage')),
                ('dropbox_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='channel_dropbox.DropboxAccount')),
            ],
            options={
                'verbose_name': 'Dropbox User',
                'verbose_name_plural': 'Dropbox Users',
            },
        ),
    ]
