from django.contrib.gis.db import models

# Create your models here.
class Farm(models.Model):
    farm_id = models.BigIntegerField(null=True)
    crop = models.CharField(max_length=10, null=True)
    size = models.FloatField(null=True)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self): 
        return str(self.farm_id)

    class Meta:
        ordering = ['farm_id']



