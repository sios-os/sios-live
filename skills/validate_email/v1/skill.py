def validate_email(email):
    """Validate an email address format without using regex."""
    if "@" not in email:
        return False
    local_part, domain = email.split("@")
    if "." not in domain:
        return False
    domain_parts = domain.split(".")
    if len(domain_parts) < 2:
        return False
    for part in [local_part] + domain_parts:
        if not part or any(c.isspace() for c in part):
            return False
    return True