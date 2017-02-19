for roi in xrange(0,105,5):
	for qp_delta in xrange(1,11):
		print 'static_roi.exe 1280x720 %.2f %d nfs_30s.yuv nfs_30s_%.2f_%d.h264 2>log_nfs_30s_%.2f_%d.txt' % ((roi/100.0), qp_delta, (roi/100.0), qp_delta, (roi/100.0), qp_delta)