# Generated by Django 2.0.3 on 2018-04-01 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='XMPPSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=1023, verbose_name='username')),
                ('resource', models.CharField(max_length=1023, verbose_name='resource')),
                ('priority', models.SmallIntegerField(blank=True, null=True, verbose_name='priority')),
                ('stanza', models.TextField(blank=True, verbose_name='last presence stanza')),
                ('login_time', models.DateTimeField(auto_now_add=True, verbose_name='time of login')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='time of last update')),
                ('server_id', models.CharField(blank=True, db_index=True, max_length=64, verbose_name='server ID')),
            ],
            options={
                'verbose_name': 'session',
                'verbose_name_plural': 'sessions',
            },
        ),
        migrations.AlterUniqueTogether(
            name='xmppsession',
            unique_together={('username', 'resource')},
        ),
    ]
