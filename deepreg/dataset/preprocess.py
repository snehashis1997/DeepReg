"""
Module for generating the preprocessing
3D Affine/DDF Transforms for moving and fixed images.
"""

import tensorflow as tf

import deepreg.model.layer_util as layer_util


class AffineTransformation3D:
    """
    AffineTransformation3D class for maintaining and updating
    the transformed grids for the moving and fixed images.
    """

    def __init__(self, moving_image_size, fixed_image_size, batch_size, scale=0.1):
        self._batch_size = batch_size
        self._scale = scale
        self._moving_grid_ref = layer_util.get_reference_grid(
            grid_size=moving_image_size
        )
        self._fixed_grid_ref = layer_util.get_reference_grid(grid_size=fixed_image_size)

    def _gen_transforms(self):
        """
        Function that generates a random 3D transformation parameters
        for a batch of data.

        :return: shape = (batch, 4, 3)
        """
        return layer_util.random_transform_generator(
            batch_size=self._batch_size, scale=self._scale
        )

    @staticmethod
    def _transform(image, grid_ref, transforms):
        """
        Resamples an input image from the reference grid by the series
        of input transforms.

        :param image: shape = (batch, dim1, dim2, dim3)
        :param grid_ref: shape = [dim1, dim2, dim3, 3]
        :param transforms: shape = [batch, 4, 3]
        :return: shape = (batch, dim1, dim2, dim3)
        """
        transformed = layer_util.resample(
            vol=image, loc=layer_util.warp_grid(grid_ref, transforms)
        )
        return transformed

    def transform(self, inputs: dict):
        """
        Creates random transforms for the input images and their labels,
        and transforms them based on the resampled reference grids.
        :param inputs:
            if labeled:
                moving_image, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_image, shape = (batch, f_dim1, f_dim2, f_dim3)
                moving_label, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_label, shape = (batch, f_dim1, f_dim2, f_dim3)
                indices, shape = (batch, num_indices, )
            else, unlabeled:
                moving_image, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_image, shape = (batch, f_dim1, f_dim2, f_dim3)
                indices, shape = (batch, num_indices, )
        :return: dictionary with the same structure as inputs
        """

        moving_image = inputs.get("moving_image")
        fixed_image = inputs.get("fixed_image")
        moving_label = inputs.get("moving_label", None)
        fixed_label = inputs.get("fixed_label", None)
        indices = inputs.get("indices")

        moving_transforms = self._gen_transforms()
        fixed_transforms = self._gen_transforms()

        moving_image = self._transform(
            moving_image, self._moving_grid_ref, moving_transforms
        )
        fixed_image = self._transform(
            fixed_image, self._fixed_grid_ref, fixed_transforms
        )

        if moving_label is None:  # unlabeled
            return dict(
                moving_image=moving_image, fixed_image=fixed_image, indices=indices
            )

        moving_label = self._transform(
            moving_label, self._moving_grid_ref, moving_transforms
        )
        fixed_label = self._transform(
            fixed_label, self._fixed_grid_ref, fixed_transforms
        )

        return dict(
            moving_image=moving_image,
            fixed_image=fixed_image,
            moving_label=moving_label,
            fixed_label=fixed_label,
            indices=indices,
        )


