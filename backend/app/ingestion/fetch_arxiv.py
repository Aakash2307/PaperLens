import arxiv

# Client handles the actual HTTP communication with arXiv's API —
# retries, rate-limiting, pagination are all handled internally.
client = arxiv.Client()

# Search is just a *description* of what you want — it doesn't fetch anything yet.
search = arxiv.Search(
    query="Telomere Length Analysis",
    max_results=5
)

# client.results() takes the search description and actually hits the API,
# returning an iterator of Result objects.
results = client.results(search)

for paper in results:
    print("Title:", paper.title)
    print("Authors:", [author.name for author in paper.authors])
    print("Year:", paper.published.year)
    print("Abstract:", paper.summary)
    print("Categories:", paper.categories)

    print("---")