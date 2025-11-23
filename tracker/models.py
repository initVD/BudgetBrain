# tracker/models.py
from django.db import models
from django.contrib.auth.models import User

# --- THIS IS NEW ---
# Our new Category model. Each user will have their own set of categories.
# tracker/models.py

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)

    # --- ADD THIS NEW LINE ---
    # We'll allow it to be 0 (no budget) by default.
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')
        verbose_name_plural = "Categories"

# --- NOTICE THE `CATEGORY_CHOICES` TUPLE IS GONE


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # --- THIS IS THE BIG CHANGE ---
    # Instead of a CharField, this is now a "link" to the Category table.
    # on_delete=models.SET_NULL: If a user deletes a category (e.g., "Groceries"),
    # we don't want to delete all their transactions. Just set them to "Null".
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"