from django.db import models
from django.contrib.auth.models import User
from onadata.apps.fieldsight.models import Organization


PLAN_CHOICES = (
    (0, 'Free Plan'),
    (1, 'Basic Monthly Plan'),
    (2, 'Basic Yearly Plan'),
    (3, 'Extended Monthly Plan'),
    (4, 'Extended Yearly Plan'),
    (5, 'Pro Monthly Plan'),
    (6, 'Pro Yearly Plan'),
    (7, 'Scale Monthly Plan'),
    (8, 'Scale Yearly Plan'),
    (9, 'Starter Monthly Plan'),
    (10, 'Starter Yearly Plan')

)

PERIOD_TYPE = (
    (0, 'Free'),
    (1, 'Month'),
    (2, 'Year'),

)


class Package(models.Model):
    plan = models.IntegerField(choices=PLAN_CHOICES, default=0)
    submissions = models.IntegerField()
    total_charge = models.FloatField(null=True, blank=True)
    extra_submissions_charge = models.FloatField(default=0)
    period_type = models.IntegerField(choices=PERIOD_TYPE, default=0)


class Customer(models.Model):
    user = models.OneToOneField(User, related_name="customer")
    stripe_cust_id = models.CharField(max_length=300)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)


class Subscription(models.Model):
    stripe_sub_id = models.CharField(max_length=300)
    stripe_customer = models.ForeignKey(Customer, related_name="subscriptions", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    initiated_on = models.DateTimeField()
    terminated_on = models.DateTimeField(null=True, blank=True)
    package = models.ForeignKey(Package, related_name="subscriptions", null=True, blank=True)
    organization = models.OneToOneField(Organization, related_name="subscription", null=True, blank=True)


class Invoice(models.Model):
    customer = models.ForeignKey(Customer, related_name="invoices")
    created = models.DateTimeField()
    amount = models.FloatField()
    quantity = models.IntegerField()
    overage = models.IntegerField(default=0)
    roll_over = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)


class TrackPeriodicWarningEmail(models.Model):
    """
        Track Warning E-Mails when total usage reached and overage charges begin, and then at 1 day, 3 days, 1 week,
        and then monthly (for annual plans)
    """
    subscriber = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="periodic_warning_email")
    is_email_send = models.BooleanField(default=False)
    date = models.DateField()



