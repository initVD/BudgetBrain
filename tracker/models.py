# tracker/models.py
from django.db import models
from django.contrib.auth.models import User

# These are our pre-defined categories.
# We will use these for a dropdown menu later.
CATEGORY_CHOICES = (
    ('Groceries', 'Groceries'),
    ('Rent', 'Rent'),
    ('Utilities', 'Utilities'),
    ('Subscriptions', 'Subscriptions'),
    ('Restaurants', 'Restaurants'),
    ('Transportation', 'Transportation'),
    ('Shopping', 'Shopping'),
    ('Entertainment', 'Entertainment'),
    ('Other', 'Other'),
)


class Transaction(models.Model):
    # This links the transaction to a specific user.
    # If a user is deleted, all their transactions are also deleted.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # The date the transaction happened
    date = models.DateField()
    
    # The text description from the bank (e.g., "SPOTIFY AB F8E12")
    description = models.CharField(max_length=255)
    
    # We use DecimalField for money. It's more accurate than a regular float.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # This is the category we will assign (e.g., "Groceries")
    # The 'choices' part will give us a dropdown.
    # 'blank=True, null=True' means it can be empty, which is important.
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        # This is just a "nickname" for the transaction
        # so it's easy to read in the admin panel.
        return f"{self.date} - {self.description} - {self.amount}"