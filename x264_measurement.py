import subprocess, os, datetime
import numpy as np

folder_name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

os.makedirs(".\\data\\"+folder_name)

for game_str in ['nfs','cv','bo3']:
	game_folder = ".\\data\\"+folder_name+"\\"+game_str
	os.makedirs(game_folder)
	video_folder = ".\\data\\"+folder_name+"\\"+game_str+"\\video"
	detaillog_folder = ".\\data\\"+folder_name+"\\"+game_str+"\\detaillog"
	os.makedirs(video_folder)
	os.makedirs(detaillog_folder)

	averagetime_matrix = np.zeros(shape=(21,10))
	averagessim_matrix = np.zeros(shape=(21,10))
	averagebitrate_matrix = np.zeros(shape=(21,10))

	input_yuv_filepath = "F:\\x264-roi\\"+game_str+"_30s_720p.yuv"
	output_yuv_filepath = ".\\data\\temp.yuv"

	for roi in xrange(0,105,5):
		for qp_delta in xrange(1,11):
			output_h264_filepath = video_folder+"\\"+game_str+"_30s_"+("%.2f_%d.h264" % ((roi/100.0), qp_delta))

			encoder_args = "static_roi.exe 1280x720 %.2f %d %s %s" % ((roi/100.0), qp_delta, input_yuv_filepath, output_h264_filepath)
			#encoder_args = ".\\bin\\x64\\Release\\NvEncoder.exe -i "+input_yuv_filepath+" -o "+output_h264_filepath+" -size 1280 720 -codec 0 -rcmode 1 -targetQuality 23 -roisize "+("%.2f" % (roi/100.0)) + " -qpdelta "+str(qp_delta)
			print encoder_args
			s = subprocess.Popen(encoder_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out = s.communicate()

			sizes = [string.split()[4] for string in out[1].split('\r\n') if (string.startswith('Frame Index'))]
			detailframesize_filepath = detaillog_folder+"\\framesize_"+"%.2f_%d.log"%((roi/100.0), qp_delta)
			detailframesize_file = open(detailframesize_filepath,'w')
			for size in sizes:
				detailframesize_file.write("%s\n" % size)

			average_time = [float(string.split()[1])*1000 for string in out[1].split('\r\n') if (string.startswith('TotalTimeElapseAverage'))][0]
			print average_time
			averagetime_matrix[roi/5][qp_delta-1] = average_time

			file_size = os.path.getsize(output_h264_filepath)
			average_bitrate = file_size * 8 / 30.0 / 1024.0 / 1024.0
			print average_bitrate
			averagebitrate_matrix[roi/5][qp_delta-1] = average_bitrate

			ffmpeg_args = ".\\tools\\ffmpeg.exe -i "+output_h264_filepath+" -c:v rawvideo -pix_fmt yuv420p "+output_yuv_filepath
			s = subprocess.Popen(ffmpeg_args, shell=True, stdout=subprocess.PIPE)
			out = s.communicate()

			ssim_args = ".\\tools\\psnr.exe 1280 720 420 "+input_yuv_filepath+" "+output_yuv_filepath+" ssim"
			s = subprocess.Popen(ssim_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out = s.communicate()

			ssims = out[0].split('\r\n')
			detailssim_filepath = detaillog_folder+"\\ssim_"+"%.2f_%d.log"%((roi/100.0), qp_delta)
			detailssim_file = open(detailssim_filepath,'w')
			for ssim in ssims:
				detailssim_file.write("%s\n" % ssim)

			average_ssim = np.mean([float(ssim) for ssim in ssims[:-1]])
			#average_ssim = out[1].split()[-3]
			print average_ssim
			averagessim_matrix[roi/5][qp_delta-1] = average_ssim

			os.remove(output_yuv_filepath)

	np.savetxt(game_folder+"\\time.csv",averagetime_matrix,delimiter=",",fmt="%.5f")
	np.savetxt(game_folder+"\\ssim.csv",averagessim_matrix,delimiter=",",fmt="%.5f")
	np.savetxt(game_folder+"\\bitrate.csv",averagebitrate_matrix,delimiter=",",fmt="%.5f")