import arxiv

# Construct the default API client.
client = arxiv.Client()

# Search for the 10 most recent articles matching the keyword "quantum."
search = arxiv.Search(
    query="cat:cs.AI OR cat:cs.LG OR cat:cs.CV OR cat:cs.CL OR cat:cs.NE OR cat:stat.ML OR cat:stat.AP OR cat:stat.CO OR cat:stat.ME OR cat:stat.TH",
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate,
)

results = client.results(search)

# `results` is a generator; you can iterate over its elements one by one...
for r in client.results(search):
    print(r.title)
