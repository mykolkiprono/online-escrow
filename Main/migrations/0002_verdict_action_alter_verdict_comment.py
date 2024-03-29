# Generated by Django 4.2 on 2024-02-20 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='verdict',
            name='action',
            field=models.TextField(choices=[('Reject', 'Reject'), ('Proceed', 'Proceed')], default='Proceed'),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='comment',
            field=models.CharField(default='none', max_length=50),
        ),
    ]
