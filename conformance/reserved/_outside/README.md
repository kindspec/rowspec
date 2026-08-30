Not a case. This directory holds an artifact that is *outside* the repository
root of every case, so that `parse/lookup-path-escape` has something real to
reach for. It contains no `expect.json`, so the runner walks past it.
