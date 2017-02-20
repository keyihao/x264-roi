import subprocess, os, datetime, sys
import numpy as np

bitrate_target_inmbps = float(sys.argv[1])

psi_list = [(1,1)]
total_exp_num = len(psi_list) + 2
video_length_inseconds = 300.0

folder_name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+"_experiment"

os.makedirs(".\\data\\"+folder_name)

for game_str in ['nfs']:
	game_folder = ".\\data\\"+folder_name+"\\"+game_str
	os.makedirs(game_folder)
	video_folder = ".\\data\\"+folder_name+"\\"+game_str+"\\video"
	detaillog_folder = ".\\data\\"+folder_name+"\\"+game_str+"\\detaillog"
	os.makedirs(video_folder)
	os.makedirs(detaillog_folder)

	averagetime_matrix = np.zeros(shape=(1,total_exp_num))
	averagessim_matrix = np.zeros(shape=(1,total_exp_num))
	averagebitrate_matrix = np.zeros(shape=(1,total_exp_num))

	input_yuv_filepath = "F:\\x264-roi\\"+game_str+"_5min_720p.yuv"
	output_yuv_filepath = ".\\data\\temp.yuv"

	#find the closest crf
	crf_factor = 25
	final_crf_factor = 0
	min_bitrate_gap = 10000
	crf_sizes = None
	crf_average_time = None

	while True:
		output_h264_filepath = video_folder+"\\"+game_str+"_crf_5min.h264"

		encoder_args = "crf 1280x720 0.1 %d %s %s" % (crf_factor, input_yuv_filepath, output_h264_filepath)
		print encoder_args
		s = subprocess.Popen(encoder_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out = s.communicate()

		file_size = os.path.getsize(output_h264_filepath)
		average_bitrate = file_size * 8 / video_length_inseconds / 1024.0 / 1024.0
		print("average bitrate %f"%average_bitrate)

		if abs(average_bitrate - bitrate_target_inmbps) < min_bitrate_gap:
			min_bitrate_gap = abs(average_bitrate - bitrate_target_inmbps)
			final_crf_factor = crf_factor
			crf_sizes = [string.split()[4] for string in out[1].split('\r\n') if (string.startswith('Frame Index'))]
			crf_average_time = [float(string.split()[1]) for string in out[1].split('\r\n') if (string.startswith('AverageTime'))][0]
		else:
			detailframesize_filepath = detaillog_folder+"\\framesize_crf_"+"%d.log"%(final_crf_factor)
			detailframesize_file = open(detailframesize_filepath,'w')
			for size in crf_sizes:
				detailframesize_file.write("%s\n" % size)

			averagetime_matrix[0][0] = crf_average_time

			file_size = os.path.getsize(output_h264_filepath)
			average_bitrate = file_size * 8 / video_length_inseconds / 1024.0 / 1024.0
			print average_bitrate
			averagebitrate_matrix[0][0] = average_bitrate

			ffmpeg_args = ".\\tools\\ffmpeg.exe -i "+output_h264_filepath+" -c:v rawvideo -pix_fmt yuv420p "+output_yuv_filepath
			s = subprocess.Popen(ffmpeg_args, shell=True, stdout=subprocess.PIPE)
			out = s.communicate()

			ssim_args = ".\\tools\\psnr.exe 1280 720 420 "+input_yuv_filepath+" "+output_yuv_filepath+" ssim"
			s = subprocess.Popen(ssim_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out = s.communicate()

			ssims = out[0].split('\r\n')
			detailssim_filepath = detaillog_folder+"\\ssim_crf_"+"_%d.log"%(final_crf_factor)
			detailssim_file = open(detailssim_filepath,'w')
			for ssim in ssims:
				detailssim_file.write("%s\n" % ssim)

			average_ssim = np.mean([float(ssim) for ssim in ssims[:-1]])
			#average_ssim = out[1].split()[-3]
			print average_ssim
			averagessim_matrix[0][0] = average_ssim

			os.remove(output_yuv_filepath)
			break

		if (average_bitrate > bitrate_target_inmbps):
			crf_factor = crf_factor + 1
		else:
			crf_factor = crf_factor - 1

	#vbr
	output_h264_filepath = video_folder+"\\"+game_str+"_vbr_5min.h264"
	encoder_args = "vbr 1280x720 0.1 %d %s %s" % (bitrate_target_inmbps, input_yuv_filepath, output_h264_filepath)
	print encoder_args
	s = subprocess.Popen(encoder_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out = s.communicate()

	vbr_sizes = [string.split()[4] for string in out[1].split('\r\n') if (string.startswith('Frame Index'))]
	detailframesize_filepath = detaillog_folder+"\\framesize_vbr.log"
	detailframesize_file = open(detailframesize_filepath,'w')
	for size in vbr_sizes:
		detailframesize_file.write("%s\n" % size)

	vbr_average_time = [float(string.split()[1]) for string in out[1].split('\r\n') if (string.startswith('AverageTime'))][0]
	print vbr_average_time
	averagetime_matrix[0][1] = vbr_average_time

	vbr_file_size = os.path.getsize(output_h264_filepath)
	vbr_average_bitrate = vbr_file_size * 8 / video_length_inseconds / 1024.0 / 1024.0
	print vbr_average_bitrate
	averagebitrate_matrix[0][1] = vbr_average_bitrate

	ffmpeg_args = ".\\tools\\ffmpeg.exe -i "+output_h264_filepath+" -c:v rawvideo -pix_fmt yuv420p "+output_yuv_filepath
	s = subprocess.Popen(ffmpeg_args, shell=True, stdout=subprocess.PIPE)
	out = s.communicate()

	ssim_args = ".\\tools\\psnr.exe 1280 720 420 "+input_yuv_filepath+" "+output_yuv_filepath+" ssim"
	s = subprocess.Popen(ssim_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out = s.communicate()

	vbr_ssims = out[0].split('\r\n')
	detailssim_filepath = detaillog_folder+"\\ssim_vbr.log"
	detailssim_file = open(detailssim_filepath,'w')
	for ssim in vbr_ssims:
		detailssim_file.write("%s\n" % ssim)

	vbr_average_ssim = np.mean([float(ssim) for ssim in vbr_ssims[:-1]])
	#average_ssim = out[1].split()[-3]
	print vbr_average_ssim
	averagessim_matrix[0][1] = vbr_average_ssim

	os.remove(output_yuv_filepath)

	pc_count = 0
	#p_controller
	for (psir, psid) in psi_list:
		pc_count = pc_count + 1
		output_h264_filepath = video_folder+"\\"+game_str+"_pc_5min_%d_%d"%(psir,psid)+".h264"
		encoder_args = "p_controller 1280x720 0.1 1 1 %s %s %f %d %d" % (input_yuv_filepath, output_h264_filepath, bitrate_target_inmbps, psir, psid)

		print encoder_args
		s = subprocess.Popen(encoder_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out = s.communicate()

		pc_sizes = [string.split()[4] for string in out[1].split('\r\n') if (string.startswith('Frame Index'))]
		detailframesize_filepath = detaillog_folder+"\\framesize_pc_%d_%d.log"%(psir,psid)
		detailframesize_file = open(detailframesize_filepath,'w')
		for size in pc_sizes:
			detailframesize_file.write("%s\n" % size)

		pc_roi_sizes = [string.split()[1] for string in out[1].split('\r\n') if (string.startswith('R(k)'))]
		detailroisizes_filepath = detaillog_folder+"\\roisize_pc_%d_%d.log"%(psir,psid)
		detailroisizes_file = open(detailroisizes_filepath,'w')
		for size in pc_roi_sizes:
			detailroisizes_file.write("%s\n" % size)

		pc_qpdeltas = [string.split()[3] for string in out[1].split('\r\n') if (string.startswith('R(k)'))]
		detailqpdelta_filepath = detaillog_folder+"\\qpdelta_pc_%d_%d.log"%(psir,psid)
		detailqpdelta_file = open(detailqpdelta_filepath,'w')
		for size in pc_qpdeltas:
			detailqpdelta_file.write("%s\n" % size)

		pc_average_time = [float(string.split()[1]) for string in out[1].split('\r\n') if (string.startswith('AverageTime'))][0]
		print pc_average_time
		averagetime_matrix[0][pc_count+1] = pc_average_time

		pc_file_size = os.path.getsize(output_h264_filepath)
		pc_average_bitrate = pc_file_size * 8 / video_length_inseconds / 1024.0 / 1024.0
		print pc_average_bitrate
		averagebitrate_matrix[0][pc_count+1] = pc_average_bitrate

		ffmpeg_args = ".\\tools\\ffmpeg.exe -i "+output_h264_filepath+" -c:v rawvideo -pix_fmt yuv420p "+output_yuv_filepath
		s = subprocess.Popen(ffmpeg_args, shell=True, stdout=subprocess.PIPE)
		out = s.communicate()

		ssim_args = ".\\tools\\psnr.exe 1280 720 420 "+input_yuv_filepath+" "+output_yuv_filepath+" ssim"
		s = subprocess.Popen(ssim_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out = s.communicate()

		pc_ssims = out[0].split('\r\n')
		detailssim_filepath = detaillog_folder+"\\ssim_pc_%d_%d.log"%(psir,psid)
		detailssim_file = open(detailssim_filepath,'w')
		for ssim in pc_ssims:
			detailssim_file.write("%s\n" % ssim)

		pc_average_ssim = np.mean([float(ssim) for ssim in pc_ssims[:-1]])
		#average_ssim = out[1].split()[-3]
		print pc_average_ssim
		averagessim_matrix[0][pc_count+1] = pc_average_ssim

		os.remove(output_yuv_filepath)


	np.savetxt(game_folder+"\\time.csv",averagetime_matrix,delimiter=",",fmt="%.5f")
	np.savetxt(game_folder+"\\ssim.csv",averagessim_matrix,delimiter=",",fmt="%.5f")
	np.savetxt(game_folder+"\\bitrate.csv",averagebitrate_matrix,delimiter=",",fmt="%.5f")
