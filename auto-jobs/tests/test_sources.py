from auto_jobs.config import SearchConfig
from auto_jobs.models import JobPosting
from auto_jobs.sources.base import matches_search, strip_html


def make_search(**overrides):
    defaults = dict(keywords=[], locations=[], exclude_keywords=[], max_results_per_company=20)
    defaults.update(overrides)
    return SearchConfig(**defaults)


def make_job(**overrides):
    defaults = dict(
        source="greenhouse",
        company="acme",
        job_id="1",
        title="Backend Engineer",
        location="Remote - Brazil",
        url="https://example.com/job/1",
        description_text="We build APIs in Python.",
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_strip_html_removes_tags():
    html = "<p>Hello <b>World</b></p>"
    assert strip_html(html) == "Hello World"


def test_matches_search_by_keyword():
    job = make_job(title="Backend Engineer")
    search = make_search(keywords=["backend"])
    assert matches_search(job, search)


def test_matches_search_rejects_missing_keyword():
    job = make_job(title="Sales Manager", description_text="")
    search = make_search(keywords=["backend"])
    assert not matches_search(job, search)


def test_matches_search_by_location():
    job = make_job(location="Remote - Brazil")
    search = make_search(locations=["Brazil"])
    assert matches_search(job, search)


def test_matches_search_excludes_keyword():
    job = make_job(title="Principal Backend Engineer")
    search = make_search(keywords=["backend"], exclude_keywords=["principal"])
    assert not matches_search(job, search)
