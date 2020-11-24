from os import PathLike
from typing import Union, Sequence, Tuple

from detectron2.structures import ImageList
import torch
from torch import FloatTensor, IntTensor

from allennlp.common.detectron import DetectronConfig
from allennlp.common.file_utils import cached_path
from allennlp.common.registrable import Registrable

OnePath = Union[str, PathLike]
ManyPaths = Sequence[OnePath]
ImagesWithSize = Tuple[FloatTensor, IntTensor]


class ImageLoader(Registrable):
    """
    An `ImageLoader` is a callable that takes as input one or more filenames, and outputs two
    tensors. The first one contains the images and is of shape (batch, color, height, width). The
    second one contains the image sizes and is of shape (batch, 2) (where the two dimensions contain
    height and width).
    """

    default_implementation = "detectron"

    def __call__(self, filename_or_filenames: Union[OnePath, ManyPaths]) -> ImagesWithSize:
        if not isinstance(filename_or_filenames, list):
            pixels, sizes = self([filename_or_filenames])  # type: ignore
            return pixels[0], sizes[0]

        filenames = [cached_path(f) for f in filename_or_filenames]
        return self.load(filenames)

    def load(self, filenames: ManyPaths) -> ImagesWithSize:
        raise NotImplementedError()


@ImageLoader.register("detectron")
class DetectronImageLoader(ImageLoader):
    def __init__(
        self,
        config: DetectronConfig = DetectronConfig.from_flat_parameters(),
    ):
        self.mapper = config.build_dataset_mapper()

    def load(self, filenames: ManyPaths) -> ImagesWithSize:
        images = [{"file_name": str(f)} for f in filenames]
        images = [self.mapper(i) for i in images]
        images = ImageList.from_tensors([image["image"] for image in images])
        return (images.tensor.float() / 256, torch.tensor(images.image_sizes, dtype=torch.int32))  # type: ignore
