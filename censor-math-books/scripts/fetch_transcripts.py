#!/usr/bin/env python3
"""
Download the English captions of Dr. Aviv Censor's Technion lecture playlists
and turn them into clean, timestamped plain-text transcripts.

    pip install yt-dlp
    python censor-math-books/scripts/fetch_transcripts.py            # all three courses
    python censor-math-books/scripts/fetch_transcripts.py algebra1m  # just one

Run it on your own computer: YouTube refuses caption requests from cloud
servers ("Sign in to confirm you're not a bot"). If it refuses you as well,
add  --cookies-from-browser chrome  (or firefox / edge / safari) so yt-dlp uses
your normal browser session.

Output (git-ignored, for personal study only):
    censor-math-books/transcripts/<course>/NNN-<title>.txt
    censor-math-books/transcripts/<course>/index.tsv

Each transcript line looks like
    [12:34] text spoken at that moment ...
and the file header carries the video URL, so  URL&t=754s  jumps to [12:34].
Re-running skips lectures that are already downloaded.
"""
import argparse
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PLAYLISTS = {
    "algebra1m": ("Algebra 1M (104016)", "PLW3u28VuDAHJNrf3JCgT0GG_rjFVz0-j9"),
    "calculus1": ("Differential and Integral Calculus 1 (104003)", "PLW3u28VuDAHJymExTBCNnaI6TymzRGsUV"),
    "calculus2": ("Differential and Integral Calculus 2 (104004)", "PLW3u28VuDAHLWNxKyfoBQSVBp-fhWrDr0"),
}
OUT_ROOT = Path(__file__).resolve().parent.parent / "transcripts"
TS = re.compile(r"(\d+):(\d\d):(\d\d)\.\d+ -->")
TAG = re.compile(r"<[^>]+>")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def list_playlist(pid, extra):
    r = run(["yt-dlp", "--flat-playlist", *extra,
             "--print", "%(playlist_index)s\t%(id)s\t%(title)s\t%(duration)s",
             f"https://www.youtube.com/playlist?list={pid}"])
    if r.returncode != 0 and not r.stdout:
        sys.exit(r.stderr)
    rows = []
    for line in r.stdout.splitlines():
        idx, vid, title, dur = line.split("\t")
        rows.append((int(idx), vid, " ".join(title.split()), dur))
    return rows


def vtt_to_lines(vtt_text, every=20):
    """
    YouTube auto-captions repeat each phrase in 2-3 overlapping cues. Keep each
    new line of text once, and group it into paragraphs that start with a
    [mm:ss] stamp roughly every `every` seconds.
    """
    out, seen_last, cur_t, buf, para_start = [], None, 0, [], None
    for block in vtt_text.split("\n\n"):
        m = TS.search(block)
        if not m:
            continue
        h, mi, s = map(int, m.groups())
        cur_t = h * 3600 + mi * 60 + s
        for raw in block.splitlines()[1:]:
            line = TAG.sub("", raw).strip()
            if not line or "-->" in line or line == seen_last:
                continue
            seen_last = line
            if para_start is None:
                para_start = cur_t
            buf.append(line)
        if para_start is not None and cur_t - para_start >= every:
            out.append((para_start, " ".join(buf)))
            buf, para_start = [], None
    if buf:
        out.append((para_start, " ".join(buf)))
    return out


def stamp(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:60]


def fetch(course, extra, sleep):
    name, pid = PLAYLISTS[course]
    outdir = OUT_ROOT / course
    outdir.mkdir(parents=True, exist_ok=True)
    rows = list_playlist(pid, extra)
    with open(outdir / "index.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["index", "video_id", "title", "duration_s", "url"])
        for idx, vid, title, dur in rows:
            w.writerow([idx, vid, title, dur, f"https://www.youtube.com/watch?v={vid}"])
    print(f"{name}: {len(rows)} lectures -> {outdir}")
    failed = []
    for idx, vid, title, dur in rows:
        dest = outdir / f"{idx:03d}-{slug(title)}.txt"
        if dest.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            r = run(["yt-dlp", *extra, "--skip-download",
                     "--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en",
                     "--sub-format", "vtt", "--sleep-subtitles", str(sleep),
                     "-o", f"{tmp}/%(id)s.%(ext)s",
                     f"https://www.youtube.com/watch?v={vid}"])
            vtts = sorted(Path(tmp).glob("*.vtt"))
            if not vtts:
                failed.append((idx, title, (r.stderr.strip().splitlines() or ["?"])[-1]))
                print(f"  [{idx:03d}] FAILED  {title}")
                continue
            # prefer the plain "en" track (human-made when it exists) over variants
            best = next((v for v in vtts if v.name.endswith(".en.vtt")), vtts[0])
            text = best.read_text(encoding="utf-8")
        lines = vtt_to_lines(text)
        url = f"https://www.youtube.com/watch?v={vid}"
        with open(dest, "w", encoding="utf-8") as f:
            f.write(f"# {name} — lecture {idx}: {title}\n# {url}\n# duration {stamp(int(float(dur or 0)))}\n\n")
            for t, para in lines:
                f.write(f"[{stamp(t)}] {para}\n")
        print(f"  [{idx:03d}] ok      {title}  ({len(lines)} paragraphs)")
    if failed:
        print(f"\n{len(failed)} lecture(s) failed; re-run to retry. Last error:\n  {failed[-1][2]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("courses", nargs="*", help=f"any of {', '.join(PLAYLISTS)} (default: all)")
    ap.add_argument("--cookies-from-browser", metavar="BROWSER",
                    help="pass through to yt-dlp, e.g. chrome, firefox, edge, safari")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between caption requests")
    a = ap.parse_args()
    extra = ["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser else []
    unknown = set(a.courses) - set(PLAYLISTS)
    if unknown:
        ap.error(f"unknown course(s): {', '.join(sorted(unknown))}")
    for c in a.courses or list(PLAYLISTS):
        fetch(c, extra, a.sleep)


if __name__ == "__main__":
    main()
