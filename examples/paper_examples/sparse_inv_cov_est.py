"""
Copyright 2019 Anqi Fu, Junzi Zhang

This file is part of A2DR.

A2DR is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

A2DR is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with A2DR. If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import scipy as sp
import numpy.linalg as LA
import copy
import time
import scipy.sparse.linalg
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

from cvxpy import *
from scipy import sparse
from scipy.optimize import nnls
from sklearn.datasets import make_sparse_spd_matrix

from a2dr import a2dr
from a2dr.proximal import *
from a2dr.tests.base_test import BaseTest

class TestPaper(BaseTest):
    """Unit tests for A2DR paper experiments."""

    def setUp(self):
        np.random.seed(1)
        self.eps_rel = 1e-8   # specify these in all examples?
        self.eps_abs = 1e-6
        self.MAX_ITER = 1000

    def test_sparse_inv_covariance(self, n, alpha_ratio):
        # minimize -log(det(S)) + trace(S*Y) + \alpha*||S||_1 subject to S is symmetric PSD.

        # Problem data.
        # n: Dimension of matrix.
        m = 1000  # Number of samples.
        ratio = 0.9   # Fraction of zeros in S.

        S_true = sparse.csc_matrix(make_sparse_spd_matrix(n, ratio))
        R = sparse.linalg.inv(S_true).todense()
        q_sample = sp.linalg.sqrtm(R).dot(np.random.randn(n,m))
        Q = np.cov(q_sample)
        mask = np.ones(Q.shape, dtype=bool)
        np.fill_diagonal(mask, 0)
        alpha_max = np.max(np.abs(Q)[mask])
        alpha = alpha_ratio*alpha_max #0.001 for n=100, 0.01 for n=50

        # Convert problem to standard form.
        # f_1(S) = -log(det(S)) on symmetric PSD matrices, f_2(S) = trace(S*Q), f_3(S) = \alpha*||S||_1.
        # A_1 = [I; 0], A_2 = [-I; I], A_3 = [0; -I], b = 0.
        prox_list = [lambda v, t: prox_neg_log_det_aff(v.reshape((n,n), order='C'), Q, t, order='C'),
                     prox_norm1(alpha)]
        A_list = [sparse.eye(n*n), -sparse.eye(n*n)]
        b = np.zeros(n*n)

        # Solve with DRS.
        drs_result = a2dr(prox_list, A_list, b, anderson=False, precond=True, max_iter=self.MAX_ITER)
        print('Finished DRS.')

        # Solve with A2DR.
        a2dr_result = a2dr(prox_list, A_list, b, anderson=True, precond=True, max_iter=self.MAX_ITER) 
        #lam_accel=0 seems to work well sometimes, although oscillating very much
        a2dr_S = a2dr_result["x_vals"][-1].reshape((n,n), order='C')
        self.compare_total(drs_result, a2dr_result)
        print('Finished A2DR.')
        print('recovered sparsity = {}'.format(np.sum(a2dr_S!=0)*1.0/a2dr_S.shape[0]**2))

if __name__ == '__main__':
    tests = TestPaper()
    tests.setUp()
    tests.test_sparse_inv_covariance(80, 0.001)

