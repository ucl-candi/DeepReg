import os

from deepreg.data.loader import PairedDataLoader, GeneratorDataLoader
from deepreg.data.nifti.nifti_loader import NiftiFileLoader
from deepreg.data.util import check_difference_between_two_lists


class NiftiPairedDataLoader(PairedDataLoader, GeneratorDataLoader):
    def __init__(self,
                 data_dir_path: str, labeled: bool, sample_label: str, seed,
                 moving_image_shape: (list, tuple), fixed_image_shape: (list, tuple)):
        """
        Load data which are paired, labeled or unlabeled.

        :param data_dir_path: path of the directory storing data,  the data has to be saved under four different
                              sub-directories: moving_images, fixed_images, moving_labels, fixed_labels
        :param labeled: true if the data are labeled
        :param sample_label:
        :param seed:
        :param moving_image_shape: (width, height, depth)
        :param fixed_image_shape: (width, height, depth)
        """
        super(NiftiPairedDataLoader, self).__init__(moving_image_shape=moving_image_shape,
                                                    fixed_image_shape=fixed_image_shape,
                                                    labeled=labeled,
                                                    sample_label=sample_label,
                                                    seed=seed)
        
        self.loader_moving_image = NiftiFileLoader(os.path.join(data_dir_path, "moving_images"), grouped=False)
        self.loader_fixed_image = NiftiFileLoader(os.path.join(data_dir_path, "fixed_images"), grouped=False)
        if self.labeled:
            self.loader_moving_label = NiftiFileLoader(os.path.join(data_dir_path, "moving_labels"), grouped=False)
            self.loader_fixed_label = NiftiFileLoader(os.path.join(data_dir_path, "fixed_labels"), grouped=False)
        self.validate_data_files()
        self.num_images = len(self.loader_moving_image.file_paths)

    def validate_data_files(self):
        """Verify all loader have the same files"""
        filenames_moving_image = self.loader_moving_image.get_relative_file_paths()
        filenames_fixed_image = self.loader_fixed_image.get_relative_file_paths()
        check_difference_between_two_lists(list1=filenames_moving_image, list2=filenames_fixed_image)

        if self.labeled:
            filenames_moving_label = self.loader_moving_label.get_relative_file_paths()
            filenames_fixed_label = self.loader_fixed_label.get_relative_file_paths()
            check_difference_between_two_lists(list1=filenames_moving_image, list2=filenames_moving_label)
            check_difference_between_two_lists(list1=filenames_moving_image, list2=filenames_fixed_label)

    def get_generator(self):
        for image_index in range(self.num_images):
            moving_image = self.loader_moving_image.get_data(index=image_index) / 255.
            fixed_image = self.loader_fixed_image.get_data(index=image_index) / 255.
            moving_label = self.loader_moving_label.get_data(index=image_index) if self.labeled else None
            fixed_label = self.loader_fixed_label.get_data(index=image_index) if self.labeled else None

            for sample in self.sample_image_label(moving_image=moving_image,
                                                  fixed_image=fixed_image,
                                                  moving_label=moving_label,
                                                  fixed_label=fixed_label,
                                                  image_indices=[image_index]):
                yield sample
