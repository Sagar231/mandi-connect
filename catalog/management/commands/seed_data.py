"""Populate MandiConnect with realistic, image-backed demo data.

Safe to run repeatedly (idempotent via get_or_create) and designed to run
unchanged against Railway Postgres:

    python manage.py seed_data          # add/refresh demo data
    python manage.py seed_data --reset  # wipe non-superuser data first
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Category, Product
from markets.models import Market
from notifications.models import Favorite, PriceAlert
from pricing.models import PriceHistory, PriceListing
from reviews.models import Review
from vendors.models import Vendor

User = get_user_model()

MEAL = "https://www.themealdb.com/images/ingredients/{}.png"
UNSPLASH = "https://images.unsplash.com/{}?w=1200&q=80"


def shop_banner(seed):
    return f"https://loremflickr.com/800/500/grocery,vegetable,shop?lock={seed}"


# (name, icon, image ingredient) — image uses TheMealDB clean produce icons
CATEGORIES = [
    ("Vegetables", "🥬", "Tomato"),
    ("Fruits", "🍎", "Apple"),
    ("Dairy & Eggs", "🥛", "Milk"),
    ("Grains & Staples", "🌾", "Rice"),
    ("Herbs & Spices", "🌿", "Garlic"),
]

# category -> list of (product, unit, mealdb-ingredient, base_price)
PRODUCTS = {
    "Vegetables": [
        ("Tomato", "kg", "Tomato", 40), ("Onion", "kg", "Onion", 35),
        ("Potato", "kg", "Potatoes", 30), ("Carrot", "kg", "Carrots", 50),
        ("Cabbage", "kg", "Cabbage", 28), ("Cauliflower", "kg", "Cauliflower", 45),
        ("Spinach", "kg", "Spinach", 25), ("Cucumber", "kg", "Cucumber", 32),
        ("Green Chilli", "kg", "Chilli", 80), ("Capsicum", "kg", "Red Pepper", 70),
    ],
    "Fruits": [
        ("Apple", "kg", "Apple", 120), ("Banana", "dozen", "Banana", 50),
        ("Mango", "kg", "Mango", 90), ("Orange", "kg", "Orange", 70),
        ("Grapes", "kg", "Grapes", 85), ("Pomegranate", "kg", "Pomegranate", 140),
        ("Lemon", "kg", "Lemon", 60),
    ],
    "Dairy & Eggs": [
        ("Milk", "litre", "Milk", 55), ("Curd", "kg", "Yogurt", 70),
        ("Butter", "kg", "Butter", 480), ("Eggs", "dozen", "Eggs", 84),
    ],
    "Grains & Staples": [
        ("Basmati Rice", "kg", "Rice", 95), ("Wheat Flour", "kg", "Flour", 45),
        ("Sugar", "kg", "Sugar", 44), ("Chickpeas", "kg", "Chickpeas", 90),
    ],
    "Herbs & Spices": [
        ("Garlic", "kg", "Garlic", 160), ("Ginger", "kg", "Ginger", 120),
        ("Coriander", "kg", "Coriander", 40),
    ],
}

# name, city, area, lat, lng, hours, unsplash photo id
MARKETS = [
    ("Azadpur Mandi", "Delhi", "Azadpur", 28.7076, 77.1751, "5:00 AM - 9:00 PM", "photo-1542838132-92c53300491e"),
    ("Ghazipur Mandi", "Delhi", "Ghazipur", 28.6260, 77.3258, "6:00 AM - 8:00 PM", "photo-1488459716781-31db52582fe9"),
    ("Vashi APMC", "Navi Mumbai", "Vashi", 19.0760, 72.9986, "4:00 AM - 10:00 PM", "photo-1567306226416-28f0efdc88ce"),
    ("Yeshwanthpur Market", "Bengaluru", "Yeshwanthpur", 13.0287, 77.5547, "5:30 AM - 9:00 PM", "photo-1605000797499-95a51c5269ae"),
    ("Koyambedu Market", "Chennai", "Koyambedu", 13.0694, 80.1948, "5:00 AM - 9:30 PM", "photo-1519996529931-28324d5a630e"),
    ("Bowenpally Market", "Hyderabad", "Bowenpally", 17.4769, 78.4868, "6:00 AM - 8:30 PM", "photo-1573246123716-6b1782bfc499"),
]

SHOP_PREFIXES = ["Sharma", "Verma", "Patel", "Reddy", "Khan", "Gupta", "Singh", "Iyer", "Das", "Nair"]
SHOP_SUFFIXES = ["Sabzi Bhandar", "Fresh Mart", "Fruit Stall", "Provision Store", "Vegetable Depot", "Dairy & More"]
REVIEW_TEXTS = [
    "Fresh stock every morning, fair prices.", "Good quality but a bit pricey.",
    "Very friendly vendor, always reliable.", "Best tomatoes in the market!",
    "Sometimes runs out of stock by evening.", "Clean shop and honest weights.",
    "Great deals on bulk buying.", "Produce is consistently fresh.",
]


class Command(BaseCommand):
    help = "Populate sample markets, vendors, products, prices, history, reviews."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing non-superuser data first")
        parser.add_argument("--days", type=int, default=60, help="Days of price history to generate")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(42)
        if opts["reset"]:
            self.stdout.write("Clearing existing demo data…")
            for model in (Favorite, PriceAlert, PriceHistory, PriceListing, Review, Vendor, Product, Category, Market):
                model.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        admin = self._user("admin@mandiconnect.local", "admin12345", User.Roles.ADMIN, staff=True, super=True)
        customer = self._user("customer@mandiconnect.local", "customer12345", User.Roles.CUSTOMER)

        # Categories + products
        categories, products_by_cat = {}, {}
        for name, icon, img in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={"icon": icon, "image_url": MEAL.format(img)}
            )
            categories[name] = cat
            products_by_cat[name] = []
            for pname, unit, ing, base in PRODUCTS[name]:
                p, _ = Product.objects.get_or_create(
                    category=cat, name=pname,
                    defaults={"unit": unit, "image_url": MEAL.format(ing),
                              "description": f"Fresh {pname.lower()} sold by weight."},
                )
                products_by_cat[name].append((p, Decimal(base)))

        all_products = [pp for plist in products_by_cat.values() for pp in plist]

        # Markets
        markets = []
        for name, city, area, lat, lng, hours, photo in MARKETS:
            m, _ = Market.objects.get_or_create(
                name=name, city=city,
                defaults={"area": area, "latitude": lat, "longitude": lng,
                          "opening_hours": hours, "image_url": UNSPLASH.format(photo),
                          "address": f"{area}, {city}"},
            )
            markets.append(m)

        # Vendors + listings + history
        today = timezone.localdate()
        days = opts["days"]
        vendor_n = 0
        total_listings = 0
        for market in markets:
            n_vendors = random.randint(3, 5)
            for _ in range(n_vendors):
                vendor_n += 1
                vu = self._user(f"vendor{vendor_n}@mandiconnect.local", "vendor12345", User.Roles.VENDOR)
                cat_name = random.choice(list(categories.keys()))
                shop_name = f"{random.choice(SHOP_PREFIXES)} {random.choice(SHOP_SUFFIXES)}"
                vendor, created = Vendor.objects.get_or_create(
                    user=vu,
                    defaults={
                        "shop_name": shop_name, "market": market,
                        "primary_category": categories[cat_name],
                        "description": f"Family-run shop in {market.area}, serving fresh produce daily.",
                        "phone": f"+91 9{random.randint(100000000, 999999999)}",
                        "image_url": shop_banner(vendor_n),
                        "is_verified": random.random() > 0.15,  # ~85% verified
                    },
                )
                if not created:
                    continue
                # Each vendor sells a random subset of products
                catalog = random.sample(all_products, k=random.randint(6, 10))
                for product, base in catalog:
                    # market-level bias so different markets have different price levels
                    market_bias = Decimal(random.randint(-5, 8))
                    vendor_bias = Decimal(random.randint(-6, 6))
                    cur = max(Decimal(5), base + market_bias + vendor_bias)
                    PriceListing.objects.create(
                        vendor=vendor, product=product, price=cur, date=today,
                        stock_status=random.choices(
                            ["in_stock", "low", "out"], weights=[7, 2, 1])[0],
                    )
                    total_listings += 1
                    # history: random walk backwards
                    walk = cur
                    for d in range(days):
                        day = today - timedelta(days=d)
                        PriceHistory.objects.update_or_create(
                            vendor=vendor, product=product, date=day,
                            defaults={"price": max(Decimal(5), walk)},
                        )
                        walk += Decimal(random.randint(-3, 3))
                # Reviews
                for reviewer in self._reviewers(customer, vendor_n):
                    Review.objects.get_or_create(
                        vendor=vendor, user=reviewer,
                        defaults={"rating": random.randint(3, 5),
                                  "comment": random.choice(REVIEW_TEXTS)},
                    )

        # Demo customer favorites + alerts
        verified_vendors = list(Vendor.objects.filter(is_verified=True)[:3])
        for v in verified_vendors:
            Favorite.objects.get_or_create(user=customer, vendor=v)
        for product, base in random.sample(all_products, k=3):
            PriceAlert.objects.get_or_create(
                user=customer, product=product,
                defaults={"threshold": base - Decimal(5)},
            )

        # Recompute ratings
        from reviews.tasks import recompute_vendor_ratings
        recompute_vendor_ratings()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded:\n"
            f"  {Market.objects.count()} markets\n"
            f"  {Category.objects.count()} categories, {Product.objects.count()} products\n"
            f"  {Vendor.objects.count()} vendors ({Vendor.objects.filter(is_verified=True).count()} verified)\n"
            f"  {PriceListing.objects.count()} active listings\n"
            f"  {PriceHistory.objects.count()} price-history rows ({days}d)\n"
            f"  {Review.objects.count()} reviews\n"
        ))
        self.stdout.write(self.style.WARNING(
            "Demo logins:\n"
            "  admin     admin@mandiconnect.local / admin12345\n"
            "  customer  customer@mandiconnect.local / customer12345\n"
            "  vendor    vendor1@mandiconnect.local / vendor12345 (…vendorN)\n"
        ))

    # helpers ---------------------------------------------------------------
    def _user(self, email, password, role, staff=False, super=False):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"role": role, "is_staff": staff, "is_superuser": super,
                      "is_email_verified": True},
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    def _reviewers(self, customer, n):
        """Return a small set of reviewer users (reuse demo customer + a few synthetic)."""
        reviewers = [customer]
        for i in range(random.randint(1, 3)):
            reviewers.append(self._user(f"buyer{n}_{i}@mandiconnect.local", "buyer12345", User.Roles.CUSTOMER))
        return reviewers
