import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
import simplejpeg


# https://pytorch.org/tutorials/beginner/basics/data_tutorial.html
class GalaxyDataset(Dataset):
    def __init__(self, catalog: pd.DataFrame, label_cols, album=False, transform=None, target_transform=None):
        # catalog should be split already
        # should have correct image locations under file_loc
        self.catalog = catalog
        self.album = album
        self.label_cols = label_cols
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.catalog)

    def __getitem__(self, idx):
        galaxy = self.catalog.iloc[idx]
        # option A
        # img_path = galaxy['file_loc']
        # image = read_image(img_path) # PIL under the hood: Returns CHW Tensor.
        # option B - tiny bit faster when CPU-limited
        with open(galaxy['file_loc'], 'rb') as f:
            image = torch.from_numpy(decode_jpeg(f.read()).transpose(2, 0, 1))
        label = get_galaxy_label(galaxy, self.label_cols)

        # logging.info((image.shape, torch.max(image), image.dtype, label))  # always 0-255 uint8

        if self.transform:
            # TODO eww an extra if
            if self.album:
                # album wants HWC np.array
                # send it back to np from tensor...
                image = np.asarray(image).transpose(1, 2, 0)
                # Returns torch.tensor CHW for torch using ToTensorV2() as last transform
                # e.g.: https://albumentations.ai/docs/examples/pytorch_classification/
                image = self.transform(image=image)['image']
            else:
                # already a CHW tensor, which torchvision wants
                image = self.transform(image)

        if self.target_transform:
            label = self.target_transform(label)

        # logging.info((image.shape, torch.max(image), image.dtype, label))  #  should be 0-1 float
        return image, label


def load_encoded_jpeg(loc):
    with open(loc, "rb") as f:
        return f.read()  # bytes, not yet decoded


def decode_jpeg(encoded_bytes):
    return simplejpeg.decode_jpeg(encoded_bytes, fastdct=True, fastupsample=True)


def get_galaxy_label(galaxy, label_cols):
    return galaxy[label_cols].values.astype(np.int64).squeeze()  # squeeze for if there's one label_col
