def normalize_country_string(country):
    if country and country.startswith('{') and country.endswith('}'):
        return country.strip('{}').replace('"', '').split(',')[0].strip().lower()
    return country.lower() if country else ""