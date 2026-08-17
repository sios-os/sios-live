def time_ago(timestamp):
    """Converts a timestamp to a human-readable 'time ago' string."""
    import datetime

    now = datetime.datetime.now()
    target_time = datetime.datetime.fromtimestamp(timestamp)

    if target_time > now:
        raise ValueError("Future timestamp")

    difference = now - target_time
    seconds = difference.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{int(minutes)} minutes ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{int(hours)} hours ago"
    else:
        days = seconds // 86400
        return f"{int(days)} days ago"