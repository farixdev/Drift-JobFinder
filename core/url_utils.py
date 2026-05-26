from urllib.parse import urlparse


class InvalidJobsUrlError(ValueError):
    pass


# Backwards compat alias
InvalidRootUrlError = InvalidJobsUrlError


def normalize_jobs_url(raw: str) -> str:
    """
    Accept only domain + /jobs (no deeper paths).
    Valid:   company.com/jobs  https://example.com/jobs/
    Invalid: company.com, company.com/careers, company.com/jobs/123
    """
    value = raw.strip()
    if not value:
        return ""

    if " " in value:
        raise InvalidJobsUrlError("URL cannot contain spaces.")

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise InvalidJobsUrlError("Use http:// or https://")

    host = parsed.netloc or ""
    if not host:
        raise InvalidJobsUrlError("Enter a domain with /jobs — e.g. company.com/jobs")

    if "@" in host:
        raise InvalidJobsUrlError("Invalid domain.")

    path = (parsed.path or "").strip("/").lower()
    if path != "jobs":
        raise InvalidJobsUrlError(
            "Only /jobs is allowed — e.g. company.com/jobs (not /careers or /jobs/engineer)"
        )

    if parsed.query or parsed.fragment:
        raise InvalidJobsUrlError("Remove ?query and #anchor from the URL.")

    return f"https://{host.lower()}/jobs"


def normalize_root_url(raw: str) -> str:
    """Alias used by setup screen."""
    return normalize_jobs_url(raw)
