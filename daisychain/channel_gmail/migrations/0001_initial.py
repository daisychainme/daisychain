# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-03 00:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import oauth2client.contrib.django_orm


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GmailAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credentials', oauth2client.contrib.django_orm.CredentialsField(null=True)),
                ('flow', oauth2client.contrib.django_orm.FlowField(null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Gmail accounts',
                'verbose_name': 'Gmail account',
            },
        ),
    ]
