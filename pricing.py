from decimal import Decimal, ROUND_HALF_UP

def _money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def regular_tow(miles_total: float):
    base = Decimal("105.00")
    included = Decimal("7")
    per_mile = Decimal("5.00")
    extra = max(Decimal(str(miles_total)) - included, Decimal("0"))
    extra_cost = extra * per_mile
    total = base + extra_cost
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider, "extra_miles": float(extra), "extra_cost": _money(extra_cost)}

def accident_tow(miles_total: float):
    base = Decimal("295.00"); included = Decimal("21"); per_mile = Decimal("5.00")
    extra = max(Decimal(str(miles_total)) - included, Decimal("0"))
    extra_cost = extra * per_mile
    total = base + extra_cost
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider, "extra_miles": float(extra), "extra_cost": _money(extra_cost)}

def motorcycle_tow(miles_total: float):
    base = Decimal("185.00"); included = Decimal("7"); per_mile = Decimal("4.00")
    extra = max(Decimal(str(miles_total)) - included, Decimal("0"))
    extra_cost = extra * per_mile
    total = base + extra_cost
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider, "extra_miles": float(extra), "extra_cost": _money(extra_cost)}

def flat_tire(vehicle_class: str):
    # vehicle_class: sedan | truck | dually | semi_rv
    prices = {"sedan": "75.00", "truck": "85.00", "dually": "125.00", "semi_rv": "220.00"}
    total = Decimal(prices[vehicle_class])
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider}

def jumpstart(distance_miles: float):
    base = Decimal("65.00")
    discount = Decimal("0.10") if Decimal(str(distance_miles)) <= Decimal("5") else Decimal("0.00")
    total = base * (Decimal("1.00") - discount)
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider, "discount_applied": float(discount)}

def lockout(distance_miles: float):
    base = Decimal("75.00")
    discount = Decimal("0.10") if Decimal(str(distance_miles)) <= Decimal("5") else Decimal("0.00")
    total = base * (Decimal("1.00") - discount)
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": _money(total), "platform_cut": cut, "provider": provider, "discount_applied": float(discount)}

def winch_out(minutes: int):
    hourly = Decimal("195.00")
    total = hourly * (Decimal(minutes) / Decimal("60"))
    total = _money(total)
    cut = _money(total * Decimal("0.20"))
    provider = _money(total - cut)
    return {"total": total, "platform_cut": cut, "provider": provider}
