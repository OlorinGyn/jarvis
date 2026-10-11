"""Measure the dog matching on the dogs the user named, to tune its thresholds.

Usage: uv run tools/dog_tuning.py [--gallery PATH]

Leave-one-out: each view of a named dog is taken out in turn and matched
against everything else, exactly as a new crop would be. It counts, per
lighting, how often the answer is right and sure, right but only probable,
wrong (sure or probable), or no name at all; then the same for a grid of
other thresholds, so SURE_* and PROBABLE_* in dogs.py can be set from data.
See CONTEXTO backlog 22.
"""

import argparse
import itertools
from collections import Counter

from jarvis import dogs


def outcomes(gallery):
    """(lighting, true name, match result) for every view of every named dog, left out in turn."""
    named = [dog for dog in gallery.people if dog["name"]]
    results = []
    for dog in named:
        for index, view in enumerate(dog["embeddings"]):
            others = []
            for other in named:
                views = other["embeddings"]
                if other is dog:
                    views = views[:index] + views[index + 1:]
                if views:
                    others.append({**other, "embeddings": views})
            probe = type("Probe", (), {"people": others})()
            lighting = "infrared" if view[0] else "day"
            results.append((lighting, dog["name"], dogs.match(view, probe)))
    return results


def tally(results):
    counts = Counter()
    for lighting, truth, result in results:
        if result["certainty"] is None:
            verdict = "no name"
        elif result["name"] == truth:
            verdict = f"right, {result['certainty']}"
        else:
            verdict = f"WRONG, {result['certainty']}"
        counts[(lighting, verdict)] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gallery", default=str(dogs.GALLERY_FILE))
    options = parser.parse_args()
    gallery = dogs.DogGallery(options.gallery)
    names = Counter(dog["name"] for dog in gallery.people if dog["name"]
                    for _ in dog["embeddings"])
    print("named views:", dict(names) or "none yet: name some crops on the Dogs tab first")
    if len(names) < 2:
        return
    current = (dogs.SURE_DISTANCE, dogs.SURE_RATIO, dogs.PROBABLE_DISTANCE, dogs.PROBABLE_RATIO)
    print(f"\ncurrent thresholds {current}:")
    for (lighting, verdict), count in sorted(tally(outcomes(gallery)).items()):
        print(f"  {lighting:9} {verdict:18} {count}")
    print("\nsure distance / ratio -> right sure, wrong sure, no name (all lightings):")
    for sure, ratio in itertools.product((0.25, 0.3, 0.35, 0.4, 0.45), (0.5, 0.6, 0.7)):
        dogs.SURE_DISTANCE, dogs.SURE_RATIO = sure, ratio
        counts = Counter(verdict for (_, verdict), n in tally(outcomes(gallery)).items() for _ in range(n))
        print(f"  {sure:.2f} / {ratio:.1f}: {counts['right, sure']:4} {counts['WRONG, sure']:4} "
              f"{counts['no name']:4}")
    dogs.SURE_DISTANCE, dogs.SURE_RATIO, dogs.PROBABLE_DISTANCE, dogs.PROBABLE_RATIO = current


if __name__ == "__main__":
    main()
