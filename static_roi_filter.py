import os
import numpy as np

bitrate_matrix = np.zeros(shape=(21,10))
dssim_matrix = np.zeros(shape=(21,10))

for roi in xrange(0,35,5):
	for qp_delta in xrange(1,11):
		bitrate = float(os.popen('grep "kb/s" log_30s_%.2f_%d.txt' % ((roi/100.0), qp_delta)).read().split()[2].split(":")[1]) / 1024
		ssim = float(os.popen('grep "SSIM Mean" log_30s_%.2f_%d.txt' % ((roi/100.0), qp_delta)).read().split()[4].split(":")[1])
		dssim = ((1.0 / ssim) - 1)
		bitrate_matrix[roi/5][qp_delta-1] = bitrate
		dssim_matrix[roi/5][qp_delta-1] = dssim

np.savetxt("bitrate_static_roi.csv",bitrate_matrix,delimiter=",",fmt="%.5f")
np.savetxt("dssim_static_roi.csv",dssim_matrix,delimiter=",",fmt="%.5f")