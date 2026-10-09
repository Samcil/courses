# Lecture notes: Dr. Aviv Censor's Technion courses

Notes, proofs and reproducible code for three filmed Technion courses taught by Dr. Aviv Censor:

| Course | Playlist | Lectures |
|---|---|---|
| Algebra 1M (104016) | [YouTube](https://www.youtube.com/playlist?list=PLW3u28VuDAHJNrf3JCgT0GG_rjFVz0-j9) | 73 |
| Differential and Integral Calculus 1 (104003) | [YouTube](https://www.youtube.com/playlist?list=PLW3u28VuDAHJymExTBCNnaI6TymzRGsUV) | 52 |
| Differential and Integral Calculus 2 (104004) | [YouTube](https://www.youtube.com/playlist?list=PLW3u28VuDAHLWNxKyfoBQSVBp-fhWrDr0) | 100 |

`lectures/*.tsv` lists every lecture with its video id and length.

## Getting the transcripts (run on your own computer)

YouTube blocks caption downloads from cloud servers, so fetch them locally:

```bash
pip install yt-dlp
python censor-math-books/scripts/fetch_transcripts.py                 # all three courses
python censor-math-books/scripts/fetch_transcripts.py algebra1m       # or one course
# if YouTube asks you to sign in:
python censor-math-books/scripts/fetch_transcripts.py --cookies-from-browser chrome
```

Transcripts land in `censor-math-books/transcripts/<course>/`, one timestamped file per lecture.
That folder is git-ignored: the lectures belong to Dr. Censor and the Technion, so the raw
transcripts are for personal study and are not committed.
