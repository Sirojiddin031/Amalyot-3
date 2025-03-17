from django.db import models
from django.utils.timezone import now


class Categories(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class News(models.Model):
    title = models.CharField(max_length=50, verbose_name='news')
    context = models.TextField(blank=True)
    created_ed = models.DateTimeField(auto_now_add=True)
    updated_ed = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name='get_news')
    photo = models.ImageField(upload_to='photos/%Y/%m/%d/')
    is_bool = models.BooleanField(default=True)
    deadline = models.DateTimeField(null=True,blank=True)  

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "NEW"
        verbose_name_plural = "NEWS"
        ordering = ['-created_ed']
        
    def is_expired(self):
        return self.deadline and self.deadline < now()

        
# Create your models here.