class DDFTransformation3D:
    """
    DDFTransformation3D class for using spatial transformation as a data augmentation technique
    """

    def __init__(
        self,
        moving_image_size,
        fixed_image_size,
        batch_size,
        field_strength: int = 1,
        lowres_size: tuple = (1, 1, 1),
    ):

        assert lowres_size <= moving_image_size
        assert lowres_size <= fixed_image_size

        self._moving_image_size = moving_image_size
        self._fixed_image_size = fixed_image_size
        self._batch_size = batch_size
        self._field_strength = field_strength
        self._lowres_size = lowres_size
        self._moving_grid_ref = tf.expand_dims(
            layer_util.get_reference_grid(grid_size=moving_image_size), axis=0
        )
        self._fixed_grid_ref = tf.expand_dims(
            layer_util.get_reference_grid(grid_size=fixed_image_size), axis=0
        )

    def _gen_transforms(self, image_size):
        """
        Function that generates a random ddf field
        for a batch of data.

        :param image_size (tuple): (batch, dim1, dim2, dim3) reference image shape for the transform.
        :return: shape = (batch, dim1, dim2, dim3, 3)
        """
        return layer_util.random_ddf_transform_generator(
            batch_size=self._batch_size,
            image_size=image_size,
            field_strength=self._field_strength,
            lowres_size=self._lowres_size,
        )

    @staticmethod
    def _transform(image, grid_ref, transforms):
        """
        Resamples an input image from the reference grid by the series
        of input transforms.

        :param image: shape = (batch, dim1, dim2, dim3)
        :param grid_ref: shape = [1, dim1, dim2, dim3, 3]
        :param transforms: shape = [batch, dim1, dim2, dim3, 3]
        :return: shape = (batch, dim1, dim2, dim3)
        """
        transformed = layer_util.warp_image_ddf(
            image=image, ddf=transforms, grid_ref=grid_ref
        )
        return transformed

    def transform(self, inputs: dict):
        """
        Creates random transforms for the input images and their labels,
        and transforms them based on the resampled reference grids.
        :param inputs:
            if labeled:
                moving_image, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_image, shape = (batch, f_dim1, f_dim2, f_dim3)
                moving_label, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_label, shape = (batch, f_dim1, f_dim2, f_dim3)
                indices, shape = (batch, num_indices, )
            else, unlabeled:
                moving_image, shape = (batch, m_dim1, m_dim2, m_dim3)
                fixed_image, shape = (batch, f_dim1, f_dim2, f_dim3)
                indices, shape = (batch, num_indices, )
        :return: dictionary with the same structure as inputs
        """

        moving_image = inputs.get("moving_image")
        fixed_image = inputs.get("fixed_image")
        moving_label = inputs.get("moving_label", None)
        fixed_label = inputs.get("fixed_label", None)
        indices = inputs.get("indices")

        moving_transforms = self._gen_transforms(self._moving_image_size)
        fixed_transforms = self._gen_transforms(self._fixed_image_size)

        moving_image = self._transform(
            moving_image, self._moving_grid_ref, moving_transforms
        )
        fixed_image = self._transform(
            fixed_image, self._fixed_grid_ref, fixed_transforms
        )

        if moving_label is None:  # unlabeled
            return dict(
                moving_image=moving_image, fixed_image=fixed_image, indices=indices
            )

        moving_label = self._transform(
            moving_label, self._moving_grid_ref, moving_transforms
        )
        fixed_label = self._transform(
            fixed_label, self._fixed_grid_ref, fixed_transforms
        )

        return dict(
            moving_image=moving_image,
            fixed_image=fixed_image,
            moving_label=moving_label,
            fixed_label=fixed_label,
            indices=indices,
        )


def resize_inputs(inputs: dict, moving_image_size: tuple, fixed_image_size: tuple):
    """
    Resize inputs
    :param inputs:
        if labeled:
            moving_image, shape = (None, None, None)
            fixed_image, shape = (None, None, None)
            moving_label, shape = (None, None, None)
            fixed_label, shape = (None, None, None)
            indices, shape = (num_indices, )
        else, unlabeled:
            moving_image, shape = (None, None, None)
            fixed_image, shape = (None, None, None)
            indices, shape = (num_indices, )
    :param moving_image_size: tuple, (m_dim1, m_dim2, m_dim3)
    :param fixed_image_size: tuple, (f_dim1, f_dim2, f_dim3)
    :return:
        if labeled:
            moving_image, shape = (m_dim1, m_dim2, m_dim3)
            fixed_image, shape = (f_dim1, f_dim2, f_dim3)
            moving_label, shape = (m_dim1, m_dim2, m_dim3)
            fixed_label, shape = (f_dim1, f_dim2, f_dim3)
            indices, shape = (num_indices, )
        else, unlabeled:
            moving_image, shape = (m_dim1, m_dim2, m_dim3)
            fixed_image, shape = (f_dim1, f_dim2, f_dim3)
            indices, shape = (num_indices, )
    """
    moving_image = inputs.get("moving_image")
    fixed_image = inputs.get("fixed_image")
    moving_label = inputs.get("moving_label", None)
    fixed_label = inputs.get("fixed_label", None)
    indices = inputs.get("indices")

    moving_image = layer_util.resize3d(image=moving_image, size=moving_image_size)
    fixed_image = layer_util.resize3d(image=fixed_image, size=fixed_image_size)

    if moving_label is None:  # unlabeled
        return dict(moving_image=moving_image, fixed_image=fixed_image, indices=indices)

    moving_label = layer_util.resize3d(image=moving_label, size=moving_image_size)
    fixed_label = layer_util.resize3d(image=fixed_label, size=fixed_image_size)

    return dict(
        moving_image=moving_image,
        fixed_image=fixed_image,
        moving_label=moving_label,
        fixed_label=fixed_label,
        indices=indices,
    )
