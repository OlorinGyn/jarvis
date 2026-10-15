"""Synthetic DINOv2 descriptors for the dog tests, at distances chosen by angle, and a stand-in network."""

import math

import numpy as np

from jarvis import dogs

FAKE_START = 300


def descriptor(direction, infrared=True, angle=0.0):
    """A unit embedding turned by angle radians from axis direction toward the next axis.

    Two descriptors of one direction are 1 - cos(difference of angles) apart;
    of two directions, 1 apart, as far as two unrelated dogs.
    """
    vector = [0.0] * dogs.EMBEDDING_SIZE
    vector[direction] = math.cos(angle)
    vector[direction + 1] = math.sin(angle)
    return [1.0 if infrared else 0.0] + vector


def at_distance(direction, distance, infrared=True):
    """A descriptor exactly distance away from descriptor(direction, infrared)."""
    return descriptor(direction, infrared, math.acos(1.0 - distance))


def fake_embed(self, image):
    """The image's mean colour as a unit embedding, on axes the descriptors above never use."""
    vector = np.zeros(dogs.EMBEDDING_SIZE, np.float32)
    vector[FAKE_START:FAKE_START + 3] = np.asarray(image, np.float32).reshape(-1, 3).mean(axis=0) / 255.0
    vector[FAKE_START + 3] = 0.5
    return vector / float(np.linalg.norm(vector))
