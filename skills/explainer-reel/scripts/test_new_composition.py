"""Self-check for the moments a scene is fully built: python3 scripts/test_new_composition.py"""
from new_composition import settled_times


def test_each_scene_is_sampled_just_before_the_next_beat_and_the_last_near_the_end():
    timeline = {"duration": 10.0, "words": [{"i": 0, "start": 0.0}, {"i": 1, "start": 2.0}, {"i": 3, "start": 6.0}]}
    beats = [{"from_word": 0}, {"from_word": 1}, {"from_word": 2}]
    # Word 2 was cut from the edit, so the third beat starts at the next word that remains.
    assert settled_times(timeline, beats) == [1.7, 5.7, 9.7]


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok")
