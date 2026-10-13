from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("video_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="hls_output_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="video",
            name="processing_error",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="video",
            name="processing_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("PROCESSING", "Processing"),
                    ("READY", "Ready"),
                    ("FAILED", "Failed"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
    ]