from sklearn.metrics import mean_squared_error
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import unittest

def normalize_2d(matrix):
    """
    :param matrix: Matrix
    :return: Normalized matrix
    """
    norm = np.linalg.norm(matrix)
    matrix = matrix / norm
    return matrix

def _sum(arr):
    """
    :param arr: Array of matrix
    :return: sum of array
    """
    s = 0
    for i in arr:
        s = s + i
    return s

def r_mse(matrix1, matrix2):
    """
    :param matrix1: matrix1 in form of single array
    :param matrix2: matrix2 in form of single array
    :return: Root mean square error
    """

    normalized_matrix1 = normalize_2d(matrix1)
    normalized_matrix2 = normalize_2d(matrix2)

    """ Calculate root mean square error """
    mse = mean_squared_error(normalized_matrix1, normalized_matrix2)
    rmse = np.sqrt(mse)
    return rmse


def s_sim(matrix1, matrix2):
    """
    :param matrix1: matrix 1 in the form of single array
    :param matrix2: matrix 2 in the form of single array
    :return: Structural Similarity Index Metric
    """

    normalized_matrix1 = normalize_2d(matrix1)
    normalized_matrix2 = normalize_2d(matrix2)
    """ Calculate mean of normalized matrix """
    m1 = np.mean(normalized_matrix1)
    m2 = np.mean(normalized_matrix2)
    """ Calculate standard deviation of normalized matrix"""
    s1 = np.std(normalized_matrix1)
    s2 = np.std(normalized_matrix2)
    """ Calculating three parameters of Structural similarity index - Luminance, Contrast, Structure """
    lum = (2 * m1 * m2) / (m1 ** 2 + m2 ** 2)
    con = (2 * s1 * s2) / (s1 ** 2 + s2 ** 2)
    strut = (((np.cov(normalized_matrix1, normalized_matrix2))[0, 1]) / (s1 * s2)) * (
                (len(normalized_matrix1) - 1) / (len(normalized_matrix1)))
    """ Calculate Structural Similarity Index Metric whose range is (-1,1) """
    ssim = (lum * con * strut)
    """ Converting it into range of (0,1) where 0 indicates structural similarity and 1 indicates dissimilarity """
    ssim1 = (1 - ((1 + ssim) / 2))
    return ssim1


def mean_ssim(row1, column1, row2, column2, entries1, entries2):
    """
    :param row1: No. of rows of first matrix
    :param column1: No. of columns of first matrix
    :param row2: No. of rows of second matrix
    :param column2: No. of columns of second matrix
    :param entries1: matrix1 in form of single array
    :param entries2: matrix2 in form of single array
    :return: Mean Structural Similarity Index Metric
    """

    matrix1 = np.array(entries1).reshape(row1, column1)
    normalized_matrix1 = normalize_2d(matrix1)

    matrix2 = np.array(entries2).reshape(row2, column2)
    normalized_matrix2 = normalize_2d(matrix2)

    """ Creates 2*2 matrices by window sliding over the matrix with single step unit """
    ws1 = np.lib.stride_tricks.sliding_window_view(normalized_matrix1, (2, 2))
    ws2 = np.lib.stride_tricks.sliding_window_view(normalized_matrix2, (2, 2))
    """ Empty array to store SSIM values we get each time by comparing those 2*2 matrices """
    T_SSIM = []
    """ For loop to calculate SSIM for each 2*2 matrix we got by window sliding """
    for x, y in zip(ws1, ws2):
        for i, j in zip(x, y):
            k1 = (i.reshape(-1))
            k2 = (j.reshape(-1))
            """ Calculate mean """
            m1 = np.mean(k1)
            m2 = np.mean(k2)
            """ Calculate Standard deviation """
            s1 = np.std(k1)
            s2 = np.std(k2)
            """ Calculating three parameters of Structural similarity index - Luminance, Contrast, Structure """
            lum = (2 * m1 * m2) / (m1 ** 2 + m2 ** 2)
            con = (2 * s1 * s2) / (s1 ** 2 + s2 ** 2)
            strut = ((np.cov(k1, k2))[0, 1] / (s1 * s2)) * ((len(k1) - 1) / (len(k1)))
            """ Calculate Structural Similarity Index Metric whose range is (-1,1) """
            ssim = (lum * con * strut)
            """ Storing SSIM values we get in T_SSIM """
            T_SSIM.append(ssim)

    """ Calculate Mean Structural Similarity Index Metric """
    mssim = _sum(T_SSIM) / len(T_SSIM)
    """ Converting it into range of (0,1) where 0 indicates structural similarity and 1 indicates dissimilarity """
    mssim1 = (1 - ((1 + mssim) / 2))
    return mssim1


class TestRoot(unittest.TestCase):

    def test_rmse(self):
        """
        Test the root mean square error of two similar matrices
        """
        m = [1, 2, 3, 4, 5, 6]
        n = [1, 2, 3, 4, 5, 6]
        result = (r_mse(m, n))
        self.assertEqual(result, 0)

    def test_ssim(self):
        """
        Test the structural similarity index of two similar matrices
        """
        m = [1, 2, 3, 4, 5, 6]
        n = [1, 2, 3, 4, 5, 6]
        result = (s_sim(m, n))
        self.assertEqual(result, 0)

    def test_mssim(self):
        """
        Test the mean structural similarity index of two similar matrices
        """
        m = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        n = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        r1 = 3
        r2 = 3
        c1 = 3
        c2 = 3
        result = (mean_ssim(r1, c1, r2, c2, m, n))
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
