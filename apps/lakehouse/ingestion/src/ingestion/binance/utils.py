import pendulum


def datetime_to_utc_ms(dt: pendulum.DateTime) -> int:
    return dt.int_timestamp * 1000
